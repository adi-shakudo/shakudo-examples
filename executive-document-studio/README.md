# Executive Document Studio

A premium Next.js + FastAPI demo app for secure, grounded executive document drafting.

## What this demo shows
- Figma-like enterprise UI with multi-pane drafting workspace
- Private internal document working set
- Live streaming draft generation via SSE
- Grounded provenance / citation panel
- Seeded George Weston-style mock documents and templates
- Persisted draft records in SQLite
- Real backend workflows for ingestion, retrieval, refinement, version history, audit logs, and exports

## Project structure

- `frontend/` — Next.js 14 app
- `backend/` — FastAPI backend with seeded demo data and authoring APIs
- `specs/` — original product/technical spec

## Backend capabilities
- `POST /api/documents/text` — create a document from raw text
- `POST /api/documents/upload` — upload `.txt`, `.pdf`, or `.docx` and extract text
- `GET /api/documents/search` — search across document chunks
- `GET /api/documents/audit` — inspect recent audit trail entries
- `POST /api/drafts/generate` — stream a new draft via SSE
- `POST /api/drafts/{draft_id}/refine` — stream a refined draft version via SSE
- `GET /api/drafts/{draft_id}/versions` — retrieve full draft lineage
- `POST /api/export/{draft_id}?format=markdown|text|html` — export drafts in multiple formats

## Run locally

### Backend
```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Then open: http://localhost:3000

## Notes
- The current backend uses deterministic retrieval/ranking and deterministic draft composition to maximize demo reliability.
- The UI is optimized to feel premium and enterprise-grade, with strong visual surfaces and visible runtime state.
- The backend now supports uploads, chunking, refinement, lineage, audit logs, and richer exports.
- Future upgrades can swap in true embeddings/vector infrastructure, auth, and production storage.
