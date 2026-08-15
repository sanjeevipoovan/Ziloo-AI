/**
 * TypeScript mirror of the backend's Pydantic schemas (app/schemas/*.py).
 * Keep these in sync if the API changes shape.
 */

export type Role = "system" | "user" | "assistant" | "tool";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number | null;
  stream?: boolean;
  conversation_id?: string | null;
  project_id?: string | null;
  knowledge_base_id?: string | null;
}

export interface ChatUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatChoice {
  index: number;
  message: ChatMessage;
  finish_reason: string | null;
}

export interface ChatCompletionResponse {
  id: string;
  request_id: string;
  model: string;
  provider: string;
  choices: ChatChoice[];
  usage: ChatUsage;
  conversation_id?: string | null;
}

/** Shape of each SSE `data:` event emitted by POST /v1/chat/completions?stream=true */
export type StreamEvent =
  | { type: "model_selected"; model: string; reason: string }
  | { type: "retrieval_started" }
  | { type: "retrieval_completed"; chunks_found: number }
  | { type: "response_started"; request_id: string }
  | { type: "delta"; content: string }
  | {
      type: "response_completed";
      finish_reason: string;
      usage?: { prompt_tokens: number | null; completion_tokens: number | null } | null;
    }
  | { type: "error"; message: string; request_id: string }
  | { type: "done" };

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface AIModel {
  id: string;
  name: string;
  model_type: string;
  context_window: number;
  capabilities: string[];
  is_active: boolean;
}

export interface Conversation {
  id: string;
  title: string | null;
  agent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface Agent {
  id: string;
  name: string;
  description: string | null;
  system_prompt: string;
  model_policy: string;
  temperature: number;
  max_tokens: number;
  max_steps: number;
  memory_enabled: boolean;
  tool_config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: "pending" | "processing" | "ready" | "failed";
  created_at: string;
}

export interface RetrievedChunk {
  document_id: string;
  chunk_index: number;
  content: string;
  score: number;
}

export interface ApiKeySummary {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  created_at: string;
  expires_at: string | null;
  revoked_at: string | null;
  last_used_at: string | null;
}

export interface ApiKeyCreated extends Omit<ApiKeySummary, "created_at" | "revoked_at" | "last_used_at"> {
  key: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ApiErrorShape {
  error: { code: string; message: string; request_id?: string };
}
