import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./lib/auth";
import { ToastProvider } from "./lib/toast";
import { AppShell } from "./components/layout/AppShell";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ChatPage } from "./pages/ChatPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { AgentsPage } from "./pages/AgentsPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { ApiKeysPage } from "./pages/ApiKeysPage";

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<AppShell />}>
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/agents" element={<AgentsPage />} />
              <Route path="/knowledge" element={<KnowledgePage />} />
              <Route path="/keys" element={<ApiKeysPage />} />
              <Route path="/" element={<Navigate to="/chat" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}
