from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import DraftCreate
from app.services.draft_service import draft_service

router = APIRouter()


@router.post('/generate')
async def generate_draft(payload: DraftCreate):
    generator = draft_service.generate_draft_stream(
        template_id=payload.template_id,
        doc_ids=payload.doc_ids,
        instruction=payload.instruction,
    )
    return StreamingResponse(generator, media_type='text/event-stream')


@router.get('/{draft_id}')
async def get_draft(draft_id: str):
    draft = await draft_service.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail='Draft not found')
    return draft


@router.get('/{draft_id}/versions')
async def get_draft_versions(draft_id: str):
    return await draft_service.list_draft_versions(draft_id)
