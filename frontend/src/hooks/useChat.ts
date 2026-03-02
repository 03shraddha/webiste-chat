import { useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { useAppStore } from "../store/appStore";

const STREAM_TIMEOUT_MS = 60_000;

export function useChat(sessionId: string) {
  const { addMessage, updateLastMessage, getMessages } = useAppStore();
  const abortControllerRef = useRef<AbortController | null>(null);

  async function sendMessage(text: string) {
    // Abort any in-flight request
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Set up a 60s timeout
    const timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

    const history = getMessages(sessionId).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    // Immediately show user message
    addMessage(sessionId, {
      id: uuidv4(),
      role: "user",
      content: text,
    });

    // Placeholder for assistant message (will be streamed into)
    addMessage(sessionId, {
      id: uuidv4(),
      role: "assistant",
      content: "",
      isStreaming: true,
    });

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          conversation_history: history.slice(-6),
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const rawData = line.slice(6).trim();
          if (!rawData) continue;

          try {
            const data = JSON.parse(rawData);

            if (data.type === "token") {
              accumulated += data.content;
              updateLastMessage(sessionId, { content: accumulated });
            } else if (data.type === "sources") {
              updateLastMessage(sessionId, { sources: data.urls });
            } else if (data.type === "done") {
              updateLastMessage(sessionId, { isStreaming: false });
            } else if (data.type === "error") {
              updateLastMessage(sessionId, {
                content: `Error: ${data.message}`,
                isStreaming: false,
              });
            }
          } catch {
            // Skip malformed SSE line
          }
        }
      }
    } catch (err) {
      const isAbort = err instanceof Error && err.name === "AbortError";
      updateLastMessage(sessionId, {
        content: isAbort
          ? "Request timed out. Please try again."
          : `Failed to get response: ${String(err)}`,
        isStreaming: false,
      });
    } finally {
      clearTimeout(timeoutId);
      abortControllerRef.current = null;
    }
  }

  return { sendMessage };
}
