"""新しいモジュール構造のテスト"""
import pytest
from fastapi.testclient import TestClient

from news_assistant.main import app
from news_assistant.core import settings


client = TestClient(app)


def test_root_endpoint():
    """ルートエンドポイントのテスト"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == settings.app_name
    assert data["version"] == settings.version
    assert data["status"] == "running"
    assert "debug" in data
    assert isinstance(data["debug"], bool)


def test_health_endpoint():
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in data
    assert data["version"] == settings.version
    assert data["app_name"] == settings.app_name
    assert "database" in data
    assert data["debug_mode"] == settings.debug


def test_core_config_import():
    """コア設定モジュールのインポートテスト"""
    from news_assistant.core import settings, get_settings
    
    assert settings.app_name == "News Assistant API"
    assert settings.version == "0.1.0"
    assert isinstance(settings.debug, bool)
    
    # シングルトンテスト
    settings2 = get_settings()
    assert settings is settings2


def test_core_database_import():
    """コアデータベースモジュールのインポートテスト"""
    from news_assistant.core import get_db, Base, engine
    
    # 基本的なインポートが成功することを確認
    assert get_db is not None
    assert Base is not None
    assert engine is not None


def test_core_exceptions_import():
    """コア例外モジュールのインポートテスト"""
    from news_assistant.core import (
        NewsAssistantException,
        DatabaseError,
        ValidationError,
        ArticleNotFoundError
    )
    
    # 例外クラスの基本動作テスト
    base_exc = NewsAssistantException("test message", "TEST_CODE", {"key": "value"})
    assert str(base_exc) == "test message"
    assert base_exc.error_code == "TEST_CODE"
    assert base_exc.details == {"key": "value"}
    
    # 継承関係テスト
    db_error = DatabaseError("db error")
    assert isinstance(db_error, NewsAssistantException)
    
    # 特殊例外テスト
    article_error = ArticleNotFoundError(123)
    assert "123" in str(article_error)
    assert article_error.error_code == "ARTICLE_NOT_FOUND"
    assert article_error.details["article_id"] == 123


def test_health_module_import():
    """ヘルスチェックモジュールのインポートテスト"""
    from news_assistant.health import router
    
    assert router is not None
    # ルーターにヘルスチェックエンドポイントが含まれていることを確認
    routes = [route.path for route in router.routes if hasattr(route, 'path')]
    assert "/health" in routes


def test_app_configuration():
    """FastAPIアプリケーションの設定テスト"""
    assert app.title == settings.app_name
    assert app.version == settings.version
    assert app.debug == settings.debug
    
    # ルートが正しく登録されていることを確認
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    assert "/" in routes
    assert "/health" in routes 