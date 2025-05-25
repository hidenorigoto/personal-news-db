"""News Assistant API - メインアプリケーション（新構造版）"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .articles import router as articles_router

# モデルを明示的にインポートしてテーブル作成を確実にする
from .articles.models import Article  # noqa: F401
from .core import create_tables, settings
from .health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション開始時
    if os.getenv('APP_ENV') != 'production':
        create_tables()
    
    yield


# アプリケーション初期化
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    description="AI-powered news collection and summarization service",
    lifespan=lifespan,
)


# ルーター登録
app.include_router(health_router, tags=["health"])
app.include_router(articles_router, prefix="/api/articles", tags=["articles"])


@app.get("/")
async def root() -> dict[str, str | bool]:
    """ルートエンドポイント"""
    return {
        "message": settings.app_name,
        "version": settings.version,
        "status": "running",
        "debug": settings.debug,
    }