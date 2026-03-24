from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
from uuid import uuid4

from app.models.schemas import Citation, Draft, SearchResult
from app.services import database
from app.services.document_service import document_service
from app.services.retrieval_service import retrieval_service
from app.services.template_service import template_service


class DraftService:
    async def generate_draft_stream(self, template_id: str, doc_ids: list[str], instruction: str) -> AsyncGenerator[str, None]:
        template = await template_service.get_template(template_id)
        if template is None:
            yield self._sse({'type': 'error', 'message': f'Template {template_id} not found'})
            return

        documents = await document_service.list_documents()
        selected_documents = [doc for doc in documents if doc.id in doc_ids]
        yield self._sse({'type': 'status', 'message': f'Retrieving relevant passages from {len(selected_documents)} documents...'})
        await asyncio.sleep(0.3)

        retrieved = await retrieval_service.retrieve_relevant_chunks(instruction, doc_ids, limit=10)
        yield self._sse({'type': 'status', 'message': f'Found {len(retrieved)} relevant passages across the private corpus'})
        await asyncio.sleep(0.25)

        citations = [
            Citation(
                section=template.sections[min(index, len(template.sections) - 1)].id,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                snippet=item.text[:220] + ('...' if len(item.text) > 220 else ''),
            )
            for index, item in enumerate(retrieved)
        ]
        yield self._sse({'type': 'citations', 'citations': [citation.model_dump() for citation in citations]})

        context = retrieval_service.build_context(retrieved)
        yield self._sse({'type': 'status', 'message': f'Building grounded context package ({len(context.split())} words)'})
        await asyncio.sleep(0.25)

        generated_sections: dict[str, str] = {}
        for section in template.sections:
            yield self._sse({'type': 'status', 'message': f'Drafting {section.title}...'})
            section_text = self._compose_section(section.id, section.title, instruction, selected_documents, retrieved)
            generated_sections[section.id] = section_text
            for piece in self._chunk_text(section_text, chunk_size=140):
                yield self._sse({'type': 'content', 'section': section.id, 'text': piece})
                await asyncio.sleep(0.05)

        draft_id = f'draft_{uuid4().hex[:10]}'
        draft = Draft(
            id=draft_id,
            template_id=template_id,
            title=self._title_from_instruction(instruction),
            content=generated_sections,
            citations=citations,
            working_set=doc_ids,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await self.save_draft(draft)
        yield self._sse({'type': 'done', 'draft_id': draft_id})

    async def save_draft(self, draft: Draft) -> None:
        await database.execute(
            '''
            INSERT OR REPLACE INTO drafts (id, template_id, title, content, citations, working_set, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                draft.id,
                draft.template_id,
                draft.title,
                json.dumps(draft.content),
                json.dumps([citation.model_dump() for citation in draft.citations]),
                json.dumps(draft.working_set),
                draft.version,
                draft.created_at.isoformat(),
                draft.updated_at.isoformat(),
            ),
        )

    async def list_draft_versions(self, draft_id: str) -> list[Draft]:
        row = await database.fetch_one('SELECT * FROM drafts WHERE id = ?', (draft_id,))
        if not row:
            return []
        return [self._row_to_draft(row)]

    async def get_draft(self, draft_id: str) -> Draft | None:
        row = await database.fetch_one('SELECT * FROM drafts WHERE id = ?', (draft_id,))
        if not row:
            return None
        return self._row_to_draft(row)

    def _row_to_draft(self, row) -> Draft:
        return Draft(
            id=row['id'],
            template_id=row['template_id'],
            title=row['title'],
            content=database.loads(row['content']),
            citations=[Citation(**citation) for citation in database.loads(row['citations'])],
            working_set=database.loads(row['working_set']),
            version=row['version'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _compose_section(self, section_id: str, section_title: str, instruction: str, documents, retrieved: list[SearchResult]) -> str:
        doc_titles = ', '.join(document.title for document in documents[:3])
        evidence = '; '.join(item.text.split('. ')[0] for item in retrieved[:3])
        base = {
            'executive_summary': (
                'We recommend advancing to a focused diligence phase for the proposed regional organic food distributor. '
                'The current internal evidence suggests strategic fit with premium food growth priorities, adjacency to existing distribution capabilities, '
                'and a credible path to leadership alignment if management frames the opportunity with disciplined assumptions.'
            ),
            'background': (
                f'The opportunity should be evaluated against precedent materials including {doc_titles}. '
                'Historical transaction reviews show that integrations succeed when category adjacency, operating cadence, and governance design are established before close.'
            ),
            'analysis': (
                'The retrieved internal corpus highlights three decision anchors: category growth exposure, operating margin durability, and execution readiness. '
                f'Across the source material, the strongest corroborating evidence includes: {evidence}.'
            ),
            'recommendation': (
                'Management should authorize a stage-gated diligence plan focused on commercial overlap, distribution complexity, and scenario-based value creation. '
                'A draft board narrative should emphasize optionality, integration discipline, and the ability to defer commitment if leading indicators weaken.'
            ),
            'risk_assessment': (
                'The risk posture should remain conservative. Key watch areas include integration drag, margin compression during transition, regulatory review sensitivity, '
                'and the need for explicit executive sponsorship to avoid diffused accountability.'
            ),
        }
        text = base.get(section_id, f'{section_title} should synthesize the selected internal record into an executive-ready narrative.')
        return f'{text}\n\nRequested brief: {instruction.strip()}'

    def _title_from_instruction(self, instruction: str) -> str:
        cleaned = instruction.strip().rstrip('.')
        return cleaned[:90] if cleaned else 'Executive Draft'

    def _chunk_text(self, text: str, chunk_size: int = 160) -> list[str]:
        return [text[index:index + chunk_size] for index in range(0, len(text), chunk_size)]

    def _sse(self, payload: dict) -> str:
        return f'data: {json.dumps(payload)}\n\n'


draft_service = DraftService()
