from __future__ import annotations

from collections import defaultdict

from app.models.schemas import Chunk, SearchResult
from app.services.document_service import document_service


class RetrievalService:
    async def retrieve_relevant_chunks(self, query: str, document_ids: list[str], limit: int = 8) -> list[SearchResult]:
        chunks = await document_service.get_chunks_for_documents(document_ids)
        query_tokens = {token.lower() for token in query.split() if token.strip()}
        results: list[SearchResult] = []
        for chunk in chunks:
            lower = chunk.text.lower()
            score = sum(1 for token in query_tokens if token in lower)
            if score == 0:
                score = self._soft_match_bonus(query, chunk)
            if score <= 0:
                continue
            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    text=chunk.text,
                    score=float(score),
                    metadata=chunk.metadata,
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def build_context(self, chunks: list[SearchResult]) -> str:
        grouped = defaultdict(list)
        for chunk in chunks:
            grouped[chunk.document_title].append(chunk.text)
        parts = []
        for title, entries in grouped.items():
            parts.append(f'## {title}')
            for entry in entries:
                parts.append(entry)
        return '\n\n'.join(parts)

    def _soft_match_bonus(self, query: str, chunk: Chunk | SearchResult) -> int:
        text = chunk.text.lower()
        bonuses = 0
        themes = {
            'acquisition': ['acquisition', 'integration', 'transaction', 'target'],
            'risk': ['risk', 'regulatory', 'supply chain', 'margin', 'execution'],
            'board': ['board', 'executive', 'leadership', 'memo'],
            'market': ['market', 'competitor', 'category', 'consumer'],
        }
        query_lower = query.lower()
        for trigger, keywords in themes.items():
            if trigger in query_lower and any(keyword in text for keyword in keywords):
                bonuses += 1
        return bonuses


retrieval_service = RetrievalService()
