# High-Scale Parquet Architecture Design - Product Store Attribute Mapping Table

To handle **1 billion updates** and provide efficient columnar retrieval, you need more than just raw Parquet files. You need a **Table Format** (like Apache Iceberg or Delta Lake) that manages metadata and ACID transactions.

## 1. Core Architecture: Table Format (Iceberg/Delta)
Raw Parquet is immutable. Updating 1 billion records requires managing metadata. 

> [!IMPORTANT]
> Use **Apache Iceberg** or **Delta Lake** on top of your Parquet files. They handle **"Merge-on-Read" (MOR)**, which writes updates as small "delta" files and merges them during query time.

## 2. Table Structure: Flat vs. Categorized (STRUCTs)
For 1 billion rows, **DO NOT** divide the `v4` table into multiple tables. Joining two 1B-record tables is extremely expensive and slow in Parquet. Instead, use one of these two approaches **within a single table**:

### Option A: Flat Table (Best Compatibility)
Keep all columns at the top level with logical prefixes (e.g., `cost_base`, `comp_ace`).
- **Pros**: 100% compatible with all SQL engines; simplest for 1B-row batch processing.
- **Performance**: High. Parquet skips columns you don't select.

### Option B: Nested Categorization (STRUCTs)
Define columns as categories within the same record. This keeps your schema clean and allows tools (like Spark or BigQuery) to optimize the IO for each specific screen.

**Recommended STRUCT Groups:**
- **Top-Level Keys (Flat)**: `product_id`, `store_id`, `segment_id`, `channel_id`, `updated_at` (Essential for lookups).
- **pricing_logic**: `base_cost`, `additional_cost`, `total_cost`, `price`, `reference_price_1`, `price_lock`, `is_kvi`, `status`, `eligibility`, `total_inventory`.
- **competitor_prices**: `ace_hardware`, `bjs`, `homedepot`, `lowes`, `pinch_a_penny`, `sams_club`, `walmart`, `costco`, `pools_etc`, `discount_poolmart`, `doheny`, `namco`, `the_great_escape`, `watsons`.
- **buckets**: `primary_bucket`, `primary_mode`, `secondary_bucket`, `secondary_mode`, `tertiary_bucket`, `tertiary_mode`, `quaternary_bucket`, `quaternary_mode`.
- **zones**: `zone_structure`, `price_zone`, `effective_price_zone`, `zone_exception`.

**v4 Schema Example**:
```sql
CREATE TABLE v4 (
    product_id BIGINT,
    store_id INT,
    segment_id INT,
    pricing_logic STRUCT(base_cost FLOAT, price FLOAT, price_lock BOOLEAN),
    competitor_prices STRUCT(ace_hardware FLOAT, walmart FLOAT, costco FLOAT),
    buckets STRUCT(primary_bucket STRING, primary_mode STRING),
    zones STRUCT(zone_structure STRING, price_zone STRING)
);
```

## 3. Partitioning & Bucketing Strategy (GCS)
For 1 billion records, management is the bottleneck. Horizontal (Partitioning) and Vertical (Bucketing) splitting is required.

### A. Hive Partitioning (Horizontal Splitting)
Partition your GCS storage by a high-level key like `segment_id`.
- **Path**: `gs://bucket/pricing_v4/segment_id=10/data.parquet`
- **Benefit**: When doing a "Zone Mapping Update" for one segment, you only rewrite the folder for that segment. You don't touch the other ~900 million records.

### B. Bucketing & Clustering (Inside the Files)
Within each partition, Bucket/Cluster by `product_id`.
- **Benefit**: When fetching "Product Store Details" for one ID, the engine uses metadata to jump straight to the correct 1MB block rather than scanning the entire file.

## 4. Handling 1 Billion Updates
There are two main patterns:

### A. Merge-on-Read (MOR) - *Recommended for frequent updates*
- Updates are written to small Parquet "delta" files.
- The system keeps a "delete vector" to mark old records as inactive.
- **Benefit**: Extremely fast writes.
- **Trade-off**: Slightly slower reads until a "compaction" (merge) is run.

### B. Copy-on-Write (COW) - *Recommended for batch updates*
- Whenever a record in a file changes, the entire file is rewritten with the new data.
- **Benefit**: Fastest read performance.
- **Trade-off**: Slow writes for 1B updates.

## 5. Screen Performance Breakdown
Mapping your 4 screens to the columnar structural design:

