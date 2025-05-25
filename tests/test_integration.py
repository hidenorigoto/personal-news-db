import uuid
from typing import Any

from fastapi.testclient import TestClient


def test_full_article_workflow_integration(client: TestClient, monkeypatch: Any) -> None:
    """記事の完全なワークフロー統合テスト

    URL投稿 → コンテンツ取得 → タイトル抽出 → 要約生成 → 保存 → 取得の全フローをテスト
    """
    # requests.getをモック
    class MockResponse:
        def __init__(self) -> None:
            self.content = b"<html><head><title>Integration Test Article</title></head><body><p>This is a comprehensive test content for integration testing.</p></body></html>"
            self.headers = {"Content-Type": "text/html"}

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    # openai要約APIをモック
    def mock_summary(content: str) -> str:
        return "統合テスト用の要約: この記事は統合テストの包括的なコンテンツです。"

    monkeypatch.setattr("news_assistant.content.processor.generate_summary", mock_summary)

    # 1. 記事作成（タイトル自動抽出）
    unique_url = f"http://example.com/integration-test-{uuid.uuid4()}"
    data = {"url": unique_url, "title": "ShouldBeOverridden"}

    response = client.post("/api/articles/", json=data)
    assert response.status_code == 201

    result = response.json()
    article_id = result["id"]

    # タイトルが自動抽出されていることを確認
    assert result["title"] == "Integration Test Article"
    assert result["url"] == unique_url
    assert "統合テスト用の要約" in result["summary"]

    # 2. 作成した記事を取得
    get_response = client.get(f"/api/articles/{article_id}")
    assert get_response.status_code == 200

    get_result = get_response.json()
    assert get_result["id"] == article_id
    assert get_result["title"] == "Integration Test Article"

    # 3. 記事一覧に含まれていることを確認
    list_response = client.get("/api/articles/")
    assert list_response.status_code == 200

    list_result = list_response.json()
    article_found = any(article["id"] == article_id for article in list_result.get("articles", []))
    assert article_found, "作成した記事が一覧に含まれていません"


def test_content_type_handling_integration(client: TestClient, monkeypatch: Any) -> None:
    """異なるコンテンツタイプの統合処理テスト

    HTML、PDF、プレーンテキストの処理を統合的にテスト
    """

    # HTMLコンテンツのテスト
    class MockHtmlResponse:
        def __init__(self) -> None:
            self.content = b"<html><head><title>HTML Content</title></head><body>HTML body content</body></html>"
            self.headers = {"Content-Type": "text/html"}

        def raise_for_status(self) -> None:
            pass

    # PDFコンテンツのテスト
    import io

    from pypdf import PdfWriter

    pdf_io = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": "PDF Integration Test"})
    writer.write(pdf_io)
    pdf_bytes = pdf_io.getvalue()

    class MockPdfResponse:
        def __init__(self) -> None:
            self.content = pdf_bytes
            self.headers = {"Content-Type": "application/pdf"}

        def raise_for_status(self) -> None:
            pass

    # プレーンテキストのテスト
    class MockTextResponse:
        def __init__(self) -> None:
            self.content = b"Plain text content for integration testing"
            self.headers = {"Content-Type": "text/plain"}

        def raise_for_status(self) -> None:
            pass

    test_cases = [
        ("html", MockHtmlResponse, "HTML Content"),
        ("pdf", MockPdfResponse, "PDF Integration Test"),
        ("txt", MockTextResponse, "Fallback Title"),  # プレーンテキストはフォールバック
    ]

    for content_type, mock_class, expected_title in test_cases:
        monkeypatch.setattr("requests.get", lambda url, timeout=10, cls=mock_class: cls())

        unique_url = f"http://example.com/content-{content_type}-{uuid.uuid4()}"
        data = {"url": unique_url, "title": "Fallback Title"}

        response = client.post("/api/articles/", json=data)
        assert response.status_code == 201

        result = response.json()
        assert result["title"] == expected_title
        assert result["url"] == unique_url


def test_error_handling_integration(client: TestClient, monkeypatch: Any) -> None:
    """エラーハンドリングの統合テスト

    外部リクエスト失敗、重複URL、不正なデータなどのエラーケースを統合的にテスト
    """

    # 1. 正常な記事を作成
    class MockResponse:
        def __init__(self) -> None:
            self.content = b"<html>normal content</html>"
            self.headers = {"Content-Type": "text/html"}

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    duplicate_url = f"http://example.com/duplicate-{uuid.uuid4()}"
    data = {"url": duplicate_url, "title": "Original Article"}

    response = client.post("/api/articles/", json=data)
    assert response.status_code == 201

    # 2. 同じURLで重複作成を試行
    duplicate_response = client.post("/api/articles/", json=data)
    assert duplicate_response.status_code == 409  # Conflict

    # 3. 存在しない記事の取得
    not_found_response = client.get("/api/articles/99999")
    assert not_found_response.status_code == 404

    # 4. 不正なURLでの記事作成
    invalid_data = {"url": "not-a-valid-url", "title": "Invalid URL Test"}
    invalid_response = client.post("/api/articles/", json=invalid_data)
    assert invalid_response.status_code == 422  # Validation Error


def test_api_health_and_basic_endpoints(client: TestClient) -> None:
    """API基本エンドポイントとヘルスチェックの統合テスト"""

    # ルートエンドポイント
    root_response = client.get("/")
    assert root_response.status_code == 200
    root_data = root_response.json()
    assert "message" in root_data
    assert "News Assistant" in root_data["message"]

    # ヘルスチェック
    health_response = client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["status"] == "healthy"
    assert "database" in health_data
    assert health_data["database"] == "healthy"
    assert "timestamp" in health_data
    assert "version" in health_data
