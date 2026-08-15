import { useState, type FormEvent } from "react";
import { useAppContext } from "../lib/context";
import { api, ApiError } from "../lib/api";
import { useToast } from "../lib/toast";
import { Button } from "../components/ui/Button";
import { Field, TextInput } from "../components/ui/Input";

export function ProjectsPage() {
  const { projects, refreshProjects } = useAppContext();
  const { push } = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.createProject(name, description || undefined);
      setName("");
      setDescription("");
      refreshProjects();
      push("Project created", "success");
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not create project", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-6">
        <h1 className="font-display text-xl font-semibold">Projects</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Projects scope everything else — agents, conversations, knowledge bases, and API keys.
        </p>
      </div>

      <div className="mb-6 rounded-2xl border border-border bg-surface p-5">
        <h2 className="mb-3 text-sm font-medium">New project</h2>
        <form onSubmit={handleCreate} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Field label="Name">
              <TextInput required value={name} onChange={(e) => setName(e.target.value)} placeholder="Production" />
            </Field>
          </div>
          <div className="flex-1">
            <Field label="Description" hint="Optional">
              <TextInput value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What is this for?" />
            </Field>
          </div>
          <Button type="submit" disabled={busy} className="mb-3.5 shrink-0">
            Create
          </Button>
        </form>
      </div>

      <div className="flex flex-col gap-2">
        {projects.map((p) => (
          <div key={p.id} className="flex items-center justify-between rounded-xl border border-border bg-surface px-4 py-3">
            <div>
              <p className="text-sm font-medium">{p.name}</p>
              {p.description && <p className="text-xs text-ink-muted">{p.description}</p>}
            </div>
            <span className="font-mono text-[11px] text-ink-faint">{p.id.slice(0, 8)}</span>
          </div>
        ))}
        {projects.length === 0 && <p className="py-8 text-center text-sm text-ink-muted">No projects yet.</p>}
      </div>
    </div>
  );
}
