import { useEffect, useState, type FormEvent } from "react";
import { useAppContext } from "../lib/context";
import { api, ApiError } from "../lib/api";
import { useToast } from "../lib/toast";
import type { ApiKeyCreated, ApiKeySummary } from "../types";
import { Button } from "../components/ui/Button";
import { Field, TextInput } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";

export function ApiKeysPage() {
  const { activeProjectId } = useAppContext();
  const { push } = useToast();
  const [keys, setKeys] = useState<ApiKeySummary[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [revealed, setRevealed] = useState<ApiKeyCreated | null>(null);

  useEffect(() => {
    if (activeProjectId) api.listApiKeys(activeProjectId).then(setKeys).catch(() => {});
  }, [activeProjectId]);

  async function handleRevoke(id: string) {
    if (!activeProjectId) return;
    try {
      await api.revokeApiKey(activeProjectId, id);
      setKeys((k) => k.map((key) => (key.id === id ? { ...key, revoked_at: new Date().toISOString() } : key)));
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not revoke key", "error");
    }
  }

  if (!activeProjectId) return <p className="p-6 text-sm text-ink-muted">Select or create a project first.</p>;

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold">API keys</h1>
          <p className="mt-1 text-sm text-ink-muted">For calling this project's chat completions from an external app.</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>+ New key</Button>
      </div>

      <div className="flex flex-col gap-2">
        {keys.map((k) => (
          <div key={k.id} className="flex items-center justify-between rounded-xl border border-border bg-surface px-4 py-3">
            <div>
              <p className="text-sm font-medium">{k.name}</p>
              <p className="font-mono text-xs text-ink-faint">myai_{k.key_prefix}…</p>
            </div>
            {k.revoked_at ? (
              <span className="text-xs text-danger">Revoked</span>
            ) : (
              <Button size="sm" variant="danger" onClick={() => handleRevoke(k.id)}>
                Revoke
              </Button>
            )}
          </div>
        ))}
        {keys.length === 0 && <p className="py-8 text-center text-sm text-ink-muted">No API keys yet.</p>}
      </div>

      {showCreate && (
        <CreateKeyModal
          projectId={activeProjectId}
          onClose={() => setShowCreate(false)}
          onCreated={(created) => {
            setKeys((k) => [...k, { ...created, created_at: new Date().toISOString(), revoked_at: null, last_used_at: null }]);
            setShowCreate(false);
            setRevealed(created);
          }}
        />
      )}
      {revealed && (
        <Modal title="Save this key now" onClose={() => setRevealed(null)}>
          <p className="mb-3 text-sm text-ink-muted">This is the only time the full key is shown.</p>
          <div className="mb-3 break-all rounded-lg border border-dashed border-border bg-surface-2 p-3 font-mono text-xs">{revealed.key}</div>
          <div className="mb-4 rounded-lg bg-warning/10 px-3 py-2 text-xs text-warning">
            You won't be able to see this key again after closing this dialog.
          </div>
          <Button
            className="w-full"
            onClick={() => {
              navigator.clipboard.writeText(revealed.key);
              push("Copied to clipboard", "success");
            }}
          >
            Copy key
          </Button>
        </Modal>
      )}
    </div>
  );
}

function CreateKeyModal({
  projectId,
  onClose,
  onCreated,
}: {
  projectId: string;
  onClose: () => void;
  onCreated: (k: ApiKeyCreated) => void;
}) {
  const { push } = useToast();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      onCreated(await api.createApiKey(projectId, name));
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not create key", "error");
      setBusy(false);
    }
  }

  return (
    <Modal title="New API key" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <Field label="Name">
          <TextInput required value={name} onChange={(e) => setName(e.target.value)} placeholder="Production server" />
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy}>
            {busy ? "Creating…" : "Create key"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
