"""AI プロバイダー実装"""
import logging
import time
from abc import ABC, abstractmethod

import openai

from .exceptions import (
    AIConfigurationError,
    AIProviderError,
    AIQuotaExceededError,
    AIRateLimitError,
    SummaryGenerationError,
)
from .schemas import AIConfig, AIProviderType, SummaryRequest, SummaryResponse

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """AI プロバイダー抽象基底クラス"""

    def __init__(self, config: AIConfig):
        """
        Args:
            config: AI設定
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """設定の検証"""
        pass

    @abstractmethod
    def generate_summary(self, request: SummaryRequest) -> SummaryResponse:
        """要約を生成"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """接続テスト"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI プロバイダー"""

    def __init__(self, config: AIConfig):
        super().__init__(config)
        self.client = openai.OpenAI(
            api_key=config.api_key, base_url=config.base_url, timeout=config.timeout
        )

    def _validate_config(self) -> None:
        """OpenAI設定の検証"""
        if not self.config.api_key:
            raise AIConfigurationError("OpenAI API key is required", error_code="MISSING_API_KEY")

        if self.config.provider != AIProviderType.OPENAI:
            raise AIConfigurationError(
                f"Invalid provider type: {self.config.provider}", error_code="INVALID_PROVIDER"
            )

    def generate_summary(self, request: SummaryRequest) -> SummaryResponse:
        """OpenAI APIを使用して要約を生成"""
        start_time = time.time()

        try:
            # プロンプト生成
            prompt = self._build_prompt(request)

            # OpenAI API呼び出し
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # レスポンス処理
            content = response.choices[0].message.content
            if content is None:
                raise SummaryGenerationError(
                    "OpenAI API returned empty content", error_code="EMPTY_RESPONSE"
                )

            summary = content.strip()
            processing_time = time.time() - start_time

            # メタデータ収集
            metadata = {
                "usage": response.usage.model_dump() if response.usage else {},
                "finish_reason": response.choices[0].finish_reason,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }

            return SummaryResponse(
                summary=summary,
                original_length=len(request.content),
                summary_length=len(summary),
                compression_ratio=len(summary) / len(request.content),
                provider=self.config.provider,
                model_name=self.config.model_name,
                processing_time=processing_time,
                metadata=metadata,
            )

        except openai.RateLimitError as e:
            raise AIRateLimitError(
                f"OpenAI rate limit exceeded: {e}", error_code="RATE_LIMIT_EXCEEDED"
            ) from e
        except openai.APIError as e:
            if "quota" in str(e).lower():
                raise AIQuotaExceededError(
                    f"OpenAI quota exceeded: {e}", error_code="QUOTA_EXCEEDED"
                ) from e
            raise AIProviderError(f"OpenAI API error: {e}", error_code="API_ERROR") from e
        except Exception as e:
            raise SummaryGenerationError(
                f"Summary generation failed: {e}", error_code="GENERATION_FAILED"
            ) from e

    def _build_prompt(self, request: SummaryRequest) -> str:
        """プロンプトを構築"""
        if request.custom_prompt:
            return request.custom_prompt.format(content=request.content)

        # デフォルトプロンプトテンプレート
        templates = {
            "concise": (
                "以下のニュース記事を{max_length}文字程度で簡潔に要約してください。" "重要なポイントのみを含めてください。\n\n記事:\n{content}"
            ),
            "detailed": (
                "以下のニュース記事を{max_length}文字程度で詳細に要約してください。"
                "背景情報や詳細も含めて包括的にまとめてください。\n\n記事:\n{content}"
            ),
            "bullet_points": ("以下のニュース記事の要点を箇条書きで{max_length}文字程度に" "まとめてください。\n\n記事:\n{content}"),
            "executive": (
                "以下のニュース記事をエグゼクティブサマリー形式で{max_length}文字程度に"
                "まとめてください。意思決定に必要な情報を中心に記載してください。\n\n記事:\n{content}"
            ),
        }

        template = templates.get(request.style.value, templates["concise"])
        max_length = request.max_length or 1000

        return template.format(content=request.content, max_length=max_length)

    def test_connection(self) -> bool:
        """OpenAI API接続テスト"""
        try:
            # 簡単なテストリクエスト
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.warning(f"OpenAI connection test failed: {e}")
            return False


class MockAIProvider(AIProvider):
    """テスト用モックプロバイダー"""

    def _validate_config(self) -> None:
        """モック設定の検証（常に成功）"""
        pass

    def generate_summary(self, request: SummaryRequest) -> SummaryResponse:
        """モック要約生成"""
        summary = f"これは{request.style.value}スタイルのモック要約です。"
        processing_time = 0.1

        return SummaryResponse(
            summary=summary,
            original_length=len(request.content),
            summary_length=len(summary),
            compression_ratio=len(summary) / len(request.content),
            provider=AIProviderType.LOCAL,
            model_name="mock-model",
            processing_time=processing_time,
            metadata={"mock": True},
        )

    def test_connection(self) -> bool:
        """モック接続テスト（常に成功）"""
        return True
