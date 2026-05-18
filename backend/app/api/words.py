from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.word import WordProgress
from app.schemas.word import (
    WordProgressUpdate,
    WordProgressResponse,
    WordProgressSync
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/words", tags=["单词进度"])


@router.get("/progress", response_model=List[WordProgressResponse])
def get_words_progress(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户所有单词进度"""
    progress = db.query(WordProgress).filter(
        WordProgress.user_id == current_user.id
    ).all()
    return progress


@router.get("/{chapter_name}/progress", response_model=List[WordProgressResponse])
def get_chapter_words_progress(
    chapter_name: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定章节的单词进度"""
    progress = db.query(WordProgress).filter(
        WordProgress.user_id == current_user.id,
        WordProgress.chapter_name == chapter_name
    ).all()
    return progress


@router.put("/{word_id}/progress", response_model=WordProgressResponse)
def update_word_progress(
    word_id: int,
    progress_update: WordProgressUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新单词进度"""
    # 需要提供 chapter_name
    if not progress_update.chapter_name:
        raise ValueError("必须提供 chapter_name")

    progress = db.query(WordProgress).filter(
        WordProgress.user_id == current_user.id,
        WordProgress.word_id == word_id,
        WordProgress.chapter_name == progress_update.chapter_name
    ).first()

    if progress:
        # 只更新提供的字段
        update_data = progress_update.model_dump(exclude_unset=True)
        update_data.pop("chapter_name", None)  # 移除 chapter_name
        for key, value in update_data.items():
            setattr(progress, key, value)
        db.commit()
        db.refresh(progress)
    else:
        create_data = progress_update.model_dump(exclude_unset=True, exclude_none=True)
        new_progress = WordProgress(
            user_id=current_user.id,
            word_id=word_id,
            **create_data
        )
        db.add(new_progress)
        db.commit()
        db.refresh(new_progress)
        progress = new_progress

    return progress


@router.post("/sync", status_code=status.HTTP_200_OK)
def sync_local_progress(
    sync_data: WordProgressSync,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """同步本地进度到服务器"""
    updated_count = 0
    created_count = 0

    for word_id, word_data in sync_data.words.items():
        progress = db.query(WordProgress).filter(
            WordProgress.user_id == current_user.id,
            WordProgress.word_id == int(word_id),
            WordProgress.chapter_name == sync_data.chapter
        ).first()

        if progress:
            # 更新现有记录
            for key, value in word_data.items():
                if key == "focus_level":
                    continue
                if hasattr(progress, key) and value is not None:
                    setattr(progress, key, value)
            updated_count += 1
        else:
            word_data = {k: v for k, v in word_data.items() if k != "focus_level"}
            # 创建新记录
            new_progress = WordProgress(
                user_id=current_user.id,
                word_id=int(word_id),
                chapter_name=sync_data.chapter,
                **word_data
            )
            db.add(new_progress)
            created_count += 1

    db.commit()
    return {
        "message": f"同步成功",
        "updated": updated_count,
        "created": created_count
    }


@router.post("/batch-update", status_code=status.HTTP_200_OK)
def batch_update_words(
    words_data: List[dict],  # [{"word_id": 1, "chapter_name": "xx", "focus_level": 2, ...}]
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量更新单词进度"""
    updated_count = 0
    created_count = 0

    for word_data in words_data:
        word_id = word_data.get("word_id")
        chapter_name = word_data.get("chapter_name")

        if not word_id or not chapter_name:
            continue

        progress = db.query(WordProgress).filter(
            WordProgress.user_id == current_user.id,
            WordProgress.word_id == word_id,
            WordProgress.chapter_name == chapter_name
        ).first()

        update_dict = {k: v for k, v in word_data.items() if k not in ["word_id", "chapter_name", "focus_level"] and v is not None}

        if progress:
            for key, value in update_dict.items():
                setattr(progress, key, value)
            updated_count += 1
        else:
            new_progress = WordProgress(
                user_id=current_user.id,
                word_id=word_id,
                chapter_name=chapter_name,
                **update_dict
            )
            db.add(new_progress)
            created_count += 1

    db.commit()
    return {
        "message": f"批量更新完成",
        "updated": updated_count,
        "created": created_count
    }
