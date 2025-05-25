# News Assistant

個人向けのニュース収集システムです。興味のあるニュース記事を保存し、管理することができます。

## 機能

- ニュース記事のURLとタイトルの登録
- 登録済み記事の一覧表示
- 個別記事の詳細表示

## セットアップ

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
poetry run uvicorn app.main:app --reload
```

## Dockerでの起動

### 開発用（ホットリロード）
```bash
docker compose up app-dev
```
- ホストのsrc, data, pyproject.toml, poetry.lockをマウントし、コード変更が即時反映されます。

### 本番用
```bash
docker compose up app
```
- ビルド済みイメージで起動します。
- `data/`ディレクトリはDockerボリュームで永続化されます。

### 停止
```bash
docker compose down
```

## 開発ツール

- フォーマット: `poetry run black .`
- Lint: `poetry run ruff .`
- 型チェック: `poetry run mypy .`
- テスト: `poetry run pytest`

### 型チェック・mypy利用時の注意点

- **型スタブ（types-xxx）が必要な場合は、必ず `poetry add --group dev types-xxx` で追加してください。**
- **`mypy`で「Library stubs not installed for ...」と出た場合は、`poetry run mypy --install-types --non-interactive ...` で自動インストールできます。**
- **DockerやCI環境では、`news_assistant` ディレクトリのみで型チェックを実行してください。**
  - 例: `docker compose run --rm poetry poetry run mypy news_assistant`
  - `src/news_assistant`や`tests`などのパス指定は、コンテナ内の作業ディレクトリ構成に依存します。
- **型スタブや依存関係を追加・更新した場合は、Dockerイメージを再ビルドしてください。**
  - 例: `docker compose build --no-cache`
- **CIで型チェックが失敗する場合は、パス指定やキャッシュの有無を再確認してください。**

## API仕様

APIの詳細な仕様は、サーバー起動後に以下のURLで確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 設計ドキュメント

詳細な設計ドキュメントは `docs/design.md` を参照してください。

記事要約自動生成機能の詳細な設計は [`docs/summary_generation_design.md`](docs/summary_generation_design.md) を参照してください。

## サーバー再起動時の注意

FastAPIサーバーを再起動する際、以下のエラーが発生する場合があります：

```
ERROR:    [Errno 48] Address already in use
```

これは、ポート8000が既に他のプロセス（前回のuvicornなど）で使用されている場合に発生します。

### 対処手順
1. ポート8000を使用しているプロセスを確認します：
   ```bash
   lsof -i :8000
   ```
2. 該当するプロセスID（PID）をkillコマンドで停止します：
   ```bash
   kill <PID>
   ```
   例: `kill 12345`
3. 再度サーバーを起動します：
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

これでポート競合エラーを回避できます。
