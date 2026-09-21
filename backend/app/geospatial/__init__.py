"""Geospatial processing, RFC 7946 GeoJSON serialization, and validation."""

from app.geospatial.detector import GeospatialDetector
from app.geospatial.exceptions import (
    GeospatialError,
    GeospatialValidationError,
    NoGeospatialDataError,
)
from app.geospatial.schemas import (
    GeoBoundingBox,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeographicMetadata,
    GeoPoint,
    GeoValidationError,
    GeoValidationResult,
    ValidateGeoDataRequest,
)
from app.geospatial.service import GeospatialService, geospatial_service
from app.geospatial.validator import GeoValidator

__all__ = [
    "GeospatialDetector",
    "GeospatialError",
    "GeospatialValidationError",
    "NoGeospatialDataError",
    "GeoPoint",
    "GeoBoundingBox",
    "GeographicMetadata",
    "GeoJSONGeometry",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "GeoValidationError",
    "GeoValidationResult",
    "ValidateGeoDataRequest",
    "GeoValidator",
    "GeospatialService",
    "geospatial_service",
]
