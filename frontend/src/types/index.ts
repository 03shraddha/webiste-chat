export interface Session {
  session_id: string;
  site_url: string;
  site_name: string;
  pages_indexed: number;
  chunks_indexed: number;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  isStreaming?: boolean;
}

export interface CrawlJob {
  job_id: string;
  session_id: string;
  url: string;
  status: "queued" | "crawling" | "indexing" | "analyzing" | "complete" | "error";
  pages_crawled: number;
  pages_total: number;
  current_url: string;
  error?: string;
}

export interface CrawlState {
  status: "idle" | "starting" | "crawling" | "indexing" | "analyzing" | "complete" | "error";
  job?: CrawlJob;
  error?: string;
}
