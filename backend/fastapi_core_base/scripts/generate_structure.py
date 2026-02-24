import os
from pathlib import Path

def create_structure():
    root = "fastapi_core_base"
    structure = [
        ".python-version",
        "config/",
        "config/settings.toml",
        "config/client_a.toml",
        "config/client_b.toml",
        "config/client_c.toml",
        "src/",
        "src/__init__.py",
        "src/shared/",
        "src/shared/__init__.py",
        "src/shared/auth/",
        "src/shared/db/",
        "src/shared/redis/",
        "src/shared/logging/",
        "src/shared/data/",
        "src/shared/tasks/",
        "src/shared/tasks/__init__.py",
        "src/shared/tasks/client.py",
        "src/shared/services/",
        "src/shared/services/__init__.py",
        "src/shared/services/mailer.py",
        "src/shared/services/filesystem.py",
        "src/shared/config.py",
        "src/app/",
        "src/app/__init__.py",
        "src/app/api/",
        "src/app/api/v1/",
        "src/app/api/v1/cron.py",
        "src/app/api/v1/ingestion.py",
        "src/app/users/",
        "src/app/tenants/",
        "src/app/modules/",
        "src/app/extensions/",
        "src/app/main.py",
        "src/app/routes.py",
        "src/cloud_run/",
        "src/cloud_run/data_processor/",
        "src/cloud_run/data_processor/main.py",
        "src/cloud_run/data_processor/Dockerfile",
        "src/cloud_functions/",
        "src/cloud_functions/gcs_handler/",
        "src/cloud_functions/gcs_handler/main.py",
        "scripts/",
        "scripts/bootstrap_client.py",
        "scripts/seed_db.py",
        "tests/",
        "tests/conftest.py",
        "tests/app/",
        "tests/shared/",
        "docs/",
        "docs/architecture/",
        "docs/jira/",
        "docs/technical/",
        "logs/",
        "logs/app.log",
        "duckdb_data/",
        "duckdb_data/client_a/",
        "duckdb_data/client_a/local.db",
        "duckdb_data/client_b/",
        "duckdb_data/client_b/local.db",
        "data/",
        "data/client_a/",
        "data/client_a/raw/",
        "data/client_a/processed/",
        "data/client_b/",
        "data/client_b/raw/",
        "data/client_b/processed/",
        ".env",
        ".secrets.toml",
        ".secrets.baseline",
        ".gitignore",
        ".editorconfig",
        ".pre-commit-config.yaml",
        ".markdownlint-cli2.yaml",
        ".coverage",
        "bitbucket-pipelines.yml",
        "Makefile",
        "Dockerfile",
        "pyproject.toml",
        "uv.lock",
        "alembic.ini",
        "README.md",
        "MANIFEST.in",
    ]

    base_path = Path(root)
    if not base_path.exists():
        base_path.mkdir()
        print(f"Created root: {root}")

    for item in structure:
        path = base_path / item
        if item.endswith("/"):
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            print(f"Created file: {path}")

if __name__ == "__main__":
    create_structure()