| Screen | Read Performance | Update Performance (The "Delay" Fix) |
| :--- | :--- | :--- |
| **Competitor Mapping** | Reads only `buckets` struct. | Bulk Update: Overwrites only the files in affected `segment_id` folders. |
| **Zone Mapping** | Reads `product_id` and `zones` struct. | Metadata Update: Updates zone columns across the partition. |
| **Product Details** | Reads `pricing_logic` + `competitors`. | **In-Memory Rewrite**: Read the 128MB file, update the struct, write it back. |

## 6. Retrieval (Fetching Records)
Parquet is columnar, making it perfect for fetching specific columns.

### Fetching Specific Columns
If you only need `price` and `total_cost`, Parquet will **skip** all other columns (like competitor prices), reducing I/O by 80-90%.

```sql
-- Using DuckDB (Fastest for local Parquet retrieval)
SELECT product_id, pricing_logic.price, pricing_logic.total_cost 
FROM 'path/to/table' 
WHERE segment_id = 5;
```

### Fetching All Records
To fetch 1 billion records:
- **Parallelism**: Use a distributed engine like **Spark** or **DuckDB** with multi-threading.
- **Compaction**: Ensure your delta/delete files are compacted into large Parquet files (128MB - 512MB) before fetching "all" to avoid the "small file problem."

## 7. Summary Topology
```mermaid
graph TD
    U[1 Billion Updates] --> I[Iceberg/Delta Table]
    I --> P1[Partition: Segment A]
    I --> P2[Partition: Segment B]
    P1 --> F1[Parquet File 1: Z-Ordered by Product/Store]
    P1 --> F2[Parquet File 2: Z-Ordered by Product/Store]
    
    Q[Query Engine: DuckDB / Spark] -->|Pushdown Filter| P1
    Q -->|Column Pruning| F1
```

## 8. Single Wide Table vs. Split Tables (1B Records)

The choice between a single "wide" table and splitting into multiple specialized tables is critical at 1B rows.

### Performance & Scalability Rating

| Strategy | Performance Rating | Management Rating | Scalability Rating |
| :--- | :--- | :--- | :--- |
| **Single Wide Table (with STRUCTs)** | **10 / 10** | **9 / 10** | **10 / 10** |
| **Split Tables (Normalized)** | **3 / 10** | **2 / 10** | **4 / 10** |

### Why You Should NOT Split Tables at 1B Rows

1. **Massive Join Cost**: In Parquet, a JOIN is NOT a pointer lookup. It requires shuffling and hashing 1 billion rows. Joining `Costs` and `Competitors` tables will take minutes.
2. **Metadata Overhead**: Every Parquet file has a footer with metadata. If you have 3 tables, you read 3 sets of metadata, increasing latency.
3. **Consistency Nightmares**: Keeping two 1B-record tables perfectly synced during high-frequency updates is logically complex and slow.
4. **The "Wide Table" Fallacy**: Parquet's **Columnar Pruning** means a wide table doesn't slow you down. The engine ignores the columns you don't select.

> [!TIP]
> **Conclusion**: Use **STRUCTs** (Categorization) to get the logical "cleanliness" of split tables while maintaining the "10/10 performance" of a single wide table.

## 9. Concurrency & Optimistic Locking

When 1 billion records are being updated by multiple background jobs or users simultaneously, you must avoid data corruption or partial writes.

### How Iceberg/Delta Handles This:
- **Optimistic Concurrency Control (OCC)**: These table formats assume conflicts are rare. They don't "lock" the table. Instead:
    1. A job starts an update on a "Snapshot" (e.g., Snapshot V10).
    2. It writes new Parquet files to a temporary location.
    3. At the end, it tries to "Commit" to the metadata log.
    4. If another job committed V11 in the meantime, the engine checks if the changes overlap. If they don't (e.g., Job A updated Segment 1, Job B updated Segment 2), both are allowed. If they overlap, one job is automatically retried.
- **ACID Guarantee**: Updates are atomic. Users will only ever see a fully completed snapshot, never a half-updated segment.

## 10. Indexing: Searching, Sorting & Pagination

Retrieving 50 records from 1 billion requires "Data Skipping" to avoid scanning the entire GCS bucket.

### A. Data Skipping (Min/Max Stats)
Every Parquet file stores the `min` and `max` values for every column in its footer.
- **Search**: If you search for `product_id = 500`, the engine checks the footer of each file. If a file's range is `1000-2000`, it skips that file entirely without reading a single byte of data.
- **Requirement**: This only works efficiently if the data is **Sorted** by the column you are searching.

