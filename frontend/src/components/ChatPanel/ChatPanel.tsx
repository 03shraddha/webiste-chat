import { useEffect, useRef } from "react";
import { useAppStore } from "../../store/appStore";
import { useChat } from "../../hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

interface ChatPanelProps {
  sessionId: string;
  siteName: string;
  siteUrl: string;
}

export function ChatPanel({ sessionId, siteName, siteUrl }: ChatPanelProps) {
  const messages = useAppStore((s) => s.messages[sessionId] ?? []);
  const { sendMessage } = useChat(sessionId);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isStreaming = messages.some((m) => m.isStreaming);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* ── Header ── */}
      <div style={{
        borderBottom: "1px solid rgba(192,40,62,0.18)",
        padding: "18px 28px 16px",
        background: "rgba(192,40,62,0.04)",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "8px", height: "8px", borderRadius: "50%",
            background: "var(--seafoam)",
            boxShadow: "0 0 8px var(--seafoam)",
          }} />
          <h2 className="font-display" style={{
            fontSize: "26px", fontWeight: 700,
            color: "var(--text-light)",
          }}>
            {siteName}
          </h2>
          <span style={{ color: "rgba(45,27,46,0.2)", fontSize: "14px" }}>·</span>
          <a
            href={siteUrl} target="_blank" rel="noopener noreferrer"
            className="font-label"
            style={{
              fontSize: "13px", letterSpacing: "0.02em",
              color: "rgba(192,40,62,0.62)",
              textDecoration: "none", overflow: "hidden",
              whiteSpace: "nowrap", textOverflow: "ellipsis",
              maxWidth: "300px", transition: "color .2s",
            }}
            onMouseEnter={(e) => ((e.target as HTMLElement).style.color = "rgba(192,40,62,0.95)")}
            onMouseLeave={(e) => ((e.target as HTMLElement).style.color = "rgba(192,40,62,0.62)")}
          >
            {siteUrl}
          </a>
        </div>
        <p className="font-label" style={{
          fontSize: "12px", letterSpacing: "0.08em", textTransform: "uppercase",
          color: "var(--text-dimmer)", marginTop: "4px",
        }}>
          Answers drawn strictly from this site's shores
        </p>
      </div>

      {/* ── Messages ── */}
      <div style={{
        flex: 1, overflowY: "auto",
        padding: "24px 28px",
      }}>
        {messages.length === 0 ? (
          <div style={{
            height: "100%", display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center", textAlign: "center",
          }}>
            <div style={{ fontSize: "42px", marginBottom: "16px" }}>✨</div>
            <p className="font-display" style={{
              fontSize: "26px", fontWeight: 700,
              color: "var(--text-light)", marginBottom: "10px",
            }}>
              Ask anything about {siteName}
            </p>
            <p className="font-body" style={{
              fontSize: "18px", color: "var(--text-dim)",
              maxWidth: "360px", lineHeight: 1.6,
            }}>
              Every answer is drawn only from the crawled content of this website —
              grounded, honest, and true to the source.
            </p>
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input ── */}
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
