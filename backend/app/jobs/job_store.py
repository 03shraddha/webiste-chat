import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import BASE_DIR

SESSIONS_FILE = BASE_DIR / "data" / "sessions.json"

# In-memory store for active/recent crawl jobs
_jobs: dict[str, dict] = {}


# ──────────────────────────────────────────
# Job management (in-memory, per process)
# ──────────────────────────────────────────

def create_job(job_id: str, session_id: str, url: str) -> dict:
    job = {
        "job_id": job_id,
        "session_id": session_id,
        "url": url,
        "status": "queued",  # queued | crawling | indexing | analyzing | complete | error
        "pages_crawled": 0,
        "pages_total": 0,
        "current_url": "",
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _jobs[job_id] = job
    return job


def update_job(job_id: str, **kwargs) -> None:
    if job_id in _jobs:
        _jobs[job_id].update(kwargs)


def get_job(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)


# ──────────────────────────────────────────
# Session persistence (JSON file on disk)
# ──────────────────────────────────────────

def _load_sessions() -> dict:
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_sessions(sessions: dict) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2), encoding="utf-8")


def save_session(session_id: str, metadata: dict) -> None:
    sessions = _load_sessions()
    sessions[session_id] = metadata
    _save_sessions(sessions)


def get_session_metadata(session_id: str) -> Optional[dict]:
    return _load_sessions().get(session_id)


def list_sessions() -> list[dict]:
    sessions = _load_sessions()
    return list(sessions.values())


def delete_session_record(session_id: str) -> None:
    sessions = _load_sessions()
    sessions.pop(session_id, None)
    _save_sessions(sessions)
