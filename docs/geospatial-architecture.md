# Geospatial Architecture & Civic Data Specification

**OpenCitizen AI — Stage 18 Architecture Document**

---

## 1. Overview & Objectives

OpenCitizen AI provides evidence-grounded civic intelligence across municipal documents and structured datasets. Public development datasets—such as municipal capital improvements, infrastructure developments, transit corridors, and community facilities—inherently possess geographic location attributes.

Stage 18 introduces a focused, lightweight, and standards-compliant **geospatial subsystem** designed to:
1. Support standard **geographic metadata** and **RFC 7946 GeoJSON-compatible output**.
2. Perform rigorous **coordinate bounds and structure validation** in WGS84 (EPSG:4326).
3. Query spatial datasets through **DuckDB in-process columnar execution** with bounding box filtering.
4. Render interactive **vector map visualizations** backed by actual civic data without external proprietary map keys or bloated C-library dependencies.

---

## 2. Standards & Coordinate Reference System (CRS)

All geographic data ingested, processed, and emitted by OpenCitizen AI adheres strictly to:

| Standard | Specification | Description |
| :--- | :--- | :--- |
| **CRS / SRS** | **OGC:CRS84 / EPSG:4326** | World Geodetic System 1984 (decimal degrees). |
| **Output Format** | **RFC 7946 GeoJSON** | Standard JSON format for encoding geographic data structures. |
| **Coordinate Ordering** | **`[longitude, latitude]`** | RFC 7946 Section 3.1.1: easting/longitude first, northing/latitude second. |
| **Latitude Range** | $[-90.0, +90.0]$ | Southern and Northern hemisphere limits. |
| **Longitude Range** | $[-180.0, +180.0]$ | Western and Eastern hemisphere limits. |

---

## 3. Subsystem Architecture

The geospatial architecture separates concerns across detection, validation, storage querying, API serialization, and frontend presentation:

```
                          ┌────────────────────────┐
                          │ Tabular Civic Dataset  │
                          │   (CSV, JSON, DuckDB)  │
                          └───────────┬────────────┘
                                      │
                                      ▼
                        ┌────────────────────────────┐
                        │     GeospatialDetector     │
                        │  (lat/lon/geometry columns) │
                        └─────────────┬──────────────┘
                                      │
                                      ▼
                        ┌────────────────────────────┐
                        │        GeoValidator        │
                        │  (bounds, heuristics, CRS) │
                        └─────────────┬──────────────┘
                                      │
                                      ▼
                        ┌────────────────────────────┐
                        │     GeospatialService      │
                        │   (DuckDB BBox SQL Query)  │
                        └─────────────┬──────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
      ┌──────────────────────────────┐  ┌──────────────────────────────┐
      │ RFC 7946 GeoJSON Endpoint    │  │  GeospatialMapViewer (UI)    │
      │ /api/v1/geospatial/{id}/...  │  │  Interactive SVG Vector Map  │
      └──────────────────────────────┘  └──────────────────────────────┘
```

### 3.1 Module Breakdown (`backend/app/geospatial/`)

- `schemas.py`: Pydantic models defining `GeographicMetadata`, `GeoBoundingBox`, `GeoPoint`, `GeoJSONGeometry`, `GeoJSONFeature`, `GeoJSONFeatureCollection`, and `GeoValidationResult`.
- `detector.py`: Case-insensitive regular expression pattern matching for latitude (`lat`, `latitude`, `y`, `gps_lat`), longitude (`lon`, `lng`, `longitude`, `x`, `gps_lon`), and geometry attributes.
- `validator.py`: Pure-Python validation enforcing $[-90, 90]$ latitude and $[-180, 180]$ longitude limits, unparseable/null sanitization, swapped coordinate heuristics, bounding box extent computation, and RFC 7946 structure verification.
- `service.py`: High-level geospatial service extracting records from DuckDB tables, applying spatial bounding box and categorical SQL filters, and building metadata envelopes.
- `exceptions.py`: Domain-specific exceptions (`GeospatialError`, `GeospatialValidationError`, `NoGeospatialDataError`).

---

## 4. Geographic Data Validation Rules

The `GeoValidator` enforces defense-in-depth data validation on every spatial point:

1. **Numeric Coordinate Parsing**:
   - Converts integer, float, and decimal string representations into 64-bit IEEE floats.
   - Rejects `NaN`, `Infinity`, empty strings, and sentinels (`null`, `none`, `n/a`, `#n/a`, `undefined`).

2. **Boundary Checks**:
   - $\text{Latitude} \in [-90.0, 90.0]$: Out-of-bounds values yield `LATITUDE_OUT_OF_BOUNDS`.
   - $\text{Longitude} \in [-180.0, 180.0]$: Out-of-bounds values yield `LONGITUDE_OUT_OF_BOUNDS`.

3. **Inverted / Swapped Coordinate Detection**:
   - When $\text{Latitude} \in (90, 180]$ or $[-180, -90)$, while $\text{Longitude} \in [-90, 90]$, coordinates are flagged as likely inverted (e.g., longitude inadvertently entered into the latitude field).
   - Generates an actionable warning in `GeoValidationResult.warnings`.

