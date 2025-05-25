"""コンテンツ処理関連のPydanticスキーマ"""

from pydantic import BaseModel, Field, HttpUrl


class ContentData(BaseModel):
    """取得したコンテンツデータ"""

    url: HttpUrl = Field(..., description="コンテンツのURL")
    content: bytes = Field(..., description="取得したコンテンツ（バイナリ）")
    content_type: str = Field(..., description="Content-Typeヘッダー")
    extension: str = Field(..., description="推定されたファイル拡張子")


class ProcessedContent(BaseModel):
    """処理済みコンテンツ"""

    url: HttpUrl = Field(..., description="コンテンツのURL")
    title: str = Field(..., description="抽出されたタイトル")
    extracted_text: str = Field(default="", description="抽出されたテキスト")
    summary: str = Field(default="", description="生成された要約")
    extension: str = Field(..., description="ファイル拡張子")
    file_path: str | None = Field(None, description="保存されたファイルパス")


class TitleExtractionResult(BaseModel):
    """タイトル抽出結果"""

    title: str = Field(default="", description="抽出されたタイトル")
    success: bool = Field(..., description="抽出成功フラグ")
    method: str = Field(..., description="抽出方法（html_tag, pdf_metadata, fallback等）")


class TextExtractionResult(BaseModel):
    """テキスト抽出結果"""

    text: str = Field(default="", description="抽出されたテキスト")
    success: bool = Field(..., description="抽出成功フラグ")
    word_count: int = Field(default=0, description="文字数")
