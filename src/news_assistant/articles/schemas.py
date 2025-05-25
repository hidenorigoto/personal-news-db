"""記事関連のPydanticスキーマ"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ArticleBase(BaseModel):
    """記事の基本スキーマ"""
    url: HttpUrl = Field(..., description="記事のURL")
    title: str = Field(..., min_length=1, max_length=500, description="記事のタイトル")
    summary: Optional[str] = Field(None, max_length=2000, description="記事の要約")


class ArticleCreate(ArticleBase):
    """記事作成用スキーマ"""
    pass


class ArticleUpdate(BaseModel):
    """記事更新用スキーマ"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="記事のタイトル")
    summary: Optional[str] = Field(None, max_length=2000, description="記事の要約")


class ArticleResponse(ArticleBase):
    """記事レスポンス用スキーマ"""
    id: int = Field(..., description="記事ID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")

    model_config = ConfigDict(from_attributes=True)


class ArticleList(BaseModel):
    """記事一覧レスポンス用スキーマ"""
    articles: list[ArticleResponse] = Field(..., description="記事一覧")
    total: int = Field(..., description="総記事数")
    skip: int = Field(..., description="スキップした記事数")
    limit: int = Field(..., description="取得制限数")