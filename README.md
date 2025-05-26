# News Assistant

個人向けのニュース収集システムです。興味のあるニュース記事を保存し、AI要約機能で効率的に管理することができます。

## 機能

- **記事の自動処理**: URLから記事のタイトル・内容を自動抽出
- **AI要約自動生成**: OpenAI APIを使用した高品質な要約生成
- **音声変換機能**: Azure/OpenAI Text-to-Speech APIによるテキスト音声変換
- **多様なコンテンツ対応**: HTML、PDF、テキストファイルの処理
- **RESTful API**: 記事の登録・取得・更新・削除
- **ヘルスチェック機能**: システム状態の監視
- **データベースマイグレーション**: Alembicによるスキーマ管理
- **型安全性**: MyPyによる厳密な型チェック
- **コード品質**: Ruff、Blackによる自動整形・リンティング

## アーキテクチャ

本プロジェクトは**モジュール機能ベース構造**を採用し、以下の特徴を持ちます：

- **ドメイン駆動設計**: 各機能が独立したモジュールとして分離
- **責務の明確化**: router、service、model、schemaの明確な分離
- **スケーラビリティ**: 新機能追加時の影響範囲を限定
- **保守性**: 関連するコードが同一モジュール内に集約
- **テスタビリティ**: モジュール単位での独立したテスト

## APIエンドポイント

### 基本情報
- `GET /` - API基本情報
- `GET /health` - ヘルスチェック（データベース状態含む）

### 記事管理
- `POST /api/articles/` - 記事登録（URL自動処理・要約生成）
- `GET /api/articles/` - 記事一覧取得（ページネーション対応）
- `GET /api/articles/{id}` - 個別記事取得
- `PUT /api/articles/{id}` - 記事更新
- `DELETE /api/articles/{id}` - 記事削除

### ドキュメント
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## 環境変数設定

`.env`ファイルを作成して以下を設定：

```bash
# OpenAI API設定（要約・音声機能用）
OPENAI_API_KEY=your_openai_api_key_here

# 音声プロバイダー設定
SPEECH_PROVIDER=azure  # "azure" または "openai"

# Azure Speech Service設定（SPEECH_PROVIDER=azureの場合）
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=your_azure_region_here

# OpenAI TTS設定（SPEECH_PROVIDER=openaiの場合）
OPENAI_TTS_MODEL=tts-1  # "tts-1" または "tts-1-hd"
OPENAI_TTS_VOICE=alloy  # alloy, echo, fable, onyx, nova, shimmer
OPENAI_TTS_SPEED=1.0    # 0.25-4.0

# データベース設定
NEWS_ASSISTANT_DB_URL=sqlite:///./data/news.db

# アプリケーション設定
DEBUG=true
APP_NAME="News Assistant API"
```

## セットアップ

### Docker使用（推奨）

#### 開発環境の起動
```bash
# 基本的な開発環境（API + DB）
docker compose up app-dev

# テスト実行
docker compose run --rm test

# Poetry環境でのコマンド実行
docker compose run --rm poetry bash
```

#### データベースマイグレーション
```bash
# マイグレーション実行
docker compose run --rm test poetry run alembic upgrade head

# 新しいマイグレーション作成
docker compose run --rm poetry alembic revision --autogenerate -m "変更内容の説明"
```

### Poetry使用（ローカル開発）

1. 必要なパッケージのインストール:
```bash
poetry install
```

2. サーバーの起動:
```bash
poetry run uvicorn news_assistant.main:app --reload
```

## 開発ツール

### コード品質チェック
```bash
# 全体的な品質チェック
docker compose run --rm test poetry run ruff check news_assistant --fix
docker compose run --rm test poetry run mypy news_assistant
docker compose run --rm test pytest -v

# 個別ツール実行
docker compose run --rm poetry ruff format news_assistant  # フォーマット
docker compose run --rm poetry ruff check news_assistant   # リンティング
docker compose run --rm poetry mypy news_assistant         # 型チェック
```

### テスト実行
```bash
# 全テスト実行
docker compose run --rm test pytest -v

# 特定のテストファイル
docker compose run --rm test pytest tests/test_articles.py -v

# カバレッジ付きテスト
docker compose run --rm test pytest --cov=news_assistant --cov-report=html
```

## プロジェクト構造

