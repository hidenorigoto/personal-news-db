#!/usr/bin/env python3
"""
Alembicを使用した本番環境データベース初期化スクリプト

このスクリプトはAlembicマイグレーションを使用してデータベースを初期化します。
"""

import os
import subprocess
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from news_assistant.core.config import settings
from sqlalchemy import create_engine, text


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


def run_alembic_upgrade():
    """Alembicマイグレーションを実行"""
    try:
        print("Alembicマイグレーションを実行中...")
        
        # 現在のディレクトリをプロジェクトルートに変更
        os.chdir(project_root)
        
        # alembic upgrade headを実行
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✓ Alembicマイグレーション完了")
        if result.stdout:
            print(f"  出力: {result.stdout.strip()}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Alembicマイグレーションエラー: {e}")
        if e.stdout:
            print(f"  標準出力: {e.stdout}")
        if e.stderr:
            print(f"  エラー出力: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Alembicコマンドが見つかりません")
        print("  Alembicがインストールされているか確認してください")
        return False


def check_alembic_current():
    """現在のAlembicリビジョンを確認"""
    try:
        os.chdir(project_root)
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✓ 現在のリビジョン: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ リビジョン確認エラー: {e}")
        return False


def verify_database():
    """データベースの動作確認"""
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # 基本的な接続テスト
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            
            # テーブル存在確認
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            
            print("✓ データベース接続確認完了")
            print(f"  利用可能なテーブル: {len(tables)}個")
            if tables:
                print(f"  テーブル一覧: {', '.join(tables)}")
            
            return True
            
    except Exception as e:
        print(f"✗ データベース確認エラー: {e}")
        return False


def show_alembic_history():
    """Alembicマイグレーション履歴を表示"""
    try:
        os.chdir(project_root)
        result = subprocess.run(
            ["alembic", "history", "--verbose"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("📋 マイグレーション履歴:")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 履歴確認エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("=== Alembicを使用した本番環境データベース初期化 ===")
    print(f"環境: {os.getenv('ENVIRONMENT', 'production')}")
    print(f"データベースURL: {settings.database_url}")
    print(f"プロジェクトルート: {project_root}")
    print()
    
    # 1. データディレクトリ作成
    create_data_directory()
    
    # 2. 既存データベース確認
    if check_database_exists():
        response = input("⚠️  データベースファイルが既に存在します。続行しますか？ (y/N): ")
        if response.lower() != 'y':
            print("初期化をキャンセルしました")
            return
    
    # 3. Alembicマイグレーション実行
    if not run_alembic_upgrade():
        print("\n❌ Alembicマイグレーションに失敗しました")
        sys.exit(1)
    
    # 4. 現在のリビジョン確認
    check_alembic_current()
    
    # 5. データベース動作確認
    if verify_database():
        print("\n✅ Alembicを使用したデータベース初期化が完了しました！")
        
        # 6. マイグレーション履歴表示
        print("\n" + "="*50)
        show_alembic_history()
    else:
        print("\n❌ データベース初期化に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main() 