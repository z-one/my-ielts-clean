"""Migrate vocabulary metadata out of display fields.

This script:
- adds vocabulary_words.word_variants
- adds vocabulary_words.metadata
- adds vocabulary_chapters.audio
- moves old JSON stored in vocabulary_words.extra into metadata
- restores vocabulary_words.extra to the page-display value
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any


if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_youdao_wordbook import load_database_url  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate vocabulary extra/metadata fields.")
    parser.add_argument(
        "--sources",
        default="system,youdao",
        help="Comma-separated sources to migrate. Default: system,youdao",
    )
    return parser.parse_args()


def try_load_json(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    text = value.strip()
    if not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def clean_metadata(parsed: dict[str, Any], *, source: str, word: str) -> tuple[str, str, str]:
    if source == "system":
        variants = parsed.get("wordVariants")
        if not isinstance(variants, list) or not variants:
            variants = [word]
        metadata = {
            key: value
            for key, value in parsed.items()
            if key not in {"wordVariants", "rawExtra"}
        }
        extra = str(parsed.get("rawExtra") or "")
        return extra, json.dumps(variants, ensure_ascii=False), json.dumps(metadata, ensure_ascii=False)

    if source == "youdao":
        metadata = dict(parsed)
        variants = [word]
        extra = ""
        return extra, json.dumps(variants, ensure_ascii=False), json.dumps(metadata, ensure_ascii=False)

    return "", json.dumps([word], ensure_ascii=False), json.dumps(parsed, ensure_ascii=False)


async def migrate(*, sources: list[str]) -> dict[str, int]:
    import asyncpg

    conn = await asyncpg.connect(load_database_url())
    try:
        await conn.execute(
            """
            ALTER TABLE vocabulary_words ADD COLUMN IF NOT EXISTS word_variants TEXT DEFAULT '';
            ALTER TABLE vocabulary_words ADD COLUMN IF NOT EXISTS metadata TEXT DEFAULT '';
            ALTER TABLE vocabulary_chapters ADD COLUMN IF NOT EXISTS audio VARCHAR(255) DEFAULT '';
            """
        )

        rows = await conn.fetch(
            """
            SELECT id, source, word, extra, word_variants, metadata
            FROM vocabulary_words
            WHERE source = ANY($1::text[])
            ORDER BY id
            """,
            sources,
        )

        migrated = 0
        normalized = 0
        async with conn.transaction():
            for row in rows:
                word = row["word"] or ""
                variants = row["word_variants"] or ""
                metadata = row["metadata"] or ""
                parsed = try_load_json(row["extra"])

                if parsed:
                    extra, new_variants, new_metadata = clean_metadata(parsed, source=row["source"], word=word)
                    await conn.execute(
                        """
                        UPDATE vocabulary_words
                        SET extra = $1,
                            word_variants = $2,
                            metadata = $3,
                            updated_at = now()
                        WHERE id = $4
                        """,
                        extra,
                        new_variants,
                        new_metadata,
                        row["id"],
                    )
                    migrated += 1
                    continue

                if not variants:
                    await conn.execute(
                        """
                        UPDATE vocabulary_words
                        SET word_variants = $1,
                            metadata = COALESCE(NULLIF(metadata, ''), $2),
                            updated_at = now()
                        WHERE id = $3
                        """,
                        json.dumps([word], ensure_ascii=False),
                        metadata,
                        row["id"],
                    )
                    normalized += 1

        await conn.execute(
            """
            UPDATE vocabulary_chapters AS c
            SET audio = COALESCE(chapter_audio.audio, ''),
                updated_at = now()
            FROM (
                SELECT
                    source,
                    chapter_name,
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
                GROUP BY source, chapter_name
            ) AS chapter_audio
            WHERE c.source = chapter_audio.source
              AND c.chapter_name = chapter_audio.chapter_name
            """,
            sources,
        )

        return {"checked": len(rows), "migrated": migrated, "normalized": normalized}
    finally:
        await conn.close()


def main() -> None:
    args = parse_args()
    sources = [source.strip() for source in args.sources.split(",") if source.strip()]
    result = asyncio.run(migrate(sources=sources))
    print(f"sources: {', '.join(sources)}")
    print(f"checked rows: {result['checked']}")
    print(f"migrated rows: {result['migrated']}")
    print(f"normalized rows: {result['normalized']}")


if __name__ == "__main__":
    main()
