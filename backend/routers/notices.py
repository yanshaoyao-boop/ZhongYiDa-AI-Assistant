from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from database import get_db
from models.notice import Notice
from models.user import User
from dependencies import has_permission, get_current_user

router = APIRouter(prefix="/api/notices", tags=["notices"])

class NoticeCreate(BaseModel):
    content: str

class NoticeResponse(BaseModel):
    id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=NoticeResponse)
def create_notice(
    notice: NoticeCreate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(has_permission("edit_notices"))
):
    """创建新通知（仅限超级管理员）"""
    new_notice = Notice(content=notice.content)
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    return new_notice

@router.get("/current", response_model=List[NoticeResponse])
def get_current_notices(db: Session = Depends(get_db)):
    """获取本周内的通知"""
    now = datetime.now(timezone.utc)
    # 计算本周周一的开始时间 (假设周一为一周的开始)
    monday = now - timedelta(days=now.weekday())
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    notices = db.query(Notice).filter(
        Notice.created_at >= monday_start,
        Notice.is_active == 1
    ).order_by(Notice.created_at.desc()).all()
    
    return notices

@router.get("/history", response_model=List[NoticeResponse])
def get_history_notices(db: Session = Depends(get_db)):
    """获取历史通知（排除本周，或者全部历史）"""
    # 这里直接返回全部活跃通知
    notices = db.query(Notice).filter(
        Notice.is_active == 1
    ).order_by(Notice.created_at.desc()).all()
    
    return notices

@router.delete("/{notice_id}")
def delete_notice(
    notice_id: int, 
    db: Session = Depends(get_db), 
    admin: User = Depends(has_permission("edit_notices"))
):
    """删除通知（逻辑删除）"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="通知未找到")
    
    notice.is_active = 0
    db.commit()
    return {"message": "通知已删除"}
