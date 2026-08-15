import { useEffect, useRef, useState, type FormEvent } from "react";
import { useAppContext } from "../lib/context";
import { api, ApiError } from "../lib/api";
import { useToast } from "../lib/toast";
import type { KnowledgeBase, KnowledgeDocument, RetrievedChunk } from "../types";
import { Button } from "../components/ui/Button";
import { TextInput } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";

export function KnowledgePage() {
  const { activeProjectId } = useAppContext();
  const { push } = useToast();
  const [bases, setBases] = useState<KnowledgeBase[]>([]);
  const [activeKb, setActiveKb] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [name, setName] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RetrievedChunk[] | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (activeProjectId) api.listKnowledgeBases(activeProjectId).then(setBases).catch(() => {});
  }, [activeProjectId]);

  useEffect(() => {
    if (activeProjectId && activeKb) {
      api.listDocuments(activeProjectId, activeKb.id).then(setDocuments).catch(() => {});
    }
  }, [activeProjectId, activeKb]);

  async function createBase(e: FormEvent) {
    e.preventDefault();
    if (!activeProjectId || !name.trim()) return;
    try {
      const kb = await api.createKnowledgeBase(activeProjectId, name.trim());
      setBases((b) => [...b, kb]);
      setName("");
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not create knowledge base", "error");
    }
  }

  async function uploadFile(file: File) {
    if (!activeProjectId || !activeKb) return;
    try {
      const doc = await api.uploadDocument(activeProjectId, activeKb.id, file);
      setDocuments((d) => [...d, doc]);
      push("Upload started — processing in the background", "success");
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Upload failed", "error");
    }
  }

  async function runQuery(e: FormEvent) {
    e.preventDefault();
    if (!activeProjectId || !activeKb || !query.trim()) return;
    try {
      setResults(await api.retrieve(activeProjectId, activeKb.id, query.trim()));
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Retrieval failed", "error");
    }
  }

  if (!activeProjectId) return <p className="p-6 text-sm text-ink-muted">Select or create a project first.</p>;

  return (
    <div className="mx-auto flex max-w-5xl gap-6 p-6">
      <div className="w-64 shrink-0">
        <h1 className="mb-3 font-display text-lg font-semibold">Knowledge</h1>
        <form onSubmit={createBase} className="mb-4 flex gap-2">
          <TextInput value={name} onChange={(e) => setName(e.target.value)} placeholder="New base name" className="text-xs" />
          <Button type="submit" size="sm">
            Add
          </Button>
        </form>
        <div className="flex flex-col gap-1">
          {bases.map((kb) => (
            <button
              key={kb.id}
              onClick={() => {
                setActiveKb(kb);
                setResults(null);
              }}
              className={`rounded-lg px-3 py-2 text-left text-sm ${
                activeKb?.id === kb.id ? "bg-surface-2 font-medium" : "text-ink-muted hover:bg-surface-2/60"
              }`}
            >
              {kb.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1">
        {!activeKb ? (
          <p className="text-sm text-ink-muted">Pick a knowledge base on the left, or create one.</p>
        ) : (
          <>
            <div className="mb-5 flex items-center justify-between">
              <h2 className="font-medium">{activeKb.name}</h2>
              <div>
                <input
                  ref={fileRef}
                  type="file"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
                />
                <Button size="sm" onClick={() => fileRef.current?.click()}>
                  Upload document
                </Button>
              </div>
            </div>

            <div className="mb-6 flex flex-col gap-2">
              {documents.map((d) => (
                <div key={d.id} className="flex items-center justify-between rounded-lg border border-border bg-surface px-3 py-2 text-sm">
                  <span className="truncate">{d.filename}</span>
                  <StatusBadge status={d.status} />
                </div>
              ))}
              {documents.length === 0 && <p className="text-sm text-ink-muted">No documents uploaded yet.</p>}
            </div>

            <form onSubmit={runQuery} className="mb-3 flex gap-2">
              <TextInput value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Test a retrieval query…" />
              <Button type="submit">Search</Button>
            </form>
            {results && (
              <div className="flex flex-col gap-2">
                {results.map((r, i) => (
                  <div key={i} className="rounded-lg border border-border bg-surface p-3 text-xs">
                    <div className="mb-1 flex justify-between text-ink-faint">
                      <span>chunk {r.chunk_index}</span>
                      <span>score {r.score.toFixed(3)}</span>
                    </div>
                    <p className="text-ink-muted">{r.content}</p>
                  </div>
                ))}
                {results.length === 0 && <p className="text-sm text-ink-muted">No matches.</p>}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: KnowledgeDocument["status"] }) {
  const tone = status === "ready" ? "success" : status === "failed" ? "danger" : "warning";
  return <Badge tone={tone}>{status}</Badge>;
}
