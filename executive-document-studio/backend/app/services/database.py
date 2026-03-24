from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
DB_PATH = DATA_DIR / 'studio.db'


def _row_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


async def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            '''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                tags TEXT NOT NULL,
                date TEXT,
                summary TEXT,
                content TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                sections TEXT NOT NULL,
                system_prompt TEXT
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                document_title TEXT NOT NULL,
                text TEXT NOT NULL,
                metadata TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY,
                template_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                citations TEXT NOT NULL,
                working_set TEXT NOT NULL,
                version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            '''
        )
        await db.commit()


async def fetch_all(query: str, params: tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _row_factory
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return rows


async def fetch_one(query: str, params: tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _row_factory
        cursor = await db.execute(query, params)
        row = await cursor.fetchone()
        await cursor.close()
        return row


async def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, params)
        await db.commit()


async def insert_many(query: str, rows: list[tuple[Any, ...]]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(query, rows)
        await db.commit()


def dumps(value: Any) -> str:
    return json.dumps(value)


def loads(value: str) -> Any:
    return json.loads(value)
