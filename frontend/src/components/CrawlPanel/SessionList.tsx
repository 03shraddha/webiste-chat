import type { Session } from "../../types";

interface SessionListProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function SessionList({ sessions, activeSessionId, onSelect, onDelete }: SessionListProps) {
  if (sessions.length === 0) {
    return (
      <p className="font-display" style={{
        fontSize: "16px",
        color: "var(--text-dimmer)", marginTop: "16px", lineHeight: 1.6,
      }}>
        No sites indexed yet.<br />
        <span style={{ fontSize: "14px" }}>Cast the net above to begin.</span>
      </p>
    );
  }

  return (
    <div>
      <p className="font-label" style={{
        fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase",
        color: "var(--accent-pale)", marginBottom: "10px",
      }}>
        Indexed Sites
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {sessions.map((s) => (
          <div
            key={s.session_id}
            onClick={() => onSelect(s.session_id)}
            className={`glass-card${activeSessionId === s.session_id ? " active" : ""}`}
            style={{ padding: "12px 14px", display: "flex", alignItems: "center", justifyContent: "space-between" }}
          >
            <div style={{ minWidth: 0, flex: 1 }}>
              <p className="font-display" style={{
                fontSize: "17px", fontWeight: 700,
                color: activeSessionId === s.session_id ? "var(--accent-pale)" : "var(--text-light)",
                overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis",
                marginBottom: "2px",
              }}>
                {s.site_name}
              </p>
              <p className="font-label" style={{
                fontSize: "12px", letterSpacing: "0.02em",
                color: "var(--text-dim)",
                overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis",
              }}>
                {s.site_url}
              </p>
              <p className="font-label" style={{
                fontSize: "11px", letterSpacing: "0.04em",
                color: "var(--accent-pale)", marginTop: "3px",
              }}>
                {s.pages_indexed} pages · {s.chunks_indexed} chunks
              </p>
            </div>

            <button
              onClick={(e) => { e.stopPropagation(); onDelete(s.session_id); }}
              title="Remove"
              style={{
                background: "none", border: "none", cursor: "pointer",
                padding: "4px", marginLeft: "8px", flexShrink: 0,
                color: "rgba(45,27,46,0.28)",
                borderRadius: "6px", transition: "color .2s, background .2s",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = "#c04040";
                (e.currentTarget as HTMLButtonElement).style.background = "rgba(220,60,60,0.10)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = "rgba(45,27,46,0.28)";
                (e.currentTarget as HTMLButtonElement).style.background = "none";
              }}
            >
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
