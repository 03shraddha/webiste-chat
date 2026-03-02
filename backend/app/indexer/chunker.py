def recursive_text_split(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[str]:
    """
    Splits text into chunks using a hierarchy of separators.
    Applies overlap between consecutive chunks for context continuity.
    """
    separators = ["\n\n", "\n", ". ", " "]

    def _split(text: str, sep_index: int) -> list[str]:
        if not text.strip():
            return []
        if len(text) <= chunk_size or sep_index >= len(separators):
            return [text.strip()]

        separator = separators[sep_index]
        parts = text.split(separator)
        chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = (current + separator + part).strip() if current else part.strip()
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > chunk_size:
                    # Recurse with next separator
                    chunks.extend(_split(part, sep_index + 1))
                    current = ""
                else:
                    current = part.strip()

        if current:
            chunks.append(current)

        return chunks

    raw_chunks = _split(text, 0)

    # Apply overlap: prepend tail of previous chunk to current chunk
    final_chunks: list[str] = []
    for i, chunk in enumerate(raw_chunks):
        if i > 0 and overlap > 0:
            tail = raw_chunks[i - 1][-overlap:]
            chunk = (tail + " " + chunk).strip()
        if len(chunk) >= 50:  # Skip trivially short chunks
            final_chunks.append(chunk)

    return final_chunks
