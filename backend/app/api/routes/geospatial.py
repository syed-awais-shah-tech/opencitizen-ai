"""API routes for geospatial data queries, RFC 7946 GeoJSON export, and validation."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import validate_entity_id
from app.db.session import get_db
from app.geospatial.schemas import (
    GeographicMetadata,
    GeoJSONFeatureCollection,
    GeoValidationResult,
    ValidateGeoDataRequest,
)
from app.geospatial.service import geospatial_service
from app.geospatial.validator import GeoValidator

router = APIRouter(prefix="/geospatial", tags=["Geospatial"])


@router.get(
    "/{dataset_id}/geojson",
    response_model=GeoJSONFeatureCollection,
    status_code=status.HTTP_200_OK,
    summary="Get GeoJSON FeatureCollection for dataset",
    description="Retrieve RFC 7946 compliant GeoJSON FeatureCollection with optional bounding box and category spatial filtering.",
)
async def get_dataset_geojson(
    dataset_id: str,
    min_lon: float | None = Query(default=None, ge=-180.0, le=180.0, description="Western bbox bound"),
    min_lat: float | None = Query(default=None, ge=-90.0, le=90.0, description="Southern bbox bound"),
    max_lon: float | None = Query(default=None, ge=-180.0, le=180.0, description="Eastern bbox bound"),
    max_lat: float | None = Query(default=None, ge=-90.0, le=90.0, description="Northern bbox bound"),
    category: str | None = Query(default=None, description="Optional category filter"),
    limit: int = Query(default=500, ge=1, le=1000, description="Max features to return"),
    db: Session = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return standard RFC 7946 GeoJSON FeatureCollection from a registered geospatial dataset."""
    valid_id = validate_entity_id(dataset_id)
    return geospatial_service.get_dataset_geojson(
        db=db,
        dataset_id_or_table=valid_id,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        category=category,
        limit=limit,
    )


@router.get(
    "/{dataset_id}/metadata",
    response_model=GeographicMetadata,
    status_code=status.HTTP_200_OK,
    summary="Get geographic metadata for dataset",
    description="Retrieve CRS, bounding box extent, centroid, and detected spatial column mappings.",
)
async def get_dataset_geographic_metadata(
    dataset_id: str,
    db: Session = Depends(get_db),
) -> GeographicMetadata:
    """Retrieve geographic metadata envelope for dataset."""
    valid_id = validate_entity_id(dataset_id)
    return geospatial_service.get_dataset_geographic_metadata(
        db=db,
        dataset_id_or_table=valid_id,
    )


@router.post(
    "/validate",
    response_model=GeoValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate geographic records or GeoJSON payload",
    description="Validates coordinate bounds, non-numeric values, inverted lat/lon pairs, and RFC 7946 GeoJSON schema conformity.",
)
async def validate_geographic_data(
    payload: ValidateGeoDataRequest,
) -> GeoValidationResult:
    """Validate tabular coordinates or GeoJSON structures."""
    if payload.geojson:
        return GeoValidator.validate_geojson(payload.geojson)

    records = payload.records or []
    return geospatial_service.validate_dataset(
        records=records,
        lat_column=payload.lat_column,
        lon_column=payload.lon_column,
    )
