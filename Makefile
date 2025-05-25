# Makefile for News Assistant

.PHONY: test ruff mypy all dev-up dev-down dev-logs prod-init prod-deploy prod-logs

# === 開発環境コマンド ===

# 開発環境起動
dev-up:
	docker compose up -d app-dev

# 開発環境停止
dev-down:
	docker compose down

# 開発環境ログ確認
dev-logs:
	docker compose logs -f app-dev

# === テスト・品質チェック ===

# ユニットテスト（pytest）
test:
	docker compose run --rm test

# ruffリンター
ruff:
	docker compose run --rm poetry poetry run ruff .

# mypy型チェック
mypy:
	docker compose run --rm poetry poetry run mypy .

# まとめて全部実行
all: ruff mypy test

# === 本番環境コマンド ===

# 本番環境データベース初期化
prod-init:
	docker compose -f docker-compose.prod.yml --profile init run --rm db-init

# 本番環境デプロイ
prod-deploy:
	docker compose -f docker-compose.prod.yml up -d

# 本番環境ログ確認
prod-logs:
	docker compose -f docker-compose.prod.yml logs -f app

# 本番環境停止
prod-stop:
	docker compose -f docker-compose.prod.yml down

# 本番環境完全リセット（データも削除）
prod-reset:
	docker compose -f docker-compose.prod.yml down -v
	docker volume rm news-assistant_data || true
