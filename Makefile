.PHONY: help setup sync lint test run validate compare clean

# ────────────────────────────────────────
# Kernel Scheduling — AutoResearch
# ────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## First-time setup: install uv + sync deps
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	uv sync --all-extras
	@echo "✅ Setup complete"

sync: ## Sync dependencies
	uv sync --all-extras

lint: ## Run linter
	uv run ruff check .

test: ## Run tests
	uv run pytest -v

run: ## Run an experiment (usage: make run CONFIG=experiments/configs/exp001.yaml)
	uv run python experiments/run_experiment.py $(CONFIG)

validate: ## Validate all schedules in results/
	uv run python scripts/validate_schedule.py --dir results/

compare: ## Compare all experiment results
	uv run python scripts/compare_results.py

notebook: ## Launch Jupyter Lab
	uv run jupyter lab --notebook-dir=notebooks

clean: ## Remove generated files
	rm -rf results/*/ data/processed/* output/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "🧹 Cleaned"
