import type { ReactNode } from "react";

type Tone = "glm" | "kimi" | "success" | "warning" | "danger" | "neutral";

const tones: Record<Tone, string> = {
  glm: "bg-glm/10 text-glm",
  kimi: "bg-kimi/10 text-kimi",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
  neutral: "bg-surface-3 text-ink-muted",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

/** Ties a model name to its accent color - the one signature idea in this
 * app: which model answered a message is always visible, never hidden. */
export function modelTone(modelName?: string | null): Tone {
  if (modelName === "kimi-k3") return "kimi";
  if (modelName === "glm-5.2") return "glm";
  return "neutral";
}
