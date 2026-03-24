from __future__ import annotations

from app.services.document_service import document_service


class EmbeddingService:
    async def index_document(self, document_id: str) -> dict[str, str]:
        document = await document_service.get_document(document_id)
        if document is None:
            return {'status': 'missing', 'document_id': document_id}
        return {
            'status': 'indexed',
            'document_id': document_id,
            'message': 'Demo mode uses lightweight keyword retrieval with pre-seeded chunks.',
        }


embedding_service = EmbeddingService()
