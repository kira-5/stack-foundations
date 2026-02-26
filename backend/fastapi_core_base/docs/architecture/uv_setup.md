rm -rf .venv .venv-fastapi-core uv.lock pyproject.toml requirements.txt

1. Pin and Initialize
Run these from inside your fastapi_core_base folder:

# Pin the specific version
uv python pin 3.14.2

# Initialize the uv project (creates pyproject.toml)
uv init

2. Create your "Core" Environment
# Create the venv with your preferred naming convention
uv venv .venv-fastapi-core - option 1
uv venv --prompt fastapi-core - option 2

# Activate it
source .venv-fastapi-core/bin/activate


3. The "Master Stack" Add Command

uv add --group data polars pyarrow


  


How to generate category-wise requirements.txt
Since you want the filenames to match your categories for your teammate, you can run these uv commands:


# 1. Export the Core Web dependencies
uv export --no-dev -o requirements-web.txt

# 2. Export specific categories
uv export --group data -o requirements-data.txt
uv export --group database -o requirements-db.txt
uv export --group gcp -o requirements-gcp.txt
uv export --group qa -o requirements-qa.txt

uv export --all-groups --format requirements-txt --output-file requirements.txt
# 3. Export everything for a full environment sync (without hashes for simplicity)
uv export --all-groups --no-hashes -o requirements.txt

#### 1. Lock and Sync
1. uv sync : Include dependencies only
2. uv sync --all-groups : Include all dependencies and groups
3. uv sync --group database --group qa : Include specific groups
4. uv sync --frozen --no-dev : prevents uv from accidentally updating your uv.lock
5. uv sync --no-dev : Include dependencies only

### 2. The "Ultimate" Export Script

# Export the Core (dependencies only)
uv export --no-dev -o requirements-web.txt

# Export everything into one master file (no hashes for readability)
uv export --all-groups --no-hashes -o requirements.txt

# Export everything into one master file (with hashes for readability)
uv export --all-groups --format requirements-txt --output-file requirements.txt

## CLean up

1. pre-commit install --> uv run pre-commit install
2. pre-commit run --all-files --> uv run pre-commit run --all-files
3. pre-commit gc --> uv run pre-commit gc