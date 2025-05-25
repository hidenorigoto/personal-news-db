"""AI機能関連のPydanticスキーマ"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AIProviderType(str, Enum):
    """AI プロバイダータイプ"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"


class SummaryStyle(str, Enum):
    """要約スタイル"""

    CONCISE = "concise"  # 簡潔
    DETAILED = "detailed"  # 詳細
    BULLET_POINTS = "bullet_points"  # 箇条書き
    EXECUTIVE = "executive"  # エグゼクティブサマリー


class AIConfig(BaseModel):
    """AI設定"""

    model_config = ConfigDict(extra="forbid")

    provider: AIProviderType = Field(..., description="AI プロバイダー")
    model_name: str = Field(..., description="使用するモデル名")
    api_key: str | None = Field(None, description="API キー")
    base_url: str | None = Field(None, description="ベースURL（カスタムエンドポイント用）")
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="最大トークン数")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="温度パラメータ")
    timeout: int = Field(default=30, ge=1, le=300, description="タイムアウト（秒）")


class SummaryRequest(BaseModel):
    """要約リクエスト"""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., min_length=1, description="要約対象のテキスト")
    style: SummaryStyle = Field(default=SummaryStyle.CONCISE, description="要約スタイル")
    max_length: int | None = Field(None, ge=50, le=2000, description="要約の最大文字数")
    language: str = Field(default="ja", description="要約言語（ISO 639-1）")
    custom_prompt: str | None = Field(None, description="カスタムプロンプト")


class SummaryResponse(BaseModel):
    """要約レスポンス"""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., description="生成された要約")
    original_length: int = Field(..., description="元テキストの文字数")
    summary_length: int = Field(..., description="要約の文字数")
    compression_ratio: float = Field(..., description="圧縮率")
    provider: AIProviderType = Field(..., description="使用したプロバイダー")
    model_name: str = Field(..., description="使用したモデル")
    processing_time: float = Field(..., description="処理時間（秒）")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    metadata: dict[str, Any] = Field(default_factory=dict, description="追加メタデータ")


class AIUsageStats(BaseModel):
    """AI使用統計"""

    model_config = ConfigDict(extra="forbid")

    provider: AIProviderType = Field(..., description="プロバイダー")
    model_name: str = Field(..., description="モデル名")
    total_requests: int = Field(default=0, description="総リクエスト数")
    successful_requests: int = Field(default=0, description="成功リクエスト数")
    failed_requests: int = Field(default=0, description="失敗リクエスト数")
    total_tokens: int = Field(default=0, description="総トークン数")
    total_cost: float = Field(default=0.0, description="総コスト（USD）")
    average_response_time: float = Field(default=0.0, description="平均応答時間（秒）")
    last_used: datetime | None = Field(None, description="最終使用日時")


class PromptTemplate(BaseModel):
    """プロンプトテンプレート"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="テンプレート名")
    style: SummaryStyle = Field(..., description="対応する要約スタイル")
    language: str = Field(..., description="言語")
    template: str = Field(..., description="プロンプトテンプレート")
    variables: list[str] = Field(default_factory=list, description="テンプレート変数")
    description: str | None = Field(None, description="テンプレートの説明")
