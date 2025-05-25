#!/usr/bin/env python3
"""
本番環境データベース初期化スクリプト

このスクリプトは本番環境で最初にデータベースを作成・初期化するために使用します。
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from news_assistant.core.config import settings
from news_assistant.core.database import Base, engine
from sqlalchemy import text


def create_data_directory():
    """データディレクトリを作成"""
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ データディレクトリを作成: {data_dir.absolute()}")


def check_database_exists():
    """データベースファイルの存在確認"""
    if "sqlite" in settings.database_url:
        db_path = settings.database_url.replace("sqlite:///", "")
        db_file = Path(db_path)
        return db_file.exists()
    return False


def create_database_tables():
    """データベーステーブルを作成"""
    try:
        # すべてのテーブルを作成
        Base.metadata.create_all(bind=engine)
        print("✓ データベーステーブルを作成しました")
        
        # テーブル一覧を表示
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            if tables:
                print(f"  作成されたテーブル: {', '.join(tables)}")
            else:
                print("  警告: テーブルが作成されませんでした")
                
    except Exception as e:
        print(f"✗ データベーステーブル作成エラー: {e}")
        raise


def verify_database():
    """データベースの動作確認"""
    try:
        with engine.connect() as conn:
            # 基本的な接続テスト
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            
            # テーブル存在確認
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            
            print("✓ データベース接続確認完了")
            print(f"  利用可能なテーブル: {len(tables)}個")
            
            return True
            
    except Exception as e:
        print(f"✗ データベース確認エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("=== 本番環境データベース初期化 ===")
    print(f"環境: {os.getenv('ENVIRONMENT', 'production')}")
    print(f"データベースURL: {settings.database_url}")
    print()
    
    # 1. データディレクトリ作成
    create_data_directory()
    
    # 2. 既存データベース確認
    if check_database_exists():
        response = input("⚠️  データベースファイルが既に存在します。続行しますか？ (y/N): ")
        if response.lower() != 'y':
            print("初期化をキャンセルしました")
            return
    
    # 3. データベーステーブル作成
    create_database_tables()
    
    # 4. データベース動作確認
    if verify_database():
        print("\n✅ データベース初期化が完了しました！")
    else:
        print("\n❌ データベース初期化に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main() 