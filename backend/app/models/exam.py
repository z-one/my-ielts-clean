from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ExamRecord(Base):
    """考试记录模型"""
    __tablename__ = "exam_records"

    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    timestamp = Column(DateTime, default=datetime.utcnow, comment="考试时间")
    total = Column(Integer, nullable=False, comment="总题数")
    correct = Column(Integer, nullable=False, comment="正确数")
    wrong = Column(Integer, nullable=False, comment="错误数")
    accuracy = Column(Float, nullable=False, comment="正确率")
    
    # JSON 格式存储考试详情
    words_data = Column(Text, nullable=True, comment="考试单词详情(JSON格式)")
    
    user = relationship("User", back_populates="exam_records")
