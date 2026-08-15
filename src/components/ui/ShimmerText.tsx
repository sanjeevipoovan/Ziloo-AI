import { useEffect, useState } from "react";

/** LoadingState-inspired shimmering label, in plain CSS (see .text-shimmer
 * + animate-shimmer in index.css / tailwind.config.ts). */
export function ShimmerText({ children }: { children: string }) {
  return (
    <span className="text-shimmer inline-block animate-shimmer bg-[length:200%_100%] text-sm font-medium">
      {children}
    </span>
  );
}

/** LoadingState-inspired live elapsed timer, mono tabular figures. */
export function ElapsedTimer({ running }: { running: boolean }) {
  const [tenths, setTenths] = useState(0);

  useEffect(() => {
    if (!running) {
      setTenths(0);
      return;
    }
    const id = setInterval(() => setTenths((t) => t + 1), 100);
    return () => clearInterval(id);
  }, [running]);

  const seconds = tenths / 10;
  const label = seconds < 60 ? `${seconds.toFixed(1)}s` : `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(1)}s`;

  return <span className="font-mono text-xs tabular-nums text-ink-faint">{label}</span>;
}
