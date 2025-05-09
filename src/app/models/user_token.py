from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models import Base

class UserToken(Base):
    __tablename__ = "user_tokens"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(String(450), primary_key=True)
    refresh_token = Column(String(450), nullable=False)
    ip = Column(String(40), nullable=False)
    user_agent = Column(Text, nullable=False)
    expired_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    users = relationship("User", backref="tokens")