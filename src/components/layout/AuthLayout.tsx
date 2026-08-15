import type { ReactNode } from "react";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="flex min-h-screen items-center justify-center p-6"
      style={{
        background:
          "radial-gradient(circle at 15% 20%, rgba(79,209,197,0.08), transparent 40%), radial-gradient(circle at 85% 80%, rgba(242,166,90,0.08), transparent 40%), #14161f",
      }}
    >
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8">
        <div className="mb-1 flex items-center gap-2">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden>
            <circle cx="9" cy="12" r="5.5" fill="#4fd1c5" />
            <circle cx="15" cy="12" r="5.5" fill="#f2a65a" fillOpacity="0.85" />
          </svg>
          <span className="font-display text-xl font-bold">Ziloo AI</span>
        </div>
        {children}
      </div>
    </div>
  );
}
