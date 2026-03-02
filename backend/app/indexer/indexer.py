"""
Vector store using hnswlib (HNSW approximate nearest neighbor index) + JSON for metadata.
Replaces ChromaDB to avoid Python 3.14 compatibility issues.

Storage layout:
  data/vector_store/{session_id}/
    index.bin       — HNSW binary index (hnswlib)
    documents.json  — chunk text + metadata
"""
import json
from pathlib import Path
from typing import Optional

import numpy as np
import hnswlib

from app.config import BASE_DIR, settings
from app.indexer.chunker import recursive_text_split
from app.indexer.embedder import embed_texts

STORE_DIR = BASE_DIR / "data" / "vector_store"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def _session_dir(session_id: str) -> Path:
    return STORE_DIR / session_id


def _index_path(session_id: str) -> Path:
    return _session_dir(session_id) / "index.bin"


def _docs_path(session_id: str) -> Path:
    return _session_dir(session_id) / "documents.json"


def index_pages(session_id: str, pages: list[dict]) -> int:
    """
    Chunks all pages, embeds them, and stores in an HNSW index + JSON file.
    Returns total number of chunks indexed.
    """
    all_documents: list[str] = []
    all_metadatas: list[dict] = []

    for page in pages:
        if not page.get("content"):
            continue

        chunks = recursive_text_split(
            page["content"],
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )

        heading_context = " > ".join(page.get("headings", [])[:3])

        for i, chunk in enumerate(chunks):
            all_documents.append(chunk)
            all_metadatas.append({
                "source_url": page["url"],
                "page_title": page.get("title", ""),
                "chunk_index": i,
                "heading_context": heading_context,
            })

    if not all_documents:
        return 0

    # Embed in batches
    all_embeddings: list[list[float]] = []
    batch_size = 256
    for i in range(0, len(all_documents), batch_size):
        batch = all_documents[i : i + batch_size]
        all_embeddings.extend(embed_texts(batch))

    embeddings_array = np.array(all_embeddings, dtype=np.float32)

    # Normalize for cosine similarity (HNSW cosine = inner product on unit vectors)
    norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    embeddings_array = embeddings_array / norms

    # Build HNSW index
    n_items = len(all_documents)
    index = hnswlib.Index(space="ip", dim=EMBEDDING_DIM)  # inner product = cosine on normalized
    index.init_index(max_elements=max(n_items, 100), ef_construction=200, M=16)
    index.add_items(embeddings_array, list(range(n_items)))
    index.set_ef(50)

    # Persist
    session_dir = _session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    index.save_index(str(_index_path(session_id)))

    docs_data = {
        "documents": all_documents,
        "metadatas": all_metadatas,
    }
    _docs_path(session_id).write_text(json.dumps(docs_data), encoding="utf-8")

    print(f"[INDEXER] Indexed {n_items} chunks for session {session_id}")
    return n_items


def query_collection(
    session_id: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> dict:
    """
    Query a session's HNSW index for the top-k most similar chunks.
    Returns dict with 'documents' and 'metadatas' lists (ChromaDB-compatible shape).
    """
    index_path = _index_path(session_id)
    docs_path = _docs_path(session_id)

    if not index_path.exists() or not docs_path.exists():
        return {"documents": [[]], "metadatas": [[]]}

    docs_data = json.loads(docs_path.read_text(encoding="utf-8"))
    documents = docs_data["documents"]
    metadatas = docs_data["metadatas"]

    n_items = len(documents)
    if n_items == 0:
        return {"documents": [[]], "metadatas": [[]]}

    # Load index
    index = hnswlib.Index(space="ip", dim=EMBEDDING_DIM)
    index.load_index(str(index_path), max_elements=n_items)
    index.set_ef(50)

    # Normalize query
    q = np.array(query_embedding, dtype=np.float32)
    norm = np.linalg.norm(q)
    if norm > 0:
        q = q / norm

    k = min(top_k, n_items)
    labels, _ = index.knn_query(q.reshape(1, -1), k=k)

    result_docs = [documents[i] for i in labels[0]]
    result_metas = [metadatas[i] for i in labels[0]]

    return {"documents": [result_docs], "metadatas": [result_metas]}


def delete_session_collection(session_id: str) -> None:
    """Delete all persisted data for a session."""
    import shutil
    session_dir = _session_dir(session_id)
    if session_dir.exists():
        shutil.rmtree(session_dir)
        print(f"[INDEXER] Deleted store for session {session_id}")


def list_collections() -> list[str]:
    """List all session IDs that have a vector store."""
    if not STORE_DIR.exists():
        return []
    return [d.name for d in STORE_DIR.iterdir() if d.is_dir()]
