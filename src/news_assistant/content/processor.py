"""コンテンツ処理統合機能"""
import logging
import os
from datetime import datetime

from ..ai.exceptions import SummaryGenerationError
from ..ai.summarizer import generate_summary
from ..core import ContentProcessingError
from .audio_preprocessor import AudioTextPreprocessor
from .extractor import ContentExtractor
from .schemas import ContentData, ProcessedContent

logger = logging.getLogger(__name__)


class ContentProcessor:
    """コンテンツ処理統合クラス"""

    def __init__(self, data_dir: str = "data"):
        """
        Args:
            data_dir: ファイル保存ディレクトリ
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        # rawディレクトリも作成
        os.makedirs(os.path.join(self.data_dir, "raw"), exist_ok=True)

    def process_url(
        self,
        url: str,
        fallback_title: str = "",
        article_id: int | None = None,
        generate_summary_flag: bool = True,
    ) -> ProcessedContent:
        """URLを処理して完全なコンテンツデータを生成"""
        try:
            # 1. コンテンツ取得
            content_data = ContentExtractor.fetch_content(url)

            # 2. タイトル抽出
            title_result = ContentExtractor.extract_title(content_data, fallback_title)
            final_title = title_result.title if title_result.success else fallback_title

            # 3. テキスト抽出
            text_result = ContentExtractor.extract_text(content_data)
            extracted_text = text_result.text if text_result.success else ""

            # 4. 要約生成
            summary = ""
            if generate_summary_flag and extracted_text.strip():
                try:
                    summary = generate_summary(extracted_text)
                    logger.info(f"Summary generated successfully for {url}")
                except SummaryGenerationError as e:
                    logger.warning(f"Summary generation failed for {url}: {e}")
                    summary = ""

            # 5. ファイル保存
            file_path = None
            if article_id is not None:
                file_path = self._save_content(content_data, article_id)
                # 抽出したテキストも保存
                if extracted_text:
                    self._save_extracted_text(extracted_text, article_id)

            from pydantic import HttpUrl

            return ProcessedContent(
                url=HttpUrl(url),
                title=final_title,
                extracted_text=extracted_text,
                summary=summary,
                extension=content_data.extension,
                file_path=file_path,
            )

        except Exception as e:
            if isinstance(e, ContentProcessingError):
                raise
            raise ContentProcessingError(
                f"Content processing failed for {url}: {e}",
                error_code="PROCESSING_FAILED",
                details={"url": url},
            ) from e

    def _save_content(self, content_data: ContentData, article_id: int) -> str:
        """コンテンツをファイルに保存"""
        try:
            # ファイル名生成: {日付}_{記事ID}.{拡張子}
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"{date_str}_{article_id}.{content_data.extension}"
            file_path = os.path.join(self.data_dir, filename)

            with open(file_path, "wb") as f:
                f.write(content_data.content)

            logger.info(f"Content saved to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save content for article {article_id}: {e}")
            raise ContentProcessingError(
                f"Failed to save content: {e}",
                error_code="SAVE_FAILED",
                details={"article_id": article_id, "filename": filename},
            ) from e

    def _save_extracted_text(self, text: str, article_id: int) -> str:
        """抽出したテキストをファイルに保存"""
        try:
            # ファイル名生成: article_{記事ID}.txt
            filename = f"article_{article_id}.txt"
            file_path = os.path.join(self.data_dir, "raw", filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

            logger.info(f"Extracted text saved to {file_path}")

            # 音声用の前処理済みテキストも保存
            self._save_audio_preprocessed_text(text, article_id)

            return file_path

        except Exception as e:
            logger.error(f"Failed to save extracted text for article {article_id}: {e}")
            # エラーが発生してもメイン処理は継続（ログに記録のみ）
            return ""

    def _save_audio_preprocessed_text(self, text: str, article_id: int) -> str:
        """音声読み上げ用に前処理したテキストを保存"""
        try:
            # 音声用テキストの前処理
            preprocessed_text = AudioTextPreprocessor.preprocess_for_audio(text)

            # ファイル名生成: article_{記事ID}_audio.txt
            filename = f"article_{article_id}_audio.txt"
            file_path = os.path.join(self.data_dir, "raw", filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(preprocessed_text)

            logger.info(f"Audio preprocessed text saved to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save audio preprocessed text for article {article_id}: {e}")
            # エラーが発生してもメイン処理は継続（ログに記録のみ）
            return ""

    def extract_title_only(self, url: str, fallback_title: str = "") -> str:
        """タイトルのみを抽出（軽量版）"""
        try:
            content_data = ContentExtractor.fetch_content(url)
            title_result = ContentExtractor.extract_title(content_data, fallback_title)
            return title_result.title if title_result.success else fallback_title
        except Exception as e:
            logger.warning(f"Title extraction failed for {url}: {e}")
            return fallback_title

    def extract_text_only(self, url: str) -> str:
        """テキストのみを抽出（軽量版）"""
        try:
            content_data = ContentExtractor.fetch_content(url)
            text_result = ContentExtractor.extract_text(content_data)
            return text_result.text if text_result.success else ""
        except Exception as e:
            logger.warning(f"Text extraction failed for {url}: {e}")
            return ""

    def generate_summary_from_text(self, text: str) -> str:
        """テキストから要約を生成"""
        try:
            if not text.strip():
                return ""
            return generate_summary(text)
        except SummaryGenerationError as e:
            logger.warning(f"Summary generation failed: {e}")
            return ""