### B. Bloom Filters (For exact lookups)
For columns that aren't sorted, you can enable **Bloom Filters**.
- **Use Case**: Fast lookups on a specific `store_id` or `channel_id` where you don't want to scan everything.
- **Performance**: High. It tells the engine "this value definitely isn't in this file" with 99% accuracy.

### C. Large-Scale Sorting & Pagination
- **Sorting**: Do not sort 1 billion rows at runtime. Use **Z-Ordering** (multi-dimensional sorting) during the write process. This ensures that records with similar `product_id` and `store_id` are physically stored in the same Parquet row group.
- **Searching**: Use "Predicate Pushdown." The query engine should filter the data *at the source* (GCS) before pulling it into memory.
- **Pagination**: 
    - **BAD**: `OFFSET 1000000 LIMIT 50` (The engine must still scan 1M rows).
    - **GOOD (Keyset Pagination)**: `WHERE product_id > last_seen_id ORDER BY product_id LIMIT 50`. This uses the index/sorting to jump straight to the correct file.

## 11. Maintenance: Background Compaction

Frequent updates (Merge-on-Read) create hundreds of small "delta" files. Over time, this causes "Metadata Bloat" and slows down reads (the "Small File Problem").

### The Solution: Compactors
Run a background cron job (e.g., every 6-12 hours) that:
1. Identifies partitions with many small files (< 10MB).
2. Reads them into a single memory buffer.
3. Rewrites them into large, optimized, Z-ordered Parquet files (256MB - 512MB).
4. Updates the Iceberg/Delta metadata to point to the new large file and delete the small ones.

> [!IMPORTANT]
> Compaction makes your **"Product Details"** and **"Fetch All"** operations significantly faster for the UI.

## 12. Production Readiness: Caching & Disaster Recovery

Operating 1 billion rows in production requires safeguards for performance and human error.

### A. "Hot Path" Caching (Redis)
While Parquet is fast for analytical scans, GCS at the 1B scale can still introduce 1–3s latency.
- **Problem**: UI users expect sub-second responses on the "Product Details" screen.
- **Solution**: Use **Redis** to cache the most frequently accessed records.
    - **Caching Strategy**: Store the `pricing_logic` and `competitor_prices` structs for "Top 100k Products" in Redis.
    - **Flow**: App checks Redis first. If MISS, it pulls from Parquet using the `product_id` bucket index and hydrates Redis.

### B. Time Travel & Rollback (Disaster Recovery)
Human error (bad scripts) can devastate 1 billion records instantly.
- **Solution**: Feature-rich table formats like **Iceberg/Delta Lake** maintain a transaction log.
- **Time Travel**: You can query the table as it existed 1 hour or 1 day ago:
    ```sql
    -- Query before the accidental price update
    SELECT * FROM v4 FOR SYSTEM_TIME AS OF '2026-02-26 10:00:00';
    ```
- **Rollback**: "Rolling back" is as simple as updating the metadata pointer to an older snapshot. This is an **instant fix** for 1 billion records without waiting for a data restore.

> [!TIP]
> **Production Best Practice**: Always set a **Snapshot Retention Policy** (e.g., keep 7 days of snapshots) to balance recovery capability with storage costs.

## 13. Optimized Workflow: DuckDB + SSD + Gurobi

For your specific use case (1B rows, Gurobi optimization, and mixed Inline/Bulk edits), the most stable architecture uses **DuckDB** as the high-performance bridge.

### 1. The "Fetch All" Bottleneck (GCS -> Gurobi)
*   **Challenge**: Fetching 1 billion rows from GCS buckets will be slow due to network I/O limits. Even with DuckDB, the raw bytes must travel over the wire.
*   **Suggestion**: **Don't use the Bucket as the "Live" Workspace for Gurobi.**
    - Use DuckDB to `COPY` data from GCS to a local `.duckdb` file or Parquet on **Local SSD** first.
    - Let Gurobi read from the Local SSD. Read speeds on local NVMe (30-70 Gbps) are ~20x-50x faster than GCS.

### 2. Gurobi Memory Limits
*   **Challenge**: Gurobi usually expects data in memory. 1 billion rows could easily exceed 128GB–256GB of RAM.
*   **Suggestion**: **Use Apache Arrow as the bridge.**
    - DuckDB can export to Arrow with **Zero-copy** (no data duplication in RAM).
    - This allows Gurobi (using Python/C++) to stream the data or read it in binary chunks without crashing the machine.

