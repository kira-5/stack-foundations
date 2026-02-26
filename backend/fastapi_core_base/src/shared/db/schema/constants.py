# backend/app/db/constants.py


class Schemas:
    """Database Schemas."""

    GLOBAL_SCHEMA = "global"
    PUBLIC_SCHEMA = "public"
    BASE_PRICING_SCHEMA = "base_pricing"

    def get_schema(self):
        """Returns a list of all schemas."""
        return [self.GLOBAL_SCHEMA, self.PUBLIC_SCHEMA, self.BASE_PRICING_SCHEMA]

    def get_schema_count(self):
        """Returns the number of schemas defined."""
        return len(self.get_schema())


class Tables:
    """Database Tables."""

    BP_COMPETITOR_ATTRIBUTES_METADATA = "bp_competitor_attributes_metadata"
    BP_PRICE_BUCKET_DETAILS = "bp_price_bucket_details"
    BP_PRODUCT_HIERARCHY_LEVEL = "bp_product_hierarchy_level"
    BP_STORE_HIERARCHY_LEVEL = "bp_store_hierarchy_level"
    BP_GROUPING_TYPE_LEVEL = "bp_grouping_type_level"
    BP_ZONES = "bp_zones"
    BP_ZONE_STRUCTURE = "bp_zone_structure"
    BP_STORE_ZONE_MAPPING = "bp_store_zone_mapping"
    BP_EXCEPTION_TYPES = "bp_exception_types"
    BP_EXCEPTION_DETAILS = "bp_exception_details"
    BP_MASTER_DATA = "bp_master_data"
    BP_PRODUCT_MASTER = "bp_product_master"
    BP_PRODUCT_ATTRIBUTES_INITIAL = "bp_product_attributes_initial"
    BP_PRODUCT_ATTRIBUTES_CURRENT = "bp_product_attributes_current"
    BP_STORE_MASTER = "bp_store_master"
    BP_PRODUCT_GROUP = "bp_product_group"
    BP_PRODUCT_GROUP_HIERARCHY = "bp_product_group_hierarchy"
    BP_PRODUCT_GROUP_ATTRIBUTES = "bp_product_group_attributes"
    BP_PRODUCT_GROUP_PRODUCT_MAPPING = "bp_product_group_product_mapping"
    BP_PRODUCT_HIERARCHY_CID_MAPPING = "bp_product_hierarchy_cid_mapping"
    BP_PRODUCT_PRODUCT_GROUP_MAPPING = "bp_product_group_product_mapping"
    BP_STORE_GROUP = "bp_store_group"
    BP_STORE_GROUP_HIERARCHY = "bp_store_group_hierarchy"
    BP_STORE_GROUP_STORE_MAPPING = "bp_store_group_store_mapping"
    BP_PRODUCT_STORE_ATTRIBUTES_METADATA = "bp_product_store_attributes_metadata"
    BP_PRODUCT_STORE_ATTRIBUTES_MAPPING = "bp_product_store_attributes_mapping_v4"
    BP_PRODUCT_STORE_INITIAL_MAPPING = "bp_product_store_initial_mapping"
    BP_PRODUCT_STORE_CURRENT_MAPPING = "bp_product_store_current_mapping"
    BP_PRODUCT_STORE_MAPPING = "bp_product_store_mapping"
    BP_PRODUCT_STORE_COMPETITOR_PRICES = "bp_product_store_competitor_prices"
    BP_LATEST_PRODUCT_INVENTORY_AGG = "bp_latest_product_inventory_agg"
    USER_MASTER = "user_master"
    BP_LATEST_STORE_INVENTORY_AGG = "bp_latest_store_inventory_agg"
    BP_STORE_ATTRIBUTES_METADATA = "bp_store_attributes_metadata"
    BP_STORE_CURRENT_MAPPING = "bp_store_current_mapping"
    BP_STORE_INITIAL_MAPPING = "bp_store_initial_mapping"
    BP_PRODUCT_ATTRIBUTES_MAPPING = "bp_product_attributes_mapping"
    BP_STORE_ATTRIBUTES_MAPPING = "bp_store_attributes_mapping"
    BP_STORE_GROUP_ATTRIBUTES = "bp_store_group_attributes"
    BP_PRODUCT_ATTRIBUTES_METADATA = "bp_product_attributes_metadata"
    BP_RULE_TYPES = "bp_rule_types"
    BP_RULE_MASTER = "bp_rule_master"
    BP_RULE_DETAILS = "bp_rule_details"
    BP_RULE_DETAILS = "bp_rule_details"
    BP_RULE_ATTRIBUTES_METADATA = "bp_rule_attributes_metadata"
    BP_RULE_PRODUCTS_MAPPING = "bp_rule_products_mapping"
    BP_RULE_STORES_MAPPING = "bp_rule_stores_mapping"
    BP_RULE_SEGMENTS_MAPPING = "bp_rule_segments_mapping"
    BP_RULE_HIERARCHY_MAPPING = "bp_rule_hierarchy_mapping"
    BP_RULE_PRODUCT_GROUP = "bp_rule_product_group"
    BP_RULE_STORE_GROUP = "bp_rule_store_group"
    BP_COMPARISON_TYPES = "bp_comparison_types"
    BP_SCREEN_HIERARCHIES = "bp_screen_hierarchies"
    BP_BOOKMARK_FILTERS = "bp_bookmark_filters"
    BP_STRATEGY_MASTER = "bp_strategy_master"
    BP_TABLE_METADATA = "bp_table_metadata"
    BP_TABLE_VIEW_TEMPLATE_MAPPING = "bp_table_view_template_mapping"
    BP_VIEW_TYPE_METADATA = "bp_view_type_metadata"
    BP_REPORTING_ATTRIBUTES_METADATA = "bp_reporting_attributes_metadata"
    BP_TEMPLATE_ATTRIBUTES_MAPPING = "bp_template_attributes_mapping"
    BP_TEMPLATES_METADATA = "bp_templates_metadata"
    BP_STRATEGY_RULES_MAPPING = "bp_strategy_rules_mapping"
    BP_STRATEGY_INPUT_TARGETS = "bp_strategy_input_targets"
    BP_STRATEGY_PRODUCTS = "bp_strategy_products"
    BP_STRATEGY_STORES = "bp_strategy_stores"
    BP_STRATEGY_PRODUCTS_STORES = "bp_strategy_products_stores"
    BP_OPTIMIZATION_METRICS = "bp_optimization_metrics"
    BP_STRATEGY_PRODUCT_GROUPS = "bp_strategy_product_groups"
    BP_STRATEGY_STORE_GROUPS = "bp_strategy_store_groups"
    BP_STRATEGY_PRODUCT_STORES_DETAILS = "bp_strategy_product_stores_details"
    BP_PRICE_RECO_CURRENT = "bp_price_reco_current"
    BP_PRICE_RECO_CURRENT_V2 = "bp_price_reco_current_v2"
    BP_PRICE_RECO_IA = "bp_price_reco_ia"
    BP_PRICE_RECO_IA_V2 = "bp_price_reco_ia_v2"
    BP_PRICE_RECO_FINALIZED = "bp_price_reco_finalized"
    BP_PRICE_RECO_CURRENT_V2 = "bp_price_reco_current_v2"
    BP_PRICE_RECO_IA_V2 = "bp_price_reco_ia_v2"
    BP_PRICE_RECO_FINALIZED_V2 = "bp_price_reco_finalized_v2"
    BP_SCOPE_LEVEL = "bp_scope_level"
    BP_STRATEGY_STATUS_LEVEL = "bp_strategy_status_level"
    BP_STRATEGY_PRICE_RECO_GRID_DATA_PRODUCT_STORE = "bp_strategy_price_reco_grid_data_product_store"
    BP_STRATEGY_PRICE_RECO_GRID_DATA_LINE_GROUP_STORE = "bp_strategy_price_reco_grid_data_line_group_store"
    BP_STRATEGY_PRICE_RECO_GRID_DATA_PRODUCT_PRICEZONE = "bp_strategy_price_reco_grid_data_product_pricezone"
    BP_STRATEGY_PRICE_RECO_GRID_DATA_LINE_GROUP_PRICEZONE = "bp_strategy_price_reco_grid_data_line_group_pricezone"
    BP_PRICE_CHANGE_REASON = "bp_price_change_reason"
    BP_CLOUD_TASKS = "bp_cloud_tasks"
    BP_STRATEGY_PRICE_RECOMMENDATION_PREVIEW = "bp_strategy_price_recommendation_preview"
    BP_STRATEGY_PERFORMANCE_METRICS_MONTHLY = "bp_strategy_performance_metrics_monthly"
    BP_KPI_METRICS = "bp_decision_dashboard_kpi_metrics"
    BP_STRATEGY_EDITED_PRICES = "bp_strategy_edited_prices"
    BP_TRANSACTION_DATA_WEEKLY = "bp_transaction_data_weekly"
    BP_TRANSACTION_DATA_DAILY = "bp_transaction_data_daily"
    BP_UNLOGGED_COMBINATIONS = "bp_unlogged_combinations"
    BP_SIMULATION_WEEK = "bp_simulation_week"
    BP_LAST_APPROVED_WEEK_LEVEL_SIMULATION = "bp_last_approved_week_level_simulation"
    BP_CUSTOMER_SEGMENT_MASTER = "bp_customer_segment_master"
    BP_CUSTOMER_SEGMENT_CONFIG = "bp_customer_segment_config"
    BP_STRATEGY_SEGMENTS = "bp_strategy_segments"
    BP_PRODUCT_CUSTOMER_SEGMENT_PRICES = "bp_product_customer_segment_prices"
    BP_STRATEGY_RULE_SEGMENT_CLUSTER_MAPPING = "bp_strategy_rule_segment_cluster_mapping"
    BP_SIMULATION_DAY_SPLIT_RATIO = "bp_simulation_day_split_ratio"
    BP_SIMULATION_STORE_SPLIT_RATIO = "bp_simulation_store_split_ratio"
    # New promotion-related tables
    BP_SIMULATION_PROMO_WEEK = "bp_simulation_promo_week"
    BP_SIMULATION_STORE_SPLIT_RATIO_KVI = "bp_simulation_store_split_ratio_kvi"
    BP_SIMULATION_DAY_SPLIT_RATIO_KVI = "bp_simulation_day_split_ratio_kvi"
    BP_SIMULATION_WEEK_ALT = "bp_simulation_week_alt"
    BP_STRATEGY_CHANNEL_METRICS_SUMMARY = "bp_strategy_channel_metrics_summary"
    BP_STRATEGY_CURRENT_STAGE_LEVEL = "bp_strategy_current_stage_level"
    BP_ONGOING_STRATEGY_ACTION_STATUS_TRANSITIONS = "bp_ongoing_strategy_action_status_transitions"
    BP_UPCOMING_STRATEGY_ACTION_STATUS_TRANSITIONS = "bp_upcoming_strategy_action_status_transitions"
    BP_ACTIONS = "bp_actions"
    BP_SYNC_STATUS = "bp_sync_status"
    BP_BUCKET_CONFIG = "bp_bucket_config"
    BP_PRODUCT_STORE_ATTRIBUTES_MAPPING_V2 = "bp_product_store_attributes_mapping_v4"
    BP_REGROUPING_CHANGE_LOG = "bp_regrouping_change_log"
    BP_BASELINE_METRICS = "bp_baseline_metrics"
    BP_KPI_METRICS_CONFIG = "bp_kpi_metrics_config"
    BP_STRATEGY_APPROVAL_SNAPSHOT = "bp_strategy_approval_snapshot"

    def get_table(self):
        """Returns a list of all tables."""
        return [
            self.BP_PRODUCT_HIERARCHY_LEVEL,
            self.BP_STORE_HIERARCHY_LEVEL,
            self.BP_GROUPING_TYPE_LEVEL,
            # self.BP_ZONE_MASTER,
            self.BP_ZONE_STRUCTURE,
            # self.BP_ZONE_MASTER_STORE_MAPPING,
            self.BP_EXCEPTION_TYPES,
            self.BP_EXCEPTION_DETAILS,
            self.BP_MASTER_DATA,
            self.BP_PRODUCT_MASTER,
            self.BP_PRODUCT_ATTRIBUTES_INITIAL,
            self.BP_PRODUCT_ATTRIBUTES_CURRENT,
            self.BP_STORE_MASTER,
            self.BP_PRODUCT_GROUP,
            self.BP_PRODUCT_GROUP_HIERARCHY,
            self.BP_PRODUCT_HIERARCHY_CID_MAPPING,
            self.BP_PRODUCT_PRODUCT_GROUP_MAPPING,
            self.BP_PRODUCT_STORE_MAPPING,
            self.BP_STORE_GROUP,
            self.BP_STORE_GROUP_HIERARCHY,
            self.BP_STORE_GROUP_STORE_MAPPING,
            self.BP_TABLE_METADATA,
            self.BP_TABLE_VIEW_TEMPLATE_MAPPING,
            self.BP_VIEW_TYPE_METADATA,
            # self.BP_PRODUCT_STORE_ATTRIBUTES,
            self.BP_PRODUCT_STORE_COMPETITOR_PRICES,
            self.BP_PRODUCT_STORE_ATTRIBUTES_METADATA,
            self.BP_PRODUCT_STORE_ATTRIBUTES_MAPPING,
            self.BP_PRODUCT_STORE_INITIAL_MAPPING,
            self.BP_PRODUCT_STORE_CURRENT_MAPPING,
            self.BP_PRODUCT_STORE_COMPETITOR_PRICES,
            self.BP_PRODUCT_STORE_ATTRIBUTES_METADATA,
            self.BP_LATEST_PRODUCT_INVENTORY_AGG,
            self.USER_MASTER,
            self.BP_LATEST_STORE_INVENTORY_AGG,
            self.BP_PRODUCT_ATTRIBUTES_METADATA,
            self.BP_PRODUCT_ATTRIBUTES_MAPPING,
            self.BP_STRATEGY_MASTER,
            self.BP_STRATEGY_RULES_MAPPING,
            self.BP_STRATEGY_INPUT_TARGETS,
            self.BP_OPTIMIZATION_METRICS,
            self.BP_PRICE_RECO_CURRENT,
            self.BP_PRICE_RECO_CURRENT_COPY,
            self.BP_RULE_ATTRIBUTES_METADATA,
            self.BP_STRATEGY_PERFORMANCE_METRICS_MONTHLY,
            self.BP_KPI_METRICS,
            self.BP_TRANSACTION_DATA_WEEKLY,
            self.BP_SIMULATION_WEEK,
            self.BP_LAST_APPROVED_WEEK_LEVEL_SIMULATION,
            self.BP_SIMULATION_DAY_SPLIT_RATIO,
            self.BP_SIMULATION_STORE_SPLIT_RATIO,
            self.BP_SIMULATION_STORE_SPLIT_RATIO_KVI,
            # self.RULES TABLES
            self.BP_RULE_TYPES,
            self.BP_RULE_MASTER,
            self.BP_RULE_DETAILS,
            self.BP_RULE_ATTRIBUTES_METADATA,
            self.BP_RULE_PRODUCTS_MAPPING,
            self.BP_RULE_STORES_MAPPING,
            self.BP_RULE_SEGMENTS_MAPPING,
            self.BP_RULE_HIERARCHY_MAPPING,
            self.BP_COMPARISON_TYPES,
            self.BP_SCREEN_HIERARCHIES,
            self.BP_BASELINE_METRICS,
            self.BP_KPI_METRICS_CONFIG,
            self.BP_PRICE_RECO_CURRENT_V2,
            self.BP_PRICE_RECO_IA_V2,
            self.BP_PRICE_RECO_FINALIZED_V2,
            self.BP_STRATEGY_APPROVAL_SNAPSHOT,
        ]

    def get_table_count(self):
        """Returns the number of tables defined."""
        return len(self.get_table())


class Functions:
    """Database Functions."""

    FN_REFRESH_MATERIALIZED_VIEW = "fn_refresh_materialized_view"
    FN_FETCH_PRODUCT_GROUPS = "fn_fetch_product_groups"
    FN_MANAGE_STRATEGY_RULES_MAPPING_PARTITIONS = "fn_manage_strategy_rules_mapping_partitions"
    FN_REFRESH_STORE_GROUP_HIERARCHY_MV = "fn_refresh_store_group_hierarchy_mv"
    FN_UPDATE_ZONE_STRUCTURE_AND_ZONE = "fn_update_zone_structure_and_zone"
    FN_REFRESH_AGGREGATED_ATTRIBUTES_MV = "fn_refresh_aggregated_attributes_mv"
    FN_REFRESH_PRODUCT_GROUP_HIERARCHY_MV = "fn_refresh_product_group_hierarchy_mv"
    FN_FETCH_BASELINE_SALES_DATA = "fn_fetch_baseline_sales_data"

    def get_function(self):
        """Returns a list of all functions."""
        return [
            self.FN_REFRESH_MATERIALIZED_VIEW,
            self.FN_FETCH_PRODUCT_GROUPS,
            self.FN_MANAGE_STRATEGY_RULES_MAPPING_PARTITIONS,
            self.FN_REFRESH_STORE_GROUP_HIERARCHY_MV,
            self.FN_FETCH_BASELINE_SALES_DATA,
        ]

    def get_function_count(self):
        """Returns the number of functions defined."""
        return len(self.get_function())


class StoredProcedures:
    """Stored Procedures."""

    SP_CREATE_PARTITION_FOR_PGS_OR_SGS = "sp_create_partition_for_pgs_or_sgs"
    SP_UPDATE_PRODUCT_FINAL_PRICES = "sp_update_product_final_prices"
    SP_CREATE_BP_PRODUCT_ATTRIBUTES_MAPPING = "sp_create_bp_product_attributes_mapping"
    SP_PRICE_CHANGE_DRIVER_DATA = "sp_price_change_driver_data"

    def get_stored_procedure(self):
        """Returns a list of all stored procedures."""
        return [
            self.SP_CREATE_PARTITION_FOR_PGS_OR_SGS,
            self.SP_UPDATE_PRODUCT_FINAL_PRICES,
            self.SP_CREATE_BP_PRODUCT_ATTRIBUTES_MAPPING,
        ]

    def get_stored_procedure_count(self):
        """Returns the number of stored procedures defined."""
        return len(self.get_stored_procedure())


class MaterializedViews:
    """Materialized Views."""

    MV_PRODUCT_GROUP_HIERARCHY_AGG_DATA = "mv_product_group_hierarchy_agg_data"
    MV_STORE_GROUP_HIERARCHY_AGG_DATA = "mv_store_group_hierarchy_agg_data"
    MV_BP_PRODUCT_GROUP_ATTRIBUTES_AGGREGATED = "mv_bp_product_group_attributes_aggregated"
    MV_EXCEPTION_REPORT_RULE_LIST = "mv_exception_report_rule_list"
    MV_EXCEPTION_REPORT_SUMMARY_CARDS = "mv_exception_report_summary_cards"
    MV_COMPETITOR_POSITIONING_SUMMARY_CARDS = "mv_competitor_positioning_summary_cards"
    MV_COMPETITOR_POSITIONING_HEATMAP = "mv_competitor_positioning_heatmap"
    MV_COMPETITOR_ANALYSIS = "mv_competitor_analysis"
    MV_COMPETITOR_POSITIONING_CURRENT_CPI = "mv_competitor_positioning_current_cpi"
    MV_COMPETITOR_POSITIONING_HEATMAP_DETAILS = "mv_competitor_positioning_heatmap_details"
    MV_RULE_PRODUCTS_HIERARCHY_AGG_DATA = "mv_rule_products_hierarchy_agg_data"
    MV_RULE_STORES_HIERARCHY_AGG_DATA = "mv_rule_stores_hierarchy_agg_data"
    MV_STRATEGY_PRODUCTS_HIERARCHY_AGG_DATA = "mv_strategy_products_hierarchy_agg_data"
    MV_STRATEGY_STORES_HIERARCHY_AGG_DATA = "mv_strategy_stores_hierarchy_agg_data"
    MV_BP_STORE_GROUP_ATTRIBUTES_AGGREGATED = "mv_bp_store_group_attributes_aggregated"
    MV_COMPETITOR_ATTRIBUTES_MASTER = "mv_competitor_attributes_master"
    MV_AGGREGATED_ATTRIBUTES_MASTER = "mv_aggregated_attributes_master"
    MV_EXCEPTION_REPORT_EXCEPTION_LIST = "mv_exception_report_exception_list"
    MV_PRICE_CHANGE_DRIVER_DATA = "mv_price_change_driver_data"

    def get_materialized_view(self):
        """Returns a list of all materialized views."""
        return [
            self.MV_PRODUCT_GROUP_HIERARCHY_AGG_DATA,
            self.MV_STORE_GROUP_HIERARCHY_AGG_DATA,
            self.MV_EXCEPTION_REPORT_RULE_LIST,
            self.MV_COMPETITOR_POSITIONING_SUMMARY_CARDS,
            self.MV_COMPETITOR_POSITIONING_HEATMAP,
            self.MV_COMPETITOR_ANALYSIS,
            self.MV_COMPETITOR_POSITIONING_CURRENT_CPI,
            self.MV_COMPETITOR_POSITIONING_HEATMAP_DETAILS,
            self.MV_RULE_PRODUCTS_HIERARCHY_AGG_DATA,
            self.MV_RULE_STORES_HIERARCHY_AGG_DATA,
            self.MV_STRATEGY_PRODUCTS_HIERARCHY_AGG_DATA,
            self.MV_STRATEGY_STORES_HIERARCHY_AGG_DATA,
            self.MV_BP_STORE_GROUP_ATTRIBUTES_AGGREGATED,
            self.MV_EXCEPTION_REPORT_EXCEPTION_LIST,
        ]

    def get_materialized_view_count(self):
        """Returns the number of materialized views defined."""
        return len(self.get_materialized_view())


