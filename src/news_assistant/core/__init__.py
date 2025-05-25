"""コアモジュール - 設定、データベース、例外処理"""

from .config import get_settings, settings
from .database import Base, SessionLocal, create_tables, drop_tables, engine, get_db
from .exceptions import (
    ArticleNotFoundError,
    ContentProcessingError,
    DatabaseError,
    ExternalAPIError,
    FileOperationError,
    NewsAssistantError,
    OpenAIError,
    SummaryGenerationError,
    ValidationError,
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
    "NewsAssistantError",
    "DatabaseError",
    "ValidationError",
    "ExternalAPIError",
    "OpenAIError",
    "ContentProcessingError",
    "ArticleNotFoundError",
    "SummaryGenerationError",
    "FileOperationError",
]
