"""アプリケーション例外クラス"""
from typing import Optional, Any, Dict


class NewsAssistantException(Exception):
    """ベース例外クラス"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(NewsAssistantException):
    """データベース関連エラー"""
    pass


class ValidationError(NewsAssistantException):
    """バリデーションエラー"""
    pass


class ExternalAPIError(NewsAssistantException):
    """外部API関連エラー"""
    pass


class OpenAIError(ExternalAPIError):
    """OpenAI API関連エラー"""
    pass


class ContentProcessingError(NewsAssistantException):
    """コンテンツ処理エラー"""
    pass


class ArticleNotFoundError(NewsAssistantException):
    """記事が見つからないエラー"""
    
    def __init__(self, article_id: int):
        super().__init__(
            f"Article with ID {article_id} not found",
            error_code="ARTICLE_NOT_FOUND",
            details={"article_id": article_id}
        )


class SummaryGenerationError(NewsAssistantException):
    """要約生成エラー"""
    pass


class FileOperationError(NewsAssistantException):
    """ファイル操作エラー"""
    pass 