from fastapi import APIRouter

from app.services.embedding_service import embedding_service

router = APIRouter()


@router.post('/index/{document_id}')
async def index_document(document_id: str):
    return await embedding_service.index_document(document_id)
