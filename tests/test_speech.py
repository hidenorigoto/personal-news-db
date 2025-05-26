"""音声変換モジュールのテスト"""

from pathlib import Path

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
