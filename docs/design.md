# 個人向けニュース収集システム 設計ドキュメント

## 1. システム概要

このシステムは、個人が興味のあるニュース記事を収集・管理するためのシンプルなAPIサーバーです。
MVPとして、基本的な記事の登録と取得機能を実装します。

## 2. システムアーキテクチャ

### 2.1 全体構成

```
[クライアント] <-> [APIサーバー] <-> [SQLiteデータベース]
```

### 2.2 技術スタック

- バックエンド: FastAPI (Python)
- データベース: SQLite
- 言語: Python 3.9+
- ORM: SQLAlchemy
- スキーマバリデーション: Pydantic v2
- テスト: pytest

## 3. データベース設計

### 3.1 テーブル設計

#### articles テーブル

| カラム名    | 型        | 説明                         |
|------------|-----------|------------------------------|
| id         | INTEGER   | 主キー、自動採番             |
| url        | TEXT      | 記事のURL（ユニーク）        |
| title      | TEXT      | 記事のタイトル               |
| summary    | TEXT      | 記事の要約（1000文字程度、自動生成） |
| created_at | TIMESTAMP | 登録日時                     |
| updated_at | TIMESTAMP | 更新日時                     |

## 4. API設計

### 4.1 エンドポイント一覧

#### 記事の登録
- エンドポイント: `POST /api/articles`
- リクエストボディ:
  ```json
  {
    "url": "string",
    "title": "string"
  }
  ```
- レスポンス:
  ```json
  {
    "id": "integer",
    "url": "string",
    "title": "string",
    "summary": "string",
    "created_at": "string",
    "updated_at": "string"
  }
  ```
- 処理内容:
  - 渡されたURLのコンテンツ（HTML, PDF, テキスト等）を取得する。
  - HTMLの場合は`<title>`タグ、PDFの場合はメタデータからタイトルを自動抽出し、titleフィールドにセットする。
  - タイトルが抽出できない場合はリクエストボディのtitleを利用する。
  - 取得したコンテンツを `data` ディレクトリに `{日付}_{記事ID}.{拡張子}` 形式で保存する。
    - 例: `20240608_1.html`、`20240608_2.pdf`
    - 拡張子はContent-TypeヘッダーやURLから判定（html, pdf, txt等）。
  - `data` ディレクトリが存在しない場合は自動作成する。
  - **記事本文からテキストを抽出し、OpenAI API（例: GPT-3.5/4）で1000文字程度の要約を自動生成し、summaryカラムに保存する。**

#### 記事一覧の取得
- エンドポイント: `GET /api/articles`
- レスポンス:
  ```json
  {
    "articles": [
      {
        "id": "integer",
        "url": "string",
        "title": "string",
        "summary": "string",
        "created_at": "string",
        "updated_at": "string"
      }
    ]
  }
  ```

#### 個別記事の取得
- エンドポイント: `GET /api/articles/{article_id}`
- レスポンス:
  ```json
  {
    "id": "integer",
    "url": "string",
    "title": "string",
    "summary": "string",
    "created_at": "string",
    "updated_at": "string"
  }
  ```

## 5. プロジェクト構造

```
news-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── database.py
├── tests/
│   └── test_main.py
├── docs/
│   └── design.md
├── requirements.txt
├── setup.py
└── README.md
```
