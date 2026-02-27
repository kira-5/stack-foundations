# 🔀 Dynamic Routing & Multi-Tenant Storage Guide

This document explains the "Smart Router" and the multi-tenant storage architecture for **DuckDB**, **Parquet**, **Spark**, and **Ray**.

---

## 1. Dynamic Engine Detection ("The Smart Router")

The system uses the `QueryAnalyzer` to automatically route SQL queries to the most efficient engine without requiring manual configuration from the developer.

### Logic Flow & Rules
1.  **Postgres (The OLTP Foundation)**:
    *   **Trigger**: Use of **schema-qualified names** (e.g., `leslies_base_pricing.bp_orders`).
    *   **Rule**: If the schema matches the tenant's dynamic `TENANT_APP_SCHEMA` or global schemas (`public`), it routes to Postgres.
    *   **Global Tables**: Tables like `users` or `tenants` always route here.

2.  **DuckDB (The Performance Accelerator & Default)**:
    *   **Trigger**: Use of **flat table names** starting with `bp_` (e.g., `SELECT * FROM bp_prices`).
    *   **Strategy**: This is the **default analytical engine** even for high-volume tables. It provides fast, local-speed access to tenant data without needing a cluster.
    *   **Local Prefixes**: `local_` or `temp_` also trigger DuckDB.

3.  **Spark & Ray (The Scale-Up Engines)**:
    *   **Trigger**: Explicit manual hints (`/* engine: spark */` or `/* engine: ray */`).
    *   **Tables**: The `HEAVY_TABLES` list in `constants.py` tracks eligible tables like `bp_transaction_data`.
    *   **Action**: Routes to the distributed execution lanes when scale exceeds local limits.

4.  **Federated (The Hybrid Mode)**:
    *   **Trigger**: Any query that joins tables from different engines (e.g., `users` [Postgres] + `bp_prices` [DuckDB]).
    *   **Action**: The system automatically bridges the data across engines.

---

## 2. Multi-Tenant Storage Architecture

Data is saved and organized in a strictly isolated, per-tenant structure.

### Root Directory Structure
The `Makefile` initializes the base directories:
- `duckdb_data/`: Local analytical files.
- `parquet_data/`: Large-scale data lake files.

### A. DuckDB Storage
Each tenant has a private directory containing a single `local.db` file.
- **Path**: `duckdb_data/{tenant_id}/local.db`
- **Creation**: Triggered automatically on the first query for a new tenant.

### B. Parquet Storage (Medallion Architecture)
Parquet data follows the industry-standard "Medallion" pattern to ensure data quality:
- **Raw (Bronze)**: `parquet_data/{tenant_id}/raw/` - Raw ingestion files.
- **Silver (Silver)**: `parquet_data/{tenant_id}/silver/` - Cleaned, normalized data.
- **Gold (Gold)**: `parquet_data/{tenant_id}/gold/` - Joined, business-ready tables for final consumption.

### C. Complete Filesystem View (Medallion Architecture)
Here is the complete **Medallion Architecture** filesystem view for both systems, showing how your tables (`bp_store_master`, `bp_product_master`) and the joined **Gold** results are organized:

#### 🏠 DuckDB (The Performance Layer)
Everything for the tenant is physically in **one file**, but logically separated into the Gold view.

```text
/Users/abhisheksingh/Documents/Development/stack-foundations/
└── duckdb_data/
    └── lesliespool/
        └── local.db  <-- [INSIDE THIS FILE]:
            ├── bp_store_master   (Table)
            ├── bp_product_master (Table)
            └── bp_final_recos    (GOLD VIEW/TABLE)
```

#### 🌲 Spark / Ray / Parquet (The Storage Lake)
Everything is physically separated into **Folders** following the Medallion stages.

```text
/Users/abhisheksingh/Documents/Development/stack-foundations/
└── parquet_data/
    └── lesliespool/
        ├── bronze/
        │   ├── bp_store_master.parquet   <-- Raw
        │   └── bp_product_master.parquet <-- Raw
        ├── silver/
        │   ├── bp_store_master/          <-- Cleaned (Folder)
        │   │   ├── _SUCCESS
        │   │   └── part-0000.parquet
        │   └── bp_product_master/        <-- Cleaned (Folder)
        │       ├── _SUCCESS
        │       └── part-0000.parquet
        └── gold/
            └── bp_final_recos/           <-- JOINED RESULT (Folder)
                ├── _SUCCESS
                ├── part-0000.parquet     <-- (Store + Product Join)
                └── part-0001.parquet
```

---

## 3. Developer Best Practices

### The "One List" Rule
You do not need to manage different tables for different systems. Use the unified names in `src/shared/db/constants.py`.

### Tenant Context
Always wrap analytical operations in a `TenantContext`:
```python
with TenantContext.tenant_scope("lesliespool"):
    # This automatically routes to leslies_base_pricing (Postgres)
    # or duckdb_data/lesliespool/local.db (DuckDB)
    df = await database_service.execute_analytical_query("SELECT * FROM bp_prices")
```

### Manual Engine Hints
If you need to force an engine for debugging, use a SQL comment:
```sql
-- This bypasses logic and goes straight to Postgres
SELECT /* engine: postgres */ * FROM bp_prices;
```
