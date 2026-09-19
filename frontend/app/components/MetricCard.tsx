"use client";

import React from "react";
import { SystemMetric } from "../lib/mockData";

export default function MetricCard({ metric }: { metric: SystemMetric }) {
  const renderIcon = () => {
    switch (metric.icon) {
      case "document":
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        );
      case "dataset":
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <line x1="3" y1="9" x2="21" y2="9"/>
            <line x1="9" y1="21" x2="9" y2="9"/>
          </svg>
        );
      case "shield":
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        );
      case "activity":
      default:
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        );
    }
  };

  return (
    <div className="glass-card interactive-card" style={{ padding: "20px 22px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-secondary)" }}>
          {metric.label}
        </span>
        <div style={{
          width: "36px",
          height: "36px",
          borderRadius: "8px",
          background: "rgba(6, 182, 212, 0.12)",
          color: "var(--accent-cyan)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
          {renderIcon()}
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "baseline", gap: "10px", marginBottom: "8px" }}>
        <span style={{
          fontSize: "2rem",
          fontWeight: 800,
          letterSpacing: "-0.03em",
          color: "var(--text-primary)",
        }}>
          {metric.value}
        </span>
        {metric.trend && (
          <span className="badge badge-emerald" style={{ fontSize: "0.68rem", padding: "2px 6px" }}>
            {metric.trend}
          </span>
        )}
      </div>

      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
        {metric.subtext}
      </div>
    </div>
  );
}
