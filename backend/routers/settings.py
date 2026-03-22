from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import has_permission
from models.user import SystemSetting, User
from services.settings_service import serialize_public_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    settings: Dict[str, Any]


@router.get("/")
def get_all_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(has_permission("edit_settings")),
):
    settings = db.query(SystemSetting).all()
    return {setting.key: setting.value for setting in settings}


@router.patch("/")
def update_settings(
    data: SettingUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(has_permission("edit_settings")),
):
    for key, value in data.settings.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            setting = SystemSetting(key=key, value=str(value))
            db.add(setting)
        else:
            setting.value = str(value)

    db.commit()

    from routers.chat import invalidate_config_cache

    invalidate_config_cache()
    return {"message": "设置已更新"}


@router.get("/public")
def get_public_settings(db: Session = Depends(get_db)):
    public_keys = ["welcome_message", "slogan", "app_name"]
    settings = db.query(SystemSetting).filter(SystemSetting.key.in_(public_keys)).all()
    return serialize_public_settings({setting.key: setting.value for setting in settings})
