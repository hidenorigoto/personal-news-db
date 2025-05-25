"""コンテンツ抽出機能"""
import io
import logging
from urllib.parse import urlparse

import pypdf
import requests
from bs4 import BeautifulSoup

from ..core import ContentProcessingError
from .schemas import ContentData, TextExtractionResult, TitleExtractionResult

logger = logging.getLogger(__name__)


class ContentExtractor:
    """コンテンツ抽出クラス"""

    @staticmethod
    def fetch_content(url: str, timeout: int = 10) -> ContentData:
        """URLからコンテンツを取得"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            extension = ContentExtractor._get_extension_from_content_type(content_type, url)

            from pydantic import HttpUrl

            return ContentData(
                url=HttpUrl(url),
                content=response.content,
                content_type=content_type,
                extension=extension,
            )
        except Exception as e:
            raise ContentProcessingError(
                f"Failed to fetch content from {url}: {e}",
                error_code="FETCH_FAILED",
                details={"url": url},
            ) from e

    @staticmethod
    def _get_extension_from_content_type(content_type: str, url: str = "") -> str:
        """Content-TypeとURLから拡張子を推定"""
        mime = content_type.split(";")[0].strip().lower() if content_type else ""
        mime_map = {
            "text/html": "html",
            "application/xhtml+xml": "html",
            "application/json": "json",
            "application/xml": "xml",
            "text/xml": "xml",
            "text/plain": "txt",
            "application/pdf": "pdf",
        }

        if mime in mime_map:
            return mime_map[mime]

        if not mime:
            # URLから拡張子を抽出
            path = urlparse(url).path
            ext = path.split(".")[-1].lower() if "." in path else ""
            allowed = {"html", "htm", "pdf", "txt", "json", "xml"}
            if ext in allowed:
                return "html" if ext == "htm" else ext
            return "html"

        if "/" in mime:
            return mime.split("/")[-1]
        return "bin"

    @staticmethod
    def extract_title(content_data: ContentData, fallback_title: str = "") -> TitleExtractionResult:
        """コンテンツからタイトルを抽出"""
        try:
            if content_data.extension == "html":
                return ContentExtractor._extract_title_from_html(content_data.content)
            elif content_data.extension == "pdf":
                return ContentExtractor._extract_title_from_pdf(content_data.content)
            else:
                return TitleExtractionResult(
                    title=fallback_title, success=bool(fallback_title), method="fallback"
                )
        except Exception as e:
            logger.warning(f"Title extraction failed: {e}")
            return TitleExtractionResult(
                title=fallback_title, success=bool(fallback_title), method="fallback_error"
            )

    @staticmethod
    def _extract_title_from_html(content: bytes) -> TitleExtractionResult:
        """HTMLからタイトルを抽出"""
        try:
            soup = BeautifulSoup(content, "html.parser")
            title_tag = soup.find("title")
            if title_tag and title_tag.text:
                title = title_tag.text.strip()
                return TitleExtractionResult(title=title, success=True, method="html_tag")
        except Exception as e:
            logger.warning(f"HTML title extraction failed: {e}")

        return TitleExtractionResult(title="", success=False, method="html_tag_failed")

    @staticmethod
    def _extract_title_from_pdf(content: bytes) -> TitleExtractionResult:
        """PDFからタイトルを抽出"""
        try:
            with io.BytesIO(content) as pdf_io:
                reader = pypdf.PdfReader(pdf_io)
                if reader.metadata and reader.metadata.title:
                    title = str(reader.metadata.title).strip()
                    return TitleExtractionResult(title=title, success=True, method="pdf_metadata")
        except Exception as e:
            logger.warning(f"PDF title extraction failed: {e}")

        return TitleExtractionResult(title="", success=False, method="pdf_metadata_failed")

    @staticmethod
    def extract_text(content_data: ContentData) -> TextExtractionResult:
        """コンテンツからテキストを抽出"""
        try:
            if content_data.extension == "html":
                return ContentExtractor._extract_text_from_html(content_data.content)
            elif content_data.extension == "pdf":
                return ContentExtractor._extract_text_from_pdf(content_data.content)
            elif content_data.extension == "txt":
                return ContentExtractor._extract_text_from_txt(content_data.content)
            else:
                return TextExtractionResult(text="", success=False, word_count=0)
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")
            return TextExtractionResult(text="", success=False, word_count=0)

    @staticmethod
    def _extract_text_from_html(content: bytes) -> TextExtractionResult:
        """HTMLからテキストを抽出"""
        try:
            soup = BeautifulSoup(content, "html.parser")
            # <body>タグ優先、なければ全テキスト
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            return TextExtractionResult(text=text, success=True, word_count=len(text))
        except Exception as e:
            logger.warning(f"HTML text extraction failed: {e}")
            return TextExtractionResult(text="", success=False, word_count=0)

    @staticmethod
    def _extract_text_from_pdf(content: bytes) -> TextExtractionResult:
        """PDFからテキストを抽出"""
        try:
            with io.BytesIO(content) as pdf_io:
                reader = pypdf.PdfReader(pdf_io)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                text = "\n".join(text_parts)

                return TextExtractionResult(text=text, success=True, word_count=len(text))
        except Exception as e:
            logger.warning(f"PDF text extraction failed: {e}")
            return TextExtractionResult(text="", success=False, word_count=0)

    @staticmethod
    def _extract_text_from_txt(content: bytes) -> TextExtractionResult:
        """テキストファイルからテキストを抽出"""
        try:
            # UTF-8でデコード、失敗したらlatin-1を試行
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")

            return TextExtractionResult(text=text, success=True, word_count=len(text))
        except Exception as e:
            logger.warning(f"Text file extraction failed: {e}")
            return TextExtractionResult(text="", success=False, word_count=0)
