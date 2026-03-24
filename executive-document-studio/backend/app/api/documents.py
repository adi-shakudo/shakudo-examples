from fastapi import APIRouter, HTTPException, Query

from app.services.document_service import document_service

router = APIRouter()


@router.get('')
async def list_documents():
    return await document_service.list_documents()


@router.get('/search')
async def search_documents(q: str = Query(..., min_length=2), limit: int = 10):
    return await document_service.search(q, limit=limit)


@router.get('/{document_id}')
async def get_document(document_id: str):
    document = await document_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail='Document not found')
    return document
