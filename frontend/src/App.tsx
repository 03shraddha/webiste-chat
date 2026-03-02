import { useAppStore } from "./store/appStore";
import { CrawlPanel } from "./components/CrawlPanel/CrawlPanel";
import { ChatPanel } from "./components/ChatPanel/ChatPanel";

function App() {
  const { sessions, activeSessionId } = useAppStore();
  const activeSession = sessions.find((s) => s.session_id === activeSessionId);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden" }}>
      <div className="bg-main" />
      <div className="bg-grain" />

      <div style={{ position: "relative", zIndex: 10, display: "flex", height: "100%", overflow: "hidden" }}>
        <CrawlPanel />
        <main
          style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}
          className="glass-main"
        >
          {activeSession ? (
            <ChatPanel
              sessionId={activeSession.session_id}
              siteName={activeSession.site_name}
              siteUrl={activeSession.site_url}
            />
          ) : (
            <EmptyState />
          )}
        </main>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{
      flex: 1, display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      textAlign: "center", padding: "60px 40px",
    }}>
      {/* Thin decorative border frame — like the reference image */}
      <div style={{
        position: "relative",
        padding: "40px 52px 44px",
        border: "1px solid rgba(192,40,62,0.30)",
      }}>
        {/* Corner dots */}
        {["top-left","top-right","bottom-left","bottom-right"].map((pos) => (
          <div key={pos} style={{
            position: "absolute",
            width: "6px", height: "6px",
            background: "var(--mint)",
            borderRadius: "50%",
            ...(pos === "top-left"     ? { top: "-3px",  left: "-3px"  } : {}),
            ...(pos === "top-right"    ? { top: "-3px",  right: "-3px" } : {}),
            ...(pos === "bottom-left"  ? { bottom: "-3px", left: "-3px" } : {}),
            ...(pos === "bottom-right" ? { bottom: "-3px", right: "-3px"} : {}),
          }} />
        ))}

        {/* Hero headline */}
        <p className="font-brand" style={{
          fontSize: "96px",
          lineHeight: 0.88,
          color: "var(--mint)",
          marginBottom: "20px",
        }}>
          Website<br />Chat
        </p>

        {/* Badge */}
        <div style={{
          display: "inline-block",
          background: "transparent",
          color: "var(--mint)",
          fontFamily: "'Josefin Sans', sans-serif",
          fontSize: "12px", fontWeight: 700,
          letterSpacing: "0.20em", textTransform: "uppercase",
          padding: "6px 20px",
          border: "1px solid rgba(192,40,62,0.40)",
          borderRadius: "99px",
          marginBottom: "36px",
        }}>
          AI-Powered Web Search
        </div>
      </div>

      {/* Feature cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "12px", maxWidth: "500px", marginTop: "36px" }}>
        {[
          { num: "01", label: "Crawl", desc: "Playwright renders any site, even JS-heavy SPAs" },
          { num: "02", label: "Index", desc: "Semantic vector embeddings, no cloud required" },
          { num: "03", label: "Chat",  desc: "Answers grounded strictly in the site's content" },
        ].map((f) => (
          <div key={f.label} className="glass-card" style={{ padding: "20px 16px", textAlign: "left" }}>
            <p className="font-label" style={{
              fontSize: "12px", letterSpacing: "0.1em", color: "var(--mint)",
              marginBottom: "8px",
            }}>{f.num}</p>
            <p className="font-brand" style={{
              fontSize: "26px", color: "var(--text-light)", marginBottom: "8px",
            }}>{f.label}</p>
            <p className="font-label" style={{
              fontSize: "13px", color: "var(--text-dim)", lineHeight: 1.5,
            }}>{f.desc}</p>
          </div>
        ))}
      </div>

      <p className="font-label" style={{
        marginTop: "36px", fontSize: "12px", letterSpacing: "0.12em",
        color: "var(--text-dimmer)", textTransform: "uppercase",
      }}>
        ← Enter a URL in the sidebar to begin
      </p>
    </div>
  );
}

export default App;
