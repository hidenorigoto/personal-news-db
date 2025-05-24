# Makefile for News Assistant

.PHONY: test ruff mypy all

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