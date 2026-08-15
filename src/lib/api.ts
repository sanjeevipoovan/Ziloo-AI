/**
 * Typed API client for the MyAI/Ziloo AI backend. Every function here maps
 * 1:1 to a route in app/api/routes/*.py.
 */
import type {
  Agent,
  ApiErrorShape,
  ApiKeyCreated,
  ApiKeySummary,
  ChatCompletionRequest,
  ChatCompletionResponse,
  Conversation,
  ConversationDetail,
  KnowledgeBase,
  KnowledgeDocument,
  AIModel,
  Project,
  RetrievedChunk,
  User,
} from "../types";

const DEFAULT_BASE_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return localStorage.getItem("ziloo:apiBaseUrl") || DEFAULT_BASE_URL;
}

export function setApiBaseUrl(url: string): void {
  localStorage.setItem("ziloo:apiBaseUrl", url);
}

export class ApiError extends Error {
  code: string;
  status: number;
  requestId?: string;

  constructor(code: string, message: string, status: number, requestId?: string) {
    super(message);
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

export function getToken(): string | null {
  return localStorage.getItem("ziloo:token");
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem("ziloo:token", token);
  else localStorage.removeItem("ziloo:token");
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
}

async function request<T>(path: string, { method = "GET", body, auth = true }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") || "";
  const data: unknown = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    if (res.status === 401) setToken(null);
    const shape = data as Partial<ApiErrorShape>;
    throw new ApiError(
      shape?.error?.code ?? "UNKNOWN",
      shape?.error?.message ?? "Something went wrong",
      res.status,
      shape?.error?.request_id
    );
  }

  return data as T;
}

export const api = {
  register: (email: string, password: string, fullName?: string) =>
    request<User>("/v1/auth/register", {
      method: "POST",
      body: { email, password, full_name: fullName || null },
      auth: false,
    }),

  login: (email: string, password: string) =>
    request<{ access_token: string; expires_in: number }>("/v1/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    }),

  me: () => request<User>("/v1/users/me"),

  listProjects: () => request<Project[]>("/v1/projects"),
  createProject: (name: string, description?: string) =>
    request<Project>("/v1/projects", { method: "POST", body: { name, description: description || null } }),

  listModels: () => request<AIModel[]>("/v1/models"),

  listConversations: (projectId: string) => request<Conversation[]>(`/v1/conversations?project_id=${projectId}`),
  createConversation: (projectId: string, title?: string, agentId?: string) =>
    request<Conversation>(`/v1/conversations?project_id=${projectId}`, {
      method: "POST",
      body: { title: title || null, agent_id: agentId || null },
    }),
  getConversation: (projectId: string, id: string) =>
    request<ConversationDetail>(`/v1/conversations/${id}?project_id=${projectId}`),
  deleteConversation: (projectId: string, id: string) =>
    request<void>(`/v1/conversations/${id}?project_id=${projectId}`, { method: "DELETE" }),

  listAgents: (projectId: string) => request<Agent[]>(`/v1/agents?project_id=${projectId}`),
  createAgent: (projectId: string, data: Partial<Agent>) =>
    request<Agent>(`/v1/agents?project_id=${projectId}`, { method: "POST", body: data }),
  updateAgent: (projectId: string, id: string, data: Partial<Agent>) =>
    request<Agent>(`/v1/agents/${id}?project_id=${projectId}`, { method: "PATCH", body: data }),
  deleteAgent: (projectId: string, id: string) =>
    request<void>(`/v1/agents/${id}?project_id=${projectId}`, { method: "DELETE" }),
  runAgent: (projectId: string, id: string, input: string, conversationId?: string) =>
    request<ChatCompletionResponse>(`/v1/agents/${id}/run?project_id=${projectId}`, {
      method: "POST",
      body: { input, conversation_id: conversationId || null },
    }),

  listKnowledgeBases: (projectId: string) => request<KnowledgeBase[]>(`/v1/knowledge/bases?project_id=${projectId}`),
  createKnowledgeBase: (projectId: string, name: string, description?: string) =>
    request<KnowledgeBase>(`/v1/knowledge/bases?project_id=${projectId}`, {
      method: "POST",
      body: { name, description: description || null },
    }),
  listDocuments: (projectId: string, kbId: string) =>
    request<KnowledgeDocument[]>(`/v1/knowledge/bases/${kbId}/documents?project_id=${projectId}`),
  retrieve: (projectId: string, kbId: string, query: string, topK = 5) =>
    request<RetrievedChunk[]>(`/v1/knowledge/bases/${kbId}/retrieve?project_id=${projectId}`, {
      method: "POST",
      body: { query, top_k: topK },
    }),
  uploadDocument: async (projectId: string, kbId: string, file: File): Promise<KnowledgeDocument> => {
    const form = new FormData();
    form.append("file", file);
    const token = getToken();
    const res = await fetch(`${getApiBaseUrl()}/v1/knowledge/bases/${kbId}/documents?project_id=${projectId}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new ApiError(data?.error?.code ?? "UNKNOWN", data?.error?.message ?? "Upload failed", res.status);
    }
    return data as KnowledgeDocument;
  },

  listApiKeys: (projectId: string) => request<ApiKeySummary[]>(`/v1/projects/${projectId}/api-keys`),
  createApiKey: (projectId: string, name: string, expiresInDays?: number) =>
    request<ApiKeyCreated>(`/v1/projects/${projectId}/api-keys`, {
      method: "POST",
      body: { name, expires_in_days: expiresInDays || null },
    }),
  revokeApiKey: (projectId: string, keyId: string) =>
    request<void>(`/v1/projects/${projectId}/api-keys/${keyId}`, { method: "DELETE" }),

  chatCompletion: (payload: ChatCompletionRequest) =>
    request<ChatCompletionResponse>("/v1/chat/completions", { method: "POST", body: payload }),
};