```
news-assistant/
├── src/news_assistant/           # メインアプリケーション
│   ├── main.py                  # FastAPIアプリケーション
│   ├── summary.py               # 後方互換性ラッパー
│   │
│   ├── core/                    # 共通設定・データベース
│   │   ├── __init__.py         # モジュールエクスポート
│   │   ├── config.py           # アプリケーション設定
│   │   ├── database.py         # データベース接続設定
│   │   └── exceptions.py       # カスタム例外定義
│   │
│   ├── articles/                # 記事管理機能
│   │   ├── __init__.py         # モジュールエクスポート
│   │   ├── models.py           # SQLAlchemyモデル
│   │   ├── schemas.py          # Pydanticスキーマ
│   │   ├── router.py           # APIエンドポイント
│   │   └── service.py          # ビジネスロジック
│   │
│   ├── ai/                      # AI・要約機能
│   │   ├── __init__.py         # モジュールエクスポート
│   │   ├── schemas.py          # AI設定スキーマ
│   │   ├── providers.py        # AIプロバイダー実装
│   │   └── summarizer.py       # 要約サービス
│   │
│   ├── content/                 # コンテンツ処理機能
│   │   ├── __init__.py         # モジュールエクスポート
│   │   ├── schemas.py          # コンテンツスキーマ
│   │   ├── extractor.py        # コンテンツ抽出
│   │   └── processor.py        # コンテンツ処理
│   │
│   ├── speech/                  # 音声変換機能
│   │   ├── __init__.py         # モジュールエクスポート
│   │   ├── schemas.py          # 音声設定スキーマ
│   │   ├── service.py          # 音声変換サービス
│   │   └── exceptions.py       # 音声変換例外定義
│   │
│   ├── health/                  # ヘルスチェック機能
│   │   ├── __init__.py         # モジュールエクスポート
│   │   └── router.py           # ヘルスチェックAPI
│   │
│   └── shared/                  # 共有ユーティリティ
│       └── __init__.py         # 共通ヘルパー関数
│
├── tests/                       # テストファイル
│   ├── conftest.py             # テスト設定・フィクスチャ
│   ├── test_main.py            # 統合テスト
│   ├── test_articles.py        # 記事機能テスト
│   ├── test_ai.py              # AI機能テスト
│   ├── test_content.py         # コンテンツ処理テスト
│   ├── test_speech.py          # 音声変換機能テスト
│   └── test_new_structure.py   # 新構造テスト
│
├── alembic/                     # データベースマイグレーション
│   ├── env.py                  # Alembic設定
│   ├── versions/               # マイグレーションファイル
│   └── alembic.ini             # Alembic設定ファイル
│
├── docs/                        # 設計ドキュメント
├── data/                        # データベース・ファイル保存
├── docker-compose.yml           # Docker設定
├── pyproject.toml              # プロジェクト設定・依存関係
└── README.md                   # このファイル
```

### モジュール設計の特徴

#### 1. **articles/** - 記事管理
- **models.py**: SQLAlchemyによるデータベースモデル
- **schemas.py**: API入出力のPydanticスキーマ
- **router.py**: FastAPIルーター（エンドポイント定義）
- **service.py**: ビジネスロジック（データ処理・外部API連携）

#### 2. **ai/** - AI・要約機能
- **providers.py**: OpenAI、Mock等のAIプロバイダー実装
- **summarizer.py**: 要約生成サービス
- **schemas.py**: AI設定・リクエスト・レスポンススキーマ

#### 3. **content/** - コンテンツ処理
- **extractor.py**: URL先コンテンツの取得・抽出
- **processor.py**: タイトル抽出・要約生成の統合処理
- **schemas.py**: コンテンツデータスキーマ

#### 4. **speech/** - 音声変換機能
- **service.py**: Text-to-Speech API統合・音声合成サービス
- **schemas.py**: 音声設定・リクエスト・レスポンススキーマ
- **exceptions.py**: 音声変換専用例外クラス
- **プロバイダー**: 
  - Azure Speech Service（日本語最適化、SSML対応）
  - OpenAI TTS（6種類の音声、高品質モデル）
  - Mock（テスト用）

#### 5. **core/** - 共通基盤
- **config.py**: 環境変数・アプリケーション設定
- **database.py**: SQLAlchemy設定・セッション管理
- **exceptions.py**: カスタム例外クラス

## API仕様

APIの詳細な仕様は、サーバー起動後に以下のURLで確認できます：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **ヘルスチェック**: http://localhost:8000/health

### 記事登録の例

