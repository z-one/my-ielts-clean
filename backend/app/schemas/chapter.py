from pydantic import BaseModel
from datetime import datetime
from app.models.chapter import ChapterStatus


class ChapterProgressBase(BaseModel):
    chapter_name: str
    status: ChapterStatus


class ChapterProgressCreate(ChapterProgressBase):
    pass


class ChapterProgressUpdate(BaseModel):
    status: ChapterStatus


class ChapterProgressResponse(ChapterProgressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
