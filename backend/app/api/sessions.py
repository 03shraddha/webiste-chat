from fastapi import APIRouter, HTTPException

from app.indexer.indexer import delete_session_collection
from app.jobs.job_store import delete_session_record, get_session_metadata, list_sessions
from app.models import Session

router = APIRouter()


@router.get("/sessions", response_model=list[Session])
async def get_sessions():
    """Return all indexed sessions."""
    raw = list_sessions()
    sessions = []
    for s in raw:
        sessions.append(Session(
            session_id=s["session_id"],
            site_url=s["site_url"],
            site_name=s["site_name"],
            pages_indexed=s.get("pages_indexed", 0),
            chunks_indexed=s.get("chunks_indexed", 0),
            created_at=s.get("created_at", ""),
        ))
    # Most recent first
    sessions.sort(key=lambda x: x.created_at, reverse=True)
    return sessions


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session's vector store and metadata record."""
    session = get_session_metadata(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    delete_session_collection(session_id)
    delete_session_record(session_id)

    return {"success": True, "deleted": session_id}
