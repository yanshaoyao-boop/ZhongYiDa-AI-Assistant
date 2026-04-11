from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, Text

from database import Base


class IndustryNews(Base):
    __tablename__ = "industry_news"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Integer, default=1)  # 1: active, 0: deleted/hidden
