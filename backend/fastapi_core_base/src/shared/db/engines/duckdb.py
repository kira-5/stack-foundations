import duckdb
from src.shared.db.core.path_resolver import PathResolver
from src.shared.logging import get_logger

logger = get_logger(name="duckdb_engine")

def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a connection to the tenant-specific DuckDB database.

    If the file doesn't exist, DuckDB creates it automatically at the resolved path.
    """
    db_path = PathResolver.get_duckdb_path()
    logger.debug(f"Connecting to DuckDB at: {db_path}")

    # Connect to the private DuckDB file for the client
    return duckdb.connect(database=str(db_path))


def attach_postgres(con: duckdb.DuckDBPyConnection):
    """
    Attaches the Postgres main database to the current DuckDB session.
    Enables federated queries using the 'pg' prefix.
    """
    from src.shared.db.engines.adbc import get_adbc_connection_url
    url = get_adbc_connection_url()

    # Install and load the postgres extension for federation
    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")

    # Attach Postgres as 'pg'
    con.execute(f"ATTACH '{url}' AS pg (TYPE postgres);")
    logger.info("Federated Link: Attached Postgres as 'pg'")
