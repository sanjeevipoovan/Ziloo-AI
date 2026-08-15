import { useEffect, useRef, useState } from "react";
import { Button } from "../ui/Button";
import type { AIModel, KnowledgeBase } from "../../types";

interface ComposerProps {
  models: AIModel[];
  knowledgeBases: KnowledgeBase[];
  onSend: (input: string, model: string, knowledgeBaseId: string | null) => void;
  disabled: boolean;
}

export function Composer({ models, knowledgeBases, onSend, disabled }: ComposerProps) {
  const [value, setValue] = useState("");
  const [model, setModel] = useState("auto");
  const [kbId, setKbId] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  function handleSend() {
    if (!value.trim() || disabled) return;
    onSend(value.trim(), model, kbId || null);
    setValue("");
  }

  return (
    <div className="border-t border-border-soft p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs"
        >
          <option value="auto">Auto-route</option>
          {models.map((m) => (
            <option key={m.id} value={m.name}>
              {m.name}
            </option>
          ))}
        </select>
        {knowledgeBases.length > 0 && (
          <select
            value={kbId}
            onChange={(e) => setKbId(e.target.value)}
            className="rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs"
          >
            <option value="">No knowledge base</option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="flex items-end gap-2 rounded-2xl border border-border bg-surface p-2 pl-4 focus-within:border-primary/50">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Message Ziloo AI…"
          rows={1}
          className="max-h-40 min-h-[24px] flex-1 resize-none bg-transparent py-2 text-sm outline-none placeholder:text-ink-faint"
        />
        <Button variant="shine" size="md" disabled={!value.trim() || disabled} onClick={handleSend} className="shrink-0">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 19V5M5 12l7-7 7 7" />
          </svg>
        </Button>
      </div>
      <p className="mt-1.5 text-[11px] text-ink-faint">Enter to send · Shift+Enter for a new line</p>
    </div>
  );
}
