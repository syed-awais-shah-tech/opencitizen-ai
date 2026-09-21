"""Geographic data validation adhering to WGS84 (EPSG:4326) and RFC 7946 GeoJSON standards."""

import math
from typing import Any, Sequence

from app.geospatial.schemas import (
    GeoPoint,
    GeoValidationError,
    GeoValidationResult,
)


class GeoValidator:
    """Validates geographic coordinates and GeoJSON structures for civic data."""

    LAT_MIN = -90.0
    LAT_MAX = 90.0
    LON_MIN = -180.0
    LON_MAX = 180.0

    @classmethod
    def parse_coordinate(cls, value: Any) -> float | None:
        """Parse numeric coordinate from float, int, or string, returning None if invalid or missing."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return None
            return float(value)
        if isinstance(value, str):
            clean = value.strip()
            if not clean or clean.lower() in ("null", "none", "nan", "n/a", "#n/a", "undefined"):
                return None
            try:
                val = float(clean)
                if math.isnan(val) or math.isinf(val):
                    return None
                return val
            except ValueError:
                return None
        return None

    @classmethod
    def validate_point(
        cls,
        latitude: Any,
        longitude: Any,
        row_index: int | None = None,
    ) -> tuple[GeoPoint | None, list[GeoValidationError], list[str]]:
        """Validate an individual latitude/longitude pair in EPSG:4326.

        Returns:
            Tuple of (GeoPoint if valid or None, list of errors, list of warnings).
        """
        errors: list[GeoValidationError] = []
        warnings: list[str] = []

        lat_val = cls.parse_coordinate(latitude)
        lon_val = cls.parse_coordinate(longitude)

        # 1. Missing or unparseable latitude
        if lat_val is None:
            errors.append(
                GeoValidationError(
                    row_index=row_index,
                    column="latitude",
                    raw_value=latitude,
                    error_code="MISSING_OR_INVALID_LATITUDE",
                    message=f"Latitude value '{latitude}' is missing or non-numeric.",
                )
            )

        # 2. Missing or unparseable longitude
        if lon_val is None:
            errors.append(
                GeoValidationError(
                    row_index=row_index,
                    column="longitude",
                    raw_value=longitude,
                    error_code="MISSING_OR_INVALID_LONGITUDE",
                    message=f"Longitude value '{longitude}' is missing or non-numeric.",
                )
            )

        if errors:
            return None, errors, warnings

        assert lat_val is not None
        assert lon_val is not None

        # 3. Detect probable inverted/swapped coordinates (lat > 90, lon <= 90)
        if (lat_val > 90.0 or lat_val < -90.0) and (-90.0 <= lon_val <= 90.0):
            if -180.0 <= lat_val <= 180.0:
                warnings.append(
                    f"Row {row_index}: Latitude {lat_val} exceeds ±90° while Longitude {lon_val} is within ±90°. "
                    "Coordinates appear inverted/swapped."
                )

        # 4. Latitude bounds check [-90.0, 90.0]
        if lat_val < cls.LAT_MIN or lat_val > cls.LAT_MAX:
            errors.append(
                GeoValidationError(
                    row_index=row_index,
                    column="latitude",
                    raw_value=latitude,
                    error_code="LATITUDE_OUT_OF_BOUNDS",
                    message=f"Latitude {lat_val} is outside valid WGS84 range [-90.0, +90.0].",
                )
            )

        # 5. Longitude bounds check [-180.0, 180.0]
        if lon_val < cls.LON_MIN or lon_val > cls.LON_MAX:
            errors.append(
                GeoValidationError(
                    row_index=row_index,
                    column="longitude",
                    raw_value=longitude,
                    error_code="LONGITUDE_OUT_OF_BOUNDS",
                    message=f"Longitude {lon_val} is outside valid WGS84 range [-180.0, +180.0].",
                )
            )

        if errors:
            return None, errors, warnings

        point = GeoPoint(longitude=round(lon_val, 6), latitude=round(lat_val, 6))
        return point, errors, warnings

    @classmethod
    def compute_bounding_box(cls, points: Sequence[GeoPoint]) -> tuple[list[float] | None, list[float] | None]:
        """Compute [min_lon, min_lat, max_lon, max_lat] and center [center_lon, center_lat] from points."""
        if not points:
            return None, None

        min_lon = min(p.longitude for p in points)
        max_lon = max(p.longitude for p in points)
        min_lat = min(p.latitude for p in points)
        max_lat = max(p.latitude for p in points)

        bbox = [round(min_lon, 6), round(min_lat, 6), round(max_lon, 6), round(max_lat, 6)]
        center = [round((min_lon + max_lon) / 2.0, 6), round((min_lat + max_lat) / 2.0, 6)]
        return bbox, center

    @classmethod
    def validate_records(
        cls,
        records: Sequence[dict[str, Any]],
        lat_column: str,
        lon_column: str,
    ) -> GeoValidationResult:
        """Validate a tabular collection of records against spatial bounds."""
        errors: list[GeoValidationError] = []
        warnings: list[str] = []
        valid_points: list[GeoPoint] = []
        valid_count = 0
        invalid_count = 0

        for idx, row in enumerate(records):
            lat_raw = row.get(lat_column)
            lon_raw = row.get(lon_column)

            point, row_errs, row_warns = cls.validate_point(
                latitude=lat_raw,
                longitude=lon_raw,
                row_index=idx,
            )

            if row_warns:
                warnings.extend(row_warns)

            if row_errs:
                invalid_count += 1
                errors.extend(row_errs)
            elif point:
                valid_count += 1
                valid_points.append(point)

        bbox, center = cls.compute_bounding_box(valid_points)

        return GeoValidationResult(
            is_valid=len(errors) == 0,
            total_records=len(records),
            valid_records=valid_count,
            invalid_records=invalid_count,
            errors=errors,
            warnings=warnings,
            detected_crs="EPSG:4326",
            bbox=bbox,
            center=center,
        )

    @classmethod
    def validate_geojson(cls, payload: dict[str, Any]) -> GeoValidationResult:
        """Validate a raw GeoJSON dictionary for RFC 7946 compliance."""
        errors: list[GeoValidationError] = []
        warnings: list[str] = []
        valid_points: list[GeoPoint] = []

        if not isinstance(payload, dict):
            return GeoValidationResult(
                is_valid=False,
                total_records=0,
                valid_records=0,
                invalid_records=1,
                errors=[
                    GeoValidationError(
                        error_code="INVALID_GEOJSON_ROOT",
                        message="GeoJSON payload must be a JSON object dictionary.",
                    )
                ],
            )

        root_type = payload.get("type")
        if root_type not in ("FeatureCollection", "Feature", "Point"):
            return GeoValidationResult(
                is_valid=False,
                total_records=0,
                valid_records=0,
                invalid_records=1,
                errors=[
                    GeoValidationError(
                        error_code="UNSUPPORTED_GEOJSON_TYPE",
                        message=f"Root GeoJSON type '{root_type}' is not supported. Must be FeatureCollection, Feature, or Point.",
                    )
                ],
            )

        features = []
        if root_type == "FeatureCollection":
            raw_features = payload.get("features")
            if not isinstance(raw_features, list):
                return GeoValidationResult(
                    is_valid=False,
                    total_records=0,
                    valid_records=0,
                    invalid_records=1,
                    errors=[
                        GeoValidationError(
                            error_code="INVALID_FEATURES_LIST",
                            message="FeatureCollection must contain a 'features' array.",
                        )
                    ],
                )
            features = raw_features
        elif root_type == "Feature":
            features = [payload]
        elif root_type == "Point":
            features = [{"type": "Feature", "geometry": payload, "properties": {}}]

        valid_count = 0
        invalid_count = 0

        for idx, feat in enumerate(features):
            if not isinstance(feat, dict):
                invalid_count += 1
                errors.append(
                    GeoValidationError(
                        row_index=idx,
                        error_code="INVALID_FEATURE",
                        message="Each item in features must be a dictionary object.",
                    )
                )
                continue

            geom = feat.get("geometry")
            if not isinstance(geom, dict):
                invalid_count += 1
                errors.append(
                    GeoValidationError(
                        row_index=idx,
                        error_code="MISSING_GEOMETRY",
                        message=f"Feature {idx} is missing a geometry dictionary.",
                    )
                )
                continue

            coords = geom.get("coordinates")
            geom_type = geom.get("type")

            if geom_type == "Point":
                if not isinstance(coords, (list, tuple)) or len(coords) < 2:
                    invalid_count += 1
                    errors.append(
                        GeoValidationError(
                            row_index=idx,
                            error_code="INVALID_POINT_COORDINATES",
                            message=f"Feature {idx} Point coordinates must be [longitude, latitude].",
                        )
                    )
                    continue

                lon = coords[0]
                lat = coords[1]
                point, row_errs, row_warns = cls.validate_point(
                    latitude=lat, longitude=lon, row_index=idx
                )
                if row_warns:
                    warnings.extend(row_warns)
                if row_errs:
                    invalid_count += 1
                    errors.extend(row_errs)
                elif point:
                    valid_count += 1
                    valid_points.append(point)
            else:
                # Unsupported or non-point geometry for initial validation
                valid_count += 1

        bbox, center = cls.compute_bounding_box(valid_points)

        return GeoValidationResult(
            is_valid=len(errors) == 0,
            total_records=len(features),
            valid_records=valid_count,
            invalid_records=invalid_count,
            errors=errors,
            warnings=warnings,
            detected_crs="EPSG:4326",
            bbox=bbox,
            center=center,
        )
