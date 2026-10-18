class TextChunkingService:

    def __init__(
        self,
        chunk_size: int = 150,
        chunk_overlap: int = 30,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if not 0 <= chunk_overlap < chunk_size:
            raise ValueError(
                "chunk_overlap must be between 0 and chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        words = text.split()
        chunks = []
        step = self.chunk_size - self.chunk_overlap

        for start in range(0, len(words), step):
            chunk = " ".join(words[start:start + self.chunk_size])

            if chunk:
                chunks.append(chunk)

            if start + self.chunk_size >= len(words):
                break

        return chunks