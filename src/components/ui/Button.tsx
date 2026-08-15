import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger" | "shine";
type Size = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

const base =
  "inline-flex items-center justify-center gap-2 rounded-control font-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed active:translate-y-px";

const variants: Record<Variant, string> = {
  primary: "bg-primary text-white hover:bg-primary-hover",
  ghost: "bg-transparent border border-border text-ink hover:bg-surface",
  danger: "bg-transparent border border-danger text-danger hover:bg-danger/10",
  // "Specular button", rebuilt in CSS: a diagonal light sweep that slides
  // across on hover, via a pseudo-layer translated with Tailwind's
  // group-hover - no WebGL/shader dependency needed for the effect to read.
  shine: "group relative overflow-hidden bg-surface-3 text-ink border border-border-soft hover:border-primary/50",
};

const sizes: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2.5 text-sm",
};

export function Button({ variant = "primary", size = "md", className = "", children, ...rest }: ButtonProps) {
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...rest}>
      {variant === "shine" && (
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/15 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-full"
        />
      )}
      {children}
    </button>
  );
}
