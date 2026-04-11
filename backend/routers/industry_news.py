from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import has_permission
from models.industry_news import IndustryNews


router = APIRouter(prefix="/industry-news", tags=["industry-news"])
CHINA_TZ = timezone(timedelta(hours=8))


class IndustryNewsCreate(BaseModel):
    content: str


class IndustryNewsResponse(BaseModel):
    id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


def _serialize_news(news: IndustryNews) -> dict:
    created_at = news.created_at
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    if created_at:
        created_at = created_at.astimezone(CHINA_TZ)

    return {
        "id": news.id,
        "content": news.content,
        "created_at": created_at,
    }


@router.post("/", response_model=IndustryNewsResponse)
def create_industry_news(
    payload: IndustryNewsCreate,
    db: Session = Depends(get_db),
    _admin=Depends(has_permission("edit_notices")),
):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="资讯内容不能为空")

    news = IndustryNews(content=content)
    db.add(news)
    db.commit()
    db.refresh(news)
    return _serialize_news(news)


@router.get("/current", response_model=List[IndustryNewsResponse])
def get_current_industry_news(db: Session = Depends(get_db)):
    now_cn = datetime.now(CHINA_TZ)
    monday_start_cn = (now_cn - timedelta(days=now_cn.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    monday_start_utc = monday_start_cn.astimezone(timezone.utc)

    rows = (
        db.query(IndustryNews)
        .filter(IndustryNews.created_at >= monday_start_utc, IndustryNews.is_active == 1)
        .order_by(IndustryNews.created_at.desc())
        .all()
    )
    return [_serialize_news(row) for row in rows]


@router.get("/history", response_model=List[IndustryNewsResponse])
def get_history_industry_news(db: Session = Depends(get_db)):
    rows = (
        db.query(IndustryNews)
        .filter(IndustryNews.is_active == 1)
        .order_by(IndustryNews.created_at.desc())
        .all()
    )
    return [_serialize_news(row) for row in rows]


@router.delete("/{news_id}")
def delete_industry_news(
    news_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(has_permission("edit_notices")),
):
    news = db.query(IndustryNews).filter(IndustryNews.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="资讯未找到")

    news.is_active = 0
    db.commit()
    return {"message": "资讯已删除"}
