from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = {"comment": "用户设置表"}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, comment="用户ID")
    words_per_page = Column(Integer, default=5, comment="每页显示单词数")
    auto_play_audio = Column(Boolean, default=True, comment="是否自动播放音频")
    show_meaning = Column(Boolean, default=True, comment="是否显示释义")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment="更新时间")
