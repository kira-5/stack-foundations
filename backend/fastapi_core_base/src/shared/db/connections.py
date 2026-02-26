"""
src/shared/db/connections.py
============================
Compatibility shim — re-exports PostgresConnection from its canonical location
(src.shared.db.core.connection_manager) under the legacy import path used by
startup_event.py and other modules.

Usage:
    from src.shared.db.connections import PostgresConnection
"""

from src.shared.db.core.connection_manager import PostgresConnection

__all__ = ["PostgresConnection"]
