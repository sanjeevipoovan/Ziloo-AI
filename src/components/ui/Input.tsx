import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="mb-3.5 flex flex-col gap-1.5">
      <label className="text-xs font-medium text-ink-muted">{label}</label>
      {children}
      {hint && <span className="text-[11px] text-ink-faint">{hint}</span>}
    </div>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-primary ${props.className ?? ""}`}
    />
  );
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={`w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-primary ${props.className ?? ""}`}
    />
  );
}
