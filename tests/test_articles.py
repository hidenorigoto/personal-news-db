"""記事モジュールのテスト"""
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_create_article(client: TestClient) -> None:
    """記事作成テスト"""
    article_data = {"url": "https://example.com/test-article", "title": "Test Article"}

    with patch("news_assistant.content.processor.ContentProcessor.process_url") as mock_process:
        from pydantic import HttpUrl

        from news_assistant.content.schemas import ProcessedContent

        mock_process.return_value = ProcessedContent(
            url=HttpUrl("https://example.com/test-article"),
            title="Processed Title",
            extracted_text="Extracted content",
            summary="Generated summary",
            extension="html",
            file_path=None,
        )

        response = client.post("/api/articles/", json=article_data)

    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com/test-article"
    assert data["title"] == "Processed Title"


def test_create_article_duplicate_url(client: TestClient) -> None:
    """重複URL記事作成テスト"""
    article_data = {"url": "https://example.com/duplicate", "title": "Duplicate Article"}

    # 最初の記事作成
    with patch("news_assistant.content.processor.ContentProcessor.process_url"):
        client.post("/api/articles/", json=article_data)

    # 重複記事作成試行
    with patch("news_assistant.content.processor.ContentProcessor.process_url"):
        response = client.post("/api/articles/", json=article_data)

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_get_articles_empty(client: TestClient) -> None:
    """空の記事一覧取得テスト"""
    response = client.get("/api/articles/")
    assert response.status_code == 200
    data = response.json()
    assert data["articles"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 100


def test_get_articles_with_data(client: TestClient) -> None:
    """記事データありの一覧取得テスト"""
    # テスト記事作成
    article_data = {"url": "https://example.com/test1", "title": "Test Article 1"}

    with patch("news_assistant.content.processor.ContentProcessor.process_url") as mock_process:
        from pydantic import HttpUrl

        from news_assistant.content.schemas import ProcessedContent

        mock_process.return_value = ProcessedContent(
            url=HttpUrl("https://example.com/test1"),
            title="Test Article 1",
            extracted_text="Extracted content",
            summary="Generated summary",
            extension="html",
            file_path=None,
        )

        client.post("/api/articles/", json=article_data)

    response = client.get("/api/articles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["articles"]) == 1
    assert data["total"] == 1
    assert data["articles"][0]["title"] == "Test Article 1"


def test_get_article_by_id(client: TestClient) -> None:
    """ID指定記事取得テスト"""
    # テスト記事作成
    article_data = {"url": "https://example.com/test-get", "title": "Test Get Article"}

    with patch("news_assistant.content.processor.ContentProcessor.process_url") as mock_process:
        from pydantic import HttpUrl

        from news_assistant.content.schemas import ProcessedContent

        mock_process.return_value = ProcessedContent(
            url=HttpUrl("https://example.com/test-get"),
            title="Test Get Article",
            extracted_text="Extracted content",
            summary="Generated summary",
            extension="html",
            file_path=None,
        )

        create_response = client.post("/api/articles/", json=article_data)

    article_id = create_response.json()["id"]

    response = client.get(f"/api/articles/{article_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == article_id
    assert data["title"] == "Test Get Article"


def test_get_article_not_found(client: TestClient) -> None:
    """存在しない記事取得テスト"""
    response = client.get("/api/articles/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_article(client: TestClient) -> None:
    """記事更新テスト"""
    # テスト記事作成
    article_data = {"url": "https://example.com/test-update", "title": "Original Title"}

    with patch("news_assistant.content.processor.ContentProcessor.process_url"):
        create_response = client.post("/api/articles/", json=article_data)

    article_id = create_response.json()["id"]

    # 記事更新
    update_data = {"title": "Updated Title", "summary": "Updated summary"}

    response = client.put(f"/api/articles/{article_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["summary"] == "Updated summary"


def test_delete_article(client: TestClient) -> None:
    """記事削除テスト"""
    # テスト記事作成
    article_data = {"url": "https://example.com/test-delete", "title": "Delete Test Article"}

    with patch("news_assistant.content.processor.ContentProcessor.process_url"):
        create_response = client.post("/api/articles/", json=article_data)

    article_id = create_response.json()["id"]

    # 記事削除
    response = client.delete(f"/api/articles/{article_id}")
    assert response.status_code == 204

    # 削除確認
    get_response = client.get(f"/api/articles/{article_id}")
    assert get_response.status_code == 404


def test_pagination(client: TestClient) -> None:
    """ページネーションテスト"""
    # 複数記事作成
    for i in range(5):
        article_data = {
            "url": f"https://example.com/test-page-{i}",
            "title": f"Page Test Article {i}",
        }
        with patch("news_assistant.content.processor.ContentProcessor.process_url"):
            client.post("/api/articles/", json=article_data)

    # ページネーション確認
    response = client.get("/api/articles/?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["articles"]) == 3
    assert data["total"] == 5
    assert data["skip"] == 0
    assert data["limit"] == 3
