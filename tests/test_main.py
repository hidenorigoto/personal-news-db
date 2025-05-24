import os
import shutil
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from news_assistant import database, models
from news_assistant.main import app

TEST_DATA_DIR = "data_test"
TEST_DB_FILE = "test_news.db"

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    # テスト用DBをリセット
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    os.environ["NEWS_ASSISTANT_DB_URL"] = f"sqlite:///{TEST_DB_FILE}"
    models.Base.metadata.create_all(bind=database.engine)
    yield


def setup_module(module: Any) -> None:
    # テスト用dataディレクトリを作成
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    # appのDATA_DIRをテスト用に切り替え
    app.state.DATA_DIR = TEST_DATA_DIR


def teardown_module(module: Any) -> None:
    # テスト用dataディレクトリを削除
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)


def test_create_article(monkeypatch: Any) -> None:
    # requests.getをモック
    class MockResponse:
        def __init__(self) -> None:
            self.content = b"<html>test</html>"
            self.headers = {"Content-Type": "text/html"}
        def raise_for_status(self) -> None:
            pass
    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    data = {"url": "http://example.com/unique-test-1", "title": "Example"}
    try:
        response = client.post("/api/articles/", json=data)
        if response.status_code != 200:
            print("RESPONSE:", response.status_code, response.text)
        assert response.status_code == 200
        result = response.json()
        assert result["url"] == data["url"]
        assert result["title"] == data["title"]
        # ファイルが保存されているか確認
        files = os.listdir(TEST_DATA_DIR)
        assert any(f.endswith(".html") for f in files)
    finally:
        from news_assistant.database import SessionLocal
        with SessionLocal() as db:
            db.execute(
                text("DELETE FROM articles WHERE url = :url"), {"url": data["url"]}
            )
            db.commit()


def test_create_article_html_title(monkeypatch: Any) -> None:
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
    try:
        response = client.post("/api/articles/", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "AutoTitle"
        files = os.listdir(TEST_DATA_DIR)
        assert any(f.endswith(".html") for f in files)
    finally:
        from news_assistant.database import SessionLocal
        with SessionLocal() as db:
            db.execute(
                text("DELETE FROM articles WHERE url = :url"), {"url": data["url"]}
            )
            db.commit()


def test_create_article_pdf_title(monkeypatch: Any) -> None:
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
    try:
        response = client.post("/api/articles/", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "PDF Auto Title"
        files = os.listdir(TEST_DATA_DIR)
        assert any(f.endswith(".pdf") for f in files)
    finally:
        from news_assistant.database import SessionLocal
        with SessionLocal() as db:
            db.execute(
                text("DELETE FROM articles WHERE url = :url"), {"url": data["url"]}
            )
            db.commit()


def test_create_article_fallback_title(monkeypatch: Any) -> None:
    # タイトルが抽出できない場合はリクエストボディのtitleを使う
    class MockResponse:
        def __init__(self) -> None:
            self.content = b"no title here"
            self.headers = {"Content-Type": "text/plain"}
        def raise_for_status(self) -> None:
            pass
    monkeypatch.setattr("requests.get", lambda url, timeout=10: MockResponse())

    data = {"url": "http://example.com/notitle-fallback", "title": "FallbackTitle"}
    try:
        response = client.post("/api/articles/", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "FallbackTitle"
        files = os.listdir(TEST_DATA_DIR)
        assert any(f.endswith(".txt") for f in files)
    finally:
        from news_assistant.database import SessionLocal
        with SessionLocal() as db:
            db.execute(
                text("DELETE FROM articles WHERE url = :url"), {"url": data["url"]}
            )
            db.commit()


def test_get_articles() -> None:
    response = client.get("/api/articles/")
    assert response.status_code == 200
    result = response.json()
    assert "articles" in result
    assert isinstance(result["articles"], list)


def test_get_article(monkeypatch: pytest.MonkeyPatch) -> None:
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
    if response.status_code != 200:
        print("RESPONSE:", response.status_code, response.text)
    assert response.status_code == 200
    result_post = response.json()
    article_id = result_post["id"]
    # 1件目の記事を取得
    response = client.get(f"/api/articles/{article_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == article_id
    assert "url" in result
    assert "title" in result
