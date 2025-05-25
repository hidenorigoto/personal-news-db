# プロジェクトで使用しているツール・ライブラリ サマリ

このドキュメントは、`news-assistant` プロジェクトで利用している主要なツール・ライブラリの概要をまとめたものです。新規メンバーや他の開発者がすぐに全体像を把握できるよう、役割や用途を簡潔に記載しています。

---

## アプリケーション本体

- **FastAPI**
  - Python製の高速なWeb APIフレームワーク。非同期対応で、APIサーバーの構築に利用。
- **Uvicorn**
  - ASGIサーバー。FastAPIアプリの本番・開発サーバーとして利用。
- **SQLAlchemy**
  - PythonのORM（Object Relational Mapper）。DB操作をPythonコードで記述。
- **Pydantic v2**
  - データバリデーション・シリアライズ用ライブラリ。APIのリクエスト/レスポンススキーマ定義に利用。
- **python-dotenv**
  - `.env`ファイルから環境変数を読み込むためのライブラリ。設定値の管理に利用。
- **requests**
  - HTTPリクエスト用の標準的なライブラリ。外部サイトから記事データを取得。
- **beautifulsoup4**
  - HTML/XMLパース用ライブラリ。記事HTMLからタイトル等を抽出。
- **pypdf**
  - PDFファイルの読み取り・解析用ライブラリ。PDF記事のタイトル抽出等に利用。
- **openai**
  - OpenAI API公式クライアントライブラリ。GPT-3.5/4を使用した記事要約生成に利用。
- **pydantic-settings**
  - Pydantic v2用の設定管理ライブラリ。環境変数の型安全な読み込みに利用。

## 開発・テスト・品質管理

- **ruff**
  - 高速なPythonリンター・フォーマッター。PEP8準拠の静的解析、import順序の自動修正、コードフォーマットを統合。
- **mypy**
  - 静的型チェックツール。型ヒントの検証に利用。Python 3.12の最新型機能に対応。
- **pytest**
  - 標準的なPythonテストフレームワーク。ユニットテスト・統合テストの実行。
- **pytest-cov**
  - pytest用のカバレッジ測定プラグイン。テスト網羅率の計測。
- **httpx**
  - 高機能なHTTPクライアント。テスト用のモックや非同期通信の検証に利用。
- **alembic**
  - SQLAlchemy用のデータベースマイグレーションツール。スキーマ変更の管理。

## 開発環境・インフラ

- **Poetry**
  - Pythonの依存関係管理・パッケージングツール。pyproject.tomlベースの現代的な管理。
- **Docker / docker-compose**
  - 開発・本番環境のコンテナ化、依存関係の分離・再現性確保。
- **SQLite**
  - 軽量な組み込み型RDBMS。開発・テスト・本番で共通利用。

---

### 参考
- 依存関係の詳細は `pyproject.toml` を参照
- 設計やAPI仕様は `README.md` を参照
- セットアップやコマンド例は `README.md` を参照
- 要約機能の詳細設計は `docs/summary_generation_design.md` を参照 