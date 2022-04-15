.PHONY: test
test: ## ユニットテストを実行します
	@pytest test


.PHONY: help
help: ## makeコマンド一覧を表示します
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[1m\033[36m%-30s\033[22m\033[0m %s\n", $$1, $$2}'