from sentence_transformers import SentenceTransformer
from app.config import settings

# Singleton — model loads once on first use, reused for all subsequent calls
_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[EMBEDDER] Loading model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        print("[EMBEDDER] Model loaded.")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns list of float vectors."""
    model = get_embedder()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]
