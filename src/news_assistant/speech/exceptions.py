"""音声変換モジュールの例外定義"""

from typing import Any


class SpeechServiceError(Exception):
    """音声サービス基底例外"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class SpeechConfigurationError(SpeechServiceError):
    """音声サービス設定エラー"""

    def __init__(self, message: str = "音声サービスの設定が正しくありません") -> None:
        super().__init__(message)


class SpeechSynthesisError(SpeechServiceError):
    """音声合成エラー"""

    def __init__(self, message: str, synthesis_id: str | None = None) -> None:
        details = {"synthesis_id": synthesis_id} if synthesis_id else {}
        super().__init__(message, details)


class VoiceNotFoundError(SpeechServiceError):
    """音声が見つからないエラー"""

    def __init__(self, voice_name: str) -> None:
        message = f"指定された音声が見つかりません: {voice_name}"
        super().__init__(message, {"voice_name": voice_name})


class AudioFileError(SpeechServiceError):
    """音声ファイル操作エラー"""

    def __init__(self, message: str, file_path: str | None = None) -> None:
        details = {"file_path": file_path} if file_path else {}
        super().__init__(message, details)


class SpeechQuotaExceededError(SpeechServiceError):
    """音声サービスクォータ超過エラー"""

    def __init__(self, message: str = "音声サービスのクォータを超過しました") -> None:
        super().__init__(message)
