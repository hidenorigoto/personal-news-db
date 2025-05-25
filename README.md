# News Assistant

個人向けのニュース収集システムです。興味のあるニュース記事を保存し、AI要約機能で効率的に管理することができます。

## 機能

- ニュース記事のURLとタイトルの登録
- **AI要約自動生成** (OpenAI API使用)
- 登録済み記事の一覧表示
- 個別記事の詳細表示
- ヘルスチェック機能
- データベースマイグレーション対応

## APIエンドポイント

- `GET /` - API基本情報
- `GET /health` - ヘルスチェック
- `POST /api/articles/` - 記事登録
- `GET /api/articles/` - 記事一覧取得
- `GET /api/articles/{id}` - 個別記事取得
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## 環境変数設定

`.env`ファイルを作成して以下を設定：

```bash
# OpenAI API設定（要約機能用）
OPENAI_API_KEY=your_openai_api_key_here

# データベース設定
NEWS_ASSISTANT_DB_URL=sqlite:///./data/news.db
```

## セットアップ

### Poetry使用の場合

1. 必要なパッケージのインストール:
```bash
poetry install
```

2. 仮想環境の有効化（必要に応じて）:
```bash
poetry shell
```

3. サーバーの起動:
```bash
poetry run uvicorn news_assistant.main:app --reload
```

### Docker使用の場合（推奨）

#### 開発用（ホットリロード）
```bash
docker compose up app-dev
```
- ホストのsrc, data, pyproject.toml, poetry.lockをマウントし、コード変更が即時反映されます。

#### 本番用
```bash
docker compose up app
```
- ビルド済みイメージで起動します。
- `data/`ディレクトリはDockerボリュームで永続化されます。

#### 停止
```bash
docker compose down
```

## データベースマイグレーション

### 初期セットアップ
```bash
# マイグレーション実行
docker compose run --rm poetry alembic upgrade head
```

### 新しいマイグレーション作成
```bash
# モデル変更後にマイグレーション生成
docker compose run --rm poetry alembic revision --autogenerate -m "変更内容の説明"

# マイグレーション適用
docker compose run --rm poetry alembic upgrade head
```

## 開発ツール

### Makefileコマンド（推奨）
```bash
make test      # テスト実行
make ruff      # リンティング・フォーマット
make mypy      # 型チェック
make black     # コードフォーマット
```

### Poetryコマンド（直接実行）
```bash
poetry run pytest           # テスト
poetry run ruff .           # リンティング
poetry run mypy .           # 型チェック
poetry run black .          # フォーマット
```

### Dockerコマンド
```bash
docker compose run --rm test     # テスト実行
docker compose run --rm poetry   # Poetry環境でシェル起動
```

## API仕様

APIの詳細な仕様は、サーバー起動後に以下のURLで確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- ヘルスチェック: http://localhost:8000/health

## プロジェクト構造

```
news-assistant/
├── src/news_assistant/     # メインアプリケーション
│   ├── main.py            # FastAPIアプリケーション
│   ├── models.py          # データベースモデル
│   ├── schemas.py         # Pydanticスキーマ
│   ├── database.py        # データベース設定
│   └── summary.py         # AI要約機能
├── tests/                 # テストファイル
├── alembic/              # データベースマイグレーション
├── docs/                 # 設計ドキュメント
├── data/                 # データベース・ファイル保存
├── docker-compose.yml    # Docker設定
├── pyproject.toml        # プロジェクト設定
└── Makefile             # 開発ツールコマンド
```

## 設計ドキュメント

詳細な設計ドキュメントは `docs/design.md` を参照してください。

記事要約自動生成機能の詳細な設計は [`docs/summary_generation_design.md`](docs/summary_generation_design.md) を参照してください。

## トラブルシューティング

### よくある問題

1. **OpenAI APIエラー**
   - `OPENAI_API_KEY`環境変数が設定されているか確認
   - APIキーが有効か確認

2. **データベースエラー**
   - `data/`ディレクトリの権限を確認
   - マイグレーションが適用されているか確認

3. **Docker関連**
   - `docker compose down && docker compose up app-dev`で再起動
   - `docker system prune`でクリーンアップ

### ログ確認
```bash
# アプリケーションログ
docker compose logs app-dev

# 全サービスログ
docker compose logs
```
