from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List
from uuid import uuid4

from docx import Document as DocxDocument
from fastapi import UploadFile
from PyPDF2 import PdfReader

from app.models.schemas import Chunk, Document, DocumentCreateText, DocumentType, SearchResult
from app.services import database
from app.services.audit_service import audit_service


class DocumentService:
    async def list_documents(self) -> List[Document]:
        rows = await database.fetch_all('SELECT * FROM documents ORDER BY date DESC, title ASC')
        return [self._row_to_document(row) for row in rows]

    async def get_document(self, document_id: str) -> Document | None:
        row = await database.fetch_one('SELECT * FROM documents WHERE id = ?', (document_id,))
        return self._row_to_document(row) if row else None

    async def get_chunks_for_documents(self, document_ids: list[str]) -> list[Chunk]:
        if not document_ids:
            return []
        placeholders = ', '.join('?' for _ in document_ids)
        rows = await database.fetch_all(
            f'SELECT * FROM chunks WHERE document_id IN ({placeholders}) ORDER BY document_id, position ASC',
            tuple(document_ids),
        )
        return [self._row_to_chunk(row) for row in rows]

    async def get_chunk(self, chunk_id: str) -> Chunk | None:
        row = await database.fetch_one('SELECT * FROM chunks WHERE id = ?', (chunk_id,))
        return self._row_to_chunk(row) if row else None

    async def search(self, query: str, limit: int = 10, doc_ids: list[str] | None = None) -> list[SearchResult]:
        query_tokens = self._tokenize(query)
        if doc_ids:
            chunks = await self.get_chunks_for_documents(doc_ids)
        else:
            rows = await database.fetch_all('SELECT * FROM chunks ORDER BY document_id, position ASC')
            chunks = [self._row_to_chunk(row) for row in rows]

        scored: list[SearchResult] = []
        for chunk in chunks:
            score, matched_terms = self._score_chunk(query_tokens, chunk.text)
            if score <= 0:
                continue
            scored.append(
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    text=chunk.text,
                    score=score,
                    matched_terms=matched_terms,
                    metadata=chunk.metadata,
                )
            )
        return sorted(scored, key=lambda item: (item.score, len(item.text)), reverse=True)[:limit]

    async def create_text_document(self, payload: DocumentCreateText) -> Document:
        document_id = f'doc_{uuid4().hex[:10]}'
        now = datetime.utcnow().isoformat()
        summary = payload.summary or self._summarize(payload.content)
        await database.execute(
            '''
            INSERT INTO documents (id, title, type, tags, date, summary, content, source_name, source_kind, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                document_id,
                payload.title,
                payload.type.value,
                database.dumps(payload.tags),
                payload.date,
                summary,
                payload.content,
                payload.title,
                'text',
                now,
                now,
            ),
        )
        await self._replace_chunks(document_id, payload.title, payload.content)
        await audit_service.log('document.created', 'document', document_id, {'source_kind': 'text'})
        document = await self.get_document(document_id)
        assert document is not None
        return document

    async def upload_document(self, file: UploadFile, document_type: DocumentType, tags: list[str], date: str | None = None) -> Document:
        if not file.filename:
            raise ValueError('Uploaded file must include a filename')

        suffix = Path(file.filename).suffix.lower()
        upload_path = database.UPLOADS_DIR / f'{uuid4().hex}{suffix}'
        content_bytes = await file.read()
        upload_path.write_bytes(content_bytes)
        content = self._extract_text(upload_path, suffix)
        if not content.strip():
            raise ValueError('Unable to extract any text from uploaded file')

        document_id = f'doc_{uuid4().hex[:10]}'
        now = datetime.utcnow().isoformat()
        title = Path(file.filename).stem.replace('_', ' ').replace('-', ' ').title()
        summary = self._summarize(content)
        await database.execute(
            '''
            INSERT INTO documents (id, title, type, tags, date, summary, content, source_name, source_kind, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                document_id,
                title,
                document_type.value,
                database.dumps(tags),
                date,
                summary,
                content,
                file.filename,
                suffix.lstrip('.') or 'file',
                now,
                now,
            ),
        )
        await self._replace_chunks(document_id, title, content)
        await audit_service.log(
            'document.uploaded',
            'document',
            document_id,
            {'filename': file.filename, 'source_kind': suffix.lstrip('.') or 'file'},
        )
        document = await self.get_document(document_id)
        assert document is not None
        return document

    async def list_audit_logs(self, limit: int = 50):
        return await audit_service.list_recent(limit=limit)

    async def _replace_chunks(self, document_id: str, title: str, content: str) -> None:
        await database.execute('DELETE FROM chunks WHERE document_id = ?', (document_id,))
        chunks = self._chunk_text(content)
        rows = []
        for position, text in enumerate(chunks, start=1):
            rows.append(
                (
                    f'{document_id}_chunk_{position:03d}',
                    document_id,
                    title,
                    text,
                    position,
                    database.dumps({'position': position, 'word_count': len(text.split())}),
                )
            )
        await database.insert_many(
            'INSERT INTO chunks (id, document_id, document_title, text, position, metadata) VALUES (?, ?, ?, ?, ?, ?)',
            rows,
        )

    def _extract_text(self, path: Path, suffix: str) -> str:
        if suffix == '.pdf':
            reader = PdfReader(str(path))
            return '\n'.join((page.extract_text() or '') for page in reader.pages)
        if suffix == '.docx':
            doc = DocxDocument(str(path))
            return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
        return path.read_text(encoding='utf-8', errors='ignore')

    def _chunk_text(self, content: str, target_words: int = 110) -> list[str]:
        paragraphs = [segment.strip() for segment in re.split(r'\n\s*\n', content) if segment.strip()]
        if not paragraphs:
            paragraphs = [content.strip()]
        chunks: list[str] = []
        current: list[str] = []
        current_words = 0
        for paragraph in paragraphs:
            words = paragraph.split()
            if current and current_words + len(words) > target_words:
                chunks.append('\n\n'.join(current))
                current = [paragraph]
                current_words = len(words)
            else:
                current.append(paragraph)
                current_words += len(words)
        if current:
            chunks.append('\n\n'.join(current))
        return chunks

    def _summarize(self, content: str, max_words: int = 24) -> str:
        words = content.strip().split()
        summary = ' '.join(words[:max_words])
        return summary + ('…' if len(words) > max_words else '')

    def _tokenize(self, query: str) -> list[str]:
        return [token.lower() for token in re.findall(r'[A-Za-z0-9]+', query) if token.strip()]

    def _score_chunk(self, query_tokens: list[str], text: str) -> tuple[float, list[str]]:
        lower = text.lower()
        matched = [token for token in query_tokens if token in lower]
        exact_score = float(len(matched))
        phrase_bonus = 2.5 if ' '.join(query_tokens) in lower and query_tokens else 0.0
        coverage_bonus = (len(set(matched)) / max(len(set(query_tokens)), 1)) * 3.0 if matched else 0.0
        return exact_score + phrase_bonus + coverage_bonus, list(dict.fromkeys(matched))

    def _row_to_document(self, row) -> Document:
        return Document(
            id=row['id'],
            title=row['title'],
            type=row['type'],
            tags=database.loads(row['tags']) or [],
            date=row['date'],
            summary=row['summary'],
            content=row['content'],
            source_name=row.get('source_name'),
            source_kind=row.get('source_kind'),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _row_to_chunk(self, row) -> Chunk:
        return Chunk(
            id=row['id'],
            document_id=row['document_id'],
            document_title=row['document_title'],
            text=row['text'],
            position=row.get('position', 0),
            metadata=database.loads(row['metadata']) or {},
        )


document_service = DocumentService()
