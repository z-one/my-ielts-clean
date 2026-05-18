import json
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class VocabularyWordBase(BaseModel):
    chapter_name: str = Field(..., max_length=100)
    group_name: Optional[str] = Field(default=None, max_length=100)
    word: List[str] = Field(..., min_length=1)
    word_variants: Optional[List[str]] = None
    pos: str = ""
    meaning: str = ""
    example: str = ""
    extra: str = ""
    metadata: str = ""

    @field_validator("word")
    @classmethod
    def normalize_words(cls, value: List[str]) -> List[str]:
        words = [word.strip() for word in value if word and word.strip()]
        if not words:
            raise ValueError("word 至少需要一个有效单词")
        return words


class VocabularyWordCreate(VocabularyWordBase):
    source: str = "system"


class VocabularyWordBatchCreate(BaseModel):
    words: List[VocabularyWordCreate]


class CustomVocabularyWordCreate(VocabularyWordBase):
    chapter_name: str = "23 - 自添加生词"
    source: str = "custom"


class VocabularyWordUpdate(BaseModel):
    chapter_name: Optional[str] = Field(default=None, max_length=100)
    group_name: Optional[str] = Field(default=None, max_length=100)
    word: Optional[List[str]] = None
    pos: Optional[str] = None
    meaning: Optional[str] = None
    example: Optional[str] = None
    extra: Optional[str] = None
    word_variants: Optional[List[str]] = None
    metadata: Optional[str] = None

    @field_validator("word")
    @classmethod
    def normalize_optional_words(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        words = [word.strip() for word in value if word and word.strip()]
        if not words:
            raise ValueError("word 至少需要一个有效单词")
        return words


class VocabularyWordResponse(VocabularyWordBase):
    id: int
    user_id: Optional[int] = None
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomVocabularyWordResponse(BaseModel):
    word: VocabularyWordResponse
    already_exists: bool = False


class VocabularyChapterResponse(BaseModel):
    id: int
    chapter_name: str
    label: str
    audio: str = ""
    source: str
    group_count: int
    word_count: int
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def encode_word_list(words: List[str]) -> str:
    return json.dumps(words, ensure_ascii=False)


def decode_word_list(words: str) -> List[str]:
    try:
        decoded = json.loads(words)
        if isinstance(decoded, list):
            return [str(word) for word in decoded]
    except json.JSONDecodeError:
        pass
    return [words]
