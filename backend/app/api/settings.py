from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import UserSettings
from app.models.user import User
from app.schemas.settings import UserSettingsUpdate, UserSettingsResponse
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/settings", tags=["用户设置"])


@router.get("", response_model=UserSettingsResponse)
def get_user_settings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户设置"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        # 创建默认设置
        new_settings = UserSettings(user_id=current_user.id)
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings

    return settings


@router.put("", response_model=UserSettingsResponse)
def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户设置"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        new_settings = UserSettings(
            user_id=current_user.id,
            **settings_update.model_dump(exclude_unset=True)
        )
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings

    # 只更新提供的字段
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings
