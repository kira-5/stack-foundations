"""Database Constants for the Base Pricing system.

This file acts as the source of truth for all schemas, tables, and database routines
across Postgres, DuckDB, Spark, and Parquet.
"""

from typing import Literal
from src.shared.configuration.config import settings


class BaseConstant:
    """Base class providing introspection for constant classes."""

    @classmethod
    def get_all(cls) -> list[str]:
        """Returns all string constant values defined in this class (including properties)."""
        values = []
        # Get class attributes
        for attr in dir(cls):
            if attr.startswith("_") or callable(getattr(cls, attr)):
                continue
            val = getattr(cls, attr)
            if isinstance(val, str):
                values.append(val)

        # Get properties (for dynamic constants)
        for attr, value in cls.__dict__.items():
            if isinstance(value, property):
                val = getattr(cls(), attr)
                if isinstance(val, str):
                    values.append(val)
        return list(set(values))


class Schemas(BaseConstant):
    """Database Schemas across systems."""
    GLOBAL = "global"
    PUBLIC = "public"

    @property
    def TENANT_APP_SCHEMA(self) -> str:
        """Dynamically fetch the tenant's app schema from config."""
        return settings.get("TENANT_APP_SCHEMA", "base_pricing")

    # Medallion Architecture Layers (Analytical Lake)
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class Tables(BaseConstant):
    """Namespaced database tables standardized with the BP_ prefix."""

    class METADATA(BaseConstant):
        USER_MASTER = "user_master"
        BP_TABLE_METADATA = "bp_table_metadata"
        BP_MASTER_DATA = "bp_master_data"
        BP_KPI_METRICS_CONFIG = "bp_kpi_metrics_config"

    class MASTERS(BaseConstant):
        BP_PRODUCT_MASTER = "bp_product_master"
        BP_STORE_MASTER = "bp_store_master"

    class HIERARCHY(BaseConstant):
        BP_PRODUCT_HIERARCHY_LEVEL = "bp_product_hierarchy_level"
        BP_STORE_HIERARCHY_LEVEL = "bp_store_hierarchy_level"
        BP_GROUPING_TYPE_LEVEL = "bp_grouping_type_level"
        BP_PRODUCT_GROUP = "bp_product_group"
        BP_PRODUCT_GROUP_HIERARCHY = "bp_product_group_hierarchy"
        BP_STORE_GROUP = "bp_store_group"
        BP_STORE_GROUP_HIERARCHY = "bp_store_group_hierarchy"

    class MAPPINGS(BaseConstant):
        BP_ZONES = "bp_zones"
        BP_ZONE_STRUCTURE = "bp_zone_structure"
        BP_STORE_ZONE_MAPPING = "bp_store_zone_mapping"
        BP_PRODUCT_STORE_MAPPING = "bp_product_store_mapping"
        BP_STORE_CURRENT_MAPPING = "bp_store_current_mapping"
        BP_STORE_INITIAL_MAPPING = "bp_store_initial_mapping"
        BP_PRODUCT_STORE_INITIAL_MAPPING = "bp_product_store_initial_mapping"
        BP_PRODUCT_STORE_CURRENT_MAPPING = "bp_product_store_current_mapping"

    class ATTRIBUTES(BaseConstant):
        BP_PRODUCT_ATTRIBUTES_INITIAL = "bp_product_attributes_initial"
        BP_PRODUCT_ATTRIBUTES_CURRENT = "bp_product_attributes_current"
        BP_PRODUCT_ATTRIBUTES_METADATA = "bp_product_attributes_metadata"
        BP_PRODUCT_ATTRIBUTES_MAPPING = "bp_product_attributes_mapping"
        BP_STORE_ATTRIBUTES_METADATA = "bp_store_attributes_metadata"
        BP_STORE_ATTRIBUTES_MAPPING = "bp_store_attributes_mapping"
        BP_PRODUCT_STORE_ATTRIBUTES_METADATA = "bp_product_store_attributes_metadata"
        BP_PRODUCT_STORE_ATTRIBUTES_MAPPING = "bp_product_store_attributes_mapping_v4"
        BP_COMPETITOR_ATTRIBUTES_METADATA = "bp_competitor_attributes_metadata"
        BP_PRODUCT_STORE_COMPETITOR_PRICES = "bp_product_store_competitor_prices"

    class RULES(BaseConstant):
        BP_RULE_TYPES = "bp_rule_types"
        BP_RULE_MASTER = "bp_rule_master"
        BP_RULE_DETAILS = "bp_rule_details"
        BP_RULE_ATTRIBUTES_METADATA = "bp_rule_attributes_metadata"
        BP_RULE_PRODUCTS_MAPPING = "bp_rule_products_mapping"
        BP_RULE_STORES_MAPPING = "bp_rule_stores_mapping"
        BP_RULE_SEGMENTS_MAPPING = "bp_rule_segments_mapping"
        BP_RULE_HIERARCHY_MAPPING = "bp_rule_hierarchy_mapping"
        BP_STRATEGY_MASTER = "bp_strategy_master"
        BP_STRATEGY_RULES_MAPPING = "bp_strategy_rules_mapping"
        BP_STRATEGY_INPUT_TARGETS = "bp_strategy_input_targets"
        BP_STRATEGY_PRODUCTS = "bp_strategy_products"
        BP_STRATEGY_STORES = "bp_strategy_stores"
        BP_STRATEGY_PRODUCTS_STORES = "bp_strategy_products_stores"
        BP_STRATEGY_PRODUCT_GROUPS = "bp_strategy_product_groups"
        BP_STRATEGY_STORE_GROUPS = "bp_strategy_store_groups"
        BP_STRATEGY_SEGMENTS = "bp_strategy_segments"
        BP_STRATEGY_PRODUCT_STORES_DETAILS = "bp_strategy_product_stores_details"
        BP_STRATEGY_APPROVAL_SNAPSHOT = "bp_strategy_approval_snapshot"

    class RECOMMENDATIONS(BaseConstant):
        BP_PRICE_RECO_CURRENT = "bp_price_reco_current"
        BP_PRICE_RECO_CURRENT_V2 = "bp_price_reco_current_v2"
        BP_PRICE_RECO_IA = "bp_price_reco_ia"
        BP_PRICE_RECO_IA_V2 = "bp_price_reco_ia_v2"
        BP_PRICE_RECO_FINALIZED = "bp_price_reco_finalized"
        BP_PRICE_RECO_FINALIZED_V2 = "bp_price_reco_finalized_v2"
        BP_OPTIMIZATION_METRICS = "bp_optimization_metrics"
        BP_KPI_METRICS = "bp_decision_dashboard_kpi_metrics"
        BP_BASELINE_METRICS = "bp_baseline_metrics"

    class TRANSACTIONS(BaseConstant):
        BP_TRANSACTION_DATA_WEEKLY = "bp_transaction_data_weekly"
        BP_TRANSACTION_DATA_DAILY = "bp_transaction_data_daily"
        BP_SIMULATION_WEEK = "bp_simulation_week"
        BP_SIMULATION_WEEK_ALT = "bp_simulation_week_alt"
        BP_SIMULATION_DAY_SPLIT_RATIO = "bp_simulation_day_split_ratio"
        BP_SIMULATION_STORE_SPLIT_RATIO = "bp_simulation_store_split_ratio"
        BP_LATEST_PRODUCT_INVENTORY_AGG = "bp_latest_product_inventory_agg"
        BP_LATEST_STORE_INVENTORY_AGG = "bp_latest_store_inventory_agg"

    # Backward compatibility and "One List" access
    @classmethod
    def get_all(cls) -> list[str]:
        all_tables = []
        # Need to handle nested classes explicitly
        for attr_name in dir(cls):
            attr_value = getattr(cls, attr_name)
            if isinstance(attr_value, type) and issubclass(attr_value, BaseConstant) and attr_value != BaseConstant:
                all_tables.extend(attr_value.get_all())
        return list(set(all_tables))


