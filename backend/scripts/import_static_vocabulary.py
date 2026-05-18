"""Clean and optionally import frontend vocabulary.js into vocabulary_words.

Default mode only writes a cleaned JSON file. Add --import-db to insert rows
into the configured Postgres database.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
DEFAULT_VOCABULARY_JS = REPO_DIR / "frontend" / "src" / "pages" / "vocabulary" / "vocabulary.js"
DEFAULT_OUTPUT = REPO_DIR / "data" / "imports" / "vocabulary-js-cleaned.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_youdao_wordbook import import_to_db  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean/import frontend vocabulary.js.")
    parser.add_argument(
        "--source-file",
        default=str(DEFAULT_VOCABULARY_JS),
        help="Path to frontend vocabulary.js",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUTPUT),
        help="Cleaned JSON output path. Default: data/imports/vocabulary-js-cleaned.json",
    )
    parser.add_argument("--source", default="system", help="Vocabulary source value. Default: system")
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


def load_vocabulary_js(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    marker = "const vocabulary = "
    export_marker = "export default vocabulary"
    if marker not in text or export_marker not in text:
        raise ValueError(f"Cannot find vocabulary object markers in {path}")

    start = text.index(marker) + len(marker)
    end = text.rindex(export_marker)
    body = text[start:end].strip()
    return json.loads(body)


def normalize_words(value: Any) -> list[str]:
    if isinstance(value, list):
        words = [str(item).strip() for item in value if str(item).strip()]
        return words
    if value is None:
        return []
    word = str(value).strip()
    return [word] if word else []


def clean_vocabulary(vocabulary: dict[str, Any], *, source: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    words: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for chapter_name, chapter in vocabulary.items():
        chapter_label = chapter.get("label") or chapter_name
        chapter_audio = chapter.get("audio") or ""
        groups = chapter.get("words") or []

        for group_index, group in enumerate(groups, start=1):
            if not isinstance(group, list):
                skipped.append(
                    {
                        "chapterName": chapter_name,
                        "groupIndex": group_index,
                        "reason": "group is not a list",
                        "raw": group,
                    }
                )
                continue

            group_name = f"{chapter_name} 第{group_index:02d}组"
            for word_index, item in enumerate(group, start=1):
                if not isinstance(item, dict):
                    skipped.append(
                        {
                            "chapterName": chapter_name,
                            "groupIndex": group_index,
                            "wordIndex": word_index,
                            "reason": "word item is not an object",
                            "raw": item,
                        }
                    )
                    continue

                word_variants = normalize_words(item.get("word"))
                if not word_variants:
                    skipped.append(
                        {
                            "chapterName": chapter_name,
                            "groupIndex": group_index,
                            "wordIndex": word_index,
                            "reason": "missing word",
                            "raw": item,
                        }
                    )
                    continue

                metadata = {
                    "staticVocabularyId": item.get("id"),
                    "staticChapterName": chapter_name,
                    "staticChapterLabel": chapter_label,
                    "staticChapterAudio": chapter_audio,
                    "staticGroupIndex": group_index,
                    "staticWordIndex": word_index,
                }

                words.append(
                    {
                        "chapter_name": chapter_name,
                        "group_name": group_name,
                        "word": [word_variants[0]],
                        "word_variants": word_variants,
                        "pos": item.get("pos") or "",
                        "meaning": item.get("meaning") or "",
                        "example": item.get("example") or "",
                        "extra": item.get("extra") or "",
                        "metadata": json.dumps(metadata, ensure_ascii=False),
                        "source": source,
                    }
                )

    words.sort(key=static_id_sort_key)
    return words, skipped


def static_id_sort_key(item: dict[str, Any]) -> int:
    try:
        metadata = json.loads(item.get("metadata") or "{}")
        return int(metadata.get("staticVocabularyId") or 0)
    except (TypeError, ValueError, json.JSONDecodeError):
        return 0


def write_cleaned_output(
    path: Path,
    *,
    source_file: Path,
    vocabulary: dict[str, Any],
    words: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    source: str,
) -> None:
    chapter_counts: dict[str, int] = {}
    for word in words:
        chapter_counts[word["chapter_name"]] = chapter_counts.get(word["chapter_name"], 0) + 1

    payload = {
        "source": "frontend-vocabulary-js-cleaned",
        "sourceFile": str(source_file),
        "cleanedAt": datetime.now().isoformat(timespec="seconds"),
        "vocabularySource": source,
        "stats": {
            "chapterTotal": len(vocabulary),
            "cleanedTotal": len(words),
            "skippedTotal": len(skipped),
        },
        "chapterCounts": chapter_counts,
        "skipped": skipped,
        "words": words,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    source_file = Path(args.source_file)
    out_path = Path(args.out)

    vocabulary = load_vocabulary_js(source_file)
    words, skipped = clean_vocabulary(vocabulary, source=args.source)
    write_cleaned_output(
        out_path,
        source_file=source_file,
        vocabulary=vocabulary,
        words=words,
        skipped=skipped,
        source=args.source,
    )

    print(f"chapters: {len(vocabulary)}")
    print(f"cleaned total: {len(words)}")
    print(f"skipped: {len(skipped)}")
    print(f"cleaned file: {out_path}")

    if args.import_db:
        db_result = import_to_db(
            words,
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
