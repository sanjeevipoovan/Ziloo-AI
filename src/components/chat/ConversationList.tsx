import type { Conversation } from "../../types";

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export function ConversationList({ conversations, activeId, onSelect, onNew, onDelete }: Props) {
  return (
    <div className="flex h-full w-72 shrink-0 flex-col border-r border-border-soft p-3">
      <button
        onClick={onNew}
        className="mb-3 flex items-center justify-center gap-2 rounded-lg border border-dashed border-border py-2 text-sm text-ink-muted hover:border-primary hover:text-primary"
      >
        + New conversation
      </button>
      <div className="flex flex-1 flex-col gap-1 overflow-y-auto">
        {conversations.length === 0 && (
          <p className="px-2 py-6 text-center text-xs text-ink-faint">No conversations yet. Say hello.</p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={`group flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm ${
              activeId === c.id ? "bg-surface-2 text-ink" : "text-ink-muted hover:bg-surface-2/60"
            }`}
          >
            <span className="truncate">{c.title || "Untitled conversation"}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
              className="hidden shrink-0 text-ink-faint hover:text-danger group-hover:block"
              aria-label="Delete conversation"
            >
              &#10005;
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
