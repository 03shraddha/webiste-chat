import { useState, useRef, useEffect } from "react";
import { startCrawl, fetchSessions } from "../api/client";
import { useAppStore } from "../store/appStore";
import type { CrawlState } from "../types";

export function useCrawl() {
  const [crawlState, setCrawlState] = useState<CrawlState>({ status: "idle" });
  const { setSessions, setActiveSession } = useAppStore();
  const eventSourceRef = useRef<EventSource | null>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  async function crawl(url: string, maxPages = 50, maxDepth = 3) {
    // Close any existing SSE connection before starting a new crawl
    eventSourceRef.current?.close();
    eventSourceRef.current = null;

    setCrawlState({ status: "starting" });

    let jobId: string;
    let sessionId: string;

    try {
      const res = await startCrawl({ url, max_pages: maxPages, max_depth: maxDepth });
      jobId = res.job_id;
      sessionId = res.session_id;
    } catch (err: unknown) {
      setCrawlState({ status: "error", error: String(err) });
      return;
    }

    // Open SSE connection for progress
    const eventSource = new EventSource(`/api/crawl/${jobId}/status`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "error") {
          setCrawlState({ status: "error", error: data.message });
          eventSource.close();
          eventSourceRef.current = null;
          return;
        }

        if (data.type === "progress") {
          const status = data.status as CrawlState["status"];
          setCrawlState({
            status: status === "complete" ? "complete" : status,
            job: data,
          });

          if (data.status === "complete") {
            eventSource.close();
            eventSourceRef.current = null;
            // Refresh sessions list and activate the new one
            const sessions = await fetchSessions();
            setSessions(sessions);
            setActiveSession(sessionId);
            setTimeout(() => setCrawlState({ status: "idle" }), 3000);
          }

          if (data.status === "error") {
            setCrawlState({ status: "error", error: data.error ?? "Crawl failed" });
            eventSource.close();
            eventSourceRef.current = null;
          }
        }
      } catch (e) {
        console.error("[useCrawl] Parse error:", e);
      }
    };

    eventSource.onerror = () => {
      setCrawlState({ status: "error", error: "Lost connection to server" });
      eventSource.close();
      eventSourceRef.current = null;
    };
  }

  return { crawlState, crawl };
}
