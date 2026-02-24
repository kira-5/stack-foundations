# Professional Makefile for mtp-base-pricing
# Simplified command interface for development tasks

.PHONY: setup install-hooks lint fix pre-commit test clean help

help:
	@echo "🛠️ mtp-base-pricing Development Commands:"
	@echo "  make setup          - Initial setup (install dependencies & hooks)"
	@echo "  make install-hooks  - Install pre-commit hooks"
	@echo "  make lint           - Run all Linter/Audit hooks"
	@echo "  make fix            - Run all Auto-Fix hooks"
	@echo "  make pre-commit     - Run pre-commit on all files"
	@echo "  make test           - Run backend tests"
	@echo "  make clean          - Remove temporary and build files"

setup:
	cd backend && pip install -r requirements.txt && pre-commit install

install-hooks:
	cd backend && pre-commit install

lint:
	cd backend && pre-commit run --all-files

fix:
	@cd backend && pre-commit run --all-files || ( \
		EXIT_CODE=$$?; \
		if [ $$EXIT_CODE -eq 1 ]; then \
			echo "\n✨ Auto-fixes applied! Run 'make fix', 'make pre-commit', or 'pre-commit run --all-files' to finalize the Quality Gate. ✨\n"; \
		else \
			echo "\n❌ Pre-commit hooks found issues that require manual attention. ❌\n"; \
			exit $$EXIT_CODE; \
		fi \
	)

pre-commit:
	@cd backend && pre-commit run --all-files || ( \
		EXIT_CODE=$$?; \
		if [ $$EXIT_CODE -eq 1 ]; then \
			echo "\n✨ Auto-fixes applied! Run 'make fix', 'make pre-commit', or 'pre-commit run --all-files' to finalize the Quality Gate. ✨\n"; \
		else \
			echo "\n❌ Pre-commit hooks found issues that require manual attention. ❌\n"; \
			exit $$EXIT_CODE; \
		fi \
	)

test:
	cd backend && pytest --cov=app --cov-report=xml:test-coverage.xml --cov-report=term-missing --junitxml=test-results.xml

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
