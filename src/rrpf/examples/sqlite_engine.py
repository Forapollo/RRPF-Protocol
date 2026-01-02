import sqlite3
from collections.abc import Mapping
from typing import Any

from rrpf.fulfillment.engine import FulfillmentEngine, FulfillmentResult
from rrpf.schemas.provenance import QueryStats
from rrpf.schemas.request import RRPRequest


class SQLiteResult:
    """Concrete implementation of FulfillmentResult."""

    def __init__(
        self,
        data: Mapping[str, Any],
        query_stats: Mapping[str, QueryStats],
    ) -> None:
        self._data = data
        self._query_stats = query_stats

    @property
    def data(self) -> Mapping[str, Any]:
        return self._data

    @property
    def query_stats(self) -> Mapping[str, QueryStats]:
        return self._query_stats


class SQLiteEngine(FulfillmentEngine):
    """
    A minimal SQLite-backed engine.
    Demonstrates real data interaction with an existing database.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.conn = connection
        # Ensure we can access columns by name
        self.conn.row_factory = sqlite3.Row

    def fulfill(self, request: RRPRequest) -> FulfillmentResult:
        data: dict[str, Any] = {}
        stats: dict[str, QueryStats] = {}
        cursor = self.conn.cursor()

        # 1. Handle Tables
        for table in request.data.tables:
            section_key = f"table:{table.table}"
            table_name = table.table
            limit = table.limit

            try:
                # Note: This is vulnerable to SQL injection if table_name is untrusted.
                # In a real engine, validate table_name against a schema or allow-list.
                # For this example, we assume trusted input.
                # We use double quotes for table name to handle special characters,
                # but validation is still recommended.
                query = f'SELECT * FROM "{table_name}" ORDER BY rowid ASC LIMIT ?'
                cursor.execute(query, (limit,))
                rows = [dict(row) for row in cursor.fetchall()]

                data[section_key] = {"rows": rows}
                stats[section_key] = QueryStats(rows=len(rows), groups=1)
            except sqlite3.Error:
                # If table doesn't exist or other error, we omit the section.
                # The runner will mark it as missing.
                pass

        # 2. Handle Events
        # This minimal engine does not support event queries as they require
        # schema assumptions (e.g. a specific 'events' table or filtering).

        return SQLiteResult(data=data, query_stats=stats)
