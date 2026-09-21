"""Detector for identifying geographic and spatial columns in civic datasets."""

import re
from typing import Sequence


class GeospatialDetector:
    """Introspects dataset column names to locate latitude, longitude, and geometry representations."""

    # Explicit regex patterns for latitude
    LATITUDE_PATTERNS = [
        re.compile(r"^lat(itude)?$", re.IGNORECASE),
        re.compile(r"^.*_lat(itude)?$", re.IGNORECASE),
        re.compile(r"^lat(itude)?_.*$", re.IGNORECASE),
        re.compile(r"^declat(itude)?$", re.IGNORECASE),
        re.compile(r"^y(_coord(inate)?)?$", re.IGNORECASE),
        re.compile(r"^gps_lat$", re.IGNORECASE),
    ]

    # Explicit regex patterns for longitude
    LONGITUDE_PATTERNS = [
        re.compile(r"^lon(g|gitude)?$", re.IGNORECASE),
        re.compile(r"^lng$", re.IGNORECASE),
        re.compile(r"^.*_lon(g|gitude)?$", re.IGNORECASE),
        re.compile(r"^.*_lng$", re.IGNORECASE),
        re.compile(r"^lon(g|gitude)?_.*$", re.IGNORECASE),
        re.compile(r"^lng_.*$", re.IGNORECASE),
        re.compile(r"^declon(g|gitude)?$", re.IGNORECASE),
        re.compile(r"^x(_coord(inate)?)?$", re.IGNORECASE),
        re.compile(r"^gps_lon(g)?$", re.IGNORECASE),
        re.compile(r"^gps_lng$", re.IGNORECASE),
    ]

    # Geometry patterns (WKT or GeoJSON column)
    GEOMETRY_PATTERNS = [
        re.compile(r"^geom(etry)?$", re.IGNORECASE),
        re.compile(r"^the_geom$", re.IGNORECASE),
        re.compile(r"^geojson$", re.IGNORECASE),
        re.compile(r"^wkt$", re.IGNORECASE),
        re.compile(r"^shape$", re.IGNORECASE),
    ]

    @classmethod
    def detect_coordinate_columns(
        cls, columns: Sequence[str]
    ) -> tuple[str | None, str | None, str | None]:
        """Detect (latitude_col, longitude_col, geometry_col) from available column names.

        Returns:
            Tuple of (latitude_column, longitude_column, geometry_column).
            Unmatched components return None.
        """
        lat_col: str | None = None
        lon_col: str | None = None
        geom_col: str | None = None

        clean_cols = [c.strip() for c in columns if c and c.strip()]

        # Pass 1: exact matches first (e.g. "latitude", "longitude")
        for col in clean_cols:
            lower = col.lower()
            if lower == "latitude" and not lat_col:
                lat_col = col
            elif lower in ("longitude", "lon", "lng") and not lon_col:
                lon_col = col
            elif lower in ("geometry", "geom", "the_geom", "geojson") and not geom_col:
                geom_col = col

        # Pass 2: pattern matching for remaining
        for col in clean_cols:
            if not lat_col:
                for pattern in cls.LATITUDE_PATTERNS:
                    if pattern.match(col):
                        lat_col = col
                        break

            if not lon_col:
                for pattern in cls.LONGITUDE_PATTERNS:
                    if pattern.match(col):
                        lon_col = col
                        break

            if not geom_col:
                for pattern in cls.GEOMETRY_PATTERNS:
                    if pattern.match(col):
                        geom_col = col
                        break

        return lat_col, lon_col, geom_col

    @classmethod
    def has_geospatial_columns(cls, columns: Sequence[str]) -> bool:
        """Check whether the column list contains geographic coordinates or a geometry column."""
        lat_col, lon_col, geom_col = cls.detect_coordinate_columns(columns)
        return (lat_col is not None and lon_col is not None) or (geom_col is not None)
