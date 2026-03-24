from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services.draft_service import draft_service
from app.services.export_service import export_service

router = APIRouter()


@router.post('/{draft_id}')
async def export_draft(draft_id: str, format: str = Query('markdown')):
    if format != 'markdown':
        raise HTTPException(status_code=400, detail='Demo export currently supports markdown only')
    draft = await draft_service.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail='Draft not found')
    content = export_service.to_markdown_bytes(draft)
    return Response(
        content=content,
        media_type='text/markdown',
        headers={'Content-Disposition': f'attachment; filename={draft_id}.md'},
    )
