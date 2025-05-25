"""アプリケーション設定管理"""
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 環境変数を読み込み
load_dotenv()


class Settings(BaseSettings):
    """アプリケーション設定"""

    # アプリケーション基本設定
    app_name: str = "News Assistant API"
    version: str = "0.1.0"
    debug: bool = Field(default=False, description="デバッグモード")

    # データベース設定
    database_url: str = Field(
        default="sqlite:///./data/news.db",
        alias="NEWS_ASSISTANT_DB_URL",
        description="データベース接続URL"
    )

    # OpenAI API設定
    openai_api_key: str | None = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI APIキー"
    )

    # ファイル保存設定
    data_dir: str = Field(
        default="data",
        description="データファイル保存ディレクトリ"
    )

    # AI要約設定
    summary_model: str = Field(
        default="gpt-3.5-turbo",
        description="要約生成に使用するモデル"
    )
    summary_max_tokens: int = Field(
        default=900,
        description="要約生成の最大トークン数"
    )
    summary_temperature: float = Field(
        default=0.3,
        description="要約生成の温度パラメータ"
    )

    # HTTP設定
    request_timeout: int = Field(
        default=10,
        description="HTTP リクエストタイムアウト（秒）"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


# グローバル設定インスタンス
settings = get_settings()
