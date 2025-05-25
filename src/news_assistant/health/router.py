"""ヘルスチェック機能"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core import get_db, settings

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """アプリケーションのヘルスチェック"""
    try:
        # データベース接続確認
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.version,
        "app_name": settings.app_name,
        "database": db_status,
        "debug_mode": settings.debug,
    }
