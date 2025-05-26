"""Azure Text-to-Speech サービス実装"""

import logging
import uuid
from pathlib import Path
from typing import Protocol

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None

from news_assistant.core.config import settings

from .exceptions import (
    SpeechConfigurationError,
    SpeechQuotaExceededError,
    SpeechServiceError,
    SpeechSynthesisError,
    VoiceNotFoundError,
)
from .schemas import (
    OutputFormat,
    SpeechRequest,
    SpeechResponse,
    VoiceInfo,
    VoiceListResponse,
)

logger = logging.getLogger(__name__)


class SpeechProvider(Protocol):
    """音声プロバイダーのプロトコル"""

    async def synthesize_speech(self, request: SpeechRequest) -> SpeechResponse:
        """テキストを音声に変換"""
        ...

    async def get_available_voices(self) -> VoiceListResponse:
        """利用可能な音声一覧を取得"""
        ...


class AzureSpeechProvider:
    """Azure Speech Service プロバイダー"""

    def __init__(self, api_key: str | None = None, region: str | None = None) -> None:
        if speechsdk is None:
            raise SpeechConfigurationError(
                "Azure Speech SDK がインストールされていません。"
                "pip install azure-cognitiveservices-speech を実行してください。"
            )

        self.api_key = api_key or settings.azure_speech_key
        self.region = region or settings.azure_speech_region

        if not self.api_key:
            raise SpeechConfigurationError(
                "Azure Speech Service APIキーが設定されていません。"
                "AZURE_SPEECH_KEY 環境変数を設定してください。"
            )

        if not self.region:
            raise SpeechConfigurationError(
                "Azure Speech Service リージョンが設定されていません。"
                "AZURE_SPEECH_REGION 環境変数を設定してください。"
            )

        # Azure Speech Config の初期化
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.api_key, region=self.region
        )

    def _get_audio_format(self, output_format: OutputFormat) -> speechsdk.SpeechSynthesisOutputFormat:
        """出力フォーマットをAzure Speech SDKの形式に変換"""
        format_mapping = {
            OutputFormat.WAV: speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
            OutputFormat.MP3: speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
            OutputFormat.OGG: speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus,
        }
        return format_mapping.get(output_format, speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)

    def _generate_output_path(self, output_format: OutputFormat) -> Path:
        """出力ファイルパスを自動生成"""
        output_dir = Path(settings.data_dir) / "speech"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"speech_{uuid.uuid4().hex[:8]}.{output_format.value}"
        return output_dir / filename

    def _create_ssml(self, request: SpeechRequest) -> str:
        """SSMLを生成"""
        voice_config = request.voice_config

        # 話速の設定
        rate = f"{voice_config.speaking_rate:.1f}"
        if voice_config.speaking_rate == 1.0:
            rate = "default"
        elif voice_config.speaking_rate < 1.0:
            rate = f"{voice_config.speaking_rate:.1f}"
        else:
            rate = f"+{voice_config.speaking_rate - 1.0:.1f}"

        # 音程の設定
        pitch = voice_config.pitch if voice_config.pitch != "default" else "default"

        # 音量の設定
        volume = f"{int(voice_config.volume * 100)}"

        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{voice_config.locale.value}">
            <voice name="{voice_config.name}">
                <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">
                    {request.text}
                </prosody>
            </voice>
        </speak>
        """.strip()

        return ssml

    async def synthesize_speech(self, request: SpeechRequest) -> SpeechResponse:
        """テキストを音声に変換"""
        try:
            # 出力パスの決定
            output_path = request.output_path or self._generate_output_path(request.output_format)

            # 音声設定
            audio_format = self._get_audio_format(request.output_format)
            self.speech_config.set_speech_synthesis_output_format(audio_format)

            # 音声ファイル設定
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))

            # 音声合成器の作成
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, audio_config=audio_config
            )

            # SSMLの生成
            ssml = self._create_ssml(request)

            logger.info(f"音声合成開始: {request.text[:50]}...")

            # 音声合成実行
            result = synthesizer.speak_ssml_async(ssml).get()

            # 結果の確認
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # ファイル情報の取得
                file_size = output_path.stat().st_size if output_path.exists() else 0

                # 音声の長さを推定（簡易計算）
                # WAV 16kHz 16bit mono の場合: 32000 bytes/sec
                duration = file_size / 32000 if request.output_format == OutputFormat.WAV else None

                logger.info(f"音声合成完了: {output_path}")

                return SpeechResponse(
                    success=True,
                    output_path=output_path,
                    duration_seconds=duration,
                    file_size_bytes=file_size,
                )

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speechsdk.CancellationDetails(result)

                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg = f"音声合成エラー: {cancellation_details.error_details}"

                    # 特定のエラーに応じた例外を発生
                    if "quota" in cancellation_details.error_details.lower():
                        raise SpeechQuotaExceededError(error_msg)
                    elif "voice" in cancellation_details.error_details.lower():
                        raise VoiceNotFoundError(request.voice_config.name)
                    else:
                        raise SpeechSynthesisError(error_msg)

                raise SpeechSynthesisError(f"音声合成がキャンセルされました: {cancellation_details.reason}")

            else:
                raise SpeechSynthesisError(f"予期しない結果: {result.reason}")

        except Exception as e:
            if isinstance(e, SpeechServiceError):
                raise

            logger.error(f"音声合成中にエラーが発生: {e}")
            return SpeechResponse(success=False, error_message=str(e))

    async def get_available_voices(self) -> VoiceListResponse:
        """利用可能な音声一覧を取得"""
        try:
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            result = synthesizer.get_voices_async().get()

            if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                voices = []
                for voice in result.voices:
                    voice_info = VoiceInfo(
                        name=voice.short_name,
                        display_name=voice.local_name,
                        locale=voice.locale,
                        gender=voice.gender.name,
                        voice_type=voice.voice_type.name,
                        sample_rate_hertz=24000,  # Azure Neural Voicesの標準サンプルレート
                    )
                    voices.append(voice_info)

                return VoiceListResponse(voices=voices, total_count=len(voices))

            else:
                raise SpeechServiceError(f"音声一覧の取得に失敗: {result.reason}")

        except Exception as e:
            if isinstance(e, SpeechServiceError):
                raise

            logger.error(f"音声一覧取得中にエラーが発生: {e}")
            raise SpeechServiceError(f"音声一覧の取得に失敗: {e}") from e


class MockSpeechProvider:
    """テスト用のモック音声プロバイダー"""

    async def synthesize_speech(self, request: SpeechRequest) -> SpeechResponse:
        """モック音声合成"""
        # テスト用のダミーファイルを作成
        output_path = request.output_path or Path(f"mock_speech_{uuid.uuid4().hex[:8]}.wav")

        # ダミーファイルの作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"MOCK_AUDIO_DATA")

        return SpeechResponse(
            success=True,
            output_path=output_path,
            duration_seconds=len(request.text) * 0.1,  # 文字数 × 0.1秒
            file_size_bytes=len(request.text) * 100,  # 文字数 × 100バイト
        )

    async def get_available_voices(self) -> VoiceListResponse:
        """モック音声一覧"""
        mock_voices = [
            VoiceInfo(
                name="ja-JP-NanamiNeural",
                display_name="Nanami (Neural)",
                locale="ja-JP",
                gender="Female",
                voice_type="Neural",
                sample_rate_hertz=24000,
            ),
            VoiceInfo(
                name="ja-JP-KeitaNeural",
                display_name="Keita (Neural)",
                locale="ja-JP",
                gender="Male",
                voice_type="Neural",
                sample_rate_hertz=24000,
            ),
        ]

        return VoiceListResponse(voices=mock_voices, total_count=len(mock_voices))


class SpeechService:
    """音声サービスのファサード"""

    def __init__(self, provider: SpeechProvider | None = None) -> None:
        if provider is None:
            # 本番環境では Azure プロバイダーを使用
            if settings.azure_speech_key:
                provider = AzureSpeechProvider()
            else:
                # APIキーが設定されていない場合はモックを使用
                logger.warning("Azure Speech APIキーが設定されていません。モックプロバイダーを使用します。")
                provider = MockSpeechProvider()

        self.provider = provider

    async def text_to_speech(self, request: SpeechRequest) -> SpeechResponse:
        """テキストを音声に変換"""
        return await self.provider.synthesize_speech(request)

    async def get_voices(self) -> VoiceListResponse:
        """利用可能な音声一覧を取得"""
        return await self.provider.get_available_voices()

    async def text_to_speech_simple(
        self,
        text: str,
        voice_name: str = "ja-JP-NanamiNeural",
        output_format: OutputFormat = OutputFormat.WAV,
        output_path: Path | None = None,
    ) -> SpeechResponse:
        """シンプルなテキスト音声変換"""
        from .schemas import VoiceConfig

        voice_config = VoiceConfig(name=voice_name)
        request = SpeechRequest(
            text=text,
            voice_config=voice_config,
            output_format=output_format,
            output_path=output_path,
        )

        return await self.text_to_speech(request)

    async def text_to_speech_with_template(
        self,
        text: str,
        article_title: str,
        content_type: str = "要約",
        voice_name: str = "ja-JP-NanamiNeural",
        output_format: OutputFormat = OutputFormat.WAV,
        output_path: Path | None = None,
    ) -> SpeechResponse:
        """テンプレートヘッダー付きテキスト音声変換"""
        # テンプレートヘッダーを作成
        header = f"{article_title}の{content_type}をお読みします。"
        full_text = f"{header}\n\n{text}"

        return await self.text_to_speech_simple(
            text=full_text,
            voice_name=voice_name,
            output_format=output_format,
            output_path=output_path,
        )

    def generate_article_audio_path(
        self,
        article_id: int,
        content_type: str,
        output_format: OutputFormat = OutputFormat.WAV
    ) -> Path:
        """記事用音声ファイルパスを生成"""
        output_dir = Path(settings.data_dir) / "speech"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{article_id}-{content_type}.{output_format.value}"
        return output_dir / filename
