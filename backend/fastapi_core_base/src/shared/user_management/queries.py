APP_VERSION_QUERY = """
    select
        remarks
    from
        meta_schema.tb_app_sub_master
    where name='Appversion'
"""

SYNC_USER_ACCESS_HIERARCHY_QUERY = """
    SELECT base_pricing.sync_user_access_hierarchy_flat({user_code});
"""

HIERARCHICAL_ACCESS_QUERY = """
WITH app_info AS (
    -- Get application_code for Base Pricing
    SELECT application_code
    FROM global.application_master
    WHERE name = 'Base Pricing'
    LIMIT 1
),
user_acl AS (
    -- Get acl_codes for the user_id
    SELECT DISTINCT acl_code
    FROM global.user_access_hierarchy_mapping
    WHERE user_code = {user_code}
),
user_role AS (
    -- Get role_code for the user
    SELECT role_code
    FROM global.acl_master
    WHERE acl_code IN (SELECT acl_code FROM user_acl)
      AND application_code = (SELECT application_code FROM app_info)
      AND status = true
    ORDER BY role_code
    LIMIT 1
),
role_modules AS (
    -- Get all modules accessible by the user's role
    SELECT DISTINCT UNNEST(module_code::int[]) AS module_code
    FROM global.role_action_module_mapping
    WHERE role_code = (SELECT role_code FROM user_role)
),
screen_modules AS (
    -- Get all screens for Base Pricing with their modules
    SELECT
        COALESCE(NULLIF(sm.label, ''), sm.description) AS grouping_key,
        sm.label,
        sm.description,
        sm.screen_name,
        sm.screen_code,
        mm.module_code,
        mm.module_name,
        CASE WHEN rm.module_code IS NOT NULL THEN true ELSE false END AS is_allowed
    FROM global.module_master mm
    LEFT JOIN global.screen_master sm ON sm.screen_code = mm.screen_code
    LEFT JOIN role_modules rm ON mm.module_code = rm.module_code
    WHERE mm.application_code = (SELECT application_code FROM app_info)
),
label_counts AS (
    -- Count how many modules each grouping_key (label) has
    SELECT
        grouping_key,
        label,
        COUNT(DISTINCT module_code) AS module_count,
        BOOL_OR(is_allowed) AS parent_is_allowed,
        MIN(description) AS parent_description,
        MIN(screen_name) AS parent_screen_name
    FROM screen_modules
    GROUP BY grouping_key, label
),
result_data AS (
    SELECT
        sm.grouping_key,
        sm.label,
        lc.module_count,
        lc.parent_is_allowed,
        lc.parent_description,
        lc.parent_screen_name,
        sm.module_code,
        sm.description AS child_description,
        sm.screen_name AS child_screen_name,
        sm.is_allowed AS child_is_allowed
    FROM screen_modules sm
    JOIN label_counts lc ON sm.grouping_key = lc.grouping_key
)
-- Build the final hierarchical JSON structure
SELECT JSON_AGG(
    JSON_BUILD_OBJECT(
        'label', COALESCE(label, parent_description),
        'screen_name', parent_screen_name,
        'is_allowed', parent_is_allowed,
        'children', children
    )
) AS result
FROM (
    SELECT
        label,
        parent_description,
        parent_screen_name,
        parent_is_allowed,
        CASE
            WHEN module_count = 1 THEN '[]'::json
            ELSE (
                SELECT JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'label', child_description,
                        'screen_name', child_screen_name,
                        'is_allowed', child_is_allowed
                    )
                )
                FROM result_data rd2
                WHERE rd2.grouping_key = rd1.grouping_key
            )
        END AS children
    FROM (
        SELECT DISTINCT ON (grouping_key)
            grouping_key,
            label,
            module_count,
            parent_is_allowed,
            parent_description,
            parent_screen_name
        FROM result_data
    ) rd1
) final_structure;
"""

MODULE_ACTIONS_QUERY = """
WITH app_info AS (
    -- Step 1: Get application_code from application_name
    SELECT application_code
    FROM global.application_master
    WHERE name = 'Base Pricing'
    LIMIT 1
),
user_acl AS (
    -- Step 2: Get acl_codes for the user_id
    SELECT DISTINCT acl_code
    FROM global.user_access_hierarchy_mapping
    WHERE user_code = {user_code}
),
user_role AS (
    -- Step 3: Get role_code for the user's acl_codes and application_code
    -- If multiple, select first
    SELECT role_code
    FROM global.acl_master
    WHERE acl_code IN (SELECT acl_code FROM user_acl)
      AND application_code = (SELECT application_code FROM app_info)
      AND status = true
    ORDER BY role_code
    LIMIT 1
),
all_modules AS (
    -- Step 4: Get all modules for the application_code
    SELECT
        mm.module_code,
        mm.module_name AS module
    FROM global.module_master mm
    WHERE mm.application_code = (SELECT application_code FROM app_info)
),
role_actions AS (
    -- Step 5: Get actions from role_action_module_mapping
    SELECT
        UNNEST(module_code::int[]) AS module_code,
        action_code
    FROM global.role_action_module_mapping
    WHERE role_code = (SELECT role_code FROM user_role)
),
module_actions_aggregated AS (
    -- Step 6: Aggregate action names for each module
    SELECT
        ra.module_code,
        ARRAY_AGG(am.action ORDER BY am.action_code) AS action_names
    FROM role_actions ra
    LEFT JOIN LATERAL UNNEST(ra.action_code::int[]) AS action_code_unnested ON true
    LEFT JOIN global.action_master am ON action_code_unnested = am.action_code
    GROUP BY ra.module_code
)
-- Final result combining modules with their action names
SELECT
    am.module,
    COALESCE(maa.action_names, ARRAY[]::text[]) AS actions,
    CASE
        WHEN maa.module_code IS NOT NULL THEN true
        ELSE false
    END AS has_access
FROM all_modules am
LEFT JOIN module_actions_aggregated maa ON am.module_code = maa.module_code
ORDER BY am.module_code;
"""
