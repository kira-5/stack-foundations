# 📖 Database Query Usage Guide

This guide explains the four supported ways to execute queries using the `database_service`.

### 🏁 Driver Usage Summary

| Method | Underlying Driver | Purpose |
| :--- | :--- | :--- |
| **[execute_transactional_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/async_query_executor.py#238-263)** | [asyncpg](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/connections.py#72-88) or `SQLAlchemy` | Standard API / CRUD |
| **[execute_analytical_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/bulk_query_executor.py#8-31)** | **ADBC** (via Polars) | Fast **READ** (Massive data) |
| **[execute_batch_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/async_query_executor.py#264-289)** | [asyncpg](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/connections.py#72-88) | Fast **WRITE** (1k - 10k rows) |
| **[execute_bulk_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/services/database_service.py#180-196)** | [asyncpg](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/connections.py#72-88) | Ultra-Fast **WRITE** (100k+ rows) |

---

## 1. Raw SQL (No Parameters)
Best for simple queries that don't depend on user input.

```python
from src.shared.services.database_service import database_service

# Simply pass the SQL string
results = await database_service.execute_transactional_query(
    "SELECT * FROM users LIMIT 10"
)
```

---

## 2. Named Parameters (Recommended ⭐)
The safest and most readable way. Use `:key` in your SQL and pass a dictionary.

```python
# Named parameters are safer against SQL injection
results = await database_service.execute_transactional_query(
    "SELECT * FROM users WHERE email = :email AND status = :status",
    params={
        "email": "user@example.com",
        "status": "active"
    }
)
```
> [!TIP]
> **Why use this?** It prevents bugs caused by parameter order and makes your SQL much easier to read.

---

## 3. Positional Parameters
Useful if you prefer standard PostgreSQL `$1, $2` syntax or have a simple list of values.

```python
# Values are mapped to $1, $2, etc., based on their index in the list
results = await database_service.execute_transactional_query(
    "SELECT * FROM users WHERE id = $1 AND role = $2",
    params=[123, "admin"]
)
```

---

## 💡 Internal Magic
- **asyncpg**: If you use named parameters with the [asyncpg](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/connections.py#72-88) driver, the system automatically converts `:key` to `$n` for you behind the scenes.
- **SQLAlchemy**: If you use the [sqlalchemy](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/connections.py#89-106) driver, it handles these mappings natively.
- **Logging**: All queries are logged with their parameters (masked if sensitive) to help with debugging.

## 📦 Response Formats by Operation

The library returns data based on whether the query is a "Data Fetch" or an "Action".

| Operation | Typical SQL | Success Response | Data Format |
| :--- | :--- | :--- | :--- |
| **GET** | `SELECT ...` | List of Rows | `[{ "id": 1, ... }]` |
| **POST** | `INSERT ... RETURNING` | List of Rows | `[{ "id": 99, ... }]` |
| **POST** | `INSERT ...` | Success Status | `{"status": 200, "message": "success"}` |
| **UPDATE** | `UPDATE ...` | Success Status | `{"status": 200, "message": "success"}` |
| **DELETE** | `DELETE ...` | Success Status | `{"status": 200, "message": "success"}` |

---

## 🚨 Success vs. Failure

### Success
Any response that returns without raising an exception is a success.
- For **SELECTs**, if no data is found, it returns an **empty list** `[]`.
- For **Actions**, if it succeeds, it returns the **status object**.

### Failure (Modern Approach)
Any scenario like a syntax error, unique constraint violation, or timeout will **raise an Exception**.

> [!IMPORTANT]
> **Why raise an exception?** 
> Earlier versions of this library returned an error dictionary (e.g., `{"status": "error", ...}`). This was brittle because it forced you to check the result type every time.
> Raising an exception is "louder" and safer: it stops execution immediately so you don't accidentally process an error result as real data.

### ⚠️ Legacy vs. Modern Handling

| Feature | Legacy Approach (Deprecated) | Modern Approach (Current) |
| :--- | :--- | :--- |
| **Error Format** | Returns `{"status": "error", ...}` | **Raises Exception** |
| **Response Type** | Mixed (List or Dict) | Consistent (List or Success Obj) |
| **Safety** | Silent (Easy to miss errors) | Loud (Execution stops on error) |
| **FastAPI** | Manual 400/500 mapping | Automatic 500 mapping |

---

### Recommended Usage Pattern
```python
try:
    results = await database_service.execute_transactional_query(
        "UPDATE users SET status = :status WHERE id = :id",
        params={"status": "active", "id": 123}
    )
    # results == {"status": 200, "message": "success"}
except Exception as e:
    # Handle error
    print(f"Update failed: {e}")

---

## 4. Analytical Data Exports (ADBC 🚀)

For fetching massive datasets (1,000,000+ rows) for reports or Polars analysis, use `execute_analytical_query`.

### How it works:
It uses the **ADBC** (Arrow Database Connectivity) driver to pull data directly into an **Apache Arrow** buffer. This avoids the massive "Python Tax" of creating million of Python objects, making it **10x-50x faster** for large analytical payloads.

```python
from src.shared.services.database_service import database_service

# Fetches 1M rows nearly instantly with zero memory spikes
df = database_service.execute_analytical_query(
    "SELECT * FROM massive_analytical_table"
)

# Returns a Polars DataFrame
print(df.head())
df.write_parquet("data_export.parquet")
```

### Streaming Massive Files via FastAPI
If you need to let a user download a million-row report, combine **ADBC** with FastAPI's `StreamingResponse`:

```python
from fastapi.responses import StreamingResponse
import io

@app.get("/export")
def export_data():
    # 1. Fetch instantly using ADBC (Lane 2)
    df = database_service.execute_analytical_query("SELECT * FROM massive_table")
    
    # 2. Convert to CSV buffer
    buffer = io.BytesIO()
    df.write_csv(buffer)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})
```


### Summary: When to use which?

| If you want to... | Use `execute_transactional_query` (asyncpg) | Use `execute_analytical_query` (ADBC) |
| :--- | :---: | :---: |
| Show 50 rows on a website | ✅ **Perfect** | Overkill |
| Fetch 1 row for a login | ✅ **Perfect** | Overkill |
| **Download a 100MB Report** | ❌ Slow (OOM risk) | ✅ **Best** |
| **Load data into a DataFrame** | ❌ Slow | ✅ **Best** |
| Run background data sync | ❌ Slow | ✅ **Best** |

> [!IMPORTANT]
> **Use ADBC whenever you are touching more than ~10,000 rows at once.** It will keep your FastAPI server much "cooler" and faster.

> [!TIP]
> Use **Lane 1 (`execute_transactional_query`)** for snappy API responses and **Lane 2 (`execute_analytical_query`)** for heavy data lift, calculation, and analytics.
```

---

## 5. High-Speed Bulk Writes (Ingestion ⚡)

For saving data into the database, we provide two "Fast Lanes" depending on your data volume.

### Lane A: [execute_batch_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/async_query_executor.py#264-289) (1,000 - 10,000 rows)
Uses `executemany` to send data as a single stream. Much faster than a loop. Supports `ON CONFLICT`.

```python
# $1, $2 are standard Postgres placeholders
query = "INSERT INTO users (name, email) VALUES ($1, $2) ON CONFLICT DO NOTHING"
data = [
    ("Alice", "alice@example.com"),
    ("Bob", "bob@example.com"),
    # ... 5,000 more rows
]

await database_service.execute_batch_query(query, data)
```

### Lane B: [execute_bulk_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/services/database_service.py#180-196) (100,000+ rows)
The **Fastest possible way** to load data. Uses the binary COPY protocol.

```python
# Destination table, column order, and raw tuple data
await database_service.execute_bulk_query(
    table_name="massive_logs",
    columns=["timestamp", "level", "message"],
    data=[
        ("2023-01-01 00:00:00", "INFO", "System start"),
        # ... 1,000,000 more rows
    ]
)
```

### Comparison: Which Ingestion to use?

| Volume | Method | Speed | Flexibility |
| :--- | :--- | :---: | :--- |
| **1 - 100 rows** | [execute_transactional_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/async_query_executor.py#238-263) | 🟢 Good | Full SQL (Named Params) |
| **1k - 10k rows** | [execute_batch_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/db/async_query_executor.py#264-289) | 🟡 Very Fast | Standard SQL ($1, $2) |
| **100k+ rows** | [execute_bulk_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/services/database_service.py#180-196) | 🔴 Ultra Fast | Binary (Table direct) |

> [!IMPORTANT]
> Use **[execute_bulk_query](file:///Users/abhisheksingh/Documents/Development/stack-foundations/backend/fastapi_core_base/src/shared/services/database_service.py#180-196)** for massive imports. It is roughly **100x faster** than standard per-row inserts.
