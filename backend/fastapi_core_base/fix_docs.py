import re

files_to_update = [
    "docs/technical/db_system_specification.md",
    "docs/technical/query_guide.md"
]

replacements = {
    r"src/shared/db/connections\.py#72-88": r"src/shared/db/engines/postgres.py",
    r"src/shared/db/connections\.py#39-196": r"src/shared/db/core/connection_manager.py",
    r"src/shared/db/connections\.py#89-106": r"src/shared/db/engines/postgres.py",
    r"src/shared/db/async_query_executor\.py#51-317": r"src/shared/db/execution_lanes/transactional.py",
    r"src/shared/db/async_query_executor\.py#152-179": r"src/shared/db/execution_lanes/transactional.py",
    r"src/shared/db/async_query_executor\.py#223-230": r"src/shared/db/core/session_guard.py",
    r"src/shared/db/async_query_executor\.py#120-151": r"src/shared/db/execution_lanes/transactional.py",
    r"src/shared/db/async_query_executor\.py#180-197": r"src/shared/db/execution_lanes/batch.py",
    r"src/shared/db/async_query_executor\.py#238-264": r"src/shared/db/execution_lanes/transactional.py",
    r"src/shared/db/async_query_executor\.py#291-317": r"src/shared/db/execution_lanes/bulk.py",
    r"src/shared/db/mixin\.py#7-17": r"src/shared/db/schema/mixins.py",
    r"src/shared/db/mixin\.py#10-13": r"src/shared/db/schema/mixins.py",
    r"src/shared/db/mixin\.py#14-17": r"src/shared/db/schema/mixins.py",
    r"src/shared/db/constants\.py": r"src/shared/db/schema/constants.py",
    r"src/shared/db/connections\.py": r"src/shared/db/core/connection_manager.py",
    r"src/shared/db/async_query_executor\.py": r"src/shared/db/execution_lanes/transactional.py"
}

for filepath in files_to_update:
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = re.sub(old, new, content)
        
    with open(filepath, 'w') as f:
        f.write(content)

print("Docs updated.")
