"""Import user-owned data from a legacy SQLite database into Postgres.

This script is intended for one-time production migration. It imports users,
progress, settings, exam records, and user/custom vocabulary rows. System
vocabulary should be imported separately from JSON.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import execute_values


BACKEND_DIR = Path(__file__).resolve().parents[1]

TABLES = [
    {
        "name": "users",
        "columns": ["id", "username", "email", "password_hash", "is_active", "created_at", "last_login"],
        "where": "",
    },
    {
        "name": "chapter_progress",
        "columns": ["id", "user_id", "chapter_name", "status", "created_at", "updated_at"],
        "where": "",
    },
    {
        "name": "word_progress",
        "columns": [
            "id",
            "user_id",
            "word_id",
            "chapter_name",
            "spell_value",
            "spell_error",
            "correct_count",
            "error_count",
            "show_source",
            "focus_level",
            "created_at",
            "updated_at",
        ],
        "where": "",
    },
    {
        "name": "user_settings",
        "columns": [
            "id",
            "user_id",
            "words_per_page",
            "auto_play_audio",
            "show_meaning",
            "created_at",
            "updated_at",
        ],
        "where": "",
    },
    {
        "name": "exam_records",
        "columns": ["id", "user_id", "timestamp", "total", "correct", "wrong", "accuracy", "words_data"],
        "where": "",
    },
    {
        "name": "vocabulary_words",
        "columns": [
            "id",
            "user_id",
            "chapter_name",
            "group_name",
            "word",
            "word_variants",
            "pos",
            "meaning",
            "example",
            "extra",
            "metadata",
            "source",
            "created_at",
            "updated_at",
        ],
        "where": "WHERE user_id IS NOT NULL OR source = 'custom'",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import user data from SQLite into Postgres.")
    parser.add_argument("--sqlite", required=True, help="Path to the legacy SQLite database file.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Target Postgres DATABASE_URL. Defaults to environment DATABASE_URL.",
    )
    parser.add_argument(
        "--clear-target",
        action="store_true",
        help="Delete target user data before importing. Use this for a fresh production database.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print row counts without changing Postgres.",
    )
    return parser.parse_args()


def sqlite_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


def existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()}


def read_rows(conn: sqlite3.Connection, table: dict[str, Any]) -> tuple[list[str], list[tuple[Any, ...]]]:
    columns = [column for column in table["columns"] if column in existing_columns(conn, table["name"])]
    if not columns:
        return [], []
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    query = f'SELECT {quoted_columns} FROM "{table["name"]}" {table["where"]}'
    return columns, [tuple(row) for row in conn.execute(query).fetchall()]


def delete_target_data(pg_conn: Any) -> None:
    statements = [
        "DELETE FROM exam_records",
        "DELETE FROM user_settings",
        "DELETE FROM word_progress",
        "DELETE FROM chapter_progress",
        "DELETE FROM vocabulary_words WHERE user_id IS NOT NULL OR source = 'custom'",
        "DELETE FROM users",
    ]
    with pg_conn.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def insert_rows(pg_conn: Any, table_name: str, columns: list[str], rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    sql = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES %s ON CONFLICT DO NOTHING'
    with pg_conn.cursor() as cursor:
        execute_values(cursor, sql, rows, page_size=500)


def reset_sequences(pg_conn: Any, table_names: list[str]) -> None:
    with pg_conn.cursor() as cursor:
        for table_name in table_names:
            cursor.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence(%s, 'id'),
                    COALESCE((SELECT MAX(id) FROM """ + table_name + """), 1),
                    (SELECT COUNT(*) > 0 FROM """ + table_name + """)
                )
                """,
                (table_name,),
            )


def main() -> None:
    args = parse_args()
    sqlite_path = Path(args.sqlite)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")
    if not args.database_url:
        raise RuntimeError("DATABASE_URL is required. Pass --database-url or set it in the environment.")

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    try:
        available_tables = sqlite_tables(sqlite_conn)
        payload: list[tuple[str, list[str], list[tuple[Any, ...]]]] = []
        for table in TABLES:
            if table["name"] not in available_tables:
                print(f"skip missing table: {table['name']}")
                continue
            columns, rows = read_rows(sqlite_conn, table)
            payload.append((table["name"], columns, rows))
            print(f"{table['name']}: {len(rows)} rows")
    finally:
        sqlite_conn.close()

    if args.dry_run:
        print("dry run only: target database was not changed")
        return

    pg_conn = psycopg2.connect(args.database_url)
    try:
        with pg_conn:
            if args.clear_target:
                delete_target_data(pg_conn)
                print("target user data cleared")

            imported_tables: list[str] = []
            for table_name, columns, rows in payload:
                insert_rows(pg_conn, table_name, columns, rows)
                imported_tables.append(table_name)
                print(f"imported {table_name}: {len(rows)} rows")

            reset_sequences(pg_conn, imported_tables)
            print("sequences reset")
    finally:
        pg_conn.close()


if __name__ == "__main__":
    main()
