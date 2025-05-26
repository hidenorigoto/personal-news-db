"""記事モジュールのテスト"""
from pathlib import Path
from unittest.mock import MagicMock, patch

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


def test_article_audio_generation(client: TestClient) -> None:
    """記事音声生成テスト"""
    article_data = {"url": "https://example.com/audio-test", "title": "Audio Test Article"}

    with patch("news_assistant.content.processor.ContentProcessor.process_url") as mock_process, \
         patch("news_assistant.articles.service.asyncio.create_task") as mock_task:
            from pydantic import HttpUrl

            from news_assistant.content.schemas import ProcessedContent

            mock_process.return_value = ProcessedContent(
                url=HttpUrl("https://example.com/audio-test"),
                title="Audio Test Article",
                extracted_text="Test content for audio generation",
                summary="Test summary for audio",
                extension="html",
                file_path=None,
            )

            response = client.post("/api/articles/", json=article_data)

    assert response.status_code == 201
    # 音声生成タスクが作成されたことを確認
    mock_task.assert_called_once()


def test_speech_service_audio_path_generation() -> None:
    """音声ファイルパス生成テスト"""
    from news_assistant.speech.schemas import OutputFormat
    from news_assistant.speech.service import SpeechService

    speech_service = SpeechService()

    # 要約音声ファイルパス生成
    summary_path = speech_service.generate_article_audio_path(
        article_id=123, content_type="summary"
    )
    assert summary_path.name == "123-summary.wav"
    assert "speech" in str(summary_path)

    # 本文音声ファイルパス生成
    full_path = speech_service.generate_article_audio_path(
        article_id=456, content_type="full", output_format=OutputFormat.MP3
    )
    assert full_path.name == "456-full.mp3"


def test_speech_service_template_functionality() -> None:
    """音声テンプレート機能テスト"""
    from unittest.mock import AsyncMock

    from news_assistant.speech.service import SpeechService

    # モックプロバイダーを使用してテスト
    mock_provider = AsyncMock()
    speech_service = SpeechService(provider=mock_provider)

    # テンプレートヘッダー付き音声生成のテスト実行
    import asyncio
    async def run_test() -> None:
        await speech_service.text_to_speech_with_template(
            text="これはテスト内容です。",
            article_title="テスト記事",
            content_type="要約"
        )

    asyncio.run(run_test())

    # プロバイダーが呼び出されたことを確認
    mock_provider.synthesize_speech.assert_called_once()

    # 呼び出し時の引数を確認
    call_args = mock_provider.synthesize_speech.call_args[0][0]
    expected_text = "テスト記事の要約をお読みします。\n\nこれはテスト内容です。"
    assert call_args.text == expected_text


def test_article_audio_generation_sync() -> None:
    """記事音声生成同期メソッドテスト"""
    from unittest.mock import AsyncMock

    from news_assistant.articles.models import Article
    from news_assistant.articles.service import ArticleService

    # テスト用記事オブジェクト
    article = Article(
        id=999,
        url="https://test.com",
        title="テスト記事タイトル",
        summary="テスト要約内容"
    )

    # モック音声サービス
    mock_speech_service = AsyncMock()
    mock_speech_service.generate_article_audio_path.return_value = Path("test_path.wav")
    mock_speech_service.text_to_speech_with_template.return_value = MagicMock(success=True)

    article_service = ArticleService()
    article_service.speech_service = mock_speech_service

    # テスト実行
    import asyncio
    async def run_test() -> dict[str, bool]:
        results = await article_service.generate_article_audio_sync(article)
        return results

    results = asyncio.run(run_test())

    # 結果確認
    assert "summary" in results
    assert "full" in results
    # モック音声サービスが呼び出されたことを確認
    mock_speech_service.text_to_speech_with_template.assert_called()
