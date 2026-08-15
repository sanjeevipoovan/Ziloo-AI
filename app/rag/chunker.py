"""Simple, dependency-free sliding-window chunker over characters. Good
enough for V1; swap for a token-aware splitter later without touching callers."""


def chunk_text(text: str, *, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == length:
            break
        start = end - overlap

    return chunks
