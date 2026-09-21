"""Pydantic schemas for geospatial metadata, RFC 7946 GeoJSON models, and validation."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    """Geographic coordinate pair in WGS84 (EPSG:4326)."""

    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")

    def to_coordinates(self) -> list[float]:
        """Return RFC 7946 ordered [longitude, latitude]."""
        return [self.longitude, self.latitude]


class GeoBoundingBox(BaseModel):
    """Geographic bounding box [min_lon, min_lat, max_lon, max_lat] in EPSG:4326."""

    min_lon: float = Field(..., ge=-180.0, le=180.0, description="Westernmost longitude")
    min_lat: float = Field(..., ge=-90.0, le=90.0, description="Southernmost latitude")
    max_lon: float = Field(..., ge=-180.0, le=180.0, description="Easternmost longitude")
    max_lat: float = Field(..., ge=-90.0, le=90.0, description="Northernmost latitude")

    def to_list(self) -> list[float]:
        """Format as standard RFC 7946 bounding box array."""
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    def centroid(self) -> list[float]:
        """Compute center point [center_lon, center_lat]."""
        return [
            round((self.min_lon + self.max_lon) / 2.0, 6),
            round((self.min_lat + self.max_lat) / 2.0, 6),
        ]


class GeographicMetadata(BaseModel):
    """Summary of geographic capabilities, bounding extent, and detected coordinate mappings."""

    crs: str = Field(default="EPSG:4326", description="Coordinate Reference System identifier")
    has_geospatial: bool = Field(default=True, description="Whether dataset contains spatial data")
    bbox: list[float] | None = Field(
        default=None, description="Bounding box [min_lon, min_lat, max_lon, max_lat]"
    )
    center: list[float] | None = Field(
        default=None, description="Calculated center coordinate [center_lon, center_lat]"
    )
    feature_count: int = Field(default=0, ge=0, description="Total number of geographic features")
    valid_features: int = Field(default=0, ge=0, description="Features with valid coordinates")
    invalid_features: int = Field(default=0, ge=0, description="Features with invalid/missing coordinates")
    latitude_column: str | None = Field(default=None, description="Detected latitude column name")
    longitude_column: str | None = Field(default=None, description="Detected longitude column name")
    geometry_column: str | None = Field(default=None, description="Detected geometry/GeoJSON column name")
    geometry_types: list[str] = Field(
        default_factory=lambda: ["Point"], description="Detected geometry types"
    )


class GeoJSONGeometry(BaseModel):
    """RFC 7946 compliant GeoJSON geometry definition."""

    type: Literal["Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"] = Field(
        default="Point", description="GeoJSON geometry type"
    )
    coordinates: list[Any] = Field(
        ..., description="Coordinates array ([lon, lat] for Point)"
    )


class GeoJSONFeature(BaseModel):
    """RFC 7946 compliant GeoJSON Feature."""

    type: Literal["Feature"] = Field(default="Feature")
    id: str | int | None = Field(default=None, description="Unique feature identifier")
    geometry: GeoJSONGeometry = Field(..., description="Feature spatial geometry")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Associated record properties and metrics"
    )


class GeoJSONFeatureCollection(BaseModel):
    """RFC 7946 compliant GeoJSON FeatureCollection."""

    type: Literal["FeatureCollection"] = Field(default="FeatureCollection")
    bbox: list[float] | None = Field(
        default=None, description="Bounding box [min_lon, min_lat, max_lon, max_lat]"
    )
    features: list[GeoJSONFeature] = Field(
        default_factory=list, description="List of spatial GeoJSON features"
    )
    metadata: GeographicMetadata | None = Field(
        default=None, description="OpenCitizen geographic metadata envelope"
    )


class GeoValidationError(BaseModel):
    """Detailed error reported during geographic validation."""

    row_index: int | None = Field(default=None, description="Record index in dataset")
    column: str | None = Field(default=None, description="Column containing invalid value")
    raw_value: Any = Field(default=None, description="Raw invalid value encountered")
    error_code: str = Field(..., description="Machine-readable error category")
    message: str = Field(..., description="Human-readable explanation of error")


class GeoValidationResult(BaseModel):
    """Result of geographic validation on a dataset or GeoJSON payload."""

    is_valid: bool = Field(..., description="True if no fatal coordinate errors were found")
    total_records: int = Field(default=0, ge=0, description="Total rows or features inspected")
    valid_records: int = Field(default=0, ge=0, description="Count of valid spatial records")
    invalid_records: int = Field(default=0, ge=0, description="Count of invalid spatial records")
    errors: list[GeoValidationError] = Field(
        default_factory=list, description="List of validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Warnings (e.g. swapped coordinate heuristics)"
    )
    detected_crs: str = Field(default="EPSG:4326", description="Inferred CRS")
    bbox: list[float] | None = Field(
        default=None, description="Computed bounding box of valid features"
    )
    center: list[float] | None = Field(
        default=None, description="Computed center coordinate of valid features"
    )


class ValidateGeoDataRequest(BaseModel):
    """Request payload for validating geographic dataset records or GeoJSON."""

    records: list[dict[str, Any]] | None = Field(
        default=None, description="List of tabular records with coordinates"
    )
    lat_column: str | None = Field(
        default=None, description="Explicit latitude column identifier"
    )
    lon_column: str | None = Field(
        default=None, description="Explicit longitude column identifier"
    )
    geojson: dict[str, Any] | None = Field(
        default=None, description="Raw GeoJSON dictionary to validate"
    )
