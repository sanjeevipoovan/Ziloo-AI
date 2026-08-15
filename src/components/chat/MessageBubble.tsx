import type { Message } from "../../types";
import { Badge, modelTone } from "../ui/Badge";

export function MessageBubble({ message, streaming }: { message: Message; streaming?: boolean }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70ch] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-white">
          {message.content}
        </div>
      </div>
    );
  }

  const accentClass =
    message.model === "kimi-k3" ? "border-l-kimi" : message.model === "glm-5.2" ? "border-l-glm" : "border-l-surface-3";

  return (
    <div className="flex flex-col items-start gap-1">
      {message.model && <Badge tone={modelTone(message.model)}>{message.model}</Badge>}
      <div
        className={`max-w-[70ch] whitespace-pre-wrap rounded-2xl rounded-bl-md border-l-[3px] ${accentClass} bg-surface px-4 py-2.5 text-sm leading-relaxed`}
      >
        {message.content}
        {streaming && (
          <span className="ml-0.5 inline-block h-[15px] w-[7px] translate-y-0.5 animate-blink bg-ink-muted align-text-bottom" />
        )}
      </div>
    </div>
  );
}
