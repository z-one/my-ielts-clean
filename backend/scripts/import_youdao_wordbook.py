"""Clean and optionally import a Youdao wordbook export.

Default mode only writes a cleaned JSON file. Add --import-db to insert rows
into the local vocabulary_words table.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


POS_RE = re.compile(
    r"(^|\n)\s*((?:n|v|vt|vi|adj|adv|prep|conj|pron|det|num|int|interj|abbr|aux|modal)\.)\s*",
    re.IGNORECASE,
)


@dataclass
class CleanResult:
    words: list[dict[str, Any]]
    duplicates: list[dict[str, Any]]
    skipped: list[dict[str, Any]]
    raw_total: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean/import Youdao wordbook raw JSON.")
    parser.add_argument("--raw", required=True, help="Path to youdao-wordbook-raw-*.json")
    parser.add_argument(
        "--out",
        default=str(REPO_DIR / "data" / "imports" / "youdao-wordbook-cleaned.json"),
        help="Cleaned JSON output path. Default: data/imports/youdao-wordbook-cleaned.json",
    )
    parser.add_argument("--chapter", default="有道单词本", help="chapter_name for imported rows")
    parser.add_argument("--group", default=None, help="group_name for imported rows")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200,
        help="Split cleaned words into chapter_name chunks. Default: 200. Use 0 to disable.",
    )
    parser.add_argument(
        "--source",
        default="youdao",
        help="Vocabulary source value. Default: youdao",
    )
    parser.add_argument("--user-id", type=int, default=None, help="Optional user_id for imported rows")
    parser.add_argument(
        "--import-db",
        action="store_true",
        help="Insert cleaned rows into the configured database. Omitted by default.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing rows with the same word/chapter/source/user_id.",
    )
    parser.add_argument(
        "--reset-source",
        action="store_true",
        help="Delete existing rows for the same source/user_id before importing.",
    )
    return parser.parse_args()


def read_raw(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_items(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in raw_data.get("pages", []):
        response = page.get("response") or {}
        data = response.get("data") or {}
        for item in data.get("itemList") or []:
            if isinstance(item, dict):
                items.append(item)
    return items


def default_group_name(raw_data: dict[str, Any]) -> str:
    exported_at = raw_data.get("exportedAt")
    if isinstance(exported_at, str) and exported_at:
        try:
            date_part = datetime.fromisoformat(exported_at.replace("Z", "+00:00")).date().isoformat()
            return f"有道导入-{date_part}"
        except ValueError:
            pass
    return "有道导入"


def extract_pos(trans: str) -> str:
    labels: list[str] = []
    seen: set[str] = set()
    for match in POS_RE.finditer(trans or ""):
        label = match.group(2).lower()
        if label not in seen:
            labels.append(label)
            seen.add(label)
    return "/".join(labels)


def normalize_item(
    item: dict[str, Any],
    *,
    chapter_name: str,
    group_name: str,
    source: str,
) -> dict[str, Any] | None:
    word = str(item.get("word") or "").strip()
    if not word:
        return None

    trans = str(item.get("trans") or "").strip()
    metadata = {
        "youdaoItemId": item.get("itemId"),
        "lanFrom": item.get("lanFrom"),
        "lanTo": item.get("lanTo"),
        "ukphone": item.get("ukphone"),
        "usphone": item.get("usphone"),
        "youdaoCreateTime": item.get("createTime"),
        "rawTrans": trans,
    }

    return {
        "chapter_name": chapter_name,
        "group_name": group_name,
        "word": [word],
        "word_variants": [word],
        "pos": extract_pos(trans),
        "meaning": trans,
        "example": "",
        "extra": "",
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "source": source,
    }


def chunk_chapter_name(base_chapter_name: str, word_index: int, chunk_size: int) -> str:
    if chunk_size <= 0:
        return base_chapter_name
    chunk_no = word_index // chunk_size + 1
    return f"{base_chapter_name} {chunk_no:02d}"


def chunk_group_name(base_group_name: str, word_index: int, chunk_size: int) -> str:
    if chunk_size <= 0:
        return base_group_name
    chunk_no = word_index // chunk_size + 1
    return f"{base_group_name} 第{chunk_no:02d}组"


def clean_words(
    raw_data: dict[str, Any],
    *,
    chapter_name: str,
    group_name: str,
    source: str,
    chunk_size: int,
) -> CleanResult:
    items = iter_items(raw_data)
    words: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen_words: set[str] = set()

    for index, item in enumerate(items):
        normalized = normalize_item(
            item,
            chapter_name=chapter_name,
            group_name=group_name,
            source=source,
        )
        if not normalized:
            skipped.append({"index": index, "reason": "missing word", "raw": item})
            continue

        word_key = normalized["word"][0].strip().lower()
        if word_key in seen_words:
            duplicates.append(
                {
                    "index": index,
                    "word": normalized["word"][0],
                    "keptPolicy": "keep first occurrence from time-sorted export",
                    "raw": item,
                }
            )
            continue

        seen_words.add(word_key)
        word_index = len(words)
        normalized["chapter_name"] = chunk_chapter_name(chapter_name, word_index, chunk_size)
        normalized["group_name"] = chunk_group_name(group_name, word_index, chunk_size)
        words.append(normalized)

    return CleanResult(words=words, duplicates=duplicates, skipped=skipped, raw_total=len(items))


def write_cleaned_output(
    path: Path,
    *,
    raw_data: dict[str, Any],
    result: CleanResult,
    chapter_name: str,
    group_name: str,
    source: str,
    chunk_size: int,
) -> None:
    chapter_names = sorted({word["chapter_name"] for word in result.words})
    payload = {
        "source": "youdao-wordbook-cleaned",
        "cleanedAt": datetime.now().isoformat(timespec="seconds"),
        "rawExportedAt": raw_data.get("exportedAt"),
        "chapterName": chapter_name,
        "groupName": group_name,
        "chunkSize": chunk_size,
        "chapterNames": chapter_names,
        "vocabularySource": source,
        "stats": {
            "rawTotal": result.raw_total,
            "cleanedTotal": len(result.words),
            "duplicateTotal": len(result.duplicates),
            "skippedTotal": len(result.skipped),
            "chapterTotal": len(chapter_names),
        },
        "duplicates": result.duplicates,
        "skipped": result.skipped,
        "words": result.words,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def import_to_db(
    words: list[dict[str, Any]],
    *,
    user_id: int | None,
    replace_existing: bool,
    reset_source: bool,
) -> dict[str, int]:
    current_dir = Path.cwd()
    os.chdir(BACKEND_DIR)
    try:
        try:
            from app.database import Base, SessionLocal, engine
            from app.models.vocabulary import VocabularyWord
            from app.schemas.vocabulary import encode_word_list
        except ModuleNotFoundError as error:
            if error.name not in {"sqlalchemy", "psycopg2", "psycopg", "pg8000"}:
                raise
            database_url = load_database_url()
            if database_url.startswith(("postgresql://", "postgres://")):
                try:
                    import asyncpg  # noqa: F401

                    return asyncio.run(
                        import_to_postgres_asyncpg(
                            words,
                            database_url=database_url,
                            user_id=user_id,
                            replace_existing=replace_existing,
                            reset_source=reset_source,
                        )
                    )
                except ModuleNotFoundError:
                    pass
                return import_to_postgres_cli(
                    words,
                    database_url=database_url,
                    user_id=user_id,
                    replace_existing=replace_existing,
                    reset_source=reset_source,
                )
            return import_to_sqlite(
                words,
                user_id=user_id,
                replace_existing=replace_existing,
                reset_source=reset_source,
            )

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            created = 0
            skipped_existing = 0
            replaced = 0
            deleted_existing = 0

            if reset_source and words:
                delete_query = db.query(VocabularyWord).filter(VocabularyWord.source == words[0]["source"])
                if user_id is None:
                    delete_query = delete_query.filter(VocabularyWord.user_id.is_(None))
                else:
                    delete_query = delete_query.filter(VocabularyWord.user_id == user_id)
                deleted_existing = delete_query.delete(synchronize_session=False)

            for item in words:
                word_text = item["word"][0]
                query = db.query(VocabularyWord).filter(
                    VocabularyWord.chapter_name == item["chapter_name"],
                    VocabularyWord.source == item["source"],
                    VocabularyWord.word.in_([word_text, encode_word_list([word_text])]),
                )
                if user_id is None:
                    query = query.filter(VocabularyWord.user_id.is_(None))
                else:
                    query = query.filter(VocabularyWord.user_id == user_id)

                existing = query.first()
                if existing and not replace_existing:
                    skipped_existing += 1
                    continue

                if existing and replace_existing:
                    existing.group_name = item["group_name"]
                existing.pos = item["pos"]
                existing.meaning = item["meaning"]
                existing.example = item["example"]
                existing.extra = item["extra"]
                existing.word_variants = json.dumps(item.get("word_variants") or item["word"], ensure_ascii=False)
                existing.metadata_json = item.get("metadata", "")
                replaced += 1
                continue

                db.add(
                    VocabularyWord(
                        user_id=user_id,
                        chapter_name=item["chapter_name"],
                        group_name=item["group_name"],
                        word=word_text,
                        word_variants=json.dumps(item.get("word_variants") or item["word"], ensure_ascii=False),
                        pos=item["pos"],
                        meaning=item["meaning"],
                        example=item["example"],
                        extra=item["extra"],
                        metadata_json=item.get("metadata", ""),
                        source=item["source"],
                    )
                )
                created += 1

            db.commit()
            return {
                "created": created,
                "replaced": replaced,
                "skippedExisting": skipped_existing,
                "deletedExisting": deleted_existing,
            }
        finally:
            db.close()
    finally:
        os.chdir(current_dir)


def load_database_url() -> str:
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "DATABASE_URL":
                return value.strip().strip("\"'")
    return "postgresql://ielts:ielts_password@localhost:5432/ielts_db"


def sqlite_path_from_url(database_url: str) -> Path:
    if database_url == "sqlite:///:memory:":
        raise RuntimeError("Cannot import persistent data into sqlite memory database.")
    if not database_url.startswith("sqlite:///"):
        raise RuntimeError(
            "SQLAlchemy is not installed and DATABASE_URL is not sqlite. "
            "Install backend requirements, then rerun with --import-db."
        )

    raw_path = database_url.removeprefix("sqlite:///")
    path = Path(raw_path)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path


def sql_string(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def postgres_psql_base_cmd(database_url: str, *, stdin: bool) -> list[str]:
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip("/") or "postgres"
    user = parsed.username or "postgres"
    host = parsed.hostname or "localhost"
    password = parsed.password or ""
    port = str(parsed.port or 5432)

    local_psql = os.environ.get("PSQL_BIN") or "psql"
    if shutil_which(local_psql):
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password
        postgres_psql_base_cmd.env = env
        return [
            local_psql,
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            db_name,
        ]

    container = os.environ.get("POSTGRES_CONTAINER", "ielts-postgres")
    postgres_psql_base_cmd.env = None
    docker_cmd = ["docker", "exec"]
    if stdin:
        docker_cmd.append("-i")
    return docker_cmd + [
        container,
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        user,
        "-d",
        db_name,
    ]


def shutil_which(command: str) -> str | None:
    from shutil import which

    return which(command)


def run_psql(database_url: str, sql: str, *, stdin: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = postgres_psql_base_cmd(database_url, stdin=stdin)
    env = getattr(postgres_psql_base_cmd, "env", None)
    return subprocess.run(
        cmd,
        input=sql if stdin else None,
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )


def postgres_count(database_url: str, source: str, user_id: int | None) -> int:
    if user_id is None:
        where = f"source = {sql_string(source)} AND user_id IS NULL"
    else:
        where = f"source = {sql_string(source)} AND user_id = {user_id}"
    sql = f"SELECT COUNT(*) FROM vocabulary_words WHERE {where};"
    try:
        result = run_psql(database_url, sql)
    except subprocess.CalledProcessError:
        return 0
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)
    return 0


def postgres_table_sql() -> str:
    return """
