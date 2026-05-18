"""Sync vocabulary_chapters from vocabulary_words."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_youdao_wordbook import load_database_url  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync vocabulary_chapters from vocabulary_words.")
    parser.add_argument(
        "--sources",
        default="system,youdao",
        help="Comma-separated sources to sync. Default: system,youdao",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete chapter rows for selected sources when no matching words exist.",
    )
    return parser.parse_args()


def chapter_table_sql() -> str:
    return """
CREATE TABLE IF NOT EXISTS vocabulary_chapters (
    id SERIAL PRIMARY KEY,
    chapter_name VARCHAR(100) NOT NULL,
    label VARCHAR(100) NOT NULL,
    audio VARCHAR(255) DEFAULT '',
    source VARCHAR(20) NOT NULL DEFAULT 'system',
    group_count INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_vocabulary_chapters_source_chapter UNIQUE (source, chapter_name)
);
ALTER TABLE vocabulary_chapters ADD COLUMN IF NOT EXISTS audio VARCHAR(255) DEFAULT '';
CREATE INDEX IF NOT EXISTS ix_vocabulary_chapters_id ON vocabulary_chapters (id);
CREATE INDEX IF NOT EXISTS ix_vocabulary_chapters_chapter_name ON vocabulary_chapters (chapter_name);
CREATE INDEX IF NOT EXISTS ix_vocabulary_chapters_source ON vocabulary_chapters (source);
CREATE INDEX IF NOT EXISTS ix_vocabulary_chapters_sort_order ON vocabulary_chapters (sort_order);
"""


def source_priority(source: str) -> int:
    priorities = {
        "system": 1,
        "youdao": 2,
        "custom": 3,
    }
    return priorities.get(source, 9)


async def fetch_chapter_stats(conn: Any, sources: list[str]) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT
            source,
            chapter_name,
            COUNT(*)::int AS word_count,
            COUNT(DISTINCT COALESCE(group_name, ''))::int AS group_count,
            MAX(NULLIF(
                CASE
                    WHEN metadata IS NOT NULL AND metadata <> '' AND left(metadata, 1) = '{'
                    THEN metadata::jsonb ->> 'staticChapterAudio'
                    ELSE ''
                END,
                ''
            )) AS audio
        FROM vocabulary_words
        WHERE source = ANY($1::text[])
          AND user_id IS NULL
        GROUP BY source, chapter_name
        ORDER BY
            CASE source
                WHEN 'system' THEN 1
                WHEN 'youdao' THEN 2
                WHEN 'custom' THEN 3
                ELSE 9
            END,
            chapter_name
        """,
        sources,
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "source": row["source"],
                "chapter_name": row["chapter_name"],
                "label": row["chapter_name"],
                "audio": row["audio"] or "",
                "group_count": row["group_count"],
                "word_count": row["word_count"],
            }
        )
    return result


async def sync_chapters(*, sources: list[str], prune: bool) -> dict[str, int]:
    import asyncpg

    database_url = load_database_url()
    conn = await asyncpg.connect(database_url)
    try:
        await conn.execute(chapter_table_sql())
        rows = await fetch_chapter_stats(conn, sources)

        updated = 0
        async with conn.transaction():
            if prune:
                await conn.execute(
                    """
                    DELETE FROM vocabulary_chapters
                    WHERE source = ANY($1::text[])
                      AND NOT EXISTS (
                          SELECT 1
                          FROM vocabulary_words
                          WHERE vocabulary_words.source = vocabulary_chapters.source
                            AND vocabulary_words.chapter_name = vocabulary_chapters.chapter_name
                            AND vocabulary_words.user_id IS NULL
                      )
                    """,
                    sources,
                )

            for index, row in enumerate(rows, start=1):
                # Keep each source in its own stable range while still producing one global order.
                sort_order = source_priority(row["source"]) * 1000 + index
                await conn.execute(
                    """
                    INSERT INTO vocabulary_chapters (
                        chapter_name,
                        label,
                        audio,
                        source,
                        group_count,
                        word_count,
                        sort_order
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (source, chapter_name)
                    DO UPDATE SET
                        label = EXCLUDED.label,
                        audio = EXCLUDED.audio,
                        group_count = EXCLUDED.group_count,
                        word_count = EXCLUDED.word_count,
                        sort_order = EXCLUDED.sort_order,
                        updated_at = now()
                    """,
                    row["chapter_name"],
                    row["label"],
                    row["audio"],
                    row["source"],
                    row["group_count"],
                    row["word_count"],
                    sort_order,
                )
                updated += 1

        return {"synced": updated}
    finally:
        await conn.close()


def main() -> None:
    args = parse_args()
    sources = [source.strip() for source in args.sources.split(",") if source.strip()]
    if not sources:
        raise ValueError("At least one source is required.")
    result = asyncio.run(sync_chapters(sources=sources, prune=args.prune))
    print(f"sources: {', '.join(sources)}")
    print(f"synced chapters: {result['synced']}")


if __name__ == "__main__":
    main()
