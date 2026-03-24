from __future__ import annotations

from typing import List

from app.models.schemas import Chunk, Document, SearchResult
from app.services import database


class DocumentService:
    async def list_documents(self) -> List[Document]:
        rows = await database.fetch_all(
            'SELECT * FROM documents ORDER BY date DESC, title ASC'
        )
        return [
            Document(
                id=row['id'],
                title=row['title'],
                type=row['type'],
                tags=database.loads(row['tags']),
                date=row['date'],
                summary=row['summary'],
                content=row['content'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
            )
            for row in rows
        ]

    async def get_document(self, document_id: str) -> Document | None:
        row = await database.fetch_one('SELECT * FROM documents WHERE id = ?', (document_id,))
        if not row:
            return None
        return Document(
            id=row['id'],
            title=row['title'],
            type=row['type'],
            tags=database.loads(row['tags']),
            date=row['date'],
            summary=row['summary'],
            content=row['content'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    async def get_chunks_for_documents(self, document_ids: list[str]) -> list[Chunk]:
        placeholders = ', '.join('?' for _ in document_ids)
        if not placeholders:
            return []
        rows = await database.fetch_all(
            f'SELECT * FROM chunks WHERE document_id IN ({placeholders})',
            tuple(document_ids),
        )
        return [
            Chunk(
                id=row['id'],
                document_id=row['document_id'],
                document_title=row['document_title'],
                text=row['text'],
                metadata=database.loads(row['metadata']),
            )
            for row in rows
        ]

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        query_tokens = {token.lower() for token in query.split() if token.strip()}
        rows = await database.fetch_all('SELECT * FROM chunks')
        scored: list[SearchResult] = []
        for row in rows:
            text = row['text']
            lower = text.lower()
            score = sum(1 for token in query_tokens if token in lower)
            if score <= 0:
                continue
            scored.append(
                SearchResult(
                    chunk_id=row['id'],
                    document_id=row['document_id'],
                    document_title=row['document_title'],
                    text=text,
                    score=float(score),
                    metadata=database.loads(row['metadata']),
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]


document_service = DocumentService()
