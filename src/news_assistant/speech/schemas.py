"""音声変換モジュールのスキーマ定義"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class VoiceGender(str, Enum):
    """音声の性別"""

    MALE = "Male"
    FEMALE = "Female"
    NEUTRAL = "Neutral"


class VoiceLocale(str, Enum):
    """音声のロケール"""

    JA_JP = "ja-JP"
    EN_US = "en-US"
    EN_GB = "en-GB"


class OutputFormat(str, Enum):
    """音声出力フォーマット"""

    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


class VoiceConfig(BaseModel):
    """音声設定"""

    name: str = Field(description="音声名（例: ja-JP-NanamiNeural）")
    locale: VoiceLocale = Field(default=VoiceLocale.JA_JP, description="ロケール")
    gender: VoiceGender = Field(default=VoiceGender.FEMALE, description="性別")
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0, description="話速（0.5-2.0）")
    pitch: str = Field(default="default", description="音程（例: +10Hz, -5Hz, default）")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="音量（0.0-1.0）")


class SpeechRequest(BaseModel):
    """音声変換リクエスト"""

    text: str = Field(min_length=1, max_length=10000, description="変換するテキスト")
    voice_config: VoiceConfig = Field(default_factory=lambda: VoiceConfig(name="ja-JP-NanamiNeural"), description="音声設定")
    output_format: OutputFormat = Field(default=OutputFormat.WAV, description="出力フォーマット")
    output_path: Path | None = Field(default=None, description="出力ファイルパス（Noneの場合は自動生成）")


class SpeechResponse(BaseModel):
    """音声変換レスポンス"""

    success: bool = Field(description="変換成功フラグ")
    output_path: Path | None = Field(default=None, description="出力ファイルパス")
    duration_seconds: float | None = Field(default=None, description="音声の長さ（秒）")
    file_size_bytes: int | None = Field(default=None, description="ファイルサイズ（バイト）")
    error_message: str | None = Field(default=None, description="エラーメッセージ")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class VoiceInfo(BaseModel):
    """利用可能な音声情報"""

    name: str = Field(description="音声名")
    display_name: str = Field(description="表示名")
    locale: str = Field(description="ロケール")
    gender: str = Field(description="性別")
    voice_type: str = Field(description="音声タイプ（Neural/Standard）")
    sample_rate_hertz: int = Field(description="サンプルレート")


class VoiceListResponse(BaseModel):
    """利用可能な音声一覧レスポンス"""

    voices: list[VoiceInfo] = Field(description="音声一覧")
    total_count: int = Field(description="総数")
