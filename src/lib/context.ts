import { useOutletContext } from "react-router-dom";
import type { Project } from "../types";

export interface AppOutletContext {
  activeProjectId: string | null;
  projects: Project[];
  refreshProjects: () => void;
}

export function useAppContext(): AppOutletContext {
  return useOutletContext<AppOutletContext>();
}
