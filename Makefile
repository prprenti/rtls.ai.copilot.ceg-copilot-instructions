.PHONY: help validate validate-check validate-apply test-quality test-all sync

UV := /p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv

help:
	@echo "CEG Copilot Plugin Development Commands"
	@echo ""
	@echo "Plugin Validation:"
	@echo "  make validate              - Full validation: update, check remotes, test quality, run tests"
	@echo "  make validate-check        - Check plugin metadata (including remotes)"
	@echo "  make validate-apply        - Rewrite generated marketplace fields"
	@echo ""
	@echo "Testing:"
	@echo "  make test-quality          - Run prompt-quality test suite"
	@echo "  make test-all              - Run all tests"
	@echo ""
	@echo "Setup:"
	@echo "  make sync                  - Sync dependencies"

sync:
	$(UV) sync

# Full validation: update metadata, validate remotes, test quality, run all tests
validate: validate-apply validate-check test-quality test-all
	@echo ""
	@echo "✓ Full validation passed!"

# Check plugin metadata and remote sources
# Automatically fetches GitHub token for remote repository access
validate-check:
	@export GH_TOKEN=$${GH_TOKEN:-$$(gh auth token)} && \
	$(UV) run python scripts/validate_plugin_metadata.py --check --check-remotes --github-token-env GH_TOKEN

# Update generated marketplace fields from local plugin manifests
validate-apply:
	$(UV) run python scripts/validate_plugin_metadata.py --apply

test-quality:
	$(UV) run pytest tests/prompt_quality/ -v

test-all:
	$(UV) run pytest
