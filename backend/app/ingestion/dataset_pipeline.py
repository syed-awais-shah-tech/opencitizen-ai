"""Pipeline for structured civic dataset ingestion (CSV, XLSX, JSON).

Implements:
upload
→ detect file format
→ inspect schema
→ identify columns
→ infer basic data types
→ validate dataset
→ store dataset metadata
→ create dataset preview (columns, inferred types, row count, missing values, sample rows)
"""

import io
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

import numpy as np
import pandas as pd

from app.ingestion.exceptions import (
    DatasetValidationError,
    UnsupportedDatasetFormatError,
)
from app.schemas.datasets import DatasetColumnSchema, DatasetPreview

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS: set[str] = {"CSV", "XLSX", "JSON"}


@dataclass
class DatasetIngestionResult:
    """Outcome of processing a tabular civic dataset."""

    dataset_id: str
    name: str
    category: str
    format: Literal["CSV", "XLSX", "JSON", "PARQUET"]
    row_count: int
    columns_count: int
    table_name: str
    size_bytes: int
    columns_metadata: list[DatasetColumnSchema]
    preview: DatasetPreview
    dataframe: pd.DataFrame


class DatasetIngestionPipeline:
    """Orchestrates format detection, schema inspection, data type inference, validation, and preview generation."""

    def detect_format(self, filename: str, content: bytes) -> Literal["CSV", "XLSX", "JSON"]:
        """Detect file format based on extension and content heuristics."""
        lower_name = (filename or "").lower()

        # Check by extension first
        if lower_name.endswith(".csv") or lower_name.endswith(".tsv"):
            return "CSV"
        if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
            return "XLSX"
        if lower_name.endswith(".json"):
            return "JSON"

        # Content sniffing fallback
        stripped = content.strip()
        if stripped.startswith(b"PK\x03\x04"):
            return "XLSX"
        if stripped.startswith(b"{") or stripped.startswith(b"["):
            return "JSON"

        # Check if text looks like CSV (contains commas or newlines and is decodable)
        try:
            sample = stripped[:1024].decode("utf-8")
            if "," in sample or "\t" in sample or "\n" in sample:
                return "CSV"
        except UnicodeDecodeError:
            pass

        raise UnsupportedDatasetFormatError(
            f"Unsupported dataset format for '{filename}'. Supported formats: CSV, XLSX, JSON."
        )

    def load_dataframe(self, content: bytes, file_format: str) -> pd.DataFrame:
        """Load tabular data into a pandas DataFrame using appropriate loader."""
        if not content:
            raise DatasetValidationError("Uploaded dataset is empty (0 bytes).")

        buffer = io.BytesIO(content)

        if file_format == "CSV":
            try:
                df = pd.read_csv(buffer, encoding="utf-8")
            except UnicodeDecodeError:
                buffer.seek(0)
                try:
                    df = pd.read_csv(buffer, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    buffer.seek(0)
                    df = pd.read_csv(buffer, encoding="latin1")
            except Exception as e:
                raise DatasetValidationError(f"Failed to parse CSV file: {e}") from e

        elif file_format == "XLSX":
            try:
                df = pd.read_excel(buffer, engine="openpyxl")
            except Exception as e:
                raise DatasetValidationError(f"Failed to parse Excel file: {e}") from e

        elif file_format == "JSON":
            try:
                text = content.decode("utf-8")
                parsed_json = json.loads(text)

                if isinstance(parsed_json, list):
                    df = pd.DataFrame(parsed_json)
                elif isinstance(parsed_json, dict):
                    # Check for standard tabular wrappers like {"data": [...]} or {"records": [...]}
                    for key in ["data", "records", "rows", "items", "results"]:
                        if key in parsed_json and isinstance(parsed_json[key], list):
                            df = pd.DataFrame(parsed_json[key])
                            break
                    else:
                        # Fall back to pandas default json reader
                        buffer.seek(0)
                        df = pd.read_json(buffer)
                else:
                    raise DatasetValidationError("JSON root must be an array of records or tabular dictionary.")
            except json.JSONDecodeError as e:
                raise DatasetValidationError(f"Invalid JSON format: {e}") from e
            except Exception as e:
                raise DatasetValidationError(f"Failed to parse JSON tabular dataset: {e}") from e

        else:
            raise UnsupportedDatasetFormatError(f"Unsupported tabular format: {file_format}")

        return df

    def validate_dataset(self, df: pd.DataFrame) -> None:
        """Ensure dataset contains columns and rows, and sanitize column identifiers."""
        if df.empty or len(df.columns) == 0:
            raise DatasetValidationError("Dataset is empty. At least one row and one column are required.")

        # Clean and stringify column headers
        cleaned_columns: list[str] = []
        seen_cols: dict[str, int] = {}

        for idx, col in enumerate(df.columns):
            name = str(col).strip() if str(col).strip() else f"column_{idx + 1}"
            if name in seen_cols:
                seen_cols[name] += 1
                name = f"{name}_{seen_cols[name]}"
            else:
                seen_cols[name] = 0
            cleaned_columns.append(name)

        df.columns = cleaned_columns

    def infer_column_types(
        self, df: pd.DataFrame
    ) -> tuple[dict[str, str], dict[str, int], list[DatasetColumnSchema]]:
        """Infer DuckDB/SQL types, calculate missing-value counts, and build column schemas."""
        inferred_types: dict[str, str] = {}
        missing_counts: dict[str, int] = {}
        columns_metadata: list[DatasetColumnSchema] = []
        total_rows = len(df)

        for col in df.columns:
            series = df[col]
            missing = int(series.isna().sum())
            missing_counts[col] = missing
            null_pct = round((missing / total_rows) * 100, 2) if total_rows > 0 else 0.0

            non_null = series.dropna()

            if non_null.empty:
                inferred = "VARCHAR"
            elif pd.api.types.is_bool_dtype(series):
                inferred = "BOOLEAN"
            elif pd.api.types.is_integer_dtype(series):
                inferred = "INTEGER"
            elif pd.api.types.is_float_dtype(series):
                inferred = "DOUBLE"
            elif pd.api.types.is_datetime64_any_dtype(series):
                inferred = "DATE"
            else:
                # String / Object inspection
                str_vals = non_null.astype(str).str.strip()

                # Check for boolean strings
                if str_vals.str.lower().isin(["true", "false", "yes", "no", "1", "0"]).all():
                    inferred = "BOOLEAN"
                else:
                    # Check for date parsing
                    is_date = False
                    # Check if sample strings look like dates (YYYY-MM-DD or MM/DD/YYYY)
                    sample = str_vals.head(50)
                    if any(re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", s) for s in sample):
                        try:
                            parsed_dates = pd.to_datetime(sample, errors="coerce")
                            if parsed_dates.notna().mean() >= 0.8:
                                is_date = True
                        except Exception:
                            is_date = False

                    if is_date:
                        inferred = "DATE"
                    else:
                        # Check for integer strings
                        if str_vals.str.match(r"^-?\d+$").all():
                            inferred = "INTEGER"
                        # Check for float strings
                        elif str_vals.str.match(r"^-?\d+(\.\d+)?$").all():
                            inferred = "DOUBLE"
                        else:
                            inferred = "VARCHAR"

            inferred_types[col] = inferred
            columns_metadata.append(
                DatasetColumnSchema(
                    name=col,
                    type=inferred,  # type: ignore[arg-type]
                    missing_count=missing,
                    null_percentage=null_pct,
                )
            )

        return inferred_types, missing_counts, columns_metadata

    def extract_sample_rows(self, df: pd.DataFrame, max_rows: int = 5) -> list[dict[str, Any]]:
        """Extract top N sample rows with safe JSON-serializable types."""
        sample_df = df.head(max_rows)
        clean_rows: list[dict[str, Any]] = []

        for _, row in sample_df.iterrows():
            record: dict[str, Any] = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    record[col] = None
                elif isinstance(val, (datetime, date, pd.Timestamp)):
                    record[col] = val.isoformat()
                elif isinstance(val, (np.bool_, bool)):
                    record[col] = bool(val)
                elif isinstance(val, (np.integer, int)):
                    record[col] = int(val)
                elif isinstance(val, (np.floating, float)):
                    record[col] = float(val)
                elif isinstance(val, str) and val.strip().lower() in ("true", "yes"):
                    record[col] = True
                elif isinstance(val, str) and val.strip().lower() in ("false", "no"):
                    record[col] = False
                else:
                    record[col] = str(val)
            clean_rows.append(record)

        return clean_rows

    def generate_preview(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        name: str,
        file_format: str,
        max_sample_rows: int = 5,
    ) -> DatasetPreview:
        """Assemble interactive DatasetPreview showing columns, inferred types, missing counts, and sample rows."""
        inferred_types, missing_counts, _ = self.infer_column_types(df)
        sample_rows = self.extract_sample_rows(df, max_rows=max_sample_rows)

        return DatasetPreview(
            dataset_id=dataset_id,
            name=name,
            format=file_format,
            row_count=len(df),
            columns_count=len(df.columns),
            columns=list(df.columns),
            inferred_types=inferred_types,
            missing_value_counts=missing_counts,
            sample_rows=sample_rows,
        )

    def generate_table_name(self, filename: str) -> str:
        """Derive safe SQL table identifier from filename."""
        base_name = re.sub(r"\.[a-zA-Z0-9]+$", "", filename)
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", base_name.lower()).strip("_")
        if not clean or not clean[0].isalpha():
            clean = f"table_{clean}"
        suffix = uuid.uuid4().hex[:6]
        return f"{clean}_{suffix}"[:63]

    def process_bytes(
        self,
        content: bytes,
        filename: str,
        category: str = "General",
        table_name: str | None = None,
    ) -> DatasetIngestionResult:
        """Execute end-to-end dataset ingestion pipeline.

        upload → detect format → inspect schema → identify columns → infer basic data types → validate → generate preview
        """
        logger.info("Ingesting structured dataset from filename '%s' (%d bytes)", filename, len(content))

        # 1. Detect file format
        file_format = self.detect_format(filename=filename, content=content)

        # 2. Load DataFrame using Pandas
        df = self.load_dataframe(content=content, file_format=file_format)

        # 3. Validate dataset & sanitize column headers
        self.validate_dataset(df)

        # 4. Infer data types & compute missing-value metrics
        inferred_types, missing_counts, columns_metadata = self.infer_column_types(df)

        dataset_id = f"ds_{uuid.uuid4().hex[:12]}"
        safe_table_name = table_name or self.generate_table_name(filename)

        # 5. Build dataset preview
        sample_rows = self.extract_sample_rows(df, max_rows=5)
        preview = DatasetPreview(
            dataset_id=dataset_id,
            name=filename,
            format=file_format,
            row_count=len(df),
            columns_count=len(df.columns),
            columns=list(df.columns),
            inferred_types=inferred_types,
            missing_value_counts=missing_counts,
            sample_rows=sample_rows,
        )

        return DatasetIngestionResult(
            dataset_id=dataset_id,
            name=filename,
            category=category,
            format=file_format,
            row_count=len(df),
            columns_count=len(df.columns),
            table_name=safe_table_name,
            size_bytes=len(content),
            columns_metadata=columns_metadata,
            preview=preview,
            dataframe=df,
        )


dataset_pipeline = DatasetIngestionPipeline()
