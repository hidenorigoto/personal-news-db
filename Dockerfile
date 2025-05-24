# syntax=docker/dockerfile:1
FROM python:3.9-slim

# Poetryインストール
ENV POETRY_VERSION=1.7.1
RUN pip install "poetry==$POETRY_VERSION"

# 作業ディレクトリ
WORKDIR /app

# 依存ファイルコピー
COPY pyproject.toml poetry.lock ./

# 依存インストール
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --with dev

# アプリケーションコピー
COPY src/news_assistant ./news_assistant
COPY data ./data

# ポート
EXPOSE 8000

# 本番用CMD（docker-composeで上書き可）
CMD ["uvicorn", "news_assistant.main:app", "--host", "0.0.0.0", "--port", "8000"] 