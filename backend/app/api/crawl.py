import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.brand.analyzer import analyze_brand_tone
from app.crawler.crawler import crawl_site
from app.crawler.url_utils import extract_site_name
from app.indexer.indexer import index_pages
from app.jobs.job_store import create_job, get_job, save_session, update_job
from app.models import CrawlRequest, CrawlResponse

router = APIRouter()


@router.post("/crawl", response_model=CrawlResponse)
async def start_crawl(request: CrawlRequest):
    """Start an async crawl job. Returns job_id and session_id immediately."""
    # Validate URL
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=422, detail="URL cannot be empty")
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="URL must start with http:// or https://")

    # Clamp parameters to safe ranges
    request.url = url
    request.max_pages = max(1, min(request.max_pages, 500))
    request.max_depth = max(1, min(request.max_depth, 10))

    job_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    create_job(job_id, session_id, url)

    # Fire-and-forget background crawl task
    asyncio.create_task(
        _run_crawl_pipeline(job_id, session_id, request)
    )

    return CrawlResponse(job_id=job_id, session_id=session_id, status="queued")


@router.get("/crawl/{job_id}/status")
async def crawl_status(job_id: str):
    """SSE stream of crawl job progress events."""

    async def event_generator():
        while True:
            job = get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                break

            yield f"data: {json.dumps({'type': 'progress', **job})}\n\n"

            if job["status"] in ("complete", "error"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _run_crawl_pipeline(job_id: str, session_id: str, request: CrawlRequest):
    """Background task: crawl → index → analyze brand → save session."""
    try:
        update_job(job_id, status="crawling")

        async def progress_cb(count: int, current_url: str):
            update_job(job_id, pages_crawled=count, current_url=current_url)

        pages = await crawl_site(
            start_url=request.url,
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            progress_callback=progress_cb,
        )

        if not pages:
            update_job(job_id, status="error", error="No readable content found on this site. It may require login, block crawlers, or contain only images/PDFs.")
            return

        update_job(job_id, status="indexing", pages_total=len(pages))

        # Run embedding/indexing in a thread pool to avoid blocking the event loop
        total_chunks = await asyncio.get_event_loop().run_in_executor(
            None, index_pages, session_id, pages
        )

        if total_chunks == 0:
            update_job(job_id, status="error", error="Pages were crawled but no indexable text content was found. The site may be image-heavy or require JavaScript rendering.")
            return

        update_job(job_id, status="analyzing")

        site_name = extract_site_name(request.url)

        # Brand analysis also in thread pool (sync Claude call)
        brand_profile = await asyncio.get_event_loop().run_in_executor(
            None, analyze_brand_tone, pages, site_name
        )

        # Persist session metadata to disk
        save_session(session_id, {
            "session_id": session_id,
            "site_url": request.url,
            "site_name": site_name,
            "pages_indexed": len(pages),
            "chunks_indexed": total_chunks,
            "brand_profile": brand_profile,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        update_job(job_id, status="complete", pages_total=len(pages))
        print(f"[CRAWL] Job {job_id} complete. {len(pages)} pages, {total_chunks} chunks.")

    except Exception as e:
        print(f"[CRAWL] Job {job_id} failed: {e}")
        update_job(job_id, status="error", error=str(e))
