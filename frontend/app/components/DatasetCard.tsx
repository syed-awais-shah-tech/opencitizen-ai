"use client";

import React from "react";
import { DatasetItem } from "../lib/mockData";

export type { DatasetItem };

interface DatasetCardProps {
  dataset: DatasetItem;
  onClick?: (dataset: DatasetItem) => void;
}

export default function DatasetCard({ dataset, onClick }: DatasetCardProps) {
  return (
    <div
      className="glass-card interactive-card"
      style={{
        padding: "18px",
        marginBottom: "12px",
        cursor: onClick ? "pointer" : "default",
      }}
      onClick={() => onClick?.(dataset)}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "38px",
            height: "38px",
            borderRadius: "8px",
            background: "rgba(16, 185, 129, 0.12)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--accent-emerald)",
            flexShrink: 0,
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="3" y1="15" x2="21" y2="15"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
              <line x1="15" y1="3" x2="15" y2="21"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: "0.94rem", fontWeight: 600, color: "var(--text-primary)" }}>
              {dataset.name}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
              {dataset.size}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span className="badge badge-purple" style={{ fontSize: "0.68rem" }}>
            {dataset.format}
          </span>
          <span className="badge badge-emerald" style={{ fontSize: "0.68rem" }}>
            <span className="badge-dot" />
            {dataset.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Columns Pills preview */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "12px" }}>
        {dataset.columns.map((col) => (
          <span
            key={col.name}
            style={{
              fontSize: "0.7rem",
              fontFamily: "var(--font-mono)",
              padding: "2px 8px",
              borderRadius: "var(--radius-sm)",
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "var(--text-secondary)",
            }}
          >
            {col.name} <span style={{ color: "var(--accent-cyan)", fontSize: "0.65rem" }}>{col.type}</span>
          </span>
        ))}
      </div>

      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginTop: "12px",
        paddingTop: "10px",
        borderTop: "1px solid var(--border-subtle)",
        fontSize: "0.75rem",
        color: "var(--text-secondary)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ color: "var(--accent-emerald)", fontWeight: 600 }}>{dataset.rowCount}</span> rows
          <span>•</span>
          <span>{dataset.columnsCount} columns</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--accent-cyan)", fontSize: "0.72rem" }}>
          <span>Ready for questions</span>
        </div>
      </div>
    </div>
  );
}
