import { useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { useAuth } from "../../lib/auth";
import { api, ApiError } from "../../lib/api";
import type { Project } from "../../types";
import { useToast } from "../../lib/toast";
import { ShimmerText } from "../ui/ShimmerText";
import type { AppOutletContext } from "../../lib/context";

export function AppShell() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const { push } = useToast();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(() =>
    localStorage.getItem("ziloo:activeProjectId")
  );

  useEffect(() => {
    if (!loading && !user) navigate("/login", { replace: true });
  }, [loading, user, navigate]);

  const refreshProjects = () => {
    api
      .listProjects()
      .then((list) => {
        setProjects(list);
        if (!localStorage.getItem("ziloo:activeProjectId") && list.length > 0) {
          selectProject(list[0].id);
        }
      })
      .catch((err) => push(err instanceof ApiError ? err.message : "Could not load projects", "error"));
  };

  useEffect(() => {
    if (user) refreshProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  function selectProject(id: string) {
    setActiveProjectId(id);
    localStorage.setItem("ziloo:activeProjectId", id);
  }

  if (loading) return <FullScreenLoader />;
  if (!user) return null;

  const outletContext: AppOutletContext = { activeProjectId, projects, refreshProjects };

  return (
    <div className="flex min-h-screen">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-4 border-b border-border-soft px-5 py-3">
          <button className="text-ink-muted md:hidden" onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M3 6h18M3 12h18M3 18h18" />
            </svg>
          </button>
          {projects.length > 0 ? (
            <select
              value={activeProjectId ?? ""}
              onChange={(e) => selectProject(e.target.value)}
              className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          ) : (
            <span className="text-sm text-ink-muted">No projects yet — create one in Projects</span>
          )}
        </header>
        <main className="min-h-0 flex-1 overflow-y-auto">
          <Outlet context={outletContext} />
        </main>
      </div>
    </div>
  );
}

function FullScreenLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <ShimmerText>Loading Ziloo AI…</ShimmerText>
    </div>
  );
}
