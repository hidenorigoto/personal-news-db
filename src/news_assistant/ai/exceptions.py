"""AI機能関連の例外クラス"""

from ..core.exceptions import NewsAssistantException


class AIServiceError(NewsAssistantException):
    """AI サービス基底例外"""
    pass


class SummaryGenerationError(AIServiceError):
    """要約生成エラー"""
    pass


class AIProviderError(AIServiceError):
    """AI プロバイダーエラー"""
    pass


class AIConfigurationError(AIServiceError):
    """AI 設定エラー"""
    pass


class AIQuotaExceededError(AIServiceError):
    """AI API クォータ超過エラー"""
    pass


class AIRateLimitError(AIServiceError):
    """AI API レート制限エラー"""
    pass 