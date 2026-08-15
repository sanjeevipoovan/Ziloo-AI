/**
 * Reads the SSE stream from POST /v1/chat/completions?stream=true.
 * Uses fetch + a ReadableStream reader rather than EventSource, because
 * EventSource can't send a POST body or an Authorization header.
 */
import type { ChatCompletionRequest, StreamEvent } from "../types";
import { getApiBaseUrl, getToken } from "./api";

export async function streamChatCompletion(
  payload: ChatCompletionRequest,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const token = getToken();
  const res = await fetch(`${getApiBaseUrl()}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ ...payload, stream: true }),
    signal,
  });

  if (!res.ok || !res.body) {
    let message = `Stream failed with status ${res.status}`;
    try {
      const data = await res.json();
      message = data?.error?.message ?? message;
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(message);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payloadText = line.slice(5).trim();
      if (payloadText === "[DONE]") {
        onEvent({ type: "done" });
        continue;
      }
      try {
        onEvent(JSON.parse(payloadText) as StreamEvent);
      } catch {
        // ignore a malformed/partial chunk - the next read() will complete it
      }
    }
  }
}