CREATE TABLE IF NOT EXISTS vocabulary_words (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL,
    chapter_name VARCHAR(100) NOT NULL,
    group_name VARCHAR(100) NULL,
    word TEXT NOT NULL,
    pos VARCHAR(100) DEFAULT '',
    meaning TEXT DEFAULT '',
    example TEXT DEFAULT '',
    extra TEXT DEFAULT '',
    word_variants TEXT DEFAULT '',
    metadata TEXT DEFAULT '',
    source VARCHAR(20) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_vocabulary_words_id ON vocabulary_words (id);
CREATE INDEX IF NOT EXISTS ix_vocabulary_words_user_id ON vocabulary_words (user_id);
CREATE INDEX IF NOT EXISTS ix_vocabulary_words_chapter_name ON vocabulary_words (chapter_name);
CREATE INDEX IF NOT EXISTS ix_vocabulary_words_source ON vocabulary_words (source);
"""


async def ensure_postgres_table(conn: Any) -> None:
    await conn.execute(postgres_table_sql())


async def postgres_async_count(conn: Any, source: str, user_id: int | None) -> int:
    if user_id is None:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM vocabulary_words WHERE source = $1 AND user_id IS NULL",
            source,
        )
    return await conn.fetchval(
        "SELECT COUNT(*) FROM vocabulary_words WHERE source = $1 AND user_id = $2",
        source,
        user_id,
    )


async def import_to_postgres_asyncpg(
    words: list[dict[str, Any]],
    *,
    database_url: str,
    user_id: int | None,
    replace_existing: bool,
    reset_source: bool,
) -> dict[str, int]:
    import asyncpg

    source = words[0]["source"] if words else "youdao"
    conn = await asyncpg.connect(database_url)
    try:
        await ensure_postgres_table(conn)
        before_count = await postgres_async_count(conn, source, user_id)

        created = 0
        skipped_existing = 0
        replaced = 0
        deleted_existing = 0

        async with conn.transaction():
            if reset_source and words:
                if user_id is None:
                    deleted = await conn.execute(
                        "DELETE FROM vocabulary_words WHERE source = $1 AND user_id IS NULL",
                        source,
                    )
                else:
                    deleted = await conn.execute(
                        "DELETE FROM vocabulary_words WHERE source = $1 AND user_id = $2",
                        source,
                        user_id,
                    )
                deleted_existing = int(deleted.split()[-1])

            for item in words:
                word_text = item["word"][0]
                encoded_word = json.dumps(item["word"], ensure_ascii=False)
                if user_id is None:
                    existing_id = await conn.fetchval(
                        """
                        SELECT id FROM vocabulary_words
                        WHERE chapter_name = $1
                          AND source = $2
                          AND word = ANY($3::text[])
                          AND user_id IS NULL
                        LIMIT 1
                        """,
                        item["chapter_name"],
                        item["source"],
                        [word_text, encoded_word],
                    )
                else:
                    existing_id = await conn.fetchval(
                        """
                        SELECT id FROM vocabulary_words
                        WHERE chapter_name = $1
                          AND source = $2
                          AND word = ANY($3::text[])
                          AND user_id = $4
                        LIMIT 1
                        """,
                        item["chapter_name"],
                        item["source"],
                        [word_text, encoded_word],
                        user_id,
                    )

                if existing_id and not replace_existing:
                    skipped_existing += 1
                    continue

                if existing_id and replace_existing:
                    await conn.execute(
                        """
                        UPDATE vocabulary_words
                        SET group_name = $1,
                            word = $2,
                            pos = $3,
                            meaning = $4,
                            example = $5,
                            extra = $6,
                            word_variants = $7,
                            metadata = $8,
                            updated_at = now()
                        WHERE id = $9
                        """,
                        item["group_name"],
                        word_text,
                        item["pos"],
                        item["meaning"],
                        item["example"],
                        item["extra"],
                        json.dumps(item.get("word_variants") or item["word"], ensure_ascii=False),
                        item.get("metadata", ""),
                        existing_id,
                    )
                    replaced += 1
                    continue

                await conn.execute(
                    """
                    INSERT INTO vocabulary_words (
                        user_id, chapter_name, group_name, word, word_variants, pos, meaning, example, extra, metadata, source
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    user_id,
                    item["chapter_name"],
                    item["group_name"],
                    word_text,
                    json.dumps(item.get("word_variants") or item["word"], ensure_ascii=False),
                    item["pos"],
                    item["meaning"],
                    item["example"],
                    item["extra"],
                    item.get("metadata", ""),
                    item["source"],
                )
                created += 1

        after_count = await postgres_async_count(conn, source, user_id)
        if reset_source:
            created = after_count
        return {
            "created": created,
            "replaced": replaced,
            "skippedExisting": skipped_existing,
            "deletedExisting": deleted_existing,
        }
    finally:
        await conn.close()


def import_to_postgres_cli(
    words: list[dict[str, Any]],
    *,
    database_url: str,
    user_id: int | None,
    replace_existing: bool,
    reset_source: bool,
) -> dict[str, int]:
    source = words[0]["source"] if words else "youdao"
    before_count = postgres_count(database_url, source, user_id)

    statements = ["BEGIN;", postgres_table_sql()]
    if reset_source and words:
        if user_id is None:
            statements.append(f"DELETE FROM vocabulary_words WHERE source = {sql_string(source)} AND user_id IS NULL;")
        else:
            statements.append(
                f"DELETE FROM vocabulary_words WHERE source = {sql_string(source)} AND user_id = {user_id};"
            )

    for item in words:
        word_text = item["word"][0]
        encoded_word = json.dumps(item["word"], ensure_ascii=False)
        user_condition = "user_id IS NULL" if user_id is None else f"user_id = {user_id}"
        existing_condition = (
            f"chapter_name = {sql_string(item['chapter_name'])} "
            f"AND source = {sql_string(item['source'])} "
            f"AND word IN ({sql_string(word_text)}, {sql_string(encoded_word)}) "
            f"AND {user_condition}"
        )

        if replace_existing:
            statements.append(
                f"""
UPDATE vocabulary_words
SET group_name = {sql_string(item['group_name'])},
    word = {sql_string(word_text)},
    pos = {sql_string(item['pos'])},
    meaning = {sql_string(item['meaning'])},
    example = {sql_string(item['example'])},
    extra = {sql_string(item['extra'])},
    word_variants = {sql_string(json.dumps(item.get('word_variants') or item['word'], ensure_ascii=False))},
    metadata = {sql_string(item.get('metadata', ''))},
    updated_at = now()
WHERE {existing_condition};
"""
            )

        statements.append(
            f"""
INSERT INTO vocabulary_words (
    user_id, chapter_name, group_name, word, word_variants, pos, meaning, example, extra, metadata, source
)
SELECT
    {user_id if user_id is not None else 'NULL'},
    {sql_string(item['chapter_name'])},
    {sql_string(item['group_name'])},
    {sql_string(word_text)},
    {sql_string(json.dumps(item.get('word_variants') or item['word'], ensure_ascii=False))},
    {sql_string(item['pos'])},
    {sql_string(item['meaning'])},
    {sql_string(item['example'])},
    {sql_string(item['extra'])},
    {sql_string(item.get('metadata', ''))},
    {sql_string(item['source'])}
WHERE NOT EXISTS (
    SELECT 1 FROM vocabulary_words WHERE {existing_condition}
);
"""
        )

    statements.append("COMMIT;")
    try:
        run_psql(database_url, "\n".join(statements))
    except subprocess.CalledProcessError as error:
        print(error.stdout)
        print(error.stderr, file=sys.stderr)
        raise

    after_count = postgres_count(database_url, source, user_id)
    deleted_existing = before_count if reset_source else 0
    created = after_count if reset_source else max(after_count - before_count, 0)
    skipped_existing = 0 if reset_source else max(len(words) - created, 0)
    return {
        "created": created,
        "replaced": 0,
        "skippedExisting": skipped_existing,
        "deletedExisting": deleted_existing,
    }


def ensure_sqlite_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS vocabulary_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            chapter_name VARCHAR(100) NOT NULL,
            group_name VARCHAR(100) NULL,
            word TEXT NOT NULL,
            pos VARCHAR(100) DEFAULT '',
            meaning TEXT DEFAULT '',
            example TEXT DEFAULT '',
            extra TEXT DEFAULT '',
            word_variants TEXT DEFAULT '',
            metadata TEXT DEFAULT '',
            source VARCHAR(20) NOT NULL DEFAULT 'system',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS ix_vocabulary_words_id ON vocabulary_words (id)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_vocabulary_words_user_id ON vocabulary_words (user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_vocabulary_words_chapter_name ON vocabulary_words (chapter_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_vocabulary_words_source ON vocabulary_words (source)")


def import_to_sqlite(
    words: list[dict[str, Any]],
    *,
    user_id: int | None,
    replace_existing: bool,
    reset_source: bool,
) -> dict[str, int]:
    db_path = sqlite_path_from_url(load_database_url())
    db_path.parent.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped_existing = 0
    replaced = 0
    deleted_existing = 0

    with sqlite3.connect(db_path) as conn:
        ensure_sqlite_table(conn)
        if reset_source and words:
            if user_id is None:
                cursor = conn.execute(
                    "DELETE FROM vocabulary_words WHERE source = ? AND user_id IS NULL",
                    (words[0]["source"],),
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM vocabulary_words WHERE source = ? AND user_id = ?",
                    (words[0]["source"], user_id),
                )
            deleted_existing = cursor.rowcount

        for item in words:
            word_text = item["word"][0]
            encoded_word = json.dumps(item["word"], ensure_ascii=False)
            if user_id is None:
                existing = conn.execute(
                    """
                    SELECT id FROM vocabulary_words
                    WHERE chapter_name = ?
                      AND source = ?
                      AND word IN (?, ?)
                      AND user_id IS NULL
                    LIMIT 1
                    """,
                    (item["chapter_name"], item["source"], word_text, encoded_word),
                ).fetchone()
            else:
                existing = conn.execute(
                    """
                    SELECT id FROM vocabulary_words
                    WHERE chapter_name = ?
                      AND source = ?
                      AND word IN (?, ?)
                      AND user_id = ?
                    LIMIT 1
                    """,
                    (item["chapter_name"], item["source"], word_text, encoded_word, user_id),
                ).fetchone()

            if existing and not replace_existing:
                skipped_existing += 1
                continue

            if existing and replace_existing:
                conn.execute(
                    """
                    UPDATE vocabulary_words
                    SET group_name = ?,
                        word = ?,
                        pos = ?,
                        meaning = ?,
                        example = ?,
                        extra = ?,
                        word_variants = ?,
                        metadata = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        item["group_name"],
                        word_text,
                        item["pos"],
                        item["meaning"],
                        item["example"],
                        item["extra"],
                        json.dumps(item.get("word_variants") or item["word"], ensure_ascii=False),
                        item.get("metadata", ""),
                        existing[0],
                    ),
                )
                replaced += 1
                continue

            conn.execute(
                """
                INSERT INTO vocabulary_words (
                    user_id,
                    chapter_name,
                    group_name,
                    word,
                    pos,
                    meaning,
                    example,
                    extra,
                    word_variants,
                    metadata,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    item["chapter_name"],
                    item["group_name"],
                    word_text,
                    item["pos"],
                    item["meaning"],
                    item["example"],
                    item["extra"],
                    json.dumps(item.get("word_variants") or item["word"], ensure_ascii=False),
                    item.get("metadata", ""),
                    item["source"],
                ),
            )
            created += 1

    return {
        "created": created,
        "replaced": replaced,
        "skippedExisting": skipped_existing,
        "deletedExisting": deleted_existing,
    }


def main() -> None:
    args = parse_args()
    raw_path = Path(args.raw)
    out_path = Path(args.out)

    raw_data = read_raw(raw_path)
    group_name = args.group or default_group_name(raw_data)
    result = clean_words(
        raw_data,
        chapter_name=args.chapter,
        group_name=group_name,
        source=args.source,
        chunk_size=args.chunk_size,
    )
    write_cleaned_output(
        out_path,
        raw_data=raw_data,
        result=result,
        chapter_name=args.chapter,
        group_name=group_name,
        source=args.source,
        chunk_size=args.chunk_size,
    )

    print(f"raw total: {result.raw_total}")
    print(f"cleaned total: {len(result.words)}")
    print(f"duplicates removed: {len(result.duplicates)}")
    print(f"skipped: {len(result.skipped)}")
    print(f"cleaned file: {out_path}")

    if args.import_db:
        db_result = import_to_db(
            result.words,
            user_id=args.user_id,
            replace_existing=args.replace_existing,
            reset_source=args.reset_source,
        )
        print(f"db deleted existing: {db_result['deletedExisting']}")
        print(f"db created: {db_result['created']}")
        print(f"db replaced: {db_result['replaced']}")
        print(f"db skipped existing: {db_result['skippedExisting']}")
    else:
        print("dry run only: database was not changed. Add --import-db to insert rows.")


if __name__ == "__main__":
    main()
