import uuid

from sqlalchemy.orm import Session

from app.models.candidate_chunk import CandidateChunk
from app.repositories.candidate_chunk_repository import (
    CandidateChunkRepository,
)
from app.services.embedding_service import EmbeddingService
from app.services.text_chunking_service import TextChunkingService


class CVIndexingService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = CandidateChunkRepository(db)
        self.chunking_service = TextChunkingService()
        self.embedding_service = EmbeddingService()

    def index_cv(
        self,
        candidate_id: uuid.UUID,
        cv_text: str,
    ) -> int:

        chunks = self.chunking_service.split_text(cv_text)

        if not chunks:
            raise ValueError("Cannot index an empty CV")

        # Generate embeddings before modifying existing data
        embeddings = [self.embedding_service.embed_text(chunk) for chunk in chunks]

        # Replace previous chunks
        self.repository.delete_by_candidate_id(candidate_id)

        entities = [
            CandidateChunk(
                candidate_id=candidate_id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
            )
            for index, (chunk, embedding)
            in enumerate(zip(chunks, embeddings))
        ]

        self.repository.save_all(entities)

        return len(entities)