"""Geospatial Service managing spatial dataset extraction, GeoJSON serialization, and metadata."""

from typing import Any, Sequence
from sqlalchemy.orm import Session

from app.analytics.engine import duckdb_engine
from app.geospatial.detector import GeospatialDetector
from app.geospatial.exceptions import NoGeospatialDataError
from app.geospatial.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeoPoint,
    GeographicMetadata,
    GeoValidationResult,
)
from app.geospatial.validator import GeoValidator
from app.models.dataset import Dataset


class GeospatialService:
    """Service providing geographic capabilities for civic datasets."""

    def __init__(self) -> None:
        self.detector = GeospatialDetector
        self.validator = GeoValidator

    def detect_table_spatial_columns(
        self, table_name: str
    ) -> tuple[str | None, str | None, str | None]:
        """Inspect a registered DuckDB table and determine coordinate/geometry columns."""
        clean_name = table_name.strip().lower()
        if not duckdb_engine.has_table(clean_name):
            raise NoGeospatialDataError(clean_name)

        schema = duckdb_engine.get_table_schema(clean_name)
        return self.detector.detect_coordinate_columns(list(schema.keys()))

    def extract_features_from_records(
        self,
        records: Sequence[dict[str, Any]],
        lat_column: str,
        lon_column: str,
        id_column: str | None = None,
    ) -> tuple[list[GeoJSONFeature], list[GeoPoint], int, int]:
        """Convert a list of tabular records into GeoJSON features.

        Returns:
            Tuple of (features, valid_points, valid_count, invalid_count).
        """
        features: list[GeoJSONFeature] = []
        valid_points: list[GeoPoint] = []
        valid_count = 0
        invalid_count = 0

        # Heuristic for ID column if not explicitly given
        possible_id_cols = [
            id_column,
            "project_id",
            "record_id",
            "id",
            "item_id",
            "contract_id",
            "grant_id",
        ]
        resolved_id_col = None
        if records:
            first_row = records[0]
            for col in possible_id_cols:
                if col and col in first_row:
                    resolved_id_col = col
                    break

        for idx, row in enumerate(records):
            lat_raw = row.get(lat_column)
            lon_raw = row.get(lon_column)

            point, errors, _ = self.validator.validate_point(
                latitude=lat_raw,
                longitude=lon_raw,
                row_index=idx,
            )

            if errors or not point:
                invalid_count += 1
                continue

            valid_count += 1
            valid_points.append(point)

            # Copy properties, omitting or retaining coordinate keys
            properties = {k: v for k, v in row.items()}

            feature_id = str(row[resolved_id_col]) if resolved_id_col and resolved_id_col in row else str(idx + 1)

            features.append(
                GeoJSONFeature(
                    type="Feature",
                    id=feature_id,
                    geometry=GeoJSONGeometry(
                        type="Point",
                        coordinates=point.to_coordinates(),
                    ),
                    properties=properties,
                )
            )

        return features, valid_points, valid_count, invalid_count

    def get_table_geojson(
        self,
        table_name: str,
        min_lon: float | None = None,
        min_lat: float | None = None,
        max_lon: float | None = None,
        max_lat: float | None = None,
        category: str | None = None,
        limit: int = 500,
    ) -> GeoJSONFeatureCollection:
        """Query a registered DuckDB table and produce a standard RFC 7946 GeoJSON FeatureCollection."""
        clean_name = table_name.strip().lower()
        lat_col, lon_col, _ = self.detect_table_spatial_columns(clean_name)

        if not lat_col or not lon_col:
            raise NoGeospatialDataError(clean_name)

        # Build SQL with optional bounding box and category filtering
        where_clauses = [f"{lat_col} IS NOT NULL", f"{lon_col} IS NOT NULL"]
        params: list[Any] = []

        if min_lat is not None:
            where_clauses.append(f"{lat_col} >= ?")
            params.append(min_lat)
        if max_lat is not None:
            where_clauses.append(f"{lat_col} <= ?")
            params.append(max_lat)
        if min_lon is not None:
            where_clauses.append(f"{lon_col} >= ?")
            params.append(min_lon)
        if max_lon is not None:
            where_clauses.append(f"{lon_col} <= ?")
            params.append(max_lon)

        if category and category.strip() and category.lower() != "all":
            # Check if category column exists
            schema = duckdb_engine.get_table_schema(clean_name)
            if "category" in schema:
                where_clauses.append("LOWER(category) = LOWER(?)")
                params.append(category.strip())

        where_sql = " AND ".join(where_clauses)
        sql = f"SELECT * FROM {clean_name} WHERE {where_sql} LIMIT {int(limit)};"

        _, rows, _, _ = duckdb_engine.execute_query(sql, params=params if params else None)

        features, valid_points, valid_count, invalid_count = self.extract_features_from_records(
            records=rows,
            lat_column=lat_col,
            lon_column=lon_col,
        )

        bbox, center = self.validator.compute_bounding_box(valid_points)

        metadata = GeographicMetadata(
            crs="EPSG:4326",
            has_geospatial=True,
            bbox=bbox,
            center=center,
            feature_count=len(features),
            valid_features=valid_count,
            invalid_features=invalid_count,
            latitude_column=lat_col,
            longitude_column=lon_col,
            geometry_types=["Point"] if features else [],
        )

        return GeoJSONFeatureCollection(
            type="FeatureCollection",
            bbox=bbox,
            features=features,
            metadata=metadata,
        )

    def get_dataset_geojson(
        self,
        db: Session | None,
        dataset_id_or_table: str,
        min_lon: float | None = None,
        min_lat: float | None = None,
        max_lon: float | None = None,
        max_lat: float | None = None,
        category: str | None = None,
        limit: int = 500,
    ) -> GeoJSONFeatureCollection:
        """Resolve dataset by UUID or table name, then return RFC 7946 GeoJSON."""
        table_name = dataset_id_or_table

        if db is not None:
            ds = db.get(Dataset, dataset_id_or_table)
            if ds:
                table_name = ds.table_name

        return self.get_table_geojson(
            table_name=table_name,
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            category=category,
            limit=limit,
        )

    def get_dataset_geographic_metadata(
        self,
        db: Session | None,
        dataset_id_or_table: str,
    ) -> GeographicMetadata:
        """Retrieve geographic metadata envelope for a dataset."""
        fc = self.get_dataset_geojson(db=db, dataset_id_or_table=dataset_id_or_table, limit=500)
        assert fc.metadata is not None
        return fc.metadata

    def validate_dataset(
        self,
        records: Sequence[dict[str, Any]],
        lat_column: str | None = None,
        lon_column: str | None = None,
    ) -> GeoValidationResult:
        """Perform full spatial validation on tabular records."""
        if not records:
            return GeoValidationResult(
                is_valid=True,
                total_records=0,
                valid_records=0,
                invalid_records=0,
            )

        if not lat_column or not lon_column:
            sample_keys = list(records[0].keys())
            detected_lat, detected_lon, _ = self.detector.detect_coordinate_columns(sample_keys)
            lat_column = lat_column or detected_lat
            lon_column = lon_column or detected_lon

        if not lat_column or not lon_column:
            raise NoGeospatialDataError("provided records")

        return self.validator.validate_records(
            records=records,
            lat_column=lat_column,
            lon_column=lon_column,
        )


# Singleton service instance
geospatial_service = GeospatialService()
