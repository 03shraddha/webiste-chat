interface ProgressBarProps {
  pagesCount: number;
  pagesTotal: number;
  currentUrl: string;
  status: string;
}

const statusLabel: Record<string, string> = {
  queued:    "Queued…",
  starting:  "Starting…",
  crawling:  "Crawling pages…",
  indexing:  "Indexing content…",
  analyzing: "Analyzing brand…",
  complete:  "Done",
  error:     "Failed",
};

export function ProgressBar({ pagesCount, pagesTotal, currentUrl, status }: ProgressBarProps) {
  const percent = pagesTotal > 0 ? Math.min(100, Math.round((pagesCount / pagesTotal) * 100)) : 0;
  const isIndeterminate = ["queued", "starting", "analyzing"].includes(status);
  const isComplete = status === "complete";
  const isError = status === "error";

  return (
    <div style={{ marginTop: "18px" }}>
      <div style={{
        display: "flex", justifyContent: "space-between",
        alignItems: "baseline", marginBottom: "8px",
      }}>
        <span className="font-label" style={{
          fontSize: "13px", letterSpacing: "0.08em", textTransform: "uppercase",
          color: isError ? "#c04040" : isComplete ? "var(--seafoam-pale)" : "var(--text-dim)",
        }}>
          {statusLabel[status] ?? status}
        </span>
        {pagesTotal > 0 && (
          <span className="font-label" style={{
            fontSize: "12px", letterSpacing: "0.06em",
            color: "var(--accent-pale)",
          }}>
            {pagesCount} / {pagesTotal}
          </span>
        )}
      </div>

      <div className="wave-track">
        <div
          className={`wave-fill${isIndeterminate ? " indeterminate" : ""}${isComplete ? " done" : ""}`}
          style={{
            ...(!isIndeterminate ? { width: isComplete ? "100%" : `${percent}%` } : undefined),
            ...(isError ? { background: "#c04040", width: "100%" } : undefined),
          }}
        />
      </div>

      {currentUrl && !isComplete && !isError && (
        <p className="font-label" style={{
          marginTop: "6px", fontSize: "12px", letterSpacing: "0.02em",
          color: "var(--text-dimmer)",
          overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis",
        }} title={currentUrl}>
          {currentUrl}
        </p>
      )}
    </div>
  );
}
