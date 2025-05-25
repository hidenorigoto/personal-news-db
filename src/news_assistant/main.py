"""News Assistant API - メインアプリケーション（新構造版）"""
from fastapi import FastAPI

from .articles import router as articles_router
from .core import create_tables, settings
from .health import router as health_router

# アプリケーション初期化
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    description="AI-powered news collection and summarization service",
)

# データベーステーブル作成
create_tables()

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
