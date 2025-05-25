"""記事関連のAPIエンドポイント"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..core import get_db, DatabaseError, ArticleNotFoundError
from .schemas import ArticleCreate, ArticleUpdate, ArticleResponse, ArticleList
from .service import ArticleService

router = APIRouter()


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db)
) -> ArticleResponse:
    """記事を新規作成"""
    try:
        db_article = ArticleService.create_article(db, article)
        return ArticleResponse.model_validate(db_article)
    except DatabaseError as e:
        if e.error_code == "DUPLICATE_URL":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"URL already registered: {e.details.get('url')}"
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        ) from e


@router.get("/", response_model=ArticleList)
async def get_articles(
    skip: int = Query(0, ge=0, description="スキップする記事数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する記事数"),
    db: Session = Depends(get_db)
) -> ArticleList:
    """記事一覧を取得"""
    articles, total = ArticleService.get_articles(db, skip=skip, limit=limit)
    return ArticleList(
        articles=[ArticleResponse.model_validate(article) for article in articles],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    db: Session = Depends(get_db)
) -> ArticleResponse:
    """特定の記事を取得"""
    try:
        article = ArticleService.get_article_by_id(db, article_id)
        return ArticleResponse.model_validate(article)
    except ArticleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        ) from e


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    db: Session = Depends(get_db)
) -> ArticleResponse:
    """記事を更新"""
    try:
        article = ArticleService.update_article(db, article_id, article_data)
        return ArticleResponse.model_validate(article)
    except ArticleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        ) from e
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        ) from e


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db)
) -> None:
    """記事を削除"""
    try:
        ArticleService.delete_article(db, article_id)
    except ArticleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        ) from e
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        ) from e 