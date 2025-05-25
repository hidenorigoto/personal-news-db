"""アプリケーション例外クラス"""
from typing import Any


class NewsAssistantError(Exception):
    """ベース例外クラス"""

    def __init__(
        self, message: str, error_code: str | None = None, details: dict[str, Any] | None = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(NewsAssistantError):
    """データベース関連エラー"""

    pass


class ValidationError(NewsAssistantError):
    """バリデーションエラー"""

    pass


class ExternalAPIError(NewsAssistantError):
    """外部API関連エラー"""

    pass


class OpenAIError(ExternalAPIError):
    """OpenAI API関連エラー"""

    pass


class ContentProcessingError(NewsAssistantError):
    """コンテンツ処理エラー"""

    pass


class ArticleNotFoundError(NewsAssistantError):
    """記事が見つからないエラー"""

    def __init__(self, article_id: int):
        super().__init__(
            f"Article with ID {article_id} not found",
            error_code="ARTICLE_NOT_FOUND",
            details={"article_id": article_id},
        )


class SummaryGenerationError(NewsAssistantError):
    """要約生成エラー"""

    pass


class FileOperationError(NewsAssistantError):
    """ファイル操作エラー"""

    pass
