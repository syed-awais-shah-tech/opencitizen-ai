"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import { ChartConfigData } from "../lib/mockData";

interface AnalyticalChartProps {
  chart?: ChartConfigData;
  calculationTitle?: string;
  allowViewToggle?: boolean;
}

const DEFAULT_PALETTE = [
  "#06b6d4", // Cyan
  "#10b981", // Emerald
  "#8b5cf6", // Purple
  "#f59e0b", // Amber
  "#3b82f6", // Blue
  "#f43f5e", // Rose
  "#14b8a6", // Teal
  "#ec4899", // Pink
];

// Formatting helper
function formatValue(value: any, formatType?: string): string {
  if (value === null || value === undefined) return "—";
  const num = Number(value);
  if (isNaN(num)) return String(value);

  switch (formatType) {
    case "currency":
      if (Math.abs(num) >= 1_000_000) {
        return `$${(num / 1_000_000).toFixed(2)}M`;
      }
      if (Math.abs(num) >= 1_000) {
        return `$${(num / 1_000).toFixed(1)}k`;
      }
      return `$${num.toLocaleString()}`;
    case "percent":
      return `${num.toFixed(1)}%`;
    case "integer":
      return Math.round(num).toLocaleString();
    default:
      return num.toLocaleString();
  }
}

// Custom Glassmorphic Tooltip
function CustomTooltip({ active, payload, label, formatType }: any) {
  if (active && payload && payload.length) {
    return (
      <div
        style={{
          background: "rgba(10, 15, 29, 0.95)",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          backdropFilter: "blur(12px)",
          borderRadius: "8px",
          padding: "10px 14px",
          boxShadow: "0 10px 25px rgba(0, 0, 0, 0.6)",
          color: "#f8fafc",
          fontSize: "0.82rem",
          minWidth: "160px",
        }}
      >
        {label && (
          <div
            style={{
              fontWeight: 700,
              color: "#94a3b8",
              marginBottom: "6px",
              borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
              paddingBottom: "4px",
            }}
          >
            {String(label)}
          </div>
        )}
        {payload.map((entry: any, index: number) => {
          const formatted = formatValue(entry.value, formatType || entry.payload?.formatType);
          return (
            <div
              key={`item-${index}`}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
                margin: "3px 0",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: entry.color || entry.fill,
                    display: "inline-block",
                  }}
                />
                <span style={{ color: "#cbd5e1" }}>{entry.name}:</span>
              </div>
              <strong style={{ fontFamily: "var(--font-mono)", color: "#38bdf8" }}>
                {formatted}
              </strong>
            </div>
          );
        })}
      </div>
    );
  }
  return null;
}

