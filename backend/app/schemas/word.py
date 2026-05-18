from pydantic import BaseModel
from datetime import datetime


class WordProgressBase(BaseModel):
    word_id: int
    chapter_name: str
    spell_value: str = ""
    spell_error: bool = False
    correct_count: int = 0
    error_count: int = 0
    show_source: bool = False
    focus_level: int = 0


class WordProgressCreate(WordProgressBase):
    pass


class WordProgressUpdate(BaseModel):
    chapter_name: str | None = None
    spell_value: str | None = None
    spell_error: bool | None = None
    correct_count: int | None = None
    error_count: int | None = None
    show_source: bool | None = None
    focus_level: int | None = None


class WordProgressResponse(WordProgressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WordProgressSync(BaseModel):
    """同步数据格式"""
    chapter: str
    words: dict  # {word_id: progress_data}
