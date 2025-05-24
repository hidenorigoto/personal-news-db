from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .database import Base

__all__ = ["Base", "Article"]


class Article(Base):  # type: ignore[misc]
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
