from pydantic import BaseModel
from datetime import datetime


class UserSettingsBase(BaseModel):
    words_per_page: int = 5
    auto_play_audio: bool = True
    show_meaning: bool = True


class UserSettingsUpdate(BaseModel):
    words_per_page: int | None = None
    auto_play_audio: bool | None = None
    show_meaning: bool | None = None


class UserSettingsResponse(UserSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
