from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class WordProgress(Base):
    __tablename__ = "word_progress"
    __table_args__ = {"comment": "单词学习进度表"}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    word_id = Column(Integer, nullable=False, comment="单词ID")
    chapter_name = Column(String(100), nullable=False, comment="章节名称")
    spell_value = Column(String(255), default="", comment="拼写输入值")
    spell_error = Column(Boolean, default=False, comment="拼写是否错误")
    correct_count = Column(Integer, default=0, comment="正确次数")
    error_count = Column(Integer, default=0, comment="错误次数")
    show_source = Column(Boolean, default=False, comment="是否显示原文")
    focus_level = Column(Integer, default=0, comment="关注等级：0-普通，1-关注，2-重点")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment="更新时间")
