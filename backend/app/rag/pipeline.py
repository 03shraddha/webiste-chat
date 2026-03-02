import json
from typing import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings
from app.indexer.embedder import embed_query
from app.indexer.indexer import query_collection

_async_client: AsyncOpenAI | None = None


def get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=settings.xai_api_key, base_url=settings.xai_base_url)
    return _async_client


def build_system_prompt(site_name: str, site_url: str, brand_profile: dict) -> str:
    brand_voice = brand_profile.get("brand_voice_summary", "")
    key_terms = brand_profile.get("key_terms", [])
    key_terms_str = ", ".join(key_terms) if key_terms else "none specified"

    return f"""You are a helpful assistant for {site_name} ({site_url}).

CRITICAL RULES — follow these without exception:
1. Answer ONLY using information from the CONTEXT chunks provided in each message.
2. Do NOT use your own general knowledge about the world, the company, or the topic.
3. If the context does not contain sufficient information to answer the question, respond with: "I don't have information about that from this website's content."
4. Always ground your answer in the provided context. Do not speculate or fill gaps with assumed knowledge.
5. When relevant, mention which page the information comes from.

BRAND VOICE: {brand_voice}
KEY TERMINOLOGY: Use these exact terms when applicable: {key_terms_str}

Writing style:
- Match the brand's tone and formality level as described above
- Be concise but complete — avoid unnecessary padding
- Synthesize information from multiple sources when relevant
- Cite source pages naturally within your answer when helpful"""


def format_context_chunks(retrieval_results: dict) -> tuple[str, list[str]]:
    """
    Format ChromaDB query results into a readable context string.
    Returns (context_text, list_of_unique_source_urls).
    """
    docs = retrieval_results.get("documents", [[]])[0]
    metas = retrieval_results.get("metadatas", [[]])[0]

    context_parts: list[str] = []
    source_urls: list[str] = []

    for i, (doc, meta) in enumerate(zip(docs, metas)):
        source_url = meta.get("source_url", "")
        page_title = meta.get("page_title", "")
        heading = meta.get("heading_context", "")

        header = f"[Source {i + 1}]"
        if page_title:
            header += f" {page_title}"
        if heading:
            header += f" | {heading}"
        if source_url:
            header += f"\nURL: {source_url}"

        context_parts.append(f"{header}\n{doc}")

        if source_url and source_url not in source_urls:
            source_urls.append(source_url)

    return "\n\n---\n\n".join(context_parts), source_urls


async def stream_rag_response(
    session_id: str,
    user_message: str,
    conversation_history: list[dict],
    site_name: str,
    site_url: str,
    brand_profile: dict,
) -> AsyncGenerator[str, None]:
    """
    Async generator yielding SSE-formatted strings.

    Events:
        data: {"type": "token", "content": "..."}   — streaming text token
        data: {"type": "sources", "urls": [...]}     — source URLs after completion
        data: {"type": "done"}                       — final signal
        data: {"type": "error", "message": "..."}    — on failure
    """
    try:
        # Validate and sanitize message
        user_message = user_message.strip()
        if not user_message:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Message cannot be empty'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # Truncate extremely long messages to avoid token overflow
        if len(user_message) > 4000:
            user_message = user_message[:4000]

        # 1. Embed query
        query_embedding = embed_query(user_message)

        # 2. Retrieve top-k chunks — handle case where session index was deleted
        try:
            results = query_collection(session_id, query_embedding, top_k=settings.top_k_chunks)
        except Exception as e:
            err_str = str(e).lower()
            if "not found" in err_str or "no such file" in err_str or "does not exist" in err_str:
                yield f"data: {json.dumps({'type': 'error', 'message': 'This site index no longer exists. Please re-crawl it.'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return
            raise

        context_text, source_urls = format_context_chunks(results)

        # If retrieval returned nothing, tell the user rather than hallucinating
        if not context_text.strip():
            yield f"data: {json.dumps({'type': 'token', 'content': \"I don't have any relevant content from this website to answer that question.\"})}\n\n"
            yield f"data: {json.dumps({'type': 'sources', 'urls': []})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # 3. Build system prompt
        system_prompt = build_system_prompt(site_name, site_url, brand_profile)

        # 4. Keep last 6 messages of history (3 turns)
        trimmed_history = conversation_history[-6:]

        # 5. Inject context into user message
        augmented_user_message = (
            f"CONTEXT FROM WEBSITE:\n{context_text}\n\n"
            f"---\n\n"
            f"USER QUESTION: {user_message}"
        )

        messages = [
            *[{"role": m["role"], "content": m["content"]} for m in trimmed_history],
            {"role": "user", "content": augmented_user_message},
        ]

        # 6. Stream from Grok
        client = get_async_client()
        all_messages = [{"role": "system", "content": system_prompt}, *messages]
        stream = await client.chat.completions.create(
            model=settings.xai_model,
            max_tokens=1024,
            messages=all_messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield f"data: {json.dumps({'type': 'token', 'content': delta.content})}\n\n"

        # 7. Send source citations
        yield f"data: {json.dumps({'type': 'sources', 'urls': source_urls})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        print(f"[RAG] Error during streaming: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
