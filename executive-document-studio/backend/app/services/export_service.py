from __future__ import annotations

from app.models.schemas import Draft


class ExportService:
    def to_markdown_bytes(self, draft: Draft) -> bytes:
        return self._render_markdown(draft).encode('utf-8')

    def to_text_bytes(self, draft: Draft) -> bytes:
        lines = [draft.title, '=' * len(draft.title), '']
        for section, content in draft.content.items():
            lines.append(section.replace('_', ' ').title())
            lines.append('-' * len(lines[-1]))
            lines.append(content)
            lines.append('')
        lines.append('Sources Used')
        lines.append('------------')
        for citation in draft.citations:
            lines.append(f'* {citation.document_id}: {citation.snippet or citation.chunk_id}')
        return '\n'.join(lines).encode('utf-8')

    def to_html_bytes(self, draft: Draft) -> bytes:
        html_parts = [
            '<html><head><meta charset="utf-8"><title>{}</title></head><body>'.format(self._escape(draft.title)),
            f'<h1>{self._escape(draft.title)}</h1>',
        ]
        for section, content in draft.content.items():
            html_parts.append(f'<h2>{self._escape(section.replace("_", " ").title())}</h2>')
            html_parts.append(f'<p>{self._escape(content).replace(chr(10), "<br/>")}</p>')
        html_parts.append('<h2>Sources Used</h2><ul>')
        for citation in draft.citations:
            html_parts.append(
                f'<li><strong>{self._escape(citation.document_id)}</strong>: {self._escape(citation.snippet or citation.chunk_id)}</li>'
            )
        html_parts.append('</ul></body></html>')
        return ''.join(html_parts).encode('utf-8')

    def _render_markdown(self, draft: Draft) -> str:
        lines = [f'# {draft.title}', '']
        for section, content in draft.content.items():
            pretty = section.replace('_', ' ').title()
            lines.append(f'## {pretty}')
            lines.append(content)
            lines.append('')
        lines.append('## Sources Used')
        for citation in draft.citations:
            lines.append(f'- {citation.document_id}: {citation.snippet or citation.chunk_id}')
        return '\n'.join(lines)

    def _escape(self, value: str) -> str:
        return (
            value.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
        )


export_service = ExportService()
