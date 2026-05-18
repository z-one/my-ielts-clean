from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chapter import ChapterProgress, ChapterStatus
from app.schemas.chapter import ChapterProgressUpdate, ChapterProgressResponse
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/chapters", tags=["章节进度"])


@router.get("/progress", response_model=List[ChapterProgressResponse])
def get_chapters_progress(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户所有章节进度"""
    progress = db.query(ChapterProgress).filter(
        ChapterProgress.user_id == current_user.id
    ).all()
    return progress


@router.get("/{chapter_name}/progress", response_model=ChapterProgressResponse | None)
def get_chapter_progress(
    chapter_name: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定章节的进度"""
    progress = db.query(ChapterProgress).filter(
        ChapterProgress.user_id == current_user.id,
        ChapterProgress.chapter_name == chapter_name
    ).first()
    return progress


@router.put("/{chapter_name}/status", response_model=ChapterProgressResponse)
def update_chapter_status(
    chapter_name: str,
    status_update: ChapterProgressUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新章节学习状态"""
    progress = db.query(ChapterProgress).filter(
        ChapterProgress.user_id == current_user.id,
        ChapterProgress.chapter_name == chapter_name
    ).first()

    if progress:
        progress.status = status_update.status
        db.commit()
        db.refresh(progress)
    else:
        new_progress = ChapterProgress(
            user_id=current_user.id,
            chapter_name=chapter_name,
            status=status_update.status
        )
        db.add(new_progress)
        db.commit()
        db.refresh(new_progress)
        progress = new_progress

    return progress


@router.post("/batch-update", status_code=status.HTTP_200_OK)
def batch_update_chapters(
    chapters: List[dict],  # [{"chapter_name": "xx", "status": "completed"}]
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量更新章节状态"""
    updated_count = 0
    for chapter_data in chapters:
        chapter_name = chapter_data.get("chapter_name")
        status_value = chapter_data.get("status")

        progress = db.query(ChapterProgress).filter(
            ChapterProgress.user_id == current_user.id,
            ChapterProgress.chapter_name == chapter_name
        ).first()

        if progress:
            progress.status = status_value
        else:
            new_progress = ChapterProgress(
                user_id=current_user.id,
                chapter_name=chapter_name,
                status=status_value
            )
            db.add(new_progress)

        updated_count += 1

    db.commit()
    return {"message": f"成功更新 {updated_count} 个章节状态"}
