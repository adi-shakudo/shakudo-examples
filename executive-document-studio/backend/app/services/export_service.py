from __future__ import annotations

from app.models.schemas import Draft


class ExportService:
    def to_markdown_bytes(self, draft: Draft) -> bytes:
        lines = [f'# {draft.title}', '']
        for section, content in draft.content.items():
            pretty = section.replace('_', ' ').title()
            lines.append(f'## {pretty}')
            lines.append(content)
            lines.append('')
        lines.append('## Sources Used')
        for citation in draft.citations:
            lines.append(f'- {citation.document_id}: {citation.snippet or citation.chunk_id}')
        return '\n'.join(lines).encode('utf-8')


export_service = ExportService()
