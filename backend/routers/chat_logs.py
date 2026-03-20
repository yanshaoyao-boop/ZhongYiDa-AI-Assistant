from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, func, literal
from sqlalchemy.orm import Session

from dependencies import User, get_chat_audit_user, get_db
from models.chat_history import ChatHistory
from models.user import User as UserModel

router = APIRouter(prefix="/admin/chat-logs", tags=["admin-chat-logs"])


class ChatLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    login_username: Optional[str]
    display_name: str
    user_message: str
    ai_response: str
    created_at: datetime
    processing_time: Optional[float]

    class Config:
        from_attributes = True


class UserLogStat(BaseModel):
    user_id: Optional[int] = None
    username: str
    display_name: str
    audit_key: str
    message_count: int
    last_active: datetime


def _audit_display_expr():
    trimmed_full_name = func.nullif(func.trim(UserModel.full_name), "")
    return func.coalesce(trimmed_full_name, UserModel.username, literal("Anonymous"))


@router.get("/users", response_model=List[UserLogStat])
def get_users_with_logs(
    current_user: User = Depends(get_chat_audit_user),
    db: Session = Depends(get_db),
):
    display_name_expr = _audit_display_expr()
    stats = (
        db.query(
            display_name_expr.label("display_name"),
            func.count(ChatHistory.id).label("message_count"),
            func.max(ChatHistory.created_at).label("last_active"),
        )
        .outerjoin(UserModel, ChatHistory.user_id == UserModel.id)
        .group_by(display_name_expr)
        .order_by(desc("last_active"))
        .all()
    )

    return [
        UserLogStat(
            username=stat.display_name or "Anonymous",
            display_name=stat.display_name or "Anonymous",
            audit_key=stat.display_name or "Anonymous",
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
    audit_key: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_chat_audit_user),
    db: Session = Depends(get_db),
):
    display_name_expr = _audit_display_expr()
    query = db.query(ChatHistory, UserModel.username, UserModel.full_name).outerjoin(
        UserModel, ChatHistory.user_id == UserModel.id
    )

    if audit_key:
        query = query.filter(display_name_expr == audit_key)
    elif user_id is not None:
        query = query.filter(ChatHistory.user_id == user_id)
    elif search:
        escaped = _escape_like(search)
        query = query.filter(
            (ChatHistory.user_message.ilike(f"%{escaped}%", escape="\\"))
            | (ChatHistory.ai_response.ilike(f"%{escaped}%", escape="\\"))
            | (UserModel.username.ilike(f"%{escaped}%", escape="\\"))
            | (UserModel.full_name.ilike(f"%{escaped}%", escape="\\"))
        )

    logs = query.order_by(desc(ChatHistory.created_at)).offset(skip).limit(limit).all()

    return [
        ChatLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=(full_name or "").strip() or username or "Anonymous",
            login_username=username,
            display_name=(full_name or "").strip() or username or "Anonymous",
            user_message=log.user_message,
            ai_response=log.ai_response,
            created_at=log.created_at,
            processing_time=log.processing_time,
        )
        for log, username, full_name in logs
    ]
