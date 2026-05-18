from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ExamWordDetail(BaseModel):
    """考试单词详情"""
    word_id: str = Field(..., description="单词ID")
    chapter_name: str = Field(..., description="章节名称")
    word: str = Field(..., description="单词")
    is_correct: bool = Field(..., description="是否正确")
    correct_count: int = Field(default=0, description="正确次数")
    error_count: int = Field(default=0, description="错误次数")
    focus_level: int = Field(default=0, description="关注等级")


class ExamRecordCreate(BaseModel):
    """创建考试记录"""
    total: int = Field(..., description="总题数")
    correct: int = Field(..., description="正确数")
    wrong: int = Field(..., description="错误数")
    accuracy: float = Field(..., description="正确率")
    words: Optional[List[ExamWordDetail]] = Field(default=[], description="单词详情")


class ExamRecordResponse(BaseModel):
    """考试记录响应"""
    id: int
    user_id: int
    timestamp: datetime
    total: int
    correct: int
    wrong: int
    accuracy: float
    words_data: Optional[str] = None
    
    class Config:
        from_attributes = True
