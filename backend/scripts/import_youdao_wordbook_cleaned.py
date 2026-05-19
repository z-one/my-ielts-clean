"""Import cleaned Youdao wordbook JSON into vocabulary_words table."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.models.vocabulary import VocabularyWord


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import cleaned Youdao wordbook JSON.")
    parser.add_argument("--cleaned", required=True, help="Path to youdao-wordbook-cleaned.json")
    parser.add_argument("--user-id", type=int, default=None, help="Optional user_id for imported rows")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing rows with the same word/chapter/source/user_id.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cleaned_path = Path(args.cleaned)

    print(f"Reading: {cleaned_path}")
    with open(cleaned_path, encoding="utf-8") as f:
        data = json.load(f)

    # Extract words from cleaned format
    chapters = data.get("chapterNames", [])
    words: list[dict] = data.get("words", [])

    if not words:
        print("No words found in cleaned file.")
        return

    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        for item in words:
            word_data = item.get("word", "")
            if isinstance(word_data, list):
                word_text = word_data[0].strip() if word_data else ""
            else:
                word_text = str(word_data).strip()
            if not word_text:
                continue

            chapter_name = item.get("chapter_name") or data.get("chapterName", "有道单词本")
            group_name = item.get("group_name") or data.get("groupName", "有道导入")
            pos = item.get("pos", "")
            meaning = item.get("meaning", "")
            example = item.get("example", "")
            extra = item.get("extra", "")
            word_variants = item.get("word_variants") or item.get("word", "")
            metadata = item.get("metadata", "")
            source = item.get("source") or data.get("vocabularySource", "youdao")

            # Check if exists
            query = db.query(VocabularyWord).filter(
                VocabularyWord.word.in_([word_text]),
            )
            if args.user_id is None:
                query = query.filter(VocabularyWord.user_id.is_(None))
            else:
                query = query.filter(VocabularyWord.user_id == args.user_id)

            existing = query.first()

            if existing and not args.replace_existing:
                skipped += 1
                continue

            if existing and args.replace_existing:
                existing.group_name = group_name
                existing.pos = pos
                existing.meaning = meaning
                existing.example = example
                existing.extra = extra
                existing.word_variants = json.dumps(word_variants, ensure_ascii=False)
                existing.metadata_json = metadata
            else:
                db.add(
                    VocabularyWord(
                        user_id=args.user_id,
                        chapter_name=chapter_name,
                        group_name=group_name,
                        word=word_text,
                        word_variants=json.dumps(word_variants, ensure_ascii=False),
                        pos=pos,
                        meaning=meaning,
                        example=example,
                        extra=extra,
                        metadata_json=metadata,
                        source=source,
                    )
                )
            created += 1

        db.commit()
        print(f"Total words in file: {len(words)}")
        print(f"Created: {created}")
        print(f"Skipped (existing): {skipped}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
