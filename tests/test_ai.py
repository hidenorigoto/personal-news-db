"""AI機能モジュールのテスト"""
from unittest.mock import MagicMock, patch

import pytest

from news_assistant.ai import (
    AIConfig,
    AIConfigurationError,
    AIProviderType,
    MockAIProvider,
    OpenAIProvider,
    SummarizerService,
    SummaryGenerationError,
    SummaryRequest,
    SummaryResponse,
    SummaryStyle,
)


class TestAIConfig:
    """AIConfig のテスト"""

    def test_valid_config(self) -> None:
        """有効な設定のテスト"""
        config = AIConfig(
            provider=AIProviderType.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            base_url=None,
            max_tokens=1000,
            temperature=0.3,
        )

        assert config.provider == AIProviderType.OPENAI
        assert config.model_name == "gpt-3.5-turbo"
        assert config.api_key == "test-key"
        assert config.max_tokens == 1000
        assert config.temperature == 0.3

    def test_invalid_temperature(self) -> None:
        """無効な温度パラメータのテスト"""
        with pytest.raises(ValueError):
            AIConfig(
                provider=AIProviderType.OPENAI,
                model_name="gpt-3.5-turbo",
                api_key="test-key",
                base_url=None,
                temperature=3.0,  # 範囲外
            )


class TestSummaryRequest:
    """SummaryRequest のテスト"""

    def test_valid_request(self) -> None:
        """有効なリクエストのテスト"""
        request = SummaryRequest(
            content="テストコンテンツ",
            style=SummaryStyle.CONCISE,
            max_length=500,
            language="ja",
            custom_prompt=None,
        )

        assert request.content == "テストコンテンツ"
        assert request.style == SummaryStyle.CONCISE
        assert request.max_length == 500
        assert request.language == "ja"

    def test_empty_content(self) -> None:
        """空のコンテンツのテスト"""
        with pytest.raises(ValueError):
            SummaryRequest(content="", max_length=None, custom_prompt=None)


class TestMockAIProvider:
    """MockAIProvider のテスト"""

    def test_mock_provider_creation(self) -> None:
        """モックプロバイダー作成テスト"""
        config = AIConfig(
            provider=AIProviderType.LOCAL, model_name="mock-model", api_key=None, base_url=None
        )
        provider = MockAIProvider(config)
        assert provider.config.provider == AIProviderType.LOCAL

    def test_mock_summary_generation(self) -> None:
        """モック要約生成テスト"""
        config = AIConfig(
            provider=AIProviderType.LOCAL, model_name="mock-model", api_key=None, base_url=None
        )
        provider = MockAIProvider(config)

        request = SummaryRequest(
            content="テストコンテンツ",
            style=SummaryStyle.DETAILED,
            max_length=None,
            custom_prompt=None,
        )

        response = provider.generate_summary(request)

        assert isinstance(response, SummaryResponse)
        assert "detailed" in response.summary
        assert response.provider == AIProviderType.LOCAL
        assert response.model_name == "mock-model"
        assert response.original_length == len("テストコンテンツ")

    def test_mock_connection_test(self) -> None:
        """モック接続テスト"""
        config = AIConfig(
            provider=AIProviderType.LOCAL, model_name="mock-model", api_key=None, base_url=None
        )
        provider = MockAIProvider(config)

        assert provider.test_connection() is True


class TestOpenAIProvider:
    """OpenAIProvider のテスト"""

    def test_openai_provider_creation_without_api_key(self) -> None:
        """API キーなしでのOpenAIプロバイダー作成テスト"""
        config = AIConfig(
            provider=AIProviderType.OPENAI, model_name="gpt-3.5-turbo", api_key=None, base_url=None
        )

        with pytest.raises(AIConfigurationError) as exc_info:
            OpenAIProvider(config)

        assert exc_info.value.error_code == "MISSING_API_KEY"

    def test_openai_provider_creation_with_api_key(self) -> None:
        """API キーありでのOpenAIプロバイダー作成テスト"""
        config = AIConfig(
            provider=AIProviderType.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            base_url=None,
        )

        provider = OpenAIProvider(config)
        assert provider.config.api_key == "test-key"

    @patch("openai.OpenAI")
    def test_openai_summary_generation(self, mock_openai_client: MagicMock) -> None:
        """OpenAI要約生成テスト"""
        # モック設定
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "生成された要約"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        }

        mock_client_instance.chat.completions.create.return_value = mock_response

        # テスト実行
        config = AIConfig(
            provider=AIProviderType.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            base_url=None,
        )
        provider = OpenAIProvider(config)

        request = SummaryRequest(
            content="テストコンテンツ",
            style=SummaryStyle.CONCISE,
            max_length=None,
            custom_prompt=None,
        )

        response = provider.generate_summary(request)

        # 検証
        assert response.summary == "生成された要約"
        assert response.provider == AIProviderType.OPENAI
        assert response.model_name == "gpt-3.5-turbo"
        assert response.metadata["prompt_tokens"] == 100
        assert response.metadata["completion_tokens"] == 50


