"""Unit and integration tests for Stage 18 geospatial capabilities and data validation."""

import pytest
from fastapi.testclient import TestClient

from app.geospatial.detector import GeospatialDetector
from app.geospatial.exceptions import NoGeospatialDataError
from app.geospatial.schemas import GeoPoint
from app.geospatial.service import geospatial_service
from app.geospatial.validator import GeoValidator
from app.main import app


# -----------------------------------------------------------------------------
# 1. Coordinate Parsing & Bounds Validation Tests
# -----------------------------------------------------------------------------


def test_parse_coordinate_valid():
    """Verify coordinate parser correctly parses numeric floats, ints, and string floats."""
    assert GeoValidator.parse_coordinate(30.2672) == 30.2672
    assert GeoValidator.parse_coordinate(-97.7431) == -97.7431
    assert GeoValidator.parse_coordinate(42) == 42.0
    assert GeoValidator.parse_coordinate("  -97.7431  ") == -97.7431
    assert GeoValidator.parse_coordinate("0.0") == 0.0


def test_parse_coordinate_invalid_or_missing():
    """Verify coordinate parser returns None for missing, empty, or unparseable values."""
    assert GeoValidator.parse_coordinate(None) is None
    assert GeoValidator.parse_coordinate("") is None
    assert GeoValidator.parse_coordinate("   ") is None
    assert GeoValidator.parse_coordinate("null") is None
    assert GeoValidator.parse_coordinate("N/A") is None
    assert GeoValidator.parse_coordinate("NaN") is None
    assert GeoValidator.parse_coordinate("undefined") is None
    assert GeoValidator.parse_coordinate("not_a_number") is None
    assert GeoValidator.parse_coordinate(float("nan")) is None


def test_validate_point_valid():
    """Verify valid WGS84 coordinate pair passes validation."""
    point, errors, warnings = GeoValidator.validate_point(latitude=30.2672, longitude=-97.7431)
    assert point is not None
    assert point.latitude == 30.2672
    assert point.longitude == -97.7431
    assert len(errors) == 0
    assert len(warnings) == 0


def test_validate_point_out_of_bounds():
    """Verify out-of-bounds latitude and longitude are rejected with typed errors."""
    # Latitude > 90
    point, errors, _ = GeoValidator.validate_point(latitude=95.5, longitude=-97.7)
    assert point is None
    assert any(e.error_code == "LATITUDE_OUT_OF_BOUNDS" for e in errors)

    # Latitude < -90
    point, errors, _ = GeoValidator.validate_point(latitude=-92.0, longitude=-97.7)
    assert point is None
    assert any(e.error_code == "LATITUDE_OUT_OF_BOUNDS" for e in errors)

    # Longitude > 180
    point, errors, _ = GeoValidator.validate_point(latitude=30.0, longitude=185.0)
    assert point is None
    assert any(e.error_code == "LONGITUDE_OUT_OF_BOUNDS" for e in errors)

    # Longitude < -180
    point, errors, _ = GeoValidator.validate_point(latitude=30.0, longitude=-195.0)
    assert point is None
    assert any(e.error_code == "LONGITUDE_OUT_OF_BOUNDS" for e in errors)


def test_validate_point_missing():
    """Verify missing coordinate values produce descriptive errors."""
    point, errors, _ = GeoValidator.validate_point(latitude=None, longitude="-97.7431")
    assert point is None
    assert any(e.error_code == "MISSING_OR_INVALID_LATITUDE" for e in errors)

    point, errors, _ = GeoValidator.validate_point(latitude="30.2672", longitude=None)
    assert point is None
    assert any(e.error_code == "MISSING_OR_INVALID_LONGITUDE" for e in errors)


def test_validate_point_swapped_warning():
    """Verify heuristic warning is generated when latitude > 90 and longitude is in [-90, 90]."""
    # Inverted coordinates: lat=112.5 (likely lon), lon=34.2 (likely lat)
    point, errors, warnings = GeoValidator.validate_point(latitude=112.5, longitude=34.2)
    assert point is None
    assert len(warnings) > 0
    assert "inverted/swapped" in warnings[0].lower()


# -----------------------------------------------------------------------------
# 2. Bounding Box & Centroid Computation Tests
# -----------------------------------------------------------------------------


