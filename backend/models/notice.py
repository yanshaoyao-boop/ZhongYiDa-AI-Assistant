from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from database import Base

class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Integer, default=1) # 1: active, 0: deleted/hidden
