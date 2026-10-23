import os
import json
import math
from collections import Counter
from typing import Any
 
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
 
 
# Azure Container Apps hostname.
# Set AZURE_APP_HOST to the hostname only,
# without https:// or /mcp.
AZURE_APP_HOST = os.environ.get(
    "AZURE_APP_HOST", ""
).strip()
 
PORT = int(os.environ.get("PORT", "8000"))
 
allowed_hosts = [
    "127.0.0.1:*",
    "localhost:*",
]
 
if AZURE_APP_HOST:
    allowed_hosts.extend([
        AZURE_APP_HOST,
        f"{AZURE_APP_HOST}:*",
    ])
 
 
# FastMCP server configuration.
# Host and port belong in the constructor,
# not in mcp.run().
mcp = FastMCP(
    "Data Quality MCP Server",
    host="0.0.0.0",
    port=PORT,
    transport_security=TransportSecuritySettings(
        allowed_hosts=allowed_hosts,
        allowed_origins=[],
    ),
)
 
 
@mcp.tool()
def get_server_status() -> dict:
    """Check whether the MCP server is healthy."""
    return {
        "status": "healthy",
        "server": "data-quality-mcp-server",
        "message": "MCP tool invoked successfully",
    }
 
 
@mcp.tool()
def add_numbers(a: int, b: int) -> dict:
    """Add two integers."""
    return {
        "a": a,
        "b": b,
        "result": a + b,
    }
 
 
@mcp.tool()
def validate_records(
    records: list[dict[str, Any]],
    required_fields: list[str],
) -> dict:
    """
    Validate records against required fields.
 
    Reports missing fields, null values, and invalid records.
    """
    errors = []
 
    for index, record in enumerate(records):
        missing_fields = [
            field for field in required_fields
            if field not in record
        ]
 
        null_fields = [
            field for field in required_fields
            if field in record and record[field] is None
        ]
 
        if missing_fields or null_fields:
            errors.append({
                "record_index": index,
                "missing_fields": missing_fields,
                "null_fields": null_fields,
            })
 
    return {
        "total_records": len(records),
        "valid_records": len(records) - len(errors),
        "invalid_records": len(errors),
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
 
 
@mcp.tool()
def profile_dataset(records: list[dict[str, Any]]) -> dict:
    """
    Profile a dataset represented as a list of JSON records.
 
    Returns row counts, columns, missing values,
    duplicate rows, and numeric statistics
    for each numeric column.
    """
    if not records:
        return {
            "total_rows": 0,
            "columns": [],
            "missing_values": {},
            "duplicate_rows": 0,
            "numeric_summary": {},
        }
 
    columns = list(dict.fromkeys(
        key for record in records for key in record
    ))
 
    missing_values = {
        column: sum(
            1 for record in records
            if column not in record
            or record[column] is None
        )
        for column in columns
    }
 
    serialized_rows = [
        json.dumps(
            record,
            sort_keys=True,
            default=str
        )
        for record in records
    ]
 
    row_counts = Counter(serialized_rows)
 
    duplicate_rows = sum(
        count - 1
        for count in row_counts.values()
        if count > 1
    )
 
    numeric_summary = {}
 
    for column in columns:
        values = [
            record[column]
            for record in records
            if isinstance(
                record.get(column), (int, float)
            )
            and not isinstance(
                record.get(column), bool
            )
            and math.isfinite(record[column])
        ]
 
        if values:
            numeric_summary[column] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
            }
 
    return {
        "total_rows": len(records),
        "columns": columns,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "numeric_summary": numeric_summary,
    }
 
 
@mcp.tool()
def filter_records(
    records: list[dict[str, Any]],
    filters: dict[str, Any],
) -> dict:
    """
    Filter records by exact field-value matches.
 
    Example:
    filters={
        "department": "Engineering",
        "active": True
    }
 
    Returns records matching all conditions.
    """
    matched = [
        record for record in records
        if all(
            record.get(field) == expected_value
            for field, expected_value in filters.items()
        )
    ]
 
    return {
        "filters_applied": filters,
        "input_count": len(records),
        "matched_count": len(matched),
        "records": matched,
    }
 
 
@mcp.tool()
def detect_duplicate_records(
    records: list[dict[str, Any]],
    key_fields: list[str],
) -> dict:
    """
    Detect records sharing the same business key.
 
    Example:
    key_fields=["customer_id"]
 
    Or:
    key_fields=[
        "customer_id",
        "transaction_date"
    ]
    """
    if not key_fields:
        return {
            "error": "Provide at least one key field."
        }
 
    groups = {}
 
    for index, record in enumerate(records):
        missing = [
            field for field in key_fields
            if field not in record
            or record[field] is None
        ]
 
        if missing:
            continue
 
        key = json.dumps(
            [
                record[field]
                for field in key_fields
            ],
            sort_keys=True,
            default=str,
        )
 
        groups.setdefault(key, []).append({
            "record_index": index,
            "record": record,
        })
 
    duplicates = [
        {
            "key": json.loads(key),
            "count": len(group),
            "records": group,
        }
        for key, group in groups.items()
        if len(group) > 1
    ]
 
    return {
        "key_fields": key_fields,
        "duplicate_groups": len(duplicates),
        "duplicate_records": sum(
            len(group["records"])
            for group in duplicates
        ),
        "duplicates": duplicates,
    }
 
 
@mcp.tool()
def get_column_distribution(
    records: list[dict[str, Any]],
    column: str,
) -> dict:
    """
    Calculate value frequencies
    for a categorical column.
 
    Useful for checking class imbalance,
    status counts, and category distributions.
    """
    if not records:
        return {
            "column": column,
            "total_rows": 0,
            "value_counts": {},
        }
 
    counts = Counter()
 
    for record in records:
        value = record.get(column)
 
        if value is None:
            label = "<MISSING>"
        else:
            label = json.dumps(
                value,
                sort_keys=True,
                default=str
            )
 
        counts[label] += 1
 
    return {
        "column": column,
        "total_rows": len(records),
        "distinct_values": len(counts),
        "value_counts": dict(
            counts.most_common()
        ),
    }
 
 
if __name__ == "__main__":
    print(
        f"Starting Data Quality MCP Server "
        f"on 0.0.0.0:{PORT}",
        flush=True,
    )
 
    mcp.run(
        transport="streamable-http"
    )