def test_compute_bounding_box():
    """Verify bounding box [min_lon, min_lat, max_lon, max_lat] and center calculation."""
    points = [
        GeoPoint(longitude=-97.784, latitude=30.231),
        GeoPoint(longitude=-97.705, latitude=30.345),
        GeoPoint(longitude=-97.740, latitude=30.280),
    ]
    bbox, center = GeoValidator.compute_bounding_box(points)
    assert bbox == [-97.784, 30.231, -97.705, 30.345]
    assert center == [round((-97.784 + -97.705) / 2.0, 6), round((30.231 + 30.345) / 2.0, 6)]


def test_compute_bounding_box_empty():
    """Verify empty points list returns None for bbox and center."""
    bbox, center = GeoValidator.compute_bounding_box([])
    assert bbox is None
    assert center is None


# -----------------------------------------------------------------------------
# 3. Geospatial Column Detector Tests
# -----------------------------------------------------------------------------


def test_detector_standard_names():
    """Verify detector matches standard latitude and longitude column names."""
    lat, lon, _ = GeospatialDetector.detect_coordinate_columns(["id", "name", "latitude", "longitude", "budget"])
    assert lat == "latitude"
    assert lon == "longitude"


def test_detector_shorthand_and_prefixes():
    """Verify detector handles lat/lng, project_lat, y/x coordinate aliases."""
    lat, lon, _ = GeospatialDetector.detect_coordinate_columns(["project_id", "project_lat", "project_lon"])
    assert lat == "project_lat"
    assert lon == "project_lon"

    lat2, lon2, _ = GeospatialDetector.detect_coordinate_columns(["id", "lat", "lng"])
    assert lat2 == "lat"
    assert lon2 == "lng"

    lat3, lon3, _ = GeospatialDetector.detect_coordinate_columns(["station", "y_coord", "x_coord"])
    assert lat3 == "y_coord"
    assert lon3 == "x_coord"


def test_detector_no_spatial_columns():
    """Verify detector returns None for non-spatial datasets."""
    lat, lon, geom = GeospatialDetector.detect_coordinate_columns(["department", "fiscal_year", "amount", "vendor_name"])
    assert lat is None
    assert lon is None
    assert geom is None
    assert not GeospatialDetector.has_geospatial_columns(["department", "fiscal_year", "amount"])


# -----------------------------------------------------------------------------
# 4. RFC 7946 GeoJSON Validation Tests
# -----------------------------------------------------------------------------


def test_validate_geojson_valid_feature_collection():
    """Verify valid GeoJSON FeatureCollection conforms to RFC 7946."""
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "1",
                "geometry": {"type": "Point", "coordinates": [-97.7431, 30.2672]},
                "properties": {"name": "Austin City Hall"},
            },
            {
                "type": "Feature",
                "id": "2",
                "geometry": {"type": "Point", "coordinates": [-97.7500, 30.2800]},
                "properties": {"name": "Capitol Extension"},
            },
        ],
    }
    result = GeoValidator.validate_geojson(fc)
    assert result.is_valid is True
    assert result.total_records == 2
    assert result.valid_records == 2
    assert result.invalid_records == 0
    assert result.bbox is not None


def test_validate_geojson_invalid_coordinates():
    """Verify GeoJSON with out-of-bounds coordinates is caught."""
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-97.7431, 195.0]},  # Lat 195 > 90
                "properties": {},
            }
        ],
    }
    result = GeoValidator.validate_geojson(fc)
    assert result.is_valid is False
    assert result.invalid_records == 1
    assert len(result.errors) > 0


def test_validate_geojson_malformed():
    """Verify malformed GeoJSON structure produces errors."""
    result = GeoValidator.validate_geojson({"type": "InvalidType"})
    assert result.is_valid is False
    assert any(e.error_code == "UNSUPPORTED_GEOJSON_TYPE" for e in result.errors)


# -----------------------------------------------------------------------------
# 5. Geospatial Service & DuckDB Integration Tests
# -----------------------------------------------------------------------------


