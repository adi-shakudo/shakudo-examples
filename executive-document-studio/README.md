# Executive Document Studio

A premium Next.js + FastAPI demo app for secure, grounded executive document drafting.

## What this demo shows
- Figma-like enterprise UI with multi-pane drafting workspace
- Private internal document working set
- Live streaming draft generation via SSE
- Grounded provenance / citation panel
- Seeded George Weston-style mock documents and templates
- Persisted draft records in SQLite

## Project structure

- `frontend/` — Next.js 14 app
- `backend/` — FastAPI backend with seeded demo data
- `specs/` — original product/technical spec

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
- The current backend uses lightweight seeded retrieval logic suitable for demo reliability.
- The UI is optimized to feel premium and enterprise-grade, with strong visual surfaces and visible runtime state.
- Export currently supports markdown.
- This is a solid demo foundation for future upgrades to real embedding/vector infrastructure, auth, and document ingestion.
