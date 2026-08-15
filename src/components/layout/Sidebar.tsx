import { NavLink } from "react-router-dom";
import { useAuth } from "../../lib/auth";

const NAV = [
  { to: "/chat", label: "Chat", icon: ChatIcon },
  { to: "/agents", label: "Agents", icon: AgentIcon },
  { to: "/knowledge", label: "Knowledge", icon: KnowledgeIcon },
  { to: "/keys", label: "API Keys", icon: KeyIcon },
  { to: "/projects", label: "Projects", icon: ProjectIcon },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuth();

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={onClose} />}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-56 shrink-0 flex-col border-r border-border bg-surface p-3 transition-transform duration-200 md:static md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-5 flex items-center gap-2 px-2 py-1">
          <LogoMark />
          <span className="font-display text-lg font-bold">Ziloo AI</span>
        </div>

        <nav className="flex flex-col gap-0.5">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm ${
                  isActive ? "bg-primary/10 font-medium text-primary" : "text-ink-muted hover:bg-surface-2 hover:text-ink"
                }`
              }
            >
              <Icon />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto border-t border-border-soft pt-3">
          <div className="flex items-center gap-2 px-2.5 py-1.5">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-surface-3 text-[11px] font-semibold">
              {user?.email?.[0]?.toUpperCase() ?? "?"}
            </div>
            <span className="truncate text-xs text-ink-muted">{user?.email}</span>
          </div>
          <button
            onClick={logout}
            className="mt-1 w-full rounded-lg px-2.5 py-2 text-left text-sm text-ink-muted hover:bg-surface-2 hover:text-danger"
          >
            Sign out
          </button>
        </div>
      </aside>
    </>
  );
}

function LogoMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="9" cy="12" r="5.5" fill="#4fd1c5" />
      <circle cx="15" cy="12" r="5.5" fill="#f2a65a" fillOpacity="0.85" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}
function AgentIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4M8 16h.01M16 16h.01" />
    </svg>
  );
}
function KnowledgeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  );
}
function KeyIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="7.5" cy="15.5" r="5.5" />
      <path d="m21 2-9.6 9.6M15.5 7.5 18 10M18.5 5 21 7.5" />
    </svg>
  );
}
function ProjectIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    </svg>
  );
}
