# **FastAPI Project Package Recommendations**

### 1. LINTING, FORMATTING & QUALITY ASSURANCE

- **ruff**: Handles **Linting** (replacing flake8), **Import Sorting** (replacing isort), and **Formatting** (replacing black).
- **mypy**: Enforces type safety—crucial for Pydantic/FastAPI reliability.
- **pytest (+ pytest-cov)**: The standard for testing and coverage reporting.
- **pre-commit**: The automated gatekeeper that runs these tools before every commit.

### 2. ENVIRONMENT & CONFIGURATION MANAGEMENT

- **python-dotenv:** The standard for local `.env` and secret management.
- **Dynaconf:** Powerful multi-environment support (Dev, Staging, Prod).
- **toml:** The modern format for structured, readable configuration files.

### 3. WEB FRAMEWORK & ASGI INFRASTRUCTURE

- **fastapi**: The core web framework.
- **uvicorn**: The production-grade server required to host FastAPI.
- **uvloop**: **(The Speed Multiplier)** A drop-in replacement for the standard `asyncio` loop that makes the server significantly faster on Linux/GCP.
- **python-multipart**: Required for handling file uploads and OAuth2 forms.
- **slowapi**: Provides rate limiting to protect your expensive Dask/DuckDB resources.

### 4. DATA VALIDATION & SERIALIZATION

- **pydantic**: The engine for all request/response validation.
- **pydantic-settings**: Modern environment management.
- **orjson**: A high-speed replacement for standard JSON (Rust-backed).

### 5. ASYNCHRONOUS I/O & CONCURRENCY

- **asyncio:** The foundation for all non-blocking I/O operations in your stack.

### 6. HTTP CLIENTS & NETWORKING

- **httpx**: The modern, async alternative to `requests` for external API calls.

### 7. GOOGLE CLOUD PLATFORM (GCP) INTEGRATION

- **google-cloud-secret-manager:** Mandatory for fetching production secrets securely.
- **google-cloud-logging:** Connects your application logs to GCP Stackdriver.
- **functions-framework**: Only needed for your Cloud Functions to ensure they run correctly in a local development environment.

### 8. DATABASE & ORM LAYER

- **sqlalchemy:** The primary ORM for your PostgreSQL transactional data.
- **asyncpg:** The fastest async driver for PostgreSQL/SQLAlchemy.
- **duckdb:** Your engine for lightning-fast analytical queries on large data./our analytical engine for running SQL on Parquet/local data.

### 9. DATA MANIPULATION & ANALYSIS (The Parquet Stack)

- **polars**: Your high-speed engine for medium-sized data and Parquet processing.
- **dask**: For parallelizing massive datasets that exceed machine memory.
- **pyarrow**: The mandatory engine for Parquet, DuckDB, and Dask interoperability.
- **pandas**: The primary tool for data wrangling and final formatting.
- **universal_pathlib**: **(The Path Interface)** Allows you to use standard `pathlib` syntax to interact with GCP buckets, local files, and S3 interchangeably.
- **gcsfs**: The "Cloud Bridge" that allows Dask and Polars to stream Parquet files directly from `gs://` buckets.
- **adbc-driver-manager**: The core manager for high-speed Arrow-based database connectivity.
- **adbc-driver-postgresql**: The specific driver that lets DuckDB/Polars pull from Postgres without the "Python Tax."
- **openpyxl**: For reading and generating Excel reports.
- **filelock**: Prevents data corruption during parallel writes in a Dask/multi-process environment.

### 10. OBSERVABILITY & MONITORING

- **ddtrace:** For Datadog APM tracing and performance bottleneck identification.

### 11. TASK QUEUES, REDIS & CACHING

- **redis**: High-speed in-memory cache for API responses and metadata.
- **rq**: For lightweight background tasks like sending emails or alerts.
- **fastapi-cache2**: The professional standard for adding Redis caching to your API routes.

### 12. CUSTOM LIBRARIES

- **fastapi-pagination**: Standardizes the "request/response contract" and provides high-performance cursor-based paging.
- **pip-tools:** To generate and lock deterministic `requirements.txt` files.
- **uv**: **(Replaces pip-tools)** Your single tool for package syncing, locking, and virtual environment management.

### 13. PROJECT UTILITIES

- **mtputils**: Your internal shared library.