from pathlib import Path

from src.shared.db.core.tenant_context import TenantContext

# Base directories (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
DUCKDB_BASE_DIR = PROJECT_ROOT / "duckdb_data"
PARQUET_BASE_DIR = PROJECT_ROOT / "parquet_data"

class PathResolver:
    """Resolves filesystem paths based on the current tenant context."""

    @staticmethod
    def get_duckdb_path() -> Path:
        """Resolves the path to the current tenant's DuckDB file."""
        tenant_id = TenantContext.get_tenant_id()
        if not tenant_id:
            # Fallback for system-wide or non-tenant specific operations
            return DUCKDB_BASE_DIR / "global.db"
        
        tenant_dir = DUCKDB_BASE_DIR / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir / "local.db"

    @staticmethod
    def get_parquet_dir(stage: str = "raw") -> Path:
        """Resolves the path to the current tenant's Parquet directory.
        
        Args:
            stage: The stage of the data (raw, silver, gold).
        """
        tenant_id = TenantContext.get_tenant_id()
        if not tenant_id:
            return PARQUET_BASE_DIR / "global" / stage
        
        tenant_dir = PARQUET_BASE_DIR / tenant_id / stage
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir
