import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.exam import ExamRecord
from app.schemas.exam import ExamRecordCreate, ExamRecordResponse
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/exams", tags=["考试记录"])


@router.post("", response_model=ExamRecordResponse, status_code=status.HTTP_201_CREATED)
def create_exam_record(
    exam_data: ExamRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建考试记录"""
    try:
        # 将单词详情转为 JSON 字符串存储
        words_json = json.dumps([word.model_dump() for word in exam_data.words]) if exam_data.words else None
        
        exam_record = ExamRecord(
            user_id=current_user.id,
            total=exam_data.total,
            correct=exam_data.correct,
            wrong=exam_data.wrong,
            accuracy=exam_data.accuracy,
            words_data=words_json
        )
        
        db.add(exam_record)
        db.commit()
        db.refresh(exam_record)
        
        return exam_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存考试记录失败: {str(e)}")


@router.get("", response_model=List[ExamRecordResponse])
def get_exam_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有考试记录"""
    try:
        records = db.query(ExamRecord).filter(
            ExamRecord.user_id == current_user.id
        ).order_by(ExamRecord.timestamp.desc()).all()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取考试记录失败: {str(e)}")


@router.get("/{exam_id}", response_model=ExamRecordResponse)
def get_exam_record_by_id(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定考试记录"""
    record = db.query(ExamRecord).filter(
        ExamRecord.id == exam_id,
        ExamRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    
    return record
