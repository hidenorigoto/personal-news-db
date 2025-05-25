import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient


def test_create_article(client: TestClient, monkeypatch: Any) -> None:
    # requests.getをモック
    class MockResponse:
        def __init__(self) -> None:
            self.content = b"<html>test</html>"
            self.headers = {"Content-Type": "text/html"}
        def raise_for_status(self) -> None:
            pass
    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    # openai要約APIをモック
    def mock_summary(content: str) -> str:
        return "これは要約です。"
    monkeypatch.setattr("news_assistant.content.processor.generate_summary", mock_summary)

    data = {"url": "http://example.com/unique-test-1", "title": "Example"}
    response = client.post("/api/articles/", json=data)
    if response.status_code != 201:
        print("RESPONSE:", response.status_code, response.text)
    assert response.status_code == 201
    result = response.json()
    assert result["url"] == data["url"]
    assert result["title"] == data["title"]
    assert isinstance(result["summary"], str)
    expected_summary = "これは要約です。"
    assert result["summary"] == expected_summary


def test_create_article_html_title(client: TestClient, monkeypatch: Any) -> None:
    # HTMLの<title>からタイトルを抽出
    html = b"""
    <html><head><title>AutoTitle</title></head><body>test</body></html>
    """
    class MockResponse:
        def __init__(self) -> None:
            self.content = html
            self.headers = {"Content-Type": "text/html"}
        def raise_for_status(self) -> None:
            pass
    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    data = {"url": "http://example.com/auto-title-html", "title": "ShouldNotUseThis"}
    response = client.post("/api/articles/", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "AutoTitle"


def test_create_article_pdf_title(client: TestClient, monkeypatch: Any) -> None:
    # PDFのメタデータからタイトルを抽出
    import io

    from pypdf import PdfWriter
    pdf_io = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": "PDF Auto Title"})
    writer.write(pdf_io)
    pdf_bytes = pdf_io.getvalue()
    class MockResponse:
        def __init__(self) -> None:
            self.content = pdf_bytes
            self.headers = {"Content-Type": "application/pdf"}
        def raise_for_status(self) -> None:
            pass
    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    data = {
        "url": "http://example.com/sample-pdf-title.pdf",
        "title": "ShouldNotUseThis",
    }
    response = client.post("/api/articles/", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "PDF Auto Title"


def test_create_article_fallback_title(client: TestClient, monkeypatch: Any) -> None:
    # タイトルが抽出できない場合はリクエストボディのtitleを使う
    class MockResponse:
        def __init__(self) -> None:
            self.content = b"no title here"
            self.headers = {"Content-Type": "text/plain"}
        def raise_for_status(self) -> None:
            pass
    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    data = {"url": "http://example.com/notitle-fallback", "title": "FallbackTitle"}
    response = client.post("/api/articles/", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "FallbackTitle"


def test_get_articles(client: TestClient) -> None:
    response = client.get("/api/articles/")
    assert response.status_code == 200
    result = response.json()
    assert "articles" in result
    assert isinstance(result["articles"], list)


def test_get_article(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # 外部リクエストをモック
    class MockResponse:
        def __init__(self) -> None:
            self.content = b"<html>get article</html>"
            self.headers = {"Content-Type": "text/html"}
        def raise_for_status(self) -> None:
            pass
    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())
    # まず記事を1件登録（ユニークなURLを生成）
    unique_url = f"http://example.com/get-article-{uuid.uuid4()}"
    data = {"url": unique_url, "title": "GetTest"}
    response = client.post("/api/articles/", json=data)
    if response.status_code != 201:
        print("RESPONSE:", response.status_code, response.text)
    assert response.status_code == 201
    result_post = response.json()
    article_id = result_post["id"]
    # 1件目の記事を取得
    response = client.get(f"/api/articles/{article_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == article_id
    assert "url" in result
    assert "title" in result
