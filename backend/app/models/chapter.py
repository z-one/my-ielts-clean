from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ChapterStatus(str, enum.Enum):
    NOT_LEARNED = "not_learned"
    LEARNED = "learned"
    COMPLETED = "completed"
    MASTERED = "mastered"


class ChapterProgress(Base):
    __tablename__ = "chapter_progress"
    __table_args__ = {"comment": "章节学习进度表"}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    chapter_name = Column(String(100), nullable=False, comment="章节名称")
    status = Column(Enum(ChapterStatus), default=ChapterStatus.NOT_LEARNED, comment="学习状态：not_learned-未学习，learned-已学习，completed-已完成，mastered-已熟练")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment="更新时间")
