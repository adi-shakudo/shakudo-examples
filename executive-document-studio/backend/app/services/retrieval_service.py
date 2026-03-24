from __future__ import annotations

from collections import defaultdict

from app.models.schemas import Chunk, SearchResult
from app.services.document_service import document_service


class RetrievalService:
    async def retrieve_relevant_chunks(self, query: str, document_ids: list[str], limit: int = 8) -> list[SearchResult]:
        base_results = await document_service.search(query, limit=max(limit * 3, 12), doc_ids=document_ids)
        reranked = [
            SearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                document_title=result.document_title,
                text=result.text,
                score=result.score + self._soft_match_bonus(query, result) + self._diversity_bonus(result, base_results),
                matched_terms=result.matched_terms,
                metadata=result.metadata,
            )
            for result in base_results
        ]
        return sorted(reranked, key=lambda item: item.score, reverse=True)[:limit]

    def build_context(self, chunks: list[SearchResult]) -> str:
        grouped = defaultdict(list)
        for chunk in chunks:
            grouped[chunk.document_title].append(chunk)
        parts = []
        for title, entries in grouped.items():
            parts.append(f'## {title}')
            for entry in entries:
                terms = ', '.join(entry.matched_terms) if entry.matched_terms else 'semantic match'
                parts.append(f"[{terms}] {entry.text}")
        return '\n\n'.join(parts)

    def summarize_retrieval(self, chunks: list[SearchResult]) -> dict:
        by_doc: dict[str, int] = defaultdict(int)
        for chunk in chunks:
            by_doc[chunk.document_title] += 1
        return {
            'total_chunks': len(chunks),
            'documents_hit': len(by_doc),
            'document_hits': dict(by_doc),
        }

    def _soft_match_bonus(self, query: str, chunk: Chunk | SearchResult) -> float:
        text = chunk.text.lower()
        bonuses = 0.0
        themes = {
            'acquisition': ['acquisition', 'integration', 'transaction', 'target', 'synergy'],
            'risk': ['risk', 'regulatory', 'supply chain', 'margin', 'execution', 'mitigation'],
            'board': ['board', 'executive', 'leadership', 'memo', 'recommendation'],
            'market': ['market', 'competitor', 'category', 'consumer', 'growth'],
        }
        query_lower = query.lower()
        for trigger, keywords in themes.items():
            if trigger in query_lower and any(keyword in text for keyword in keywords):
                bonuses += 1.25
        return bonuses

    def _diversity_bonus(self, result: SearchResult, candidates: list[SearchResult]) -> float:
        same_doc_count = sum(1 for item in candidates if item.document_id == result.document_id)
        return max(0.0, 1.5 - (same_doc_count * 0.1))


retrieval_service = RetrievalService()