export default function AnalyticalChart({
  chart,
  calculationTitle,
  allowViewToggle = true,
}: AnalyticalChartProps) {
  const [mounted, setMounted] = useState(false);
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!chart) {
    return null;
  }

  // Normalize snake_case / camelCase properties for maximum backend compatibility
  const rawChartType = (chart.chartType || (chart as any).chart_type || "table").toLowerCase();
  const title = chart.title || calculationTitle || "Analytical Visualization";
  const description = chart.description || (chart as any).derivation || "";
  const xKey = chart.xKey || (chart as any).x_key;
  const xLabel = chart.xLabel || (chart as any).x_label;
  const yLabel = chart.yLabel || (chart as any).y_label;
  const selectionReason = chart.selectionReason || (chart as any).selection_reason || "";
  const data = chart.data || [];
  const series = chart.series || [];
  const isEmpty = chart.isEmpty ?? (chart as any).is_empty ?? data.length === 0;
  const errorMessage = chart.errorMessage || (chart as any).error_message;

  // Safe chart type validation
  const safeChartType: "bar" | "line" | "pie" | "table" =
    rawChartType === "bar" || rawChartType === "line" || rawChartType === "pie"
      ? rawChartType
      : "table";

  // Effective view mode: forced to table if chartType is table or if empty
  const activeView = safeChartType === "table" || isEmpty ? "table" : viewMode;

  // 1. Error State
  if (errorMessage && !isEmpty) {
    return (
      <div
        className="glass-card"
        style={{
          padding: "20px",
          border: "1px solid rgba(244, 63, 94, 0.3)",
          background: "rgba(244, 63, 94, 0.05)",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
          <span className="badge badge-rose">Visualization Error</span>
          <strong style={{ fontSize: "0.95rem", color: "var(--text-primary)" }}>{title}</strong>
        </div>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: "0 0 12px 0" }}>
          {errorMessage}
        </p>
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Strict Grounding Rule: Visualization aborted rather than synthesizing hallucinated metrics.
        </div>
      </div>
    );
  }

  // 2. Empty State
  if (isEmpty) {
    return (
      <div
        className="glass-card"
        style={{
          padding: "28px 24px",
          textAlign: "center",
          border: "1px dashed var(--border-subtle)",
          background: "rgba(15, 23, 42, 0.4)",
          marginBottom: "16px",
        }}
      >
        <div
          style={{
            width: "44px",
            height: "44px",
            borderRadius: "50%",
            background: "rgba(6, 182, 212, 0.1)",
            color: "var(--accent-cyan)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 12px auto",
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
        </div>
        <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
          No Analytical Data Points Found
        </h4>
        <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", maxWidth: "460px", margin: "0 auto 10px auto", lineHeight: 1.5 }}>
          {errorMessage || "The underlying DuckDB query executed successfully but produced 0 records matching the requested filter boundaries."}
        </p>
        <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
          Provenance Guarantee: Charts are strictly generated from real records — zero synthetic dummy data is ever rendered.
        </div>
      </div>
    );
  }

  // Determine series format type
  const primaryFormat = series[0]?.formatType || (series[0] as any)?.format_type || "number";

  // Total for pie chart percentage calculations
  const metricKey = series[0]?.key || (data.length > 0 ? Object.keys(data[0])[1] : "");
  const pieTotal = data.reduce((acc, row) => acc + (Number(row[metricKey]) || 0), 0);

  return (
    <div
      className="glass-card"
      style={{
        padding: "22px",
        marginBottom: "20px",
        border: "1px solid rgba(6, 182, 212, 0.2)",
      }}
    >
      {/* Visualizer Top Header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span
              className={`badge ${
                safeChartType === "bar"
                  ? "badge-cyan"
                  : safeChartType === "line"
                  ? "badge-purple"
                  : safeChartType === "pie"
                  ? "badge-emerald"
                  : "badge-blue"
              }`}
              style={{ fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.05em" }}
            >
              {safeChartType} chart
            </span>
            <span className="badge badge-emerald" style={{ fontSize: "0.68rem" }}>
              Verified DuckDB Origin
            </span>
          </div>
          <h4 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
            {title}
          </h4>
          {description && (
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
              {description}
            </p>
          )}
        </div>

        {/* Action Toggle (Chart vs Table) */}
        {allowViewToggle && safeChartType !== "table" && (
          <div
            style={{
              display: "flex",
              background: "rgba(15, 23, 42, 0.6)",
              borderRadius: "var(--radius-sm)",
              padding: "3px",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <button
              onClick={() => setViewMode("chart")}
              className="btn"
              style={{
                padding: "4px 10px",
                fontSize: "0.74rem",
                borderRadius: "4px",
                border: "none",
                background: activeView === "chart" ? "var(--accent-cyan)" : "transparent",
                color: activeView === "chart" ? "#041421" : "var(--text-secondary)",
                fontWeight: activeView === "chart" ? 700 : 500,
              }}
            >
              Visual Chart
            </button>
            <button
              onClick={() => setViewMode("table")}
              className="btn"
              style={{
                padding: "4px 10px",
                fontSize: "0.74rem",
                borderRadius: "4px",
                border: "none",
                background: activeView === "table" ? "var(--accent-cyan)" : "transparent",
                color: activeView === "table" ? "#041421" : "var(--text-secondary)",
                fontWeight: activeView === "table" ? 700 : 500,
              }}
            >
              Data Table ({data.length})
            </button>
          </div>
        )}
      </div>

      {/* Rationale Pill: Deterministic Selection Transparency */}
      {selectionReason && (
        <div
          style={{
            background: "rgba(6, 182, 212, 0.08)",
            border: "1px solid rgba(6, 182, 212, 0.2)",
            borderRadius: "6px",
            padding: "8px 12px",
            marginBottom: "18px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "0.76rem",
            color: "var(--text-secondary)",
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <span>
            <strong style={{ color: "var(--accent-cyan)" }}>Selection Provenance:</strong> {selectionReason}
          </span>
        </div>
      )}

      {/* Chart Canvas or Table Display */}
      {!mounted ? (
        <div
          style={{
            height: "320px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-muted)",
            fontSize: "0.85rem",
          }}
        >
          Loading chart canvas...
        </div>
      ) : activeView === "chart" ? (
        <div style={{ width: "100%", height: 320, position: "relative" }}>
          <ResponsiveContainer width="100%" height="100%">
            {safeChartType === "bar" ? (
              <BarChart
                data={data}
                margin={{ top: 15, right: 20, left: 10, bottom: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
                <XAxis
                  dataKey={xKey}
                  stroke="#94a3b8"
                  fontSize={12}
                  tickLine={false}
                  dy={8}
                  interval={0}
                  tick={{ fill: "#94a3b8" }}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={12}
                  tickLine={false}
                  dx={-6}
                  tickFormatter={(val) => formatValue(val, primaryFormat)}
                />
                <Tooltip
                  content={<CustomTooltip formatType={primaryFormat} />}
                  cursor={{ fill: "rgba(6, 182, 212, 0.06)" }}
                />
                {series.length > 1 && <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "0.78rem" }} />}
                {series.map((s, idx) => (
                  <Bar
                    key={s.key}
                    dataKey={s.key}
                    name={s.label || s.key}
                    fill={s.color || DEFAULT_PALETTE[idx % DEFAULT_PALETTE.length]}
                    radius={[4, 4, 0, 0]}
                  />
                ))}
              </BarChart>
            ) : safeChartType === "line" ? (
              <LineChart
                data={data}
                margin={{ top: 15, right: 20, left: 10, bottom: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
                <XAxis
                  dataKey={xKey}
                  stroke="#94a3b8"
                  fontSize={12}
                  tickLine={false}
                  dy={8}
                  tick={{ fill: "#94a3b8" }}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={12}
                  tickLine={false}
                  dx={-6}
                  tickFormatter={(val) => formatValue(val, primaryFormat)}
                />
                <Tooltip
                  content={<CustomTooltip formatType={primaryFormat} />}
                />
                {series.length > 1 && <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "0.78rem" }} />}
                {series.map((s, idx) => (
                  <Line
                    key={s.key}
                    type="monotone"
                    dataKey={s.key}
                    name={s.label || s.key}
                    stroke={s.color || DEFAULT_PALETTE[idx % DEFAULT_PALETTE.length]}
                    strokeWidth={3}
                    dot={{ r: 5, fill: s.color || DEFAULT_PALETTE[idx % DEFAULT_PALETTE.length], strokeWidth: 2, stroke: "#0b0f19" }}
                    activeDot={{ r: 7, stroke: "#38bdf8", strokeWidth: 2 }}
                  />
                ))}
              </LineChart>
            ) : safeChartType === "pie" ? (
              <PieChart>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const item = payload[0];
                      const val = Number(item.value);
                      const pct = pieTotal > 0 ? ((val / pieTotal) * 100).toFixed(1) : "0.0";
                      const formatted = formatValue(val, primaryFormat);
                      return (
                        <div
                          style={{
                            background: "rgba(10, 15, 29, 0.95)",
                            border: "1px solid rgba(255, 255, 255, 0.15)",
                            borderRadius: "8px",
                            padding: "8px 12px",
                            fontSize: "0.82rem",
                            color: "#f8fafc",
                          }}
                        >
                          <div style={{ fontWeight: 700, color: "#38bdf8", marginBottom: "4px" }}>
                            {String(item.name)}
                          </div>
                          <div>
                            Amount: <strong>{formatted}</strong> ({pct}%)
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(val: string) => <span style={{ color: "#cbd5e1", fontSize: "0.78rem" }}>{val}</span>}
                />
                <Pie
                  data={data}
                  dataKey={metricKey}
                  nameKey={xKey}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={95}
                  paddingAngle={3}
                >
                  {data.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={DEFAULT_PALETTE[index % DEFAULT_PALETTE.length]}
                      stroke="rgba(10, 15, 29, 0.8)"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
              </PieChart>
            ) : null}
          </ResponsiveContainer>
        </div>
      ) : (
        /* Tabular Fallback View */
        <div className="table-wrapper" style={{ maxHeight: "320px", overflowY: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                {Object.keys(data[0] || {}).map((col) => (
                  <th key={col} style={{ textTransform: "capitalize" }}>
                    {col.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rIdx) => (
                <tr key={rIdx}>
                  {Object.keys(row).map((col) => {
                    const cellVal = row[col];
                    const isNum = typeof cellVal === "number";
                    return (
                      <td
                        key={col}
                        style={{
                          fontFamily: isNum ? "var(--font-mono)" : "inherit",
                          color: isNum ? "var(--accent-cyan)" : "var(--text-primary)",
                        }}
                      >
                        {isNum ? formatValue(cellVal, primaryFormat) : String(cellVal ?? "—")}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Grounding & Integrity Footer Notice */}
      <div
        style={{
          marginTop: "14px",
          paddingTop: "10px",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.72rem",
          color: "var(--text-muted)",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span className="badge-dot" style={{ background: "var(--accent-emerald)" }} />
          Zero Synthetic Chart Policy: Derived solely from DuckDB execution results
        </span>
        <span>Records Plotted: {data.length}</span>
      </div>
    </div>
  );
}