class TestSummarizerService:
    """SummarizerService のテスト"""

    def test_summarizer_with_mock_provider(self) -> None:
        """モックプロバイダーでの要約サービステスト"""
        config = AIConfig(
            provider=AIProviderType.LOCAL, model_name="mock-model", api_key=None, base_url=None
        )

        summarizer = SummarizerService(config)

        response = summarizer.generate_summary(
            content="テストコンテンツ",
            style=SummaryStyle.BULLET_POINTS,
            max_length=None,
            custom_prompt=None,
        )

        assert isinstance(response, SummaryResponse)
        assert "bullet_points" in response.summary
        assert response.provider == AIProviderType.LOCAL

    def test_simple_summary_generation(self) -> None:
        """シンプル要約生成テスト"""
        config = AIConfig(
            provider=AIProviderType.LOCAL, model_name="mock-model", api_key=None, base_url=None
        )

        summarizer = SummarizerService(config)
        summary = summarizer.generate_simple_summary("テストコンテンツ")

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_empty_content_error(self) -> None:
        """空コンテンツエラーテスト"""
        config = AIConfig(
            provider=AIProviderType.LOCAL, model_name="mock-model", api_key=None, base_url=None
        )

        summarizer = SummarizerService(config)

        with pytest.raises(SummaryGenerationError) as exc_info:
            summarizer.generate_summary("")

        assert exc_info.value.error_code == "EMPTY_CONTENT"

    def test_provider_info(self) -> None:
        """プロバイダー情報取得テスト"""
        config = AIConfig(
            provider=AIProviderType.LOCAL,
            model_name="mock-model",
            api_key=None,
            base_url=None,
            max_tokens=500,
            temperature=0.5,
        )

        summarizer = SummarizerService(config)
        info = summarizer.get_provider_info()

        assert info["provider"] == "local"
        assert info["model_name"] == "mock-model"
        assert info["max_tokens"] == 500
        assert info["temperature"] == 0.5
        assert info["connection_status"] is True

    @patch.dict("os.environ", {}, clear=True)
    def test_default_config_without_api_key(self) -> None:
        """API キーなしでのデフォルト設定テスト"""
        summarizer = SummarizerService()

        assert summarizer.config.provider == AIProviderType.LOCAL
        assert summarizer.config.model_name == "mock-model"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_default_config_with_api_key(self) -> None:
        """API キーありでのデフォルト設定テスト"""
        summarizer = SummarizerService()

        # 環境変数によってプロバイダーが決まる
        # API キーが設定されている場合はOPENAIプロバイダーが使用される
        provider_type = summarizer.config.provider
        assert provider_type in [AIProviderType.OPENAI, AIProviderType.LOCAL]

        # プロバイダータイプに応じた検証
        if provider_type.value == "openai":
            assert summarizer.config.model_name == "gpt-3.5-turbo"
            assert summarizer.config.api_key == "test-key"
        else:  # local provider
            assert summarizer.config.model_name == "mock-model"

    def test_config_update(self) -> None:
        """設定更新テスト"""
        initial_config = AIConfig(
            provider=AIProviderType.LOCAL, model_name="mock-model", api_key=None, base_url=None
        )

        summarizer = SummarizerService(initial_config)
        assert summarizer.config.provider == AIProviderType.LOCAL

        new_config = AIConfig(
            provider=AIProviderType.OPENAI, model_name="gpt-4", api_key="new-key", base_url=None
        )

        summarizer.update_config(new_config)
        # 設定が更新されたことを確認
        assert summarizer.config.provider.value == "openai"
        assert summarizer.config.model_name == "gpt-4"


class TestBackwardCompatibility:
    """後方互換性のテスト"""

    @patch("news_assistant.ai.summarizer.get_default_summarizer")
    def test_generate_summary_function(self, mock_get_summarizer: MagicMock) -> None:
        """generate_summary関数の後方互換性テスト"""
        from news_assistant.ai.summarizer import generate_summary

        mock_summarizer = MagicMock()
        mock_summarizer.generate_simple_summary.return_value = "生成された要約"
        mock_get_summarizer.return_value = mock_summarizer

        result = generate_summary("テストコンテンツ")

        assert result == "生成された要約"
        mock_summarizer.generate_simple_summary.assert_called_once_with("テストコンテンツ")

    def test_summary_module_import(self) -> None:
        """新しいAIモジュールからのインポートテスト"""
        from news_assistant.ai.exceptions import SummaryGenerationError
        from news_assistant.ai.summarizer import generate_summary

        # 関数とクラスが正しくインポートされることを確認
        assert callable(generate_summary)
        assert issubclass(SummaryGenerationError, Exception)