class Columns:
    """Database Columns."""

    PRODUCT_ID = "product_id"
    STORE_ID = "store_id"
    PRICE_ZONE_NAME = "price_zone_name"
    LINE_GROUP = "line_group"
    ATTRIBUTE_NAME = "attribute_name"
    OPT_LEVEL_BINS = "opt_level_bins"
    SOURCE = "source"
    PRICE_CHANGE_PRESERVED = "price_change_preserved"
    PRICE_CHANGE_DATA = "price_change_data"
    STRATEGY_ID = "strategy_id"
    RULE_TYPES_APPLIED = "rule_types_applied"
    RULE_EXCEPTIONS_FINALIZED = "rule_exceptions_finalized"
    PRICE_CHANGE_REASON = "price_change_reason"
    IS_RULES_REFRESH = "is_rules_refresh"
    PRODUCT_HIERARCHY_LEVEL_ID = "product_hierarchy_level_id"
    STORE_HIERARCHY_LEVEL_ID = "store_hierarchy_level_id"


class FilterDefaults:
    """Default values for filters."""

    STRATEGY_DATE_RANGE_PAST_MONTHS = 3
    STRATEGY_DATE_RANGE_FUTURE_MONTHS = 3


# Unified export for easy access
__all__ = [
    "Schemas",
    "Tables",
    "Functions",
    "StoredProcedures",
    "MaterializedViews",
    "Columns",
    "FilterDefaults",
]