def test_get_table_geojson_public_development_projects():
    """Verify GeospatialService retrieves public development projects as GeoJSON FeatureCollection."""
    fc = geospatial_service.get_table_geojson("public_development_projects")
    assert fc.type == "FeatureCollection"
    assert len(fc.features) == 8
    assert fc.bbox is not None
    assert fc.metadata is not None
    assert fc.metadata.crs == "EPSG:4326"
    assert fc.metadata.has_geospatial is True
    assert fc.metadata.valid_features == 8
    assert fc.metadata.latitude_column == "latitude"
    assert fc.metadata.longitude_column == "longitude"

    # Inspect first feature structure (RFC 7946: [lon, lat])
    first_feat = fc.features[0]
    assert first_feat.type == "Feature"
    assert first_feat.geometry.type == "Point"
    assert len(first_feat.geometry.coordinates) == 2
    lon, lat = first_feat.geometry.coordinates
    assert -98.0 <= lon <= -97.0
    assert 30.0 <= lat <= 31.0
    assert "project_name" in first_feat.properties
    assert "budget" in first_feat.properties


def test_get_table_geojson_spatial_filtering():
    """Verify bounding box and category spatial filtering in DuckDB query."""
    # Filter by category
    trans_fc = geospatial_service.get_table_geojson(
        "public_development_projects", category="Transportation"
    )
    assert len(trans_fc.features) > 0
    assert all(f.properties["category"] == "Transportation" for f in trans_fc.features)

    # Filter by bounding box
    bbox_fc = geospatial_service.get_table_geojson(
        "public_development_projects",
        min_lat=30.24,
        max_lat=30.27,
        min_lon=-97.79,
        max_lon=-97.72,
    )
    assert len(bbox_fc.features) > 0
    for f in bbox_fc.features:
        lon, lat = f.geometry.coordinates
        assert 30.24 <= lat <= 30.27
        assert -97.79 <= lon <= -97.72


def test_get_table_geojson_non_spatial_table_error():
    """Verify error when querying a table without coordinates."""
    with pytest.raises(NoGeospatialDataError):
        geospatial_service.get_table_geojson("dept_expenses")


# -----------------------------------------------------------------------------
# 6. FastAPI Endpoints Integration Tests
# -----------------------------------------------------------------------------


def test_api_get_geojson_endpoint(client: TestClient):
    """Test GET /api/v1/geospatial/{dataset_id}/geojson returns GeoJSON."""
    response = client.get("/api/v1/geospatial/public_development_projects/geojson")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 8
    assert data["metadata"]["crs"] == "EPSG:4326"
    assert data["metadata"]["valid_features"] == 8


def test_api_get_geojson_filtered_endpoint(client: TestClient):
    """Test GET /api/v1/geospatial/{dataset_id}/geojson with category filter."""
    response = client.get(
        "/api/v1/geospatial/public_development_projects/geojson?category=Parks%20%26%20Environment"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["features"]) == 2
    assert all(
        f["properties"]["category"] == "Parks & Environment" for f in data["features"]
    )


def test_api_get_metadata_endpoint(client: TestClient):
    """Test GET /api/v1/geospatial/{dataset_id}/metadata returns GeographicMetadata."""
    response = client.get("/api/v1/geospatial/public_development_projects/metadata")
    assert response.status_code == 200
    meta = response.json()
    assert meta["crs"] == "EPSG:4326"
    assert meta["has_geospatial"] is True
    assert meta["feature_count"] == 8
    assert meta["bbox"] is not None
    assert meta["center"] is not None


def test_api_validate_endpoint_tabular(client: TestClient):
    """Test POST /api/v1/geospatial/validate with tabular rows."""
    payload = {
        "records": [
            {"name": "Valid Point", "latitude": 30.26, "longitude": -97.74},
            {"name": "Invalid Point", "latitude": 999.0, "longitude": -97.74},
        ],
        "lat_column": "latitude",
        "lon_column": "longitude",
    }
    response = client.post("/api/v1/geospatial/validate", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is False
    assert res["total_records"] == 2
    assert res["valid_records"] == 1
    assert res["invalid_records"] == 1
    assert len(res["errors"]) == 1
    assert res["errors"][0]["error_code"] == "LATITUDE_OUT_OF_BOUNDS"


def test_api_validate_endpoint_geojson(client: TestClient):
    """Test POST /api/v1/geospatial/validate with raw GeoJSON."""
    geojson_payload = {
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-97.7431, 30.2672],
                    },
                    "properties": {"name": "Austin City Hall"},
                }
            ],
        }
    }
    response = client.post("/api/v1/geospatial/validate", json=geojson_payload)
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is True
    assert res["total_records"] == 1
    assert res["valid_records"] == 1
