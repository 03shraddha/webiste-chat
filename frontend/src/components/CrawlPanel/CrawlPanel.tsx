import { useState } from "react";
import { useCrawl } from "../../hooks/useCrawl";
import { useSessions } from "../../hooks/useSessions";
import { useAppStore } from "../../store/appStore";
import { ProgressBar } from "./ProgressBar";
import { SessionList } from "./SessionList";

export function CrawlPanel() {
  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState(50);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { crawlState, crawl } = useCrawl();
  const { handleDelete, setActiveSession, activeSessionId } = useSessions();
  const sessions = useAppStore((s) => s.sessions);

  const isBusy = ["starting", "crawling", "indexing", "analyzing"].includes(crawlState.status);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed || isBusy) return;
    const normalized = trimmed.startsWith("http") ? trimmed : `https://${trimmed}`;
    crawl(normalized, maxPages, 3);
  }

  return (
    <aside
      className="glass-sidebar"
      style={{
        width: "300px",
        minWidth: "280px",
        display: "flex",
        flexDirection: "column",
        padding: "28px 20px 20px",
        overflowY: "auto",
        position: "relative",
        zIndex: 20,
      }}
    >
      {/* ── Brand ── */}
      <div style={{ marginBottom: "28px" }}>
        <h1 className="font-brand" style={{
          fontSize: "46px",
          letterSpacing: "0.01em",
          color: "var(--mint)",
          lineHeight: 0.92,
          marginBottom: "8px",
        }}>
          Website<br />Chat
        </h1>
        <p className="font-label" style={{
          fontSize: "11px",
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--text-dimmer)",
        }}>
          Crawl · Index · Converse
        </p>
      </div>

      {/* ── URL Form ── */}
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div>
          <label className="font-label" style={{
            display: "block", fontSize: "12px",
            letterSpacing: "0.12em", textTransform: "uppercase",
            color: "var(--text-dim)", marginBottom: "8px",
          }}>
            Website URL
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="example.com"
            disabled={isBusy}
            className="ocean-input"
          />
        </div>

        {/* Advanced toggle */}
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="font-label"
          style={{
            fontSize: "12px", letterSpacing: "0.08em",
            color: "var(--accent-pale)", background: "none",
            border: "none", cursor: "pointer",
            display: "flex", alignItems: "center", gap: "4px",
            alignSelf: "flex-start", transition: "color .2s",
          }}
        >
          <span style={{ fontSize: "9px" }}>{showAdvanced ? "▾" : "▸"}</span>
          Advanced options
        </button>

        {showAdvanced && (
          <div style={{
            background: "rgba(192,40,62,0.05)",
            borderRadius: "10px", padding: "12px",
            border: "1px solid rgba(192,40,62,0.16)",
          }}>
            <label className="font-label" style={{
              fontSize: "12px", letterSpacing: "0.08em",
              color: "var(--text-dim)",
              display: "block", marginBottom: "8px",
            }}>
              Max pages:{" "}
              <span style={{ color: "var(--seafoam-pale)" }}>{maxPages}</span>
            </label>
            <input
              type="range" min={5} max={200} step={5}
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
            />
          </div>
        )}

        <button type="submit" disabled={!url.trim() || isBusy} className="btn-ocean">
          {isBusy ? "Sailing the web…" : "Crawl & Index"}
        </button>
      </form>

      {/* ── Progress ── */}
      {crawlState.status !== "idle" && (
        <ProgressBar
          status={crawlState.status}
          pagesCount={crawlState.job?.pages_crawled ?? 0}
          pagesTotal={crawlState.job?.pages_total ?? 0}
          currentUrl={crawlState.job?.current_url ?? ""}
        />
      )}

      {crawlState.status === "error" && (
        <div className="error-pill">
          {crawlState.error ?? "Something went adrift…"}
        </div>
      )}

      {/* ── Session list ── */}
      <div style={{ marginTop: "20px", flex: 1 }}>
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={setActiveSession}
          onDelete={handleDelete}
        />
      </div>

      {/* ── Footer wave decoration ── */}
      <div style={{
        marginTop: "auto", paddingTop: "20px",
        textAlign: "center",
      }}>
        <p className="font-label" style={{
          fontSize: "9px", letterSpacing: "0.1em",
          color: "var(--text-dimmer)", textTransform: "uppercase",
        }}>
          — — —
        </p>
      </div>
    </aside>
  );
}
