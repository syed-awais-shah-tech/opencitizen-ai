"use client";

import React, { useState } from "react";
import { CalculationData } from "../lib/mockData";

interface SqlTraceViewerProps {
  calculation: CalculationData;
}

export default function SqlTraceViewer({ calculation }: SqlTraceViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(calculation.query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const columns = calculation.rawRows.length > 0 ? Object.keys(calculation.rawRows[0]) : [];

  return (
    <div className="glass-card" style={{ padding: "20px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "30px",
            height: "30px",
            borderRadius: "6px",
            background: "rgba(16, 185, 129, 0.15)",
            color: "var(--accent-emerald)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="7" y1="8" x2="17" y2="8"/>
              <line x1="7" y1="12" x2="17" y2="12"/>
              <line x1="7" y1="16" x2="12" y2="16"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
              DuckDB SQL Trace & Derivation
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
              Target Table: <code style={{ color: "var(--accent-cyan)" }}>{calculation.tableName}</code>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span className="badge badge-emerald" style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}>
            {calculation.executionTimeMs}ms execution
          </span>
          <span className="badge badge-purple" style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}>
            {calculation.rowsScanned.toLocaleString()} rows scanned
          </span>
        </div>
      </div>

      {/* SQL Box */}
      <div style={{ position: "relative", marginBottom: "16px" }}>
        <div className="code-box">
          <code>{calculation.query}</code>
        </div>
        <button
          onClick={handleCopy}
          className="btn btn-secondary"
          style={{
            position: "absolute",
            top: "8px",
            right: "8px",
            padding: "4px 8px",
            fontSize: "0.72rem",
          }}
        >
          {copied ? "Copied!" : "Copy SQL"}
        </button>
      </div>

      {/* Derivation Explanation */}
      <div style={{
        background: "rgba(16, 185, 129, 0.08)",
        border: "1px solid rgba(16, 185, 129, 0.25)",
        borderRadius: "var(--radius-sm)",
        padding: "12px 14px",
        marginBottom: "16px",
      }}>
        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-emerald)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>
          Verified Derivation
        </div>
        <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
          {calculation.derivation}
        </div>
      </div>

      {/* Scanned Rows Sample */}
      {columns.length > 0 && (
        <div>
          <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px" }}>
            Direct Output Rows:
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  {columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {calculation.rawRows.map((row, idx) => (
                  <tr key={idx}>
                    {columns.map((col) => (
                      <td key={col} style={{ fontFamily: typeof row[col] === "number" ? "var(--font-mono)" : "inherit" }}>
                        {typeof row[col] === "number" ? Number(row[col]).toLocaleString() : String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
