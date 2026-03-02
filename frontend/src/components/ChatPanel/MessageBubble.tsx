import type { Message } from "../../types";
import { SourceCitations } from "./SourceCitations";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: "18px",
      alignItems: "flex-start",
      gap: "10px",
    }}>
      {/* AI avatar */}
      {!isUser && (
        <div className="ai-avatar">
          ✨
        </div>
      )}

      <div style={{
        maxWidth: "78%",
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
      }}>
        <div className={isUser ? "bubble-user" : "bubble-ai"}>
          {message.content}
          {message.isStreaming && <span className="stream-cursor" />}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div style={{ marginTop: "6px", paddingLeft: "4px" }}>
            <SourceCitations urls={message.sources} />
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div style={{
          width: "30px", height: "30px", borderRadius: "50%",
          background: "rgba(192,40,62,0.10)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "13px", flexShrink: 0,
          border: "1px solid rgba(192,40,62,0.28)",
        }}>
          🌸
        </div>
      )}
    </div>
  );
}
