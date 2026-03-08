from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable for anonymous users if allowed
    session_id = Column(String, index=True, nullable=True) # For grouping messages in a session
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Float, nullable=True) # Time taken for AI to respond
    token_usage = Column(Integer, nullable=True) # Optional: track token usage
    mode = Column(String, nullable=True, default="general") # record chat mode
    
    # Relationships could be added here if needed, but not strictly necessary for simple logging

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, mode='{self.mode}')>"
