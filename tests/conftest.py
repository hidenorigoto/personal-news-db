"""テスト設定とフィクスチャ"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from news_assistant.core.database import Base, get_db
from news_assistant.main import app


# 環境変数からDB URLを取得（デフォルトはインメモリ）
SQLALCHEMY_DATABASE_URL = os.getenv("NEWS_ASSISTANT_DB_URL", "sqlite:///:memory:")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """テスト用データベースセッション"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """テスト用データベースセッションフィクスチャ"""
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # テーブル削除
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """テスト用クライアントフィクスチャ"""
    # データベース依存関係をオーバーライド
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # オーバーライドをクリア
    app.dependency_overrides.clear() 