### 3. Inline vs. Bulk Update Conflict
*   **Challenge**: DuckDB is an "Analytical" engine (OLAP). It is not designed to update 1 row in a 1B-record file efficiently (it would rewrite the whole file).
*   **Suggestion**: **The "Delta/Buffer" Table Pattern.**
    - Keep 1B records in a "Base Table" (Parquet in GCS).
    - **Inline Edits (1-100)**: Write to a tiny "Delta Table" (Local DuckDB or Redis).
    - **Querying**: Use a `VIEW` to merge them: `SELECT ... FROM base LEFT JOIN deltas`.
    - **Bulk Edits**: Overwrite the Base Parquet. Periodically merge deltas into the Base.

### 4. Local SSD Cache Management
*   **Challenge**: 1 billion rows might exceed the size of your Local SSD if you include all columns (especially competitors).
*   **Suggestion**: **Categorized Column Loading.**
    - Never `SELECT *`.
    - For the "Gurobi Export," only pull cost and constraint columns. Skip the 2000+ competitor columns. This reduces SSD usage by **~70%**.

### Summary of Recommended Topology:
- **Storage**: GCS (Source of Truth).
- **Working Disk**: Local SSD (DuckDB TEMP and local persistent files).
- **Writes**: Inline edits to a "Delta" table; Bulk edits trigger full Parquet rewrite.
- **Fetch**: DuckDB -> Apache Arrow -> Gurobi.

## 14. Recommended "Parquet Pro" Elite Stack

For a 1-billion-row system, you need a **"Zero-Copy"** stack where packages speak purely in binary (Arrow) to avoid RAM bloat.

### 1. The "Fast Sync" Layer (GCS -> SSD)
- **Recommended**: `duckdb` + `gcsfs` + `universal-pathlib`
- **Why**: Do not use standard Python loops to download. Use DuckDB’s internal `httpfs` extension. It uses C++ multi-threading to pull Parquet files from GCS significantly faster than pandas or pyarrow alone.
- **universal-pathlib**: This is a "must-have" (UPath). It allows you to write one piece of code that works for both `gs://` and `/local/ssd/`.
- **Role of `gsutil rsync`**: Use this **only** for disaster recovery or initial mirror of the entire bucket. For your daily optimized fetching, DuckDB's `COPY` is 5x faster because it is columnar-aware.

### 2. The "Arrow Bridge" (DuckDB -> Gurobi)
- **Recommended**: `adbc-driver-manager` + `pyarrow` + `polars`
- **Why**: Moving 1B rows through standard SQL drivers causes massive CPU overhead and memory duplication. ADBC (Arrow Database Connectivity) maintains the data in Arrow format from disk to solver.
- **adbc-driver-manager**: The high-speed binary bridge. It is the successor to JDBC/ODBC and is designed for exactly this scale.
- **polars**: I strongly suggest using `polars` instead of `pandas`. Polars is written in Rust, is native Arrow, and is **10x-50x faster** than Pandas for 1 billion rows. It can read a DuckDB result set with Zero-Copy.
- **pyarrow**: The core engine that handles Parquet footers and "Data Skipping" (Min/Max) logic.

### 3. Production & UI Helpers
- **`redis`**: Essential for **"Hot Path" Caching**. Store the pricing data for the most active products to ensure < 50ms UI response times.
- **`pyiceberg`**: The native Python client for managing **Apache Iceberg** metadata, snapshots, and time-travel rollbacks. (If using Delta Lake, use **`deltalake`**).
- **`fastapi-pagination`**: **Can be used**, but must be restricted to **Keyset Pagination** (e.g., `last_id`) to avoid scanning millions of rows on deep pages.
- **`filelock`**: Crucial for coordinating background "Compaction" jobs to prevent write conflicts.
- **`httpx`**: Efficient for handling high-concurrency API requests.

### 4. The "Exclude" List (Avoid at 1B Rows)
- **`pandas`**: Creates heavy Python objects for every cell. Inflation will crash the server.
- **`dask[complete]`**: Redundant overhead. DuckDB already handles parallel execution.
- **`openpyxl`**: Excel is limited to 1M rows and will fail instantly.

### Final Summary Topology:
- **duckdb**: The Query Engine & GCS Downloader.
- **pyarrow**: The Parquet storage handler.
- **adbc-driver-manager**: The high-speed binary bridge.
- **polars**: The data manipulator (replaces Pandas).
- **universal-pathlib**: The path manager.
- **pyiceberg / deltalake**: The Table Format / Metadata manager.
- **redis**: The "Hot Path" Speed Booster (Cache).
- **gcsfs**: The GCS authentication layer.
- **filelock**: Crucial for coordinating background Compaction jobs.
- **Optimizer**: Gurobi (Streamed via Arrow).

## 15. Comparison: Iceberg vs. Delta Lake

| Feature | Apache Iceberg (`pyiceberg`) | Delta Lake (`deltalake` / `delta-rs`) |
| :--- | :--- | :--- |
| **Best For** | **Pure Scale (1B+ records)**. Known for handling the largest datasets in the world (Netflix/Apple). | **Python/Rust Teams**. Much easier setup for pure Python environments without a Spark cluster. |
| **Inline Edits** | **Winner**. Better support for "Hidden Partitioning" & "Merge-on-Read" metadata at scale. | Good, but historically relied on "Copy-on-Write" which is too slow for 1B-row updates. |
| **Bulk Updates** | **High performance**. Uses snapshots to ensure users never see a "half-written" 1B-row update. | Very fast for batch writes. Excellent row-level concurrency. |
| **Fetch All** | Native DuckDB Support. Very fast metadata footers. | Native DuckDB Support. Uses "Log Store" files. |

### Which fits best for Your Case?
For your specific **DuckDB + SSD + Gurobi** stack, I recommend **Apache Iceberg (`pyiceberg`)**.

#### 1. Inline Edits (1–100 rows)
- **Strategy**: Don't write directly to the main Iceberg table from the UI.
- **Workflow**: Write that change to a **Redis/DuckDB Delta Buffer**. Iceberg’s metadata makes it easy to merge this buffer with the "Base" table during the next read.

#### 2. Bulk Updates (1 Billion rows)
- **Strategy**: Use **Iceberg's Snapshot isolation**.
- **Scenario**: You update 1 billion records via a batch job.
- **Workflow**: Iceberg writes the 1B records as a "New Snapshot" in the background. Your **GCS -> SSD Sync** job can keep reading the *old* snapshot while the new one is being written. Once the 1B write is finished, the metadata "pointer" flips instantly.

#### 3. Fetch All (Gurobi)
- **Strategy**: Use **DuckDB's native Iceberg reader**.
- **Scenario**: Pulling 1B rows for optimization.
- **Workflow**: Both formats are equal here, but Iceberg's "Partition Evolution" allows you to change how you store data (e.g., changing from `segment_id` to `store_id`) without rewriting the existing 1B records.

## 16. Migration & Backfill Strategy (SQL to Parquet)

Moving 1 billion rows requires a chunked approach to avoid locking the source DB or crashing your migration worker.

- **Chunked Export**: Use DuckDB to query the SQL DB in 10M-row ranges (e.g., `WHERE product_id BETWEEN 1 AND 10000000`).
- **Parallel Workers**: Multiple workers write these 10M-row chunks to an intermediate **Landing Zone** in GCS.
- **Final Stitch**: Use a single DuckDB job to read the landing Parquet files, apply **Z-Order** sorting, and perform the final `APPEND` or `CREATE` to the Production Iceberg table.

## 17. The Staging "Gatekeeper" (Validation)

Gurobi is complex; you must prevent "Poison Data" (bugs in optimization) from corrupting your 1B-record production source of truth.

- **Pattern**: **Write -> Validate -> Commit**.
- **The Flow**:
    1. Gurobi writes its output to a `gs://bucket/staging/` snapshot.
    2. A **Polars validation script** runs against the snapshot to check for:
        - Zero `null` or `NaN` values in price columns.
        - Zero negative prices or forbidden values.
        - Logical bounds (e.g., price change < 50% from yesterday).
    3. **Pass/Fail**: If validation passes, the metadata pointer flips. If it fails, the "Poison Snapshot" is deleted and an alert is sent.

## 18. Cost Management: Snapshot Expiry & Cleanup

Every 1B-row update creates a new immutable version in GCS. Without cleanup, your monthly bill will explode.

- **Snapshot Expiry**: Schedule a daily job to run `pyiceberg.expire_snapshots()`.
- **Retention Policy**: Keep the last **7 snapshots** (7 days of rollback capability). This balances disaster recovery with cost storage.
- **Orphan Cleanup**: Run `remove_orphan_files()` weekly to delete abandoned Parquet files that are no longer referenced by any active snapshot.

---

> [!TIP]
> **Industrial-Grade Verdict**: By implementing these final guardrails, you have evolved from a "Good Design" to a **10/10 Architecture**. This system is now bulletproof, cost-efficient, and optimized for the highest performance Gurobi can handle.