```bash
# 記事登録（URL自動処理・要約生成）
curl -X POST "http://localhost:8000/api/articles/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/news-article",
    "title": "記事タイトル"
  }'
```

### 音声プロバイダーの選択

本システムは2つの音声プロバイダーをサポートしています：

#### Azure Speech Service
- **特徴**: 日本語に最適化、SSML対応、詳細な音声調整可能
- **設定方法**:
  ```bash
  SPEECH_PROVIDER=azure
  AZURE_SPEECH_KEY=your_key
  AZURE_SPEECH_REGION=japaneast
  ```

#### OpenAI TTS
- **特徴**: シンプルなAPI、6種類の音声、高品質モデル（tts-1-hd）
- **音声オプション**:
  - `alloy`: 自然でスムーズ
  - `echo`: 明瞭で正確
  - `fable`: 温かみのある声
  - `onyx`: 深く権威的
  - `nova`: 明るくエネルギッシュ
  - `shimmer`: 柔らかく優しい
- **設定方法**:
  ```bash
  SPEECH_PROVIDER=openai
  OPENAI_TTS_MODEL=tts-1-hd  # または tts-1
  OPENAI_TTS_VOICE=nova
  OPENAI_TTS_SPEED=1.2       # 0.25-4.0
  ```

## 設計ドキュメント

詳細な設計ドキュメントは以下を参照してください：
- **要約機能設計**: `docs/summary_generation_design.md`
- **使用技術・ライブラリ**: `docs/tools_and_libraries.md`

> **注**: 全体設計に関する情報は、このREADMEに統合されています。モジュール構造、API仕様、開発ガイドラインなど、プロジェクトの全体像を把握するために必要な情報はすべてここに記載されています。

## 品質保証

### テストカバレッジ
- **60個のテスト**が全て成功
- **単体テスト**: 各モジュールの独立テスト
- **統合テスト**: API全体の動作テスト
- **モックテスト**: 外部API依存の分離テスト
- **音声変換テスト**: Azure Speech Service統合テスト

### コード品質
- **Ruff**: 高速リンティング・フォーマット
- **MyPy**: 厳密な型チェック
- **Black**: 一貫したコードスタイル
- **警告ゼロ**: クリーンなコードベース

## トラブルシューティング

### よくある問題

1. **OpenAI APIエラー**
   ```bash
   # 環境変数確認
   docker compose run --rm test printenv | grep OPENAI
   ```

2. **データベースエラー**
   ```bash
   # マイグレーション状態確認
   docker compose run --rm test poetry run alembic current
   
   # マイグレーション実行
   docker compose run --rm test poetry run alembic upgrade head
   ```

3. **テスト失敗**
   ```bash
   # 詳細なテスト実行
   docker compose run --rm test pytest -v --tb=short
   
   # 特定のテストのみ実行
   docker compose run --rm test pytest tests/test_articles.py::test_create_article -v
   ```

4. **Docker関連**
   ```bash
   # 完全リセット
   docker compose down
   docker compose build --no-cache
   docker compose up app-dev
   ```

### ログ確認
```bash
# アプリケーションログ
docker compose logs app-dev --tail=50

# 全サービスログ
docker compose logs

# リアルタイムログ監視
docker compose logs -f app-dev
```

### 開発時のベストプラクティス

1. **pyproject.toml修正時の必須手順**:
   ```bash
   # 依存関係、ツール設定、メタデータ等を変更した場合は必ずリビルド
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   
   # 設定変更の確認
   docker compose run --rm poetry poetry show  # 依存関係確認
   docker compose run --rm poetry poetry run mypy --version  # ツール確認
   ```

2. **依存関係追加時**:
   ```bash
   # pyproject.toml更新後は必ずリビルド
   docker compose build --no-cache
   ```

3. **テスト実行**:
   ```bash
   # 必ずtest専用コンテナを使用
   docker compose run --rm test pytest
   ```

4. **コード品質チェック**:
   ```bash
   # コミット前に必ず実行
   docker compose run --rm test poetry run ruff check news_assistant --fix
   docker compose run --rm test poetry run mypy news_assistant
   docker compose run --rm test pytest -v
   
   # または一括実行
   make all
   ```

5. **設定変更時のトラブルシューティング**:
   ```bash
   # MyPy設定変更後にキャッシュクリア
   docker compose run --rm poetry rm -rf .mypy_cache
   
   # Ruff設定変更後の確認
   docker compose run --rm poetry poetry run ruff check --show-settings
   ```
