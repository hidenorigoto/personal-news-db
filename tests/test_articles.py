"""記事モジュールのテスト"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from news_assistant.main import app
from news_assistant.core import Base, get_db

# テスト用データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_articles.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """テスト用データベースセッション"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """各テスト前にデータベースをリセット"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_article():
    """記事作成テスト"""
    article_data = {
        "url": "https://example.com/test-article",
        "title": "Test Article",
        "summary": "This is a test article"
    }
    
    response = client.post("/api/articles/", json=article_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["url"] == article_data["url"]
    assert data["title"] == article_data["title"]
    assert data["summary"] == article_data["summary"]
    assert "id" in data
    assert "created_at" in data


def test_create_article_duplicate_url():
    """重複URL記事作成テスト"""
    article_data = {
        "url": "https://example.com/duplicate-test",
        "title": "Test Article",
        "summary": "This is a test article"
    }
    
    # 最初の記事作成
    response1 = client.post("/api/articles/", json=article_data)
    assert response1.status_code == 201
    
    # 同じURLで再度作成（エラーになるはず）
    response2 = client.post("/api/articles/", json=article_data)
    assert response2.status_code == 409


def test_get_articles_empty():
    """空の記事一覧取得テスト"""
    response = client.get("/api/articles/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["articles"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 100


def test_get_articles_with_data():
    """記事一覧取得テスト（データあり）"""
    # テスト記事を作成
    article_data = {
        "url": "https://example.com/test-list",
        "title": "Test List Article",
        "summary": "Test summary"
    }
    create_response = client.post("/api/articles/", json=article_data)
    assert create_response.status_code == 201
    
    # 記事一覧取得
    response = client.get("/api/articles/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["articles"]) == 1
    assert data["total"] == 1
    assert data["articles"][0]["title"] == article_data["title"]


def test_get_article_by_id():
    """ID指定記事取得テスト"""
    # テスト記事を作成
    article_data = {
        "url": "https://example.com/test-get-by-id",
        "title": "Test Get By ID",
        "summary": "Test summary"
    }
    create_response = client.post("/api/articles/", json=article_data)
    assert create_response.status_code == 201
    article_id = create_response.json()["id"]
    
    # ID指定で取得
    response = client.get(f"/api/articles/{article_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == article_id
    assert data["title"] == article_data["title"]


def test_get_article_not_found():
    """存在しない記事取得テスト"""
    response = client.get("/api/articles/999")
    assert response.status_code == 404


def test_update_article():
    """記事更新テスト"""
    # テスト記事を作成
    article_data = {
        "url": "https://example.com/test-update",
        "title": "Original Title",
        "summary": "Original summary"
    }
    create_response = client.post("/api/articles/", json=article_data)
    assert create_response.status_code == 201
    article_id = create_response.json()["id"]
    
    # 記事更新
    update_data = {
        "title": "Updated Title",
        "summary": "Updated summary"
    }
    response = client.put(f"/api/articles/{article_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["summary"] == update_data["summary"]


def test_delete_article():
    """記事削除テスト"""
    # テスト記事を作成
    article_data = {
        "url": "https://example.com/test-delete",
        "title": "Test Delete",
        "summary": "Test summary"
    }
    create_response = client.post("/api/articles/", json=article_data)
    assert create_response.status_code == 201
    article_id = create_response.json()["id"]
    
    # 記事削除
    response = client.delete(f"/api/articles/{article_id}")
    assert response.status_code == 204
    
    # 削除確認
    get_response = client.get(f"/api/articles/{article_id}")
    assert get_response.status_code == 404


def test_pagination():
    """ページネーションテスト"""
    # 複数の記事を作成
    for i in range(5):
        article_data = {
            "url": f"https://example.com/test-pagination-{i}",
            "title": f"Test Article {i}",
            "summary": f"Test summary {i}"
        }
        response = client.post("/api/articles/", json=article_data)
        assert response.status_code == 201
    
    # ページネーション確認
    response = client.get("/api/articles/?skip=2&limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["articles"]) == 2
    assert data["total"] == 5
    assert data["skip"] == 2
    assert data["limit"] == 2 