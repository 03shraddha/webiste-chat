import { useState } from "react";
import type { Source } from "../../types";

interface SourceCitationsProps {
  sources: Source[];
}

export function SourceCitations({ sources }: SourceCitationsProps) {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;

  return (
    <div>
      <button onClick={() => setOpen(!open)} className="source-toggle">
        <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        {open ? "Hide" : "Sources"} ({sources.length})
      </button>

      {open && (
        <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "6px" }}>
          {sources.map((source, i) => (
            <div key={i} className="source-card">
              {/* Index badge + heading breadcrumb */}
              <div style={{ display: "flex", alignItems: "flex-start", gap: "8px", marginBottom: "6px" }}>
                <span className="source-badge">{i + 1}</span>
                <div style={{ minWidth: 0, flex: 1 }}>
                  {source.heading_path && (
                    <p className="source-heading">
                      {source.heading_path}
                    </p>
                  )}
                  {source.title && (
                    <p className="source-page-title">{source.title}</p>
                  )}
                </div>
              </div>

              {/* Excerpt */}
              {source.excerpt && (
                <p className="source-excerpt">
                  {source.excerpt.length > 180
                    ? source.excerpt.slice(0, 180) + "…"
                    : source.excerpt}
                </p>
              )}

              {/* URL */}
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="source-link"
                title={source.url}
              >
                ↗ {source.url}
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
