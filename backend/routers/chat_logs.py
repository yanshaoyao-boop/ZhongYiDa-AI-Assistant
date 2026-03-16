from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from dependencies import User, get_chat_audit_user, get_db
from models.chat_history import ChatHistory
from models.user import User as UserModel

router = APIRouter(prefix="/admin/chat-logs", tags=["admin-chat-logs"])


class ChatLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    user_message: str
    ai_response: str
    created_at: datetime
    processing_time: Optional[float]

    class Config:
        from_attributes = True


class UserLogStat(BaseModel):
    user_id: Optional[int]
    username: str
    message_count: int
    last_active: datetime


@router.get("/users", response_model=List[UserLogStat])
def get_users_with_logs(
    current_user: User = Depends(get_chat_audit_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func

    stats = (
        db.query(
            ChatHistory.user_id,
            UserModel.username,
            func.count(ChatHistory.id).label("message_count"),
            func.max(ChatHistory.created_at).label("last_active"),
        )
        .outerjoin(UserModel, ChatHistory.user_id == UserModel.id)
        .group_by(ChatHistory.user_id, UserModel.username)
        .order_by(desc("last_active"))
        .all()
    )

    return [
        UserLogStat(
            user_id=stat.user_id,
            username=stat.username or "Anonymous",
            message_count=stat.message_count,
            last_active=stat.last_active,
        )
        for stat in stats
    ]


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards so keyword search stays literal."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=List[ChatLogResponse])
def get_chat_logs(
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_chat_audit_user),
    db: Session = Depends(get_db),
):
    query = db.query(ChatHistory, UserModel.username).outerjoin(
        UserModel, ChatHistory.user_id == UserModel.id
    )

    if user_id is not None:
        query = query.filter(ChatHistory.user_id == user_id)
    elif search:
        escaped = _escape_like(search)
        query = query.filter(
            (ChatHistory.user_message.ilike(f"%{escaped}%", escape="\\"))
            | (ChatHistory.ai_response.ilike(f"%{escaped}%", escape="\\"))
            | (UserModel.username.ilike(f"%{escaped}%", escape="\\"))
        )

    logs = query.order_by(desc(ChatHistory.created_at)).offset(skip).limit(limit).all()

    return [
        ChatLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username or "Anonymous",
            user_message=log.user_message,
            ai_response=log.ai_response,
            created_at=log.created_at,
            processing_time=log.processing_time,
        )
        for log, username in logs
    ]
