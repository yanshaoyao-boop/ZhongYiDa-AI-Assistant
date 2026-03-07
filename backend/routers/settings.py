from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from database import get_db
from models.user import User, SystemSetting
from dependencies import get_super_admin

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingUpdate(BaseModel):
    settings: Dict[str, Any]

@router.get("/")
def get_all_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(get_super_admin)
):
    settings = db.query(SystemSetting).all()
    # Return as {key: value} dict
    return {s.key: s.value for s in settings}

@router.patch("/")
def update_settings(
    data: SettingUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_super_admin)
):
    for key, value in data.settings.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            setting = SystemSetting(key=key, value=str(value))
            db.add(setting)
        else:
            setting.value = str(value)
    
    db.commit()
    return {"message": "设置已更新"}

# 也可以提供一个公共接口给 ChatView 使用（如果需要一些前台展示配置）
@router.get("/public")
def get_public_settings(db: Session = Depends(get_db)):
    # 限制只返回非敏感配置
    public_keys = ["welcome_message", "slogan", "app_name"]
    settings = db.query(SystemSetting).filter(SystemSetting.key.in_(public_keys)).all()
    return {s.key: s.value for s in settings}
