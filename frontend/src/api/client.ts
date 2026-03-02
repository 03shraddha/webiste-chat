import type { Session } from "../types";

const BASE = "/api";

export async function startCrawl(payload: {
  url: string;
  max_pages: number;
  max_depth: number;
}): Promise<{ job_id: string; session_id: string; status: string }> {
  const res = await fetch(`${BASE}/crawl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await fetch(`${BASE}/sessions`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteSession(session_id: string): Promise<void> {
  const res = await fetch(`${BASE}/sessions/${session_id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}
