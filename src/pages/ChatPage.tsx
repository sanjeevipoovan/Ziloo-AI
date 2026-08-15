import { useEffect, useRef, useState } from "react";
import { useAppContext } from "../lib/context";
import { api, ApiError } from "../lib/api";
import { streamChatCompletion } from "../lib/stream";
import { useToast } from "../lib/toast";
import type { AIModel, Conversation, ConversationDetail, KnowledgeBase, Message } from "../types";
import { ConversationList } from "../components/chat/ConversationList";
import { Composer } from "../components/chat/Composer";
import { MessageBubble } from "../components/chat/MessageBubble";
import { RoutingTrace, type TraceState } from "../components/chat/RoutingTrace";

const IN_FLIGHT_PHASES: TraceState["phase"][] = ["routing", "retrieving", "generating"];

export function ChatPage() {
  const { activeProjectId } = useAppContext();
  const { push } = useToast();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [models, setModels] = useState<AIModel[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [trace, setTrace] = useState<TraceState>({ phase: "idle" });
  const [streamingText, setStreamingText] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!activeProjectId) return;
    api.listConversations(activeProjectId).then(setConversations).catch(() => {});
    api.listModels().then(setModels).catch(() => {});
    api.listKnowledgeBases(activeProjectId).then(setKnowledgeBases).catch(() => {});
  }, [activeProjectId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText, trace]);

  async function openConversation(id: string) {
    if (!activeProjectId) return;
    setActiveId(id);
    try {
      const detail: ConversationDetail = await api.getConversation(activeProjectId, id);
      setMessages(detail.messages);
      setTrace({ phase: "idle" });
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not load conversation", "error");
    }
  }

  async function newConversation() {
    if (!activeProjectId) return;
    try {
      const convo = await api.createConversation(activeProjectId);
      setConversations((c) => [convo, ...c]);
      setActiveId(convo.id);
      setMessages([]);
      setTrace({ phase: "idle" });
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not start a conversation", "error");
    }
  }

  async function deleteConversation(id: string) {
    if (!activeProjectId) return;
    try {
      await api.deleteConversation(activeProjectId, id);
      setConversations((c) => c.filter((x) => x.id !== id));
      if (activeId === id) {
        setActiveId(null);
        setMessages([]);
      }
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Could not delete conversation", "error");
    }
  }

  async function handleSend(input: string, model: string, knowledgeBaseId: string | null) {
    if (!activeProjectId) return;

    let conversationId = activeId;
    if (!conversationId) {
      const convo = await api.createConversation(activeProjectId);
      setConversations((c) => [convo, ...c]);
      conversationId = convo.id;
      setActiveId(convo.id);
    }

    const userMessage: Message = {
      id: `local-${Date.now()}`,
      role: "user",
      content: input,
      model: null,
      input_tokens: null,
      output_tokens: null,
      created_at: new Date().toISOString(),
    };
    // Snapshot history for the request BEFORE the async setMessages commits,
    // so the request body reflects exactly what's about to render.
    const historyForRequest = [...messages, userMessage];
    setMessages((m) => [...m, userMessage]);
    setStreamingText("");
    setTrace({ phase: "routing" });

    // Local closures, not React state - state updates are async/batched, so
    // building the final assistant message from `streamingText` state would
    // race with the last render. These two variables are always current.
    let accumulated = "";
    let resolvedModel = model;

    try {
      await streamChatCompletion(
        {
          model,
          messages: historyForRequest.map((m) => ({ role: m.role, content: m.content })),
          conversation_id: conversationId,
          project_id: activeProjectId,
          knowledge_base_id: knowledgeBaseId,
        },
        (event) => {
          switch (event.type) {
            case "model_selected":
              resolvedModel = event.model;
              setTrace({ phase: "routing", model: event.model, reason: event.reason });
              break;
            case "retrieval_started":
              setTrace((t) => ({ ...t, phase: "retrieving" }));
              break;
            case "retrieval_completed":
              setTrace((t) => ({ ...t, phase: "generating", chunksFound: event.chunks_found }));
              break;
            case "response_started":
              setTrace((t) => ({ ...t, phase: "generating" }));
              break;
            case "delta":
              accumulated += event.content;
              setStreamingText(accumulated);
              break;
            case "response_completed":
              setTrace((t) => ({ ...t, phase: "done" }));
              break;
            case "error":
              setTrace((t) => ({ ...t, phase: "error", errorMessage: event.message }));
              break;
          }
        }
      );
    } catch (err) {
      setTrace((t) => ({ ...t, phase: "error", errorMessage: err instanceof Error ? err.message : "Stream failed" }));
      push("The model provider returned an error", "error");
      return;
    }

    if (accumulated) {
      setMessages((m) => [
        ...m,
        {
          id: `local-${Date.now()}-a`,
          role: "assistant",
          content: accumulated,
          model: resolvedModel,
          input_tokens: null,
          output_tokens: null,
          created_at: new Date().toISOString(),
        },
      ]);
    }
    setStreamingText("");
  }

  const busy = IN_FLIGHT_PHASES.includes(trace.phase);

  return (
    <div className="flex h-full">
      <ConversationList
        conversations={conversations}
        activeId={activeId}
        onSelect={openConversation}
        onNew={newConversation}
        onDelete={deleteConversation}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        {!activeProjectId ? (
          <EmptyState text="Create a project first to start chatting." />
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-6 py-6">
              {messages.length === 0 && !streamingText && trace.phase === "idle" && (
                <EmptyState text="Say hello to Ziloo AI. Short questions route to GLM-5.2; longer or trickier ones route to Kimi K3." />
              )}
              <div className="mx-auto flex max-w-3xl flex-col gap-4">
                {messages.map((m) => (
                  <MessageBubble key={m.id} message={m} />
                ))}
                {(streamingText || trace.phase !== "idle") && (
                  <div className="flex flex-col gap-1.5">
                    <RoutingTrace trace={trace} />
                    {streamingText && (
                      <MessageBubble
                        message={{
                          id: "streaming",
                          role: "assistant",
                          content: streamingText,
                          model: trace.model ?? null,
                          input_tokens: null,
                          output_tokens: null,
                          created_at: new Date().toISOString(),
                        }}
                        streaming
                      />
                    )}
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            </div>
            <div className="mx-auto w-full max-w-3xl">
              <Composer models={models} knowledgeBases={knowledgeBases} onSend={handleSend} disabled={busy} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <p className="max-w-sm text-sm text-ink-muted">{text}</p>
    </div>
  );
}
