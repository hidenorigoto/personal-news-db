"""要約サービス統合クラス"""
import os
import logging
from typing import Optional, Dict, Any

from ..core import settings
from .schemas import (
    AIConfig, 
    SummaryRequest, 
    SummaryResponse, 
    AIProviderType, 
    SummaryStyle
)
from .providers import AIProvider, OpenAIProvider, MockAIProvider
from .exceptions import AIConfigurationError, SummaryGenerationError

logger = logging.getLogger(__name__)


class SummarizerService:
    """要約サービス統合クラス"""
    
    def __init__(self, config: Optional[AIConfig] = None):
        """
        Args:
            config: AI設定（Noneの場合は環境変数から自動設定）
        """
        self.config = config or self._create_default_config()
        self.provider = self._create_provider()
    
    def _create_default_config(self) -> AIConfig:
        """環境変数からデフォルト設定を作成"""
        api_key = os.environ.get("OPENAI_API_KEY")
        
        if api_key:
            return AIConfig(
                provider=AIProviderType.OPENAI,
                model_name="gpt-3.5-turbo",
                api_key=api_key,
                max_tokens=1000,
                temperature=0.3,
                timeout=30
            )
        else:
            # API キーがない場合はモックプロバイダーを使用
            logger.warning("No OpenAI API key found, using mock provider")
            return AIConfig(
                provider=AIProviderType.LOCAL,
                model_name="mock-model",
                max_tokens=1000,
                temperature=0.3,
                timeout=30
            )
    
    def _create_provider(self) -> AIProvider:
        """設定に基づいてプロバイダーを作成"""
        if self.config.provider == AIProviderType.OPENAI:
            return OpenAIProvider(self.config)
        elif self.config.provider == AIProviderType.LOCAL:
            return MockAIProvider(self.config)
        else:
            raise AIConfigurationError(
                f"Unsupported provider: {self.config.provider}",
                error_code="UNSUPPORTED_PROVIDER"
            )
    
    def generate_summary(
        self,
        content: str,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: Optional[int] = None,
        language: str = "ja",
        custom_prompt: Optional[str] = None
    ) -> SummaryResponse:
        """要約を生成
        
        Args:
            content: 要約対象のテキスト
            style: 要約スタイル
            max_length: 最大文字数
            language: 言語
            custom_prompt: カスタムプロンプト
            
        Returns:
            要約レスポンス
            
        Raises:
            SummaryGenerationError: 要約生成に失敗した場合
        """
        if not content.strip():
            raise SummaryGenerationError(
                "Content cannot be empty",
                error_code="EMPTY_CONTENT"
            )
        
        request = SummaryRequest(
            content=content,
            style=style,
            max_length=max_length,
            language=language,
            custom_prompt=custom_prompt
        )
        
        try:
            return self.provider.generate_summary(request)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise
    
    def generate_simple_summary(self, content: str) -> str:
        """シンプルな要約生成（後方互換性のため）
        
        Args:
            content: 要約対象のテキスト
            
        Returns:
            要約テキスト
            
        Raises:
            SummaryGenerationError: 要約生成に失敗した場合
        """
        try:
            response = self.generate_summary(content)
            return response.summary
        except Exception as e:
            logger.error(f"Simple summary generation failed: {e}")
            raise SummaryGenerationError(
                f"Summary generation failed: {e}",
                error_code="SIMPLE_GENERATION_FAILED"
            ) from e
    
    def test_connection(self) -> bool:
        """AI プロバイダーへの接続をテスト"""
        try:
            return self.provider.test_connection()
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """プロバイダー情報を取得"""
        return {
            "provider": self.config.provider.value,
            "model_name": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "connection_status": self.test_connection()
        }
    
    def update_config(self, config: AIConfig) -> None:
        """設定を更新してプロバイダーを再作成"""
        self.config = config
        self.provider = self._create_provider()
        logger.info(f"AI configuration updated: {config.provider.value}/{config.model_name}")


# グローバルインスタンス（後方互換性のため）
_default_summarizer: Optional[SummarizerService] = None


def get_default_summarizer() -> SummarizerService:
    """デフォルト要約サービスを取得"""
    global _default_summarizer
    if _default_summarizer is None:
        _default_summarizer = SummarizerService()
    return _default_summarizer


def generate_summary(content: str, model: str = "gpt-3.5-turbo", max_tokens: int = 900) -> str:
    """後方互換性のための要約生成関数
    
    Args:
        content: 要約対象のテキスト
        model: モデル名（互換性のため、実際は使用されない）
        max_tokens: 最大トークン数（互換性のため、実際は使用されない）
        
    Returns:
        要約テキスト
        
    Raises:
        SummaryGenerationError: 要約生成に失敗した場合
    """
    summarizer = get_default_summarizer()
    return summarizer.generate_simple_summary(content) 