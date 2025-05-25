"""テスト設定とフィクスチャ"""
import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# モデルを明示的にインポートしてBaseに登録
from news_assistant.articles.models import Article  # noqa: F401
from news_assistant.core.database import Base, get_db
from news_assistant.main import app

# 環境変数からDB URLを取得（デフォルトはインメモリ）
SQLALCHEMY_DATABASE_URL = os.getenv("NEWS_ASSISTANT_DB_URL", "sqlite:///:memory:")

# テスト用エンジンとセッション
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# override_get_db関数は削除 - clientフィクスチャ内で直接定義


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> None:
    """テストセッション開始時にデータベースを初期化"""
    # テーブル作成を確実に実行
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """テスト用データベースセッションフィクスチャ"""
    # 既存のテーブルを削除してクリーンな状態にする
    Base.metadata.drop_all(bind=engine)
    # テーブル作成（モデルがインポートされているため、articlesテーブルも作成される）
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # テーブル削除
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """テスト用クライアントフィクスチャ"""
    # データベース依存関係をオーバーライド（db_sessionと同じセッションを使用）
    def get_test_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = get_test_db

    with TestClient(app) as test_client:
        yield test_client

    # オーバーライドをクリア
    app.dependency_overrides.clear()
