"""記事データモデル"""
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ..core import Base


class Article(Base):  # type: ignore[misc]
    """記事モデル"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>" 