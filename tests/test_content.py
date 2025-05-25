"""コンテンツ処理モジュールのテスト"""
import io
import pytest
from unittest.mock import patch, MagicMock

from news_assistant.content import ContentExtractor, ContentProcessor
from news_assistant.content.schemas import ContentData, TitleExtractionResult, TextExtractionResult
from news_assistant.core import ContentProcessingError


class TestContentExtractor:
    """ContentExtractorのテスト"""

    def test_get_extension_from_content_type_html(self):
        """HTML Content-Typeの拡張子判定テスト"""
        result = ContentExtractor._get_extension_from_content_type("text/html")
        assert result == "html"

    def test_get_extension_from_content_type_pdf(self):
        """PDF Content-Typeの拡張子判定テスト"""
        result = ContentExtractor._get_extension_from_content_type("application/pdf")
        assert result == "pdf"

    def test_get_extension_from_url(self):
        """URLからの拡張子判定テスト"""
        result = ContentExtractor._get_extension_from_content_type("", "http://example.com/test.pdf")
        assert result == "pdf"

    def test_extract_title_from_html_success(self):
        """HTMLタイトル抽出成功テスト"""
        html_content = b"<html><head><title>Test Title</title></head><body>content</body></html>"
        result = ContentExtractor._extract_title_from_html(html_content)
        
        assert result.success is True
        assert result.title == "Test Title"
        assert result.method == "html_tag"

    def test_extract_title_from_html_no_title(self):
        """HTMLタイトル抽出失敗テスト"""
        html_content = b"<html><head></head><body>content</body></html>"
        result = ContentExtractor._extract_title_from_html(html_content)
        
        assert result.success is False
        assert result.title == ""

    def test_extract_text_from_html(self):
        """HTMLテキスト抽出テスト"""
        html_content = b"<html><body><p>Test content</p><p>More content</p></body></html>"
        result = ContentExtractor._extract_text_from_html(html_content)
        
        assert result.success is True
        assert "Test content" in result.text
        assert "More content" in result.text
        assert result.word_count > 0

    def test_extract_text_from_txt(self):
        """テキストファイル抽出テスト"""
        txt_content = b"This is plain text content."
        result = ContentExtractor._extract_text_from_txt(txt_content)
        
        assert result.success is True
        assert result.text == "This is plain text content."
        assert result.word_count == len("This is plain text content.")

    @patch('requests.get')
    def test_fetch_content_success(self, mock_get):
        """コンテンツ取得成功テスト"""
        # モックレスポンス設定
        mock_response = MagicMock()
        mock_response.content = b"<html>test</html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = ContentExtractor.fetch_content("http://example.com/test")
        
        assert str(result.url) == "http://example.com/test"
        assert result.content == b"<html>test</html>"
        assert result.content_type == "text/html"
        assert result.extension == "html"

    @patch('requests.get')
    def test_fetch_content_failure(self, mock_get):
        """コンテンツ取得失敗テスト"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(ContentProcessingError) as exc_info:
            ContentExtractor.fetch_content("http://example.com/test")
        
        assert exc_info.value.error_code == "FETCH_FAILED"


class TestContentProcessor:
    """ContentProcessorのテスト"""

    def test_init(self, tmp_path):
        """初期化テスト"""
        processor = ContentProcessor(str(tmp_path))
        assert processor.data_dir == str(tmp_path)
        assert tmp_path.exists()

    @patch('news_assistant.content.extractor.ContentExtractor.fetch_content')
    @patch('news_assistant.content.extractor.ContentExtractor.extract_title')
    @patch('news_assistant.content.extractor.ContentExtractor.extract_text')
    @patch('news_assistant.content.processor.generate_summary')
    def test_process_url_success(self, mock_summary, mock_extract_text, mock_extract_title, mock_fetch, tmp_path):
        """URL処理成功テスト"""
        # モック設定
        mock_content_data = ContentData(
            url="http://example.com/test",
            content=b"<html>test</html>",
            content_type="text/html",
            extension="html"
        )
        mock_fetch.return_value = mock_content_data
        
        mock_extract_title.return_value = TitleExtractionResult(
            title="Extracted Title",
            success=True,
            method="html_tag"
        )
        
        mock_extract_text.return_value = TextExtractionResult(
            text="Extracted text content",
            success=True,
            word_count=20
        )
        
        mock_summary.return_value = "Generated summary"
        
        # テスト実行
        processor = ContentProcessor(str(tmp_path))
        result = processor.process_url(
            url="http://example.com/test",
            fallback_title="Fallback Title",
            article_id=1
        )
        
        # 検証
        assert str(result.url) == "http://example.com/test"
        assert result.title == "Extracted Title"
        assert result.extracted_text == "Extracted text content"
        assert result.summary == "Generated summary"
        assert result.extension == "html"
        assert result.file_path is not None

    @patch('news_assistant.content.extractor.ContentExtractor.fetch_content')
    def test_extract_title_only(self, mock_fetch):
        """タイトルのみ抽出テスト"""
        mock_content_data = ContentData(
            url="http://example.com/test",
            content=b"<html><title>Test Title</title></html>",
            content_type="text/html",
            extension="html"
        )
        mock_fetch.return_value = mock_content_data
        
        processor = ContentProcessor()
        result = processor.extract_title_only("http://example.com/test", "Fallback")
        
        assert result == "Test Title"

    @patch('news_assistant.content.processor.generate_summary')
    def test_generate_summary_from_text(self, mock_summary):
        """テキストから要約生成テスト"""
        mock_summary.return_value = "Generated summary"
        
        processor = ContentProcessor()
        result = processor.generate_summary_from_text("Some long text content")
        
        assert result == "Generated summary"
        mock_summary.assert_called_once_with("Some long text content")

    def test_generate_summary_from_empty_text(self):
        """空テキストから要約生成テスト"""
        processor = ContentProcessor()
        result = processor.generate_summary_from_text("")
        
        assert result == "" 