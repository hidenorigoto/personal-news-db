"""コンテンツ抽出機能"""
import contextlib
import io
import logging
from urllib.parse import urlparse

import pypdf
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, Field

from ..core import ContentProcessingError, settings
from .schemas import ContentData, TextExtractionResult, TitleExtractionResult

logger = logging.getLogger(__name__)


class ArticleContent(BaseModel):
    """記事コンテンツの構造化モデル"""
    title: str = Field(description="記事のタイトル")
    main_text: str = Field(description="記事の本文（ナビゲーション、広告、フッターなどを除く）")
    is_article: bool = Field(description="これが記事コンテンツかどうか")
    confidence: float = Field(description="抽出の信頼度（0.0-1.0）")


class ContentExtractor:
    """コンテンツ抽出クラス"""

    @staticmethod
    def fetch_content(url: str, timeout: int = 10) -> ContentData:
        """URLからコンテンツを取得"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            # Content-Typeからパラメータ部分を除去してクリーンアップ
            clean_content_type = content_type.split(";")[0].strip() if content_type else ""
            extension = ContentExtractor._get_extension_from_content_type(content_type, url)

            from pydantic import HttpUrl

            return ContentData(
                url=HttpUrl(url),
                content=response.content,
                content_type=clean_content_type,
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
                result = ContentExtractor._extract_title_from_html(content_data.content)
                if not result.success and fallback_title:
                    return TitleExtractionResult(
                        title=fallback_title, success=True, method="fallback"
                    )
                return result
            elif content_data.extension == "pdf":
                result = ContentExtractor._extract_title_from_pdf(content_data.content)
                if not result.success and fallback_title:
                    return TitleExtractionResult(
                        title=fallback_title, success=True, method="fallback"
                    )
                return result
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
        """HTMLからテキストを抽出（OpenAI API使用）"""
        try:
            logger.info("Starting HTML text extraction with AI")
            # OpenAI APIを使用した高度な抽出を試みる
            result = ContentExtractor._extract_text_from_html_with_ai(content)
            if result.success:
                logger.info("AI extraction successful")
                return result

            # フォールバック: 従来の方法
            logger.info("AI extraction failed, falling back to traditional extraction method")
            return ContentExtractor._extract_text_from_html_traditional(content)

        except Exception as e:
            logger.warning(f"HTML text extraction failed: {e}")
            return ContentExtractor._extract_text_from_html_traditional(content)

    @staticmethod
    def _extract_text_from_html_traditional(content: bytes) -> TextExtractionResult:
        """HTMLからテキストを抽出（従来の方法）"""
        logger.info("Using traditional extraction method")
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
            logger.warning(f"Traditional HTML text extraction failed: {e}")
            return TextExtractionResult(text="", success=False, word_count=0)

    @staticmethod
    def _extract_text_from_html_with_ai(content: bytes) -> TextExtractionResult:
        """HTMLからテキストを抽出（OpenAI API使用）"""
        try:
            # OpenAI APIキーの確認
            logger.info(f"Checking OpenAI API key: {'configured' if settings.openai_api_key else 'not configured'}")
            if not settings.openai_api_key:
                logger.info("OpenAI API key not configured, skipping AI extraction")
                return TextExtractionResult(text="", success=False, word_count=0)

            soup = BeautifulSoup(content, "html.parser")

            # HTMLを簡略化
            simplified_html = ContentExtractor._simplify_html(soup)

            # 長すぎる場合は切り詰める（約2000トークン相当、より保守的に）
            if len(simplified_html) > 8000:
                simplified_html = simplified_html[:8000] + "\n...（以下省略）"
                logger.info(f"HTML truncated from {len(ContentExtractor._simplify_html(soup))} to 8000 chars")

            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)

            # 構造化出力を使用
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """あなたはWebページから記事の本文を抽出する専門家です。
以下のHTMLから記事の本文のみを抽出してください：
- ナビゲーション、メニュー、サイドバー、フッターは除外
- 広告、関連記事リンク、SNSシェアボタンは除外
- 記事のタイトルと本文のみを抽出
- 著作権表示やサイト情報は除外
- 抽出した本文は最大5000文字まで"""
                    },
                    {
                        "role": "user",
                        "content": simplified_html
                    }
                ],
                response_format=ArticleContent,
                temperature=0,
                max_tokens=4000  # レスポンスの最大トークン数を制限
            )

            article = completion.choices[0].message.parsed

            if article and article.is_article and article.confidence > 0.7:
                # タイトルと本文を結合
                full_text = f"{article.title}\n\n{article.main_text}" if article.title else article.main_text
                logger.info(f"AI extraction successful with confidence: {article.confidence}")
                return TextExtractionResult(
                    text=full_text,
                    success=True,
                    word_count=len(full_text)
                )
            else:
                logger.info(f"AI extraction confidence too low: {article.confidence if article else 0}")
                return TextExtractionResult(text="", success=False, word_count=0)

        except Exception as e:
            logger.warning(f"AI text extraction failed: {e}")
            return TextExtractionResult(text="", success=False, word_count=0)

    @staticmethod
    def _simplify_html(soup: BeautifulSoup) -> str:
        """HTMLを簡略化して構造を保持"""
        # 複製を作成（元のsoupを変更しない）
        soup_copy = BeautifulSoup(str(soup), "html.parser")

        # 不要な要素を積極的に削除
        tags_to_remove = [
            'script', 'style', 'link', 'meta', 'noscript', 'iframe',
            'header', 'footer', 'aside', 'nav',  # ナビゲーション要素
            'form', 'button', 'input',  # フォーム要素
            'svg', 'img', 'video', 'audio',  # メディア要素
            'advertisement', 'ads'  # 広告関連
        ]
        for tag in soup_copy(tags_to_remove):
            tag.decompose()

        # 広告やナビゲーションを示すクラスやIDを持つ要素を削除
        nav_patterns = ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'banner', 'social', 'share', 'comment']
        elements_to_remove = []
        for element in soup_copy.find_all(True):
            if isinstance(element, Tag):
                # クラスやIDに特定のパターンが含まれる場合は削除対象に追加
                try:
                    class_list = element.get('class')
                    if isinstance(class_list, list):
                        class_str = ' '.join(class_list)
                    else:
                        class_str = str(class_list) if class_list else ''
                    id_str = str(element.get('id') or '')
                    for pattern in nav_patterns:
                        if pattern in class_str.lower() or pattern in id_str.lower():
                            elements_to_remove.append(element)
                            break
                except AttributeError:
                    continue

        # 別のループで削除（イテレーション中の削除を避ける）
        for element in elements_to_remove:
            with contextlib.suppress(Exception):
                element.decompose()

        # 属性を最小限に削減
        for element in soup_copy.find_all(True):
            if isinstance(element, Tag):
                # 記事識別に有用な最小限の属性のみ保持
                attrs_to_keep: dict[str, str | list[str]] = {}
                if element.name in ['article', 'main', 'section', 'div'] and element.get('class'):
                    class_list = element.get('class')
                    if isinstance(class_list, list):
                        # 記事に関連しそうなクラスのみ保持
                        relevant_classes = [c for c in class_list if any(
                            keyword in c.lower() for keyword in ['content', 'article', 'main', 'body', 'text', 'post']
                        )]
                        if relevant_classes:
                            attrs_to_keep['class'] = ' '.join(relevant_classes[:2])  # 最大2つまで
                element.attrs = attrs_to_keep  # type: ignore[assignment]

        # 空の要素を削除
        for element in soup_copy.find_all(True):
            if isinstance(element, Tag) and not element.get_text(strip=True) and not element.find_all(True):
                element.decompose()

        # テキストのみを保持する簡略化されたHTML
        simplified = str(soup_copy)

        # さらに簡略化：連続する空白や改行を削減
        import re
        simplified = re.sub(r'\s+', ' ', simplified)
        simplified = re.sub(r'>\s+<', '><', simplified)

        return simplified

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
