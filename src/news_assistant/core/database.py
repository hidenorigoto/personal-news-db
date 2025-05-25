"""データベース接続とセッション管理"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .config import settings

# データディレクトリの作成
os.makedirs(settings.data_dir, exist_ok=True)

# SQLAlchemy エンジンの作成
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug
)

# セッションファクトリの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスの作成
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """データベースセッションの依存性注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """全テーブルを作成"""
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """全テーブルを削除（テスト用）"""
    Base.metadata.drop_all(bind=engine) 