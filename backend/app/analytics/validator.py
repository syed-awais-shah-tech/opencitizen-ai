"""Strict query validation and security policy enforcement for DuckDB execution."""

import re
from app.analytics.exceptions import (
    SQLValidationError,
    TableNotAllowedError,
)

# Forbidden SQL keywords that indicate DDL, DML, or administrative commands
FORBIDDEN_KEYWORDS = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "CREATE",
    "ATTACH",
    "DETACH",
    "COPY",
    "EXPORT",
    "IMPORT",
    "PRAGMA",
    "CALL",
    "EXEC",
    "EXECUTE",
    "INSTALL",
    "LOAD",
    "SET",
    "RESET",
    "GRANT",
    "REVOKE",
    "COMMIT",
    "ROLLBACK",
    "TRANSACTION",
}

# Forbidden function names that access the host filesystem or system catalog
FORBIDDEN_FUNCTIONS = {
    "read_csv",
    "read_csv_auto",
    "read_parquet",
    "read_json",
    "read_json_auto",
    "write_csv",
    "write_parquet",
    "sqlite_scan",
    "postgres_scan",
    "duckdb_settings",
    "duckdb_secrets",
}


class QueryValidator:
    """Security and semantic validator preventing arbitrary unverified SQL execution."""

    @classmethod
    def validate_sql(cls, sql: str, allowed_tables: list[str]) -> str:
        """Validate raw SQL string against strict security constraints.

        Rules:
        1. Query must not be empty.
        2. Must start with SELECT (ignoring whitespace).
        3. No semicolons or multiple stacked statements.
        4. No SQL comments (-- or /* */).
        5. No DDL, DML, or administrative keywords.
        6. No unauthorized filesystem or external connection functions.
        7. Referenced tables must strictly belong to allowed_tables.
        8. Must enforce a row LIMIT (clamped between 1 and 1000).
        """
        trimmed = sql.strip()
        if not trimmed:
            raise SQLValidationError("Query cannot be empty.")

        # 1. Disallow semicolons (stacked statements)
        if ";" in trimmed[:-1]:
            raise SQLValidationError("Multiple stacked SQL statements are forbidden.")

        clean_sql = trimmed.rstrip(";").strip()

        # 2. Disallow comment syntax that could mask injections
        if "--" in clean_sql or "/*" in clean_sql:
            raise SQLValidationError("SQL comments are not permitted in analytical queries.")

        # 3. Must be a SELECT query
        if not re.match(r"^SELECT\b", clean_sql, re.IGNORECASE):
            raise SQLValidationError("Only read-only SELECT queries are permitted.")

        # 4. Check for forbidden keywords as whole words
        tokens = re.findall(r"\b[A-Z_]+\b", clean_sql.upper())
        for token in tokens:
            if token in FORBIDDEN_KEYWORDS:
                raise SQLValidationError(
                    f"Forbidden SQL keyword '{token}' detected. Only read-only queries are allowed."
                )

        # 5. Check for forbidden filesystem/external functions
        for func in FORBIDDEN_FUNCTIONS:
            pattern = rf"\b{func}\s*\("
            if re.search(pattern, clean_sql, re.IGNORECASE):
                raise SQLValidationError(
                    f"Direct filesystem/external function '{func}()' is forbidden in analytical queries."
                )

        # 6. Verify table references against allowed_tables
        normalized_allowed = [t.lower() for t in allowed_tables]
        table_matches = re.findall(r"\bFROM\s+([a-zA-Z0-9_]+)", clean_sql, re.IGNORECASE)
        join_matches = re.findall(r"\bJOIN\s+([a-zA-Z0-9_]+)", clean_sql, re.IGNORECASE)

        referenced_tables = [t.lower() for t in (table_matches + join_matches)]
        if not referenced_tables:
            raise SQLValidationError("Query must specify a target table in the FROM clause.")

        for ref in referenced_tables:
            if ref not in normalized_allowed:
                raise TableNotAllowedError(ref, allowed_tables)

        # 7. Validate and enforce LIMIT
        limit_match = re.search(r"\bLIMIT\s+(\d+)", clean_sql, re.IGNORECASE)
        if not limit_match:
            # Safely append default limit
            clean_sql = f"{clean_sql} LIMIT 100"
        else:
            limit_val = int(limit_match.group(1))
            if limit_val > 1000:
                # Clamp limit to 1000
                clean_sql = re.sub(
                    r"\bLIMIT\s+\d+", "LIMIT 1000", clean_sql, flags=re.IGNORECASE
                )
            elif limit_val < 1:
                clean_sql = re.sub(
                    r"\bLIMIT\s+\d+", "LIMIT 1", clean_sql, flags=re.IGNORECASE
                )

        return clean_sql