4. **Bounding Box & Centroid Calculation**:
   - Given valid features, calculates extent array `[min_lon, min_lat, max_lon, max_lat]`.
   - Computes geographic centroid:
     $$\text{center} = \left[ \frac{\min(\text{lon}) + \max(\text{lon})}{2},\; \frac{\min(\text{lat}) + \max(\text{lat})}{2} \right]$$

---

## 5. API Endpoints

### 5.1 `GET /api/v1/geospatial/{dataset_id}/geojson`
Returns an RFC 7946 compliant GeoJSON `FeatureCollection`.

**Query Parameters:**
- `min_lon`, `min_lat`, `max_lon`, `max_lat`: Optional geographic bounding box filter.
- `category`: Optional categorical domain filter.
- `limit`: Max features (default 500, max 1000).

**Sample Response Payload:**
```json
{
  "type": "FeatureCollection",
  "bbox": [-97.784, 30.231, -97.705, 30.345],
  "features": [
    {
      "type": "Feature",
      "id": "DEV-101",
      "geometry": {
        "type": "Point",
        "coordinates": [-97.728, 30.245]
      },
      "properties": {
        "project_id": "DEV-101",
        "project_name": "East Riverside Transit Hub & Affordable Housing",
        "category": "Transportation",
        "status": "In Progress",
        "budget": 4200000.0,
        "spent_to_date": 2730000.0,
        "completion_pct": 65.0,
        "lead_agency": "Transportation & Public Works",
        "target_completion": "2025-11-30"
      }
    }
  ],
  "metadata": {
    "crs": "EPSG:4326",
    "has_geospatial": true,
    "bbox": [-97.784, 30.231, -97.705, 30.345],
    "center": [-97.7445, 30.288],
    "feature_count": 8,
    "valid_features": 8,
    "invalid_features": 0,
    "latitude_column": "latitude",
    "longitude_column": "longitude",
    "geometry_types": ["Point"]
  }
}
```

### 5.2 `GET /api/v1/geospatial/{dataset_id}/metadata`
Returns only the `GeographicMetadata` envelope without serializing full feature geometries.

### 5.3 `POST /api/v1/geospatial/validate`
Validates tabular coordinate arrays or raw GeoJSON payloads, returning structured error diagnostics and warnings.

---

## 6. Frontend Vector Map Visualization

The frontend component (`GeospatialMapViewer.tsx`) delivers an interactive mapping experience with:

- **Equirectangular Vector Projection**: Maps $(lon, lat)$ coordinates onto an SVG coordinate canvas $(x, y)$ with proportional aspect ratio and margin padding.
- **No Third-Party SDK Bloat**: Pure React + SVG implementation without Mapbox, Leaflet, or Google Maps API tokens, eliminating network failure modes in hermetic environments.
- **Interactive Pins**: Color-coded markers based on lifecycle status (Emerald for *Completed*, Cyan for *In Progress*, Amber for *Planned*).
- **Project Detail Inspector**: Selecting a pin presents an audit card detailing project ID, agency, allocated budget, spent to date, completion percentage, exact GPS coordinates, and RFC 7946 snippet.
- **Direct GeoJSON Export**: Browser button generating a downloadable `.geojson` file backed by actual dataset records.
- **Empty & Error States**: Contextual diagnostics when tables lack valid spatial coordinates.

---

## 7. Pre-Seeded Public Development Dataset

DuckDB seeds `public_development_projects` with 8 municipal development projects in Austin, TX:

| Project ID | Project Name | Category | Status | Budget | Coordinates |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DEV-101` | East Riverside Transit Hub | Transportation | In Progress | $4,200,000 | (30.2450°N, 97.7280°W) |
| `DEV-102` | Barton Creek Ecological Restoration | Parks & Environment | Completed | $1,850,000 | (30.2580°N, 97.7840°W) |
| `DEV-103` | Zilker Park Community Solar & Rec | Parks & Environment | In Progress | $950,000 | (30.2670°N, 97.7710°W) |
| `DEV-104` | Airport Blvd Corridor Modernization | Transportation | Planned | $6,800,000 | (30.3120°N, 97.7150°W) |
| `DEV-105` | Pleasant Valley Civic Health Clinic | Healthcare | In Progress | $3,100,000 | (30.2310°N, 97.7120°W) |
| `DEV-106` | Mueller Branch Library & Community | Public Facilities | Completed | $2,400,000 | (30.3010°N, 97.7050°W) |
| `DEV-107` | North Lamar Stormwater & Bioswale | Infrastructure | In Progress | $1,600,000 | (30.3450°N, 97.7210°W) |
| `DEV-108` | South Congress Pedestrian Corridor | Transportation | Planned | $890,000 | (30.2480°N, 97.7530°W) |

---

## 8. Non-Goals & Future Extensibility

To adhere strictly to scope:
- **No heavy C-GIS libraries**: PROJ, GDAL, or GEOS dependencies are avoided in favor of pure Python and DuckDB columnar operations.
- **Future Support**: The `GeoJSONGeometry` schema supports `Polygon` and `MultiPolygon` types, preparing the foundation for municipal boundary zoning and council district polygon rendering in subsequent stages.
