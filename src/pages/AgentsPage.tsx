import { useEffect, useState, type FormEvent } from "react";
import { useAppContext } from "../lib/context";
import { api, ApiError } from "../lib/api";
import { useToast } from "../lib/toast";
import type { Agent } from "../types";
import { Button } from "../components/ui/Button";
import { Field, TextArea, TextInput } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";

export function AgentsPage() {
  const { activeProjectId } = useAppContext();
  const { push } = useToast();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [running, setRunning] = useState<Agent | null>(null);

  useEffect(() => {
    if (activeProjectId) api.listAgents(activeProjectId).then(setAgents).catch(() => {});
  }, [activeProjectId]);

  async function handleDelete(id: string) {
    if (!activeProjectId) return;
    try {
      await api.deleteAgent(activeProjectId, id);
      setAgents((a) => a.filter((x) => x.id !== id));
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not delete agent", "error");
    }
  }

  if (!activeProjectId) return <p className="p-6 text-sm text-ink-muted">Select or create a project first.</p>;

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold">Agents</h1>
          <p className="mt-1 text-sm text-ink-muted">Configuration, not code — a system prompt and a model policy.</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>+ New agent</Button>
      </div>

      <div className="flex flex-col gap-2">
        {agents.map((a) => (
          <div key={a.id} className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium">{a.name}</p>
                {a.description && <p className="mt-0.5 text-xs text-ink-muted">{a.description}</p>}
                <p className="mt-1.5 line-clamp-2 text-xs text-ink-faint">{a.system_prompt}</p>
              </div>
              <div className="flex shrink-0 gap-1.5">
                <Button size="sm" variant="ghost" onClick={() => setRunning(a)}>
                  Run
                </Button>
                <Button size="sm" variant="danger" onClick={() => handleDelete(a.id)}>
                  Delete
                </Button>
              </div>
            </div>
          </div>
        ))}
        {agents.length === 0 && <p className="py-8 text-center text-sm text-ink-muted">No agents yet.</p>}
      </div>

      {showCreate && (
        <CreateAgentModal
          projectId={activeProjectId}
          onClose={() => setShowCreate(false)}
          onCreated={(agent) => {
            setAgents((a) => [...a, agent]);
            setShowCreate(false);
          }}
        />
      )}
      {running && <RunAgentModal projectId={activeProjectId} agent={running} onClose={() => setRunning(null)} />}
    </div>
  );
}

function CreateAgentModal({
  projectId,
  onClose,
  onCreated,
}: {
  projectId: string;
  onClose: () => void;
  onCreated: (a: Agent) => void;
}) {
  const { push } = useToast();
  const [name, setName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful assistant.");
  const [modelPolicy, setModelPolicy] = useState("auto");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const agent = await api.createAgent(projectId, { name, system_prompt: systemPrompt, model_policy: modelPolicy });
      onCreated(agent);
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not create agent", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="New agent" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <Field label="Name">
          <TextInput required value={name} onChange={(e) => setName(e.target.value)} placeholder="Support bot" />
        </Field>
        <Field label="System prompt">
          <TextArea required rows={4} value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} />
        </Field>
        <Field label="Model policy">
          <select
            value={modelPolicy}
            onChange={(e) => setModelPolicy(e.target.value)}
            className="w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-sm"
          >
            <option value="auto">Auto-route</option>
            <option value="glm-5.2">glm-5.2</option>
            <option value="kimi-k3">kimi-k3</option>
          </select>
        </Field>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy}>
            {busy ? "Creating…" : "Create agent"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function RunAgentModal({ projectId, agent, onClose }: { projectId: string; agent: Agent; onClose: () => void }) {
  const { push } = useToast();
  const [input, setInput] = useState("");
  const [output, setOutput] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleRun() {
    if (!input.trim()) return;
    setBusy(true);
    setOutput(null);
    try {
      const res = await api.runAgent(projectId, agent.id, input.trim());
      setOutput(res.choices[0]?.message.content ?? "");
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Agent run failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={`Run "${agent.name}"`} onClose={onClose}>
      <Field label="Input">
        <TextArea rows={3} value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type a test message…" />
      </Field>
      <Button onClick={handleRun} disabled={busy || !input.trim()} className="w-full">
        {busy ? "Running…" : "Run"}
      </Button>
      {output && <div className="mt-3 whitespace-pre-wrap rounded-lg bg-surface-2 p-3 text-sm">{output}</div>}
    </Modal>
  );
}
