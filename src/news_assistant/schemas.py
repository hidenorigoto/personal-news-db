from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    url: str
    title: str


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ArticleList(BaseModel):
    articles: list[Article]
