"use client";

import React, { useState, useEffect, useMemo } from "react";
import { DatasetItem, GeoJSONFeatureData, GeographicMetadataData } from "../lib/mockData";

interface GeospatialMapViewerProps {
  dataset: DatasetItem;
}

export default function GeospatialMapViewer({ dataset }: GeospatialMapViewerProps) {
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null);
  const [hoveredFeature, setHoveredFeature] = useState<GeoJSONFeatureData | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("All");
  const [statusFilter, setStatusFilter] = useState<string>("All");
  const [showJsonModal, setShowJsonModal] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);
  const [features, setFeatures] = useState<GeoJSONFeatureData[]>([]);
  const [metadata, setMetadata] = useState<GeographicMetadataData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Detect coordinate columns from dataset schema
  const { latCol, lonCol } = useMemo(() => {
    let lat: string | null = null;
    let lon: string | null = null;
    for (const col of dataset.columns) {
      const lower = col.name.toLowerCase();
      if (!lat && (lower === "latitude" || lower === "lat" || lower.endsWith("_lat") || lower === "y")) {
        lat = col.name;
      }
      if (!lon && (lower === "longitude" || lower === "lon" || lower === "lng" || lower.endsWith("_lon") || lower === "x")) {
        lon = col.name;
      }
    }
    return { latCol: lat, lonCol: lon };
  }, [dataset]);

  // Load GeoJSON features: Try backend API, fallback to client parsing of sampleRows
  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    const loadFeatures = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/geospatial/${dataset.tableName}/geojson`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data.features && data.features.length > 0) {
            setFeatures(data.features);
            setMetadata(data.metadata || null);
            setSelectedFeatureId(data.features[0].id?.toString() || null);
            setIsLoading(false);
            return;
          }
        }
      } catch {
        // Fallback to client-side parsing if backend dev server is not running
      }

      // Client-side extraction from sampleRows
      if (!latCol || !lonCol || !dataset.sampleRows) {
        if (isMounted) {
          setFeatures([]);
          setMetadata(null);
          setIsLoading(false);
        }
        return;
      }

      const clientFeats: GeoJSONFeatureData[] = [];
      const lons: number[] = [];
      const lats: number[] = [];

      dataset.sampleRows.forEach((row, idx) => {
        const rawLat = row[latCol];
        const rawLon = row[lonCol];
        const lat = typeof rawLat === "number" ? rawLat : parseFloat(String(rawLat));
        const lon = typeof rawLon === "number" ? rawLon : parseFloat(String(rawLon));

        if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
          lats.push(lat);
          lons.push(lon);
          const featId = (row.project_id || row.id || row.record_id || `feat-${idx + 1}`).toString();
          clientFeats.push({
            type: "Feature",
            id: featId,
            geometry: {
              type: "Point",
              coordinates: [lon, lat],
            },
            properties: { ...row },
          });
        }
      });

      if (isMounted) {
        setFeatures(clientFeats);
        if (clientFeats.length > 0) {
          const minLon = Math.min(...lons);
          const maxLon = Math.max(...lons);
          const minLat = Math.min(...lats);
          const maxLat = Math.max(...lats);
          setMetadata({
            crs: "EPSG:4326",
            hasGeospatial: true,
            bbox: [minLon, minLat, maxLon, maxLat],
            center: [Number(((minLon + maxLon) / 2).toFixed(4)), Number(((minLat + maxLat) / 2).toFixed(4))],
            featureCount: clientFeats.length,
            validFeatures: clientFeats.length,
            invalidFeatures: dataset.sampleRows.length - clientFeats.length,
            latitudeColumn: latCol,
            longitudeColumn: lonCol,
            geometryTypes: ["Point"],
          });
          setSelectedFeatureId(clientFeats[0].id?.toString() || null);
        } else {
          setMetadata(null);
        }
        setIsLoading(false);
      }
    };

    loadFeatures();
    return () => {
      isMounted = false;
    };
  }, [dataset, latCol, lonCol]);

  // Unique categories for filtering
  const availableCategories = useMemo(() => {
    const cats = new Set<string>();
    features.forEach((f) => {
      if (f.properties.category) cats.add(f.properties.category);
    });
    return ["All", ...Array.from(cats)];
  }, [features]);

  // Filtered features
  const filteredFeatures = useMemo(() => {
    return features.filter((f) => {
      const matchCat = categoryFilter === "All" || f.properties.category === categoryFilter;
      const matchStatus = statusFilter === "All" || f.properties.status === statusFilter;
      return matchCat && matchStatus;
    });
  }, [features, categoryFilter, statusFilter]);

  // Active selected feature
  const selectedFeature = useMemo(() => {
    return features.find((f) => f.id?.toString() === selectedFeatureId) || features[0] || null;
  }, [features, selectedFeatureId]);

  // Compute map bounds with padding
  const svgBounds = useMemo(() => {
    if (features.length === 0) {
      return { minLon: -97.8, maxLon: -97.7, minLat: 30.2, maxLat: 30.35, width: 800, height: 440 };
    }
    const lons = features.map((f) => f.geometry.coordinates[0]);
    const lats = features.map((f) => f.geometry.coordinates[1]);
    const rawMinLon = Math.min(...lons);
    const rawMaxLon = Math.max(...lons);
    const rawMinLat = Math.min(...lats);
    const rawMaxLat = Math.max(...lats);

    // Add 15% margin
    const lonSpan = Math.max(rawMaxLon - rawMinLon, 0.02);
    const latSpan = Math.max(rawMaxLat - rawMinLat, 0.02);

    return {
      minLon: rawMinLon - lonSpan * 0.15,
      maxLon: rawMaxLon + lonSpan * 0.15,
      minLat: rawMinLat - latSpan * 0.15,
      maxLat: rawMaxLat + latSpan * 0.15,
      width: 800,
      height: 440,
    };
  }, [features]);

  // Project longitude and latitude into SVG coordinate space
  const projectPoint = (lon: number, lat: number) => {
    const pad = 40;
    const availWidth = svgBounds.width - pad * 2;
    const availHeight = svgBounds.height - pad * 2;

    const x = pad + ((lon - svgBounds.minLon) / (svgBounds.maxLon - svgBounds.minLon)) * availWidth;
    const y = pad + ((svgBounds.maxLat - lat) / (svgBounds.maxLat - svgBounds.minLat)) * availHeight;
    return { x, y };
  };

  // Status color helper
  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return "#10b981"; // emerald
      case "in progress":
        return "#06b6d4"; // cyan
      case "planned":
        return "#f59e0b"; // amber
      default:
        return "#8b5cf6"; // purple
    }
  };

  // Export RFC 7946 GeoJSON to file
  const handleExportGeoJson = () => {
    const geoJsonPayload = {
      type: "FeatureCollection",
      bbox: metadata?.bbox || null,
      features: filteredFeatures,
      metadata: {
        ...metadata,
        exported_at: new Date().toISOString(),
        dataset_name: dataset.name,
        table_name: dataset.tableName,
      },
    };

    const blob = new Blob([JSON.stringify(geoJsonPayload, null, 2)], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${dataset.tableName || "dataset"}_rfc7946.geojson`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Copy GeoJSON
  const handleCopyGeoJson = () => {
    if (selectedFeature) {
      navigator.clipboard.writeText(JSON.stringify(selectedFeature, null, 2));
      setCopiedJson(true);
      setTimeout(() => setCopiedJson(false), 2000);
    }
  };

  // Non-geospatial empty state
  if (!latCol || !lonCol || (features.length === 0 && !isLoading)) {
    return (
      <div
        className="glass-card"
        style={{
          padding: "36px 24px",
          textAlign: "center",
          border: "1px dashed var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
        }}
      >
        <div
          style={{
            width: "56px",
            height: "56px",
            borderRadius: "50%",
            background: "rgba(148, 163, 184, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 16px",
          }}
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
          No Spatial Coordinates Detected
        </h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", maxWidth: "520px", margin: "0 auto 16px" }}>
          The dataset <strong>{dataset.name}</strong> does not contain recognized geographic coordinate columns.
          To enable geospatial capabilities, include <code>latitude</code> and <code>longitude</code> columns in decimal degrees (WGS84 EPSG:4326).
        </p>
        <div style={{ display: "inline-flex", gap: "8px", fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          <span>Accepted column aliases:</span>
          <span style={{ color: "var(--accent-cyan)" }}>lat, latitude, y, gps_lat</span> •
          <span style={{ color: "var(--accent-cyan)" }}>lon, lng, longitude, x, gps_lon</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Geospatial Metadata Header Bar */}
      <div
        className="glass-card"
        style={{
          padding: "16px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "14px",
          border: "1px solid rgba(6, 182, 212, 0.3)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span className="badge badge-cyan" style={{ fontSize: "0.7rem", fontWeight: 700 }}>
            <span className="badge-dot" /> WGS84 (EPSG:4326)
          </span>
          <span className="badge badge-emerald" style={{ fontSize: "0.7rem" }}>
            RFC 7946 GeoJSON
          </span>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {filteredFeatures.length} of {features.length} Features Plotted
          </span>
          {metadata?.bbox && (
            <span style={{ fontSize: "0.74rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              Extent: [{metadata.bbox[0].toFixed(3)}°, {metadata.bbox[1].toFixed(3)}°] to [{metadata.bbox[2].toFixed(3)}°, {metadata.bbox[3].toFixed(3)}°]
            </span>
          )}
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            onClick={() => setShowJsonModal(true)}
            className="btn btn-secondary"
            style={{ fontSize: "0.76rem", padding: "6px 12px" }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="16 18 22 12 16 6"/>
              <polyline points="8 6 2 12 8 18"/>
            </svg>
            View GeoJSON
          </button>
          <button
            onClick={handleExportGeoJson}
            className="btn btn-primary"
            style={{ fontSize: "0.76rem", padding: "6px 12px" }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export GeoJSON
          </button>
        </div>
      </div>

      {/* Filter Chips Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: "4px" }}>
            Category:
          </span>
          {availableCategories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`btn ${categoryFilter === cat ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.74rem", padding: "4px 10px", borderRadius: "var(--radius-full)" }}
            >
              {cat}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: "4px" }}>
            Status:
          </span>
          {["All", "In Progress", "Completed", "Planned"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`btn ${statusFilter === st ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.74rem", padding: "4px 10px", borderRadius: "var(--radius-full)" }}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Map Canvas and Feature Inspector Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.8fr) minmax(320px, 1.2fr)", gap: "20px" }}>
        {/* Left: Vector Map Canvas */}
        <div
          className="glass-card"
          style={{
            position: "relative",
            overflow: "hidden",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border-subtle)",
            background: "linear-gradient(180deg, #090e1c 0%, #060913 100%)",
            minHeight: "440px",
          }}
        >
          {/* SVG Map Canvas */}
          <svg
            viewBox={`0 0 ${svgBounds.width} ${svgBounds.height}`}
            style={{ width: "100%", height: "100%", display: "block", minHeight: "440px" }}
          >
            <defs>
              {/* Subtle grid pattern */}
              <pattern id="geoGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148, 163, 184, 0.05)" strokeWidth="1" />
              </pattern>
              {/* Radial glow filter */}
              <filter id="markerGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Background grid */}
            <rect width="100%" height="100%" fill="url(#geoGrid)" />

            {/* Latitude parallels & Longitude meridians */}
            <g stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="3,3" strokeWidth="1">
              {[0.25, 0.5, 0.75].map((pct, i) => {
                const y = 40 + pct * (svgBounds.height - 80);
                const x = 40 + pct * (svgBounds.width - 80);
                const lat = svgBounds.maxLat - pct * (svgBounds.maxLat - svgBounds.minLat);
                const lon = svgBounds.minLon + pct * (svgBounds.maxLon - svgBounds.minLon);
                return (
                  <g key={i}>
                    <line x1="30" y1={y} x2={svgBounds.width - 30} y2={y} />
                    <text x="35" y={y - 4} fill="rgba(148, 163, 184, 0.4)" fontSize="9" fontFamily="monospace">
                      {lat.toFixed(3)}°N
                    </text>
                    <line x1={x} y1="30" x2={x} y2={svgBounds.height - 30} />
                    <text x={x + 4} y={svgBounds.height - 35} fill="rgba(148, 163, 184, 0.4)" fontSize="9" fontFamily="monospace">
                      {Math.abs(lon).toFixed(3)}°W
                    </text>
                  </g>
                );
              })}
            </g>

            {/* Geographic Bounding Extent Box */}
            <rect
              x="40"
              y="40"
              width={svgBounds.width - 80}
              height={svgBounds.height - 80}
              fill="none"
              stroke="rgba(6, 182, 212, 0.2)"
              strokeWidth="1"
              rx="6"
            />

            {/* Plotted Geographic Features */}
            {filteredFeatures.map((feat) => {
              const [lon, lat] = feat.geometry.coordinates;
              const { x, y } = projectPoint(lon, lat);
              const isSelected = selectedFeature?.id === feat.id;
              const isHovered = hoveredFeature?.id === feat.id;
              const color = getStatusColor(feat.properties.status);

              return (
                <g
                  key={feat.id}
                  transform={`translate(${x}, ${y})`}
                  style={{ cursor: "pointer", transition: "transform 0.15s ease" }}
                  onClick={() => setSelectedFeatureId(feat.id?.toString() || null)}
                  onMouseEnter={(e) => {
                    setHoveredFeature(feat);
                    const rect = e.currentTarget.getBoundingClientRect();
                    setTooltipPos({ x: rect.left + rect.width / 2, y: rect.top });
                  }}
                  onMouseLeave={() => setHoveredFeature(null)}
                >
                  {/* Outer pulse wave on selected or hovered */}
                  {(isSelected || isHovered) && (
                    <circle
                      r="16"
                      fill="none"
                      stroke={color}
                      strokeWidth="2"
                      opacity="0.6"
                      style={{ animation: "pulse 2s infinite" }}
                    />
                  )}

                  {/* Marker Glow Background */}
                  <circle
                    r={isSelected ? "11" : "8"}
                    fill={color}
                    opacity={isSelected ? "0.35" : "0.2"}
                  />

                  {/* Main Marker Core */}
                  <circle
                    r={isSelected ? "7" : "5.5"}
                    fill={color}
                    stroke="#ffffff"
                    strokeWidth={isSelected ? "2" : "1.5"}
                    filter="url(#markerGlow)"
                  />

                  {/* Feature ID Label */}
                  <text
                    x="9"
                    y="4"
                    fill={isSelected ? "#ffffff" : "rgba(248, 250, 252, 0.7)"}
                    fontSize={isSelected ? "10" : "8.5"}
                    fontWeight={isSelected ? "700" : "500"}
                    fontFamily="monospace"
                  >
                    {feat.properties.project_id || feat.id}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Compass / Scale Overlay */}
          <div
            style={{
              position: "absolute",
              top: "14px",
              right: "16px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              padding: "6px 10px",
              background: "rgba(10, 15, 29, 0.75)",
              backdropFilter: "blur(6px)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.7rem",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
            }}
          >
            <div style={{ color: "var(--accent-cyan)", fontWeight: 700, marginBottom: "2px" }}>▲ N</div>
            <div style={{ fontSize: "0.62rem" }}>WGS84</div>
          </div>

          {/* Legend Overlay */}
          <div
            style={{
              position: "absolute",
              bottom: "14px",
              left: "16px",
              display: "flex",
              gap: "12px",
              padding: "8px 14px",
              background: "rgba(10, 15, 29, 0.8)",
              backdropFilter: "blur(8px)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.72rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
              <span style={{ color: "var(--text-secondary)" }}>Completed</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#06b6d4" }} />
              <span style={{ color: "var(--text-secondary)" }}>In Progress</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#f59e0b" }} />
              <span style={{ color: "var(--text-secondary)" }}>Planned</span>
            </div>
          </div>
        </div>

        {/* Right: Selected Feature Inspector Card */}
        {selectedFeature ? (
          <div
            className="glass-card"
            style={{
              padding: "22px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              border: "1px solid rgba(6, 182, 212, 0.3)",
              borderRadius: "var(--radius-lg)",
            }}
          >
            <div>
              {/* Header Badges */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <span className="badge badge-purple" style={{ fontSize: "0.7rem" }}>
                  {selectedFeature.properties.category || "Public Project"}
                </span>
                <span
                  style={{
                    fontSize: "0.72rem",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontWeight: 600,
                    background: `${getStatusColor(selectedFeature.properties.status)}22`,
                    color: getStatusColor(selectedFeature.properties.status),
                    border: `1px solid ${getStatusColor(selectedFeature.properties.status)}44`,
                  }}
                >
                  {selectedFeature.properties.status || "Active"}
                </span>
              </div>

              {/* Title & Project ID */}
              <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
                {selectedFeature.properties.project_name || selectedFeature.properties.name || `Feature ${selectedFeature.id}`}
              </h3>
              <div style={{ fontSize: "0.78rem", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)", marginBottom: "16px" }}>
                ID: {selectedFeature.properties.project_id || selectedFeature.id} • {selectedFeature.properties.lead_agency || "Municipal Development"}
              </div>

              {/* Key Metrics Grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "10px",
                  padding: "12px",
                  background: "rgba(10, 15, 29, 0.5)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-subtle)",
                  marginBottom: "16px",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Allocated Budget</div>
                  <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--accent-emerald)", fontFamily: "var(--font-mono)" }}>
                    {selectedFeature.properties.budget !== undefined
                      ? `$${Number(selectedFeature.properties.budget).toLocaleString()}`
                      : selectedFeature.properties.allocated_budget !== undefined
                      ? `$${Number(selectedFeature.properties.allocated_budget).toLocaleString()}`
                      : "N/A"}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Expenditure</div>
                  <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                    {selectedFeature.properties.spent_to_date !== undefined
                      ? `$${Number(selectedFeature.properties.spent_to_date).toLocaleString()}`
                      : selectedFeature.properties.expenditure_to_date !== undefined
                      ? `$${Number(selectedFeature.properties.expenditure_to_date).toLocaleString()}`
                      : "N/A"}
                  </div>
                </div>
              </div>

              {/* Completion Progress Bar */}
              {selectedFeature.properties.completion_pct !== undefined && (
                <div style={{ marginBottom: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.74rem", marginBottom: "6px" }}>
                    <span style={{ color: "var(--text-muted)" }}>Project Completion</span>
                    <span style={{ fontWeight: 700, color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                      {selectedFeature.properties.completion_pct}%
                    </span>
                  </div>
                  <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.08)", borderRadius: "3px", overflow: "hidden" }}>
                    <div
                      style={{
                        width: `${Math.min(selectedFeature.properties.completion_pct, 100)}%`,
                        height: "100%",
                        background: "linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald))",
                        borderRadius: "3px",
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Exact Geographic Coordinates */}
              <div
                style={{
                  padding: "10px 12px",
                  background: "rgba(6, 182, 212, 0.04)",
                  border: "1px solid rgba(6, 182, 212, 0.2)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono)",
                  marginBottom: "16px",
                }}
              >
                <div style={{ color: "var(--text-muted)", marginBottom: "4px", fontSize: "0.68rem", textTransform: "uppercase" }}>
                  WGS84 Coordinates (RFC 7946 [Lon, Lat])
                </div>
                <div style={{ color: "var(--text-primary)", fontWeight: 600 }}>
                  Lat: <span style={{ color: "var(--accent-cyan)" }}>{selectedFeature.geometry.coordinates[1].toFixed(6)}°N</span> •
                  Lon: <span style={{ color: "var(--accent-cyan)" }}>{selectedFeature.geometry.coordinates[0].toFixed(6)}°E</span>
                </div>
              </div>
            </div>

            {/* Feature Action Buttons */}
            <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
              <button
                onClick={handleCopyGeoJson}
                className="btn btn-secondary"
                style={{ fontSize: "0.74rem", padding: "6px 12px" }}
              >
                {copiedJson ? "✓ Copied Feature" : "Copy GeoJSON"}
              </button>
            </div>
          </div>
        ) : (
          <div className="glass-card" style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)" }}>
            Select a point on the map to inspect project details.
          </div>
        )}
      </div>

      {/* Floating Hover Tooltip */}
      {hoveredFeature && tooltipPos && (
        <div
          style={{
            position: "fixed",
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y - 70}px`,
            transform: "translateX(-50%)",
            background: "rgba(10, 15, 29, 0.95)",
            backdropFilter: "blur(10px)",
            border: "1px solid var(--accent-cyan)",
            borderRadius: "var(--radius-sm)",
            padding: "8px 12px",
            zIndex: 100,
            pointerEvents: "none",
            boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
            whiteSpace: "nowrap",
          }}
        >
          <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {hoveredFeature.properties.project_name || hoveredFeature.id}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
            {hoveredFeature.properties.category} • {hoveredFeature.properties.status}
          </div>
        </div>
      )}

      {/* GeoJSON Feature Collection Modal Viewer */}
      {showJsonModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.8)",
            backdropFilter: "blur(8px)",
            zIndex: 70,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div className="glass-card" style={{ maxWidth: "700px", width: "100%", maxHeight: "85vh", overflowY: "auto", padding: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div>
                <span className="badge badge-cyan" style={{ marginBottom: "4px" }}>
                  RFC 7946 Compliant
                </span>
                <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  GeoJSON FeatureCollection: {dataset.name}
                </h3>
              </div>
              <button
                onClick={() => setShowJsonModal(false)}
                className="btn-ghost"
                style={{ border: "none", cursor: "pointer", fontSize: "1.4rem" }}
              >
                &times;
              </button>
            </div>

            <div style={{ maxHeight: "400px", overflowY: "auto", background: "rgba(5, 8, 16, 0.9)", borderRadius: "var(--radius-sm)", padding: "14px", border: "1px solid var(--border-subtle)", marginBottom: "16px" }}>
              <pre style={{ margin: 0, fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "#38bdf8", lineHeight: 1.4 }}>
                {JSON.stringify(
                  {
                    type: "FeatureCollection",
                    bbox: metadata?.bbox,
                    features: filteredFeatures,
                    metadata: metadata,
                  },
                  null,
                  2
                )}
              </pre>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setShowJsonModal(false)} className="btn btn-secondary">
                Close
              </button>
              <button onClick={handleExportGeoJson} className="btn btn-primary">
                Download .geojson File
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
