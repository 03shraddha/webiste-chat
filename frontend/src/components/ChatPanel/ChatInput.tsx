import { useState, useRef, type KeyboardEvent } from "react";

const MAX_CHARS = 4000;

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isSendingRef = useRef(false);

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled || isSendingRef.current) return;
    isSendingRef.current = true;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    // Reset after a tick so rapid double-clicks can't queue a second send
    setTimeout(() => { isSendingRef.current = false; }, 300);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInput() {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const val = e.target.value;
    if (val.length <= MAX_CHARS) {
      setText(val);
    }
  }

  return (
    <div className="chat-input-bar">
      <div style={{ display: "flex", alignItems: "flex-end", gap: "12px" }}>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask the sea a question…"
          disabled={disabled}
          rows={1}
          className="chat-textarea"
        />
        <button
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className="chat-send-btn"
          title="Send (Enter)"
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      <p className="font-label" style={{
        textAlign: "center", marginTop: "8px",
        fontSize: "9px", letterSpacing: "0.1em", textTransform: "uppercase",
        color: "var(--text-dimmer)",
      }}>
        Enter to send · Shift + Enter for new line
      </p>
    </div>
  );
}
