from pydantic import BaseModel
from typing import Optional, List


# --- Crawl Models ---
class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 50
    max_depth: int = 3


class CrawlResponse(BaseModel):
    job_id: str
    session_id: str
    status: str


# --- Chat Models ---
class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    conversation_history: List[Message] = []


# --- Session Models ---
class Session(BaseModel):
    session_id: str
    site_url: str
    site_name: str
    pages_indexed: int
    chunks_indexed: int
    created_at: str


class BrandProfile(BaseModel):
    formality_level: str
    key_terms: List[str]
    writing_patterns: str
    brand_voice_summary: str
