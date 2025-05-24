from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    url: str
    title: str
    summary: str | None = None


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ArticleList(BaseModel):
    articles: list[Article]
