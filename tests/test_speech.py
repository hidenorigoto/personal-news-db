"""音声変換モジュールのテスト"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from news_assistant.speech import (
    MockSpeechProvider,
    OutputFormat,
    SpeechRequest,
    SpeechService,
    SpeechServiceError,
    VoiceConfig,
    VoiceGender,
    VoiceListResponse,
    VoiceLocale,
    VoiceNotFoundError,
)
from news_assistant.speech.service import OpenAISpeechProvider


class TestVoiceConfig:
    """VoiceConfig のテスト"""

    def test_default_voice_config(self) -> None:
        """デフォルト設定のテスト"""
        config = VoiceConfig(name="ja-JP-NanamiNeural")

        assert config.name == "ja-JP-NanamiNeural"
        assert config.locale == VoiceLocale.JA_JP
        assert config.gender == VoiceGender.FEMALE
        assert config.speaking_rate == 1.0
        assert config.pitch == "default"
        assert config.volume == 1.0

    def test_custom_voice_config(self) -> None:
        """カスタム設定のテスト"""
        config = VoiceConfig(
            name="en-US-JennyNeural",
            locale=VoiceLocale.EN_US,
            gender=VoiceGender.FEMALE,
            speaking_rate=1.2,
            pitch="+5Hz",
            volume=0.8,
        )

        assert config.name == "en-US-JennyNeural"
        assert config.locale == VoiceLocale.EN_US
        assert config.gender == VoiceGender.FEMALE
        assert config.speaking_rate == 1.2
        assert config.pitch == "+5Hz"
        assert config.volume == 0.8


class TestMockSpeechProvider:
    """MockSpeechProvider のテスト"""

    @pytest.fixture
    def mock_provider(self) -> MockSpeechProvider:
        """モックプロバイダーのフィクスチャ"""
        return MockSpeechProvider()

    @pytest.mark.asyncio
    async def test_synthesize_speech(self, mock_provider: MockSpeechProvider, tmp_path: Path) -> None:
        """音声合成のテスト"""
        output_path = tmp_path / "test.wav"
        voice_config = VoiceConfig(name="ja-JP-NanamiNeural")
        request = SpeechRequest(text="テストメッセージ", voice_config=voice_config, output_path=output_path)

        response = await mock_provider.synthesize_speech(request)

        assert response.success is True
        assert response.output_path == output_path
        assert response.duration_seconds == len("テストメッセージ") * 0.1
        assert response.file_size_bytes == len("テストメッセージ") * 100
        assert response.error_message is None

        # ファイルが作成されていることを確認
        assert output_path.exists()
        assert output_path.read_bytes() == b"MOCK_AUDIO_DATA"

    @pytest.mark.asyncio
    async def test_get_available_voices(self, mock_provider: MockSpeechProvider) -> None:
        """利用可能音声一覧のテスト"""
        response = await mock_provider.get_available_voices()

        assert isinstance(response, VoiceListResponse)
        assert response.total_count == 2
        assert len(response.voices) == 2

        # 最初の音声をチェック
        voice = response.voices[0]
        assert voice.name == "ja-JP-NanamiNeural"
        assert voice.display_name == "Nanami (Neural)"
        assert voice.locale == "ja-JP"
        assert voice.gender == "Female"
        assert voice.voice_type == "Neural"


class TestSpeechService:
    """SpeechService のテスト"""

    @pytest.mark.asyncio
    async def test_text_to_speech_simple(self) -> None:
        """シンプル音声変換のテスト"""
        service = SpeechService(provider=MockSpeechProvider())

        response = await service.text_to_speech_simple(
            text="テスト",
            voice_name="ja-JP-KeitaNeural",
            output_format=OutputFormat.MP3,
        )

        assert response.success is True
        assert response.output_path is not None


class TestOpenAISpeechProvider:
    """OpenAISpeechProvider のテスト"""

    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, tmp_path: Path) -> None:
        """OpenAI TTS音声合成成功のテスト"""
        with patch('openai.OpenAI') as mock_openai_class:
            # モックの設定
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # 音声レスポンスのモック
            mock_response = MagicMock()
            mock_response.stream_to_file = MagicMock()
            mock_client.audio.speech.create.return_value = mock_response

            # プロバイダーの作成
            provider = OpenAISpeechProvider(api_key="test-key")

            # テスト実行
            output_path = tmp_path / "test.mp3"
            voice_config = VoiceConfig(name="alloy", speaking_rate=1.5)
            request = SpeechRequest(
                text="テストメッセージ",
                voice_config=voice_config,
                output_format=OutputFormat.MP3,
                output_path=output_path
            )

            # ダミーファイルを作成（stream_to_fileの動作をシミュレート）
            output_path.write_bytes(b"OPENAI_AUDIO_DATA")

            response = await provider.synthesize_speech(request)

            # アサーション
            assert response.success is True
            assert response.output_path == output_path
            assert response.file_size_bytes == 17  # len(b"OPENAI_AUDIO_DATA")

            # API呼び出しの確認
            mock_client.audio.speech.create.assert_called_once_with(
                model=provider.model,  # 実際のプロバイダーの設定を使用
                voice="alloy",
                input="テストメッセージ",
                response_format="mp3",
                speed=1.5
            )

    @pytest.mark.asyncio
    async def test_get_available_voices(self) -> None:
        """OpenAI TTS利用可能音声一覧のテスト"""
        with patch('openai.OpenAI'):
            provider = OpenAISpeechProvider(api_key="test-key")
            response = await provider.get_available_voices()

            assert isinstance(response, VoiceListResponse)
            assert response.total_count == 6
            assert len(response.voices) == 6

            # 音声名の確認
            voice_names = [voice.name for voice in response.voices]
            expected_names = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            assert voice_names == expected_names

    @pytest.mark.asyncio
    async def test_speed_limit_validation(self, tmp_path: Path) -> None:
        """速度制限のバリデーションテスト"""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_response = MagicMock()
            mock_response.stream_to_file = MagicMock()
            mock_client.audio.speech.create.return_value = mock_response

            provider = OpenAISpeechProvider(api_key="test-key")

            # VoiceConfigの制限は2.0まで、OpenAI側で4.0に変換されることをテスト
            voice_config = VoiceConfig(name="alloy", speaking_rate=2.0)  # VoiceConfigの最大値
            request = SpeechRequest(
                text="テスト",
                voice_config=voice_config,
                output_format=OutputFormat.MP3
            )

            await provider.synthesize_speech(request)

            # 速度が2.0で呼び出されることを確認
            mock_client.audio.speech.create.assert_called_once()
            call_args = mock_client.audio.speech.create.call_args
            assert call_args.kwargs['speed'] == 2.0


class TestSpeechServiceProviderSelection:
    """SpeechServiceのプロバイダー選択テスト"""

    @patch('news_assistant.speech.service.settings')
    def test_select_openai_provider(self, mock_settings: MagicMock) -> None:
        """OpenAIプロバイダーが選択されることのテスト"""
        mock_settings.speech_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_tts_model = "tts-1"
        mock_settings.openai_tts_voice = "alloy"
        mock_settings.openai_tts_speed = 1.0

        with patch('news_assistant.speech.service.OpenAISpeechProvider') as mock_provider_class:
            _ = SpeechService()
            mock_provider_class.assert_called_once()

    @patch('news_assistant.speech.service.settings')
    def test_select_azure_provider(self, mock_settings: MagicMock) -> None:
        """Azureプロバイダーが選択されることのテスト"""
        mock_settings.speech_provider = "azure"
        mock_settings.azure_speech_key = "test-key"
        mock_settings.azure_speech_region = "japaneast"

        with patch('news_assistant.speech.service.AzureSpeechProvider') as mock_provider_class:
            _ = SpeechService()
            mock_provider_class.assert_called_once()


class TestExceptions:
    """例外クラスのテスト"""

    def test_speech_service_error(self) -> None:
        """SpeechServiceError のテスト"""
        error = SpeechServiceError("テストエラー", {"key": "value"})

        assert error.message == "テストエラー"
        assert error.details == {"key": "value"}
        assert str(error) == "テストエラー"

    def test_voice_not_found_error(self) -> None:
        """VoiceNotFoundError のテスト"""
        error = VoiceNotFoundError("ja-JP-TestVoice")

        assert "ja-JP-TestVoice" in error.message
        assert error.details["voice_name"] == "ja-JP-TestVoice"
