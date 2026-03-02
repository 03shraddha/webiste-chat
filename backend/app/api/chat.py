from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.jobs.job_store import get_session_metadata
from app.models import ChatRequest
from app.rag.pipeline import stream_rag_response

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    """SSE stream of chat response tokens, grounded in the indexed site's content."""
    session = get_session_metadata(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = [{"role": m.role, "content": m.content} for m in request.conversation_history]

    return StreamingResponse(
        stream_rag_response(
            session_id=request.session_id,
            user_message=request.message,
            conversation_history=history,
            site_name=session["site_name"],
            site_url=session["site_url"],
            brand_profile=session.get("brand_profile", {}),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
