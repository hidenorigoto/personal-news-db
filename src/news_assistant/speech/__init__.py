"""音声変換モジュール

Azure Text-to-Speech APIを使用してテキストを音声データに変換する機能を提供します。
"""

from .exceptions import (
    AudioFileError,
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
    VoiceConfig,
    VoiceGender,
    VoiceInfo,
    VoiceListResponse,
    VoiceLocale,
)
from .service import AzureSpeechProvider, MockSpeechProvider, SpeechProvider, SpeechService

__all__ = [
    # Service classes
    "SpeechService",
    "AzureSpeechProvider",
    "MockSpeechProvider",
    "SpeechProvider",
    # Schemas
    "SpeechRequest",
    "SpeechResponse",
    "VoiceConfig",
    "VoiceInfo",
    "VoiceListResponse",
    "VoiceGender",
    "VoiceLocale",
    "OutputFormat",
    # Exceptions
    "SpeechServiceError",
    "SpeechConfigurationError",
    "SpeechSynthesisError",
    "VoiceNotFoundError",
    "AudioFileError",
    "SpeechQuotaExceededError",
]
