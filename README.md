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

## API仕様

APIの詳細な仕様は、サーバー起動後に以下のURLで確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 設計ドキュメント

詳細な設計ドキュメントは `docs/design.md` を参照してください。

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

## テストの実行方法

### Dockerでユニットテストを実行

#### 推奨: testサービスを使う
```bash
docker compose run --rm test
```
- すべてのテストがDocker上で実行されます。
- テスト用DBやdataディレクトリも自動的に分離されます。

#### poetryサービスでpytestを使う（開発用シェル）
```bash
docker compose run --rm poetry poetry run pytest
```
- 対話的にpytestやmypy, ruff, blackなども実行できます。

### 注意
- テストは毎回クリーンなDB・dataディレクトリで実行されます。
- テスト用のURLはユニークになるよう自動生成されています。
