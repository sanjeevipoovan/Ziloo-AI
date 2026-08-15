import { useEffect, useState } from "react";
import { ElapsedTimer, ShimmerText } from "../ui/ShimmerText";
import { Badge, modelTone } from "../ui/Badge";

/**
 * Rebuilt from the pasted "ThinkingState" reference, but wired to this
 * app's actual SSE events (model_selected, retrieval_started/completed)
 * instead of scripted demo content - so what you see here is really what
 * the router and retriever just did, not a canned animation.
 */
export interface TraceState {
  phase: "idle" | "routing" | "retrieving" | "generating" | "done" | "error";
  model?: string;
  reason?: string;
  chunksFound?: number;
  errorMessage?: string;
}

export function RoutingTrace({ trace }: { trace: TraceState }) {
  const [expanded, setExpanded] = useState(true);
  const working = !["idle", "done", "error"].includes(trace.phase);

  useEffect(() => {
    if (trace.phase === "done") {
      const t = setTimeout(() => setExpanded(false), 900);
      return () => clearTimeout(t);
    }
    if (trace.phase === "routing") setExpanded(true);
  }, [trace.phase]);

  if (trace.phase === "idle") return null;

  const steps = [
    { key: "routing", label: "Choosing a model", done: Boolean(trace.model) },
    ...(trace.chunksFound !== undefined
      ? [
          {
            key: "retrieving",
            label: `Searched the knowledge base — ${trace.chunksFound} chunk${trace.chunksFound === 1 ? "" : "s"} found`,
            done: trace.phase !== "retrieving",
          },
        ]
      : []),
    { key: "generating", label: "Writing the response", done: trace.phase === "done" },
  ];

  return (
    <div className="mb-1 max-w-xl">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="-mx-1.5 flex items-center gap-2 rounded-lg px-1.5 py-1 hover:bg-surface-2"
      >
        <SparkIcon spinning={working} />
        {working ? (
          <ShimmerText>
            {trace.phase === "routing" ? "Routing" : trace.phase === "retrieving" ? "Searching the knowledge base" : "Generating"}
          </ShimmerText>
        ) : trace.phase === "error" ? (
          <span className="text-sm font-medium text-danger">Something went wrong</span>
        ) : (
          <span className="text-sm font-medium text-ink-muted">
            Answered by <span className={trace.model === "kimi-k3" ? "text-kimi" : "text-glm"}>{trace.model}</span>
          </span>
        )}
        {working && <ElapsedTimer running={working} />}
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          className={`text-ink-faint transition-transform duration-300 ${expanded ? "rotate-180" : ""}`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      <div className={`grid transition-all duration-300 ${expanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}>
        <div className="overflow-hidden">
          <div className="ml-[9px] mt-1 flex flex-col gap-1 border-l border-border-soft py-1 pl-4">
            {steps.map((s) => (
              <div key={s.key} className="flex items-center gap-2 text-xs text-ink-muted">
                {s.done ? (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                ) : (
                  <span className="h-2.5 w-2.5 animate-spin rounded-full border-[1.5px] border-border-soft border-t-ink-muted" />
                )}
                {s.label}
              </div>
            ))}
            {trace.model && (
              <div className="mt-0.5 flex items-center gap-1.5">
                <Badge tone={modelTone(trace.model)}>{trace.model}</Badge>
                {trace.reason && <span className="text-[11px] text-ink-faint">{trace.reason}</span>}
              </div>
            )}
            {trace.phase === "error" && trace.errorMessage && <div className="text-xs text-danger">{trace.errorMessage}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

function SparkIcon({ spinning }: { spinning: boolean }) {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill={spinning ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.5"
      className="text-ink-muted"
    >
      <path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z" />
    </svg>
  );
}