class RouteStrategy:
    """Engine Selection Logic for analytical tables."""

    # Heavy tables that can use Spark/Ray, but default to DuckDB until scaled up.
    HEAVY_TABLES = {
        Tables.TRANSACTIONS.BP_TRANSACTION_DATA_DAILY,
        Tables.TRANSACTIONS.BP_TRANSACTION_DATA_WEEKLY,
        Tables.METADATA.BP_MASTER_DATA,
    }

    @classmethod
    def get_engine(
        cls, table_name: str, use_heavy_engine: Literal["spark", "ray", None] = None
    ) -> Literal["spark", "ray", "duckdb", "postgres"]:
        """Decide the engine. Default to DuckDB for all bp_ prefixed tables."""
        if use_heavy_engine and table_name in cls.HEAVY_TABLES:
            return use_heavy_engine

        if table_name.startswith("bp_"):
            return "duckdb"

        return "postgres"


class Functions(BaseConstant):
    """Database Functions."""
    FN_REFRESH_MATERIALIZED_VIEW = "fn_refresh_materialized_view"
    FN_FETCH_PRODUCT_GROUPS = "fn_fetch_product_groups"
    FN_MANAGE_STRATEGY_RULES_MAPPING_PARTITIONS = "fn_manage_strategy_rules_mapping_partitions"
    FN_REFRESH_STORE_GROUP_HIERARCHY_MV = "fn_refresh_store_group_hierarchy_mv"
    FN_UPDATE_ZONE_STRUCTURE_AND_ZONE = "fn_update_zone_structure_and_zone"
    FN_REFRESH_AGGREGATED_ATTRIBUTES_MV = "fn_refresh_aggregated_attributes_mv"
    FN_REFRESH_PRODUCT_GROUP_HIERARCHY_MV = "fn_refresh_product_group_hierarchy_mv"
    FN_FETCH_BASELINE_SALES_DATA = "fn_fetch_baseline_sales_data"


class StoredProcedures(BaseConstant):
    """Stored Procedures."""
    SP_CREATE_PARTITION_FOR_PGS_OR_SGS = "sp_create_partition_for_pgs_or_sgs"
    SP_UPDATE_PRODUCT_FINAL_PRICES = "sp_update_product_final_prices"
    SP_CREATE_BP_PRODUCT_ATTRIBUTES_MAPPING = "sp_create_bp_product_attributes_mapping"
    SP_PRICE_CHANGE_DRIVER_DATA = "sp_price_change_driver_data"


class MaterializedViews(BaseConstant):
    """Materialized Views."""
    MV_PRODUCT_GROUP_HIERARCHY_AGG_DATA = "mv_product_group_hierarchy_agg_data"
    MV_STORE_GROUP_HIERARCHY_AGG_DATA = "mv_store_group_hierarchy_agg_data"
    MV_BP_PRODUCT_GROUP_ATTRIBUTES_AGGREGATED = "mv_bp_product_group_attributes_aggregated"
    MV_PRICE_CHANGE_DRIVER_DATA = "mv_price_change_driver_data"


class Columns(BaseConstant):
    """Database Columns."""
    PRODUCT_ID = "product_id"
    STORE_ID = "store_id"
    STRATEGY_ID = "strategy_id"


# --- Unified Export ---
__all__ = [
    "Schemas",
    "Tables",
    "RouteStrategy",
    "Functions",
    "StoredProcedures",
    "MaterializedViews",
    "Columns",
]
