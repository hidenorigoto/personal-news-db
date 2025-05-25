"""コアモジュール - 設定、データベース、例外処理"""

from .config import settings, get_settings
from .database import get_db, create_tables, drop_tables, Base, engine, SessionLocal
from .exceptions import (
    NewsAssistantException,
    DatabaseError,
    ValidationError,
    ExternalAPIError,
    OpenAIError,
    ContentProcessingError,
    ArticleNotFoundError,
    SummaryGenerationError,
    FileOperationError,
)

__all__ = [
    # 設定
    "settings",
    "get_settings",
    # データベース
    "get_db",
    "create_tables",
    "drop_tables",
    "Base",
    "engine",
    "SessionLocal",
    # 例外
    "NewsAssistantException",
    "DatabaseError",
    "ValidationError",
    "ExternalAPIError",
    "OpenAIError",
    "ContentProcessingError",
    "ArticleNotFoundError",
    "SummaryGenerationError",
    "FileOperationError",
]
