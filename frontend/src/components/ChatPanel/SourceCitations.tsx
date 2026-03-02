import { useState } from "react";

interface SourceCitationsProps {
  urls: string[];
}

export function SourceCitations({ urls }: SourceCitationsProps) {
  const [open, setOpen] = useState(false);
  if (!urls || urls.length === 0) return null;

  return (
    <div>
      <button onClick={() => setOpen(!open)} className="source-toggle">
        <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        {open ? "Hide" : "Sources"} ({urls.length})
      </button>

      {open && (
        <ul style={{ marginTop: "6px", listStyle: "none", display: "flex", flexDirection: "column", gap: "3px" }}>
          {urls.map((url, i) => (
            <li key={i}>
              <a
                href={url} target="_blank" rel="noopener noreferrer"
                className="source-link" title={url}
              >
                {url}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
