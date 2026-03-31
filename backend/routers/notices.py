from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import has_permission
from models.notice import Notice
from models.user import User

router = APIRouter(prefix="/notices", tags=["notices"])
CHINA_TZ = timezone(timedelta(hours=8))


class NoticeCreate(BaseModel):
    content: str


class NoticeResponse(BaseModel):
    id: int
    content: str
    created_by_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


def _serialize_notice(notice: Notice) -> dict:
    created_at = notice.created_at
    if created_at and created_at.tzinfo is None:
        # SQLite can return naive datetime; treat it as UTC for consistency.
        created_at = created_at.replace(tzinfo=timezone.utc)
    if created_at:
        created_at = created_at.astimezone(CHINA_TZ)

    return {
        "id": notice.id,
        "content": notice.content,
        "created_by_name": notice.created_by_name or "系统发布",
        "created_at": created_at,
    }


@router.post("/", response_model=NoticeResponse)
def create_notice(
    notice: NoticeCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(has_permission("edit_notices")),
):
    new_notice = Notice(
        content=notice.content,
        created_by_id=admin.id,
        created_by_name=admin.full_name or admin.username,
    )
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    return _serialize_notice(new_notice)


@router.get("/current", response_model=List[NoticeResponse])
def get_current_notices(db: Session = Depends(get_db)):
    now_cn = datetime.now(CHINA_TZ)
    monday_start_cn = (now_cn - timedelta(days=now_cn.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    monday_start_utc = monday_start_cn.astimezone(timezone.utc)

    notices = (
        db.query(Notice)
        .filter(Notice.created_at >= monday_start_utc, Notice.is_active == 1)
        .order_by(Notice.created_at.desc())
        .all()
    )
    return [_serialize_notice(notice) for notice in notices]


@router.get("/history", response_model=List[NoticeResponse])
def get_history_notices(db: Session = Depends(get_db)):
    notices = (
        db.query(Notice)
        .filter(Notice.is_active == 1)
        .order_by(Notice.created_at.desc())
        .all()
    )
    return [_serialize_notice(notice) for notice in notices]


@router.delete("/{notice_id}")
def delete_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(has_permission("edit_notices")),
):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="通知未找到")

    notice.is_active = 0
    db.commit()
    return {"message": "通知已删除"}
