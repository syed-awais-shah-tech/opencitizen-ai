"use client";

import React from "react";

export interface CitationData {
  documentTitle: string;
  pageNumber: number;
  similarityScore: number;
  excerpt: string;
  chunkId: string;
}

export interface CalculationData {
  query: string;
  executionTimeMs: number;
  rowsScanned: number;
  tableName: string;
  rawRows: Array<Record<string, string | number>>;
  derivation: string;
}

interface InspectionDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  tab: "citation" | "calculation";
  onTabChange: (tab: "citation" | "calculation") => void;
  citation?: CitationData;
  calculation?: CalculationData;
}

export default function InspectionDrawer({
  isOpen,
  onClose,
  tab,
  onTabChange,
  citation,
  calculation,
}: InspectionDrawerProps) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(0, 0, 0, 0.6)",
      backdropFilter: "blur(6px)",
      zIndex: 50,
      display: "flex",
      justifyContent: "flex-end",
    }}>
      <div style={{
        width: "100%",
        maxWidth: "540px",
        background: "#0c1220",
        borderLeft: "1px solid var(--border-subtle)",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        boxShadow: "-10px 0 35px rgba(0,0,0,0.7)",
      }}>
        {/* Drawer Header */}
        <div style={{
          padding: "20px 24px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Audit & Provenance Inspector
            </h3>
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
              Verifiable proof behind OpenCitizen AI responses
            </p>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{ padding: "6px", borderRadius: "8px" }}
            aria-label="Close drawer"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Tab Selectors */}
        <div style={{
          display: "flex",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "0 24px",
          gap: "12px",
          background: "rgba(0, 0, 0, 0.2)",
        }}>
          <button
            onClick={() => onTabChange("citation")}
            style={{
              padding: "12px 14px",
              background: "none",
              border: "none",
              borderBottom: tab === "citation" ? "2px solid var(--accent-cyan)" : "2px solid transparent",
              color: tab === "citation" ? "var(--accent-cyan)" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            Document Citation
          </button>

          <button
            onClick={() => onTabChange("calculation")}
            style={{
              padding: "12px 14px",
              background: "none",
              border: "none",
              borderBottom: tab === "calculation" ? "2px solid var(--accent-emerald)" : "2px solid transparent",
              color: tab === "calculation" ? "var(--accent-emerald)" : "var(--text-secondary)",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
            DuckDB Calculation Trace
          </button>
        </div>

        {/* Drawer Content */}
        <div style={{ padding: "24px", overflowY: "auto", flex: 1 }}>
          {tab === "citation" && citation && (
            <div>
              <div style={{
                background: "rgba(6, 182, 212, 0.08)",
                border: "1px solid rgba(6, 182, 212, 0.25)",
                borderRadius: "var(--radius-md)",
                padding: "14px 16px",
                marginBottom: "20px",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--accent-cyan)" }}>
                    {citation.documentTitle}
                  </span>
                  <span className="badge badge-cyan" style={{ fontSize: "0.72rem" }}>
                    Page {citation.pageNumber}
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "6px" }}>
                  Vector similarity score: {(citation.similarityScore * 100).toFixed(1)}% • Chunk ID: {citation.chunkId}
                </div>
              </div>

              <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "10px" }}>
                Retrieved Document Passage
              </h4>
              <div style={{
                background: "#080c16",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "16px",
                fontSize: "0.88rem",
                lineHeight: "1.6",
                color: "#e2e8f0",
                fontStyle: "normal",
              }}>
                &ldquo;{citation.excerpt}&rdquo;
              </div>

              <div style={{ marginTop: "20px", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                Grounding policy: Every factual claim synthesized by OpenCitizen AI must be verifiable against extracted passages indexed in Qdrant.
              </div>
            </div>
          )}

          {tab === "calculation" && calculation && (
            <div>
              <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "16px",
              }}>
                <span className="badge badge-emerald">
                  <span className="badge-dot" />
                  DuckDB Executed
                </span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  Duration: {calculation.executionTimeMs} ms • Scanned: {calculation.rowsScanned.toLocaleString()} rows
                </span>
              </div>

              <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "8px" }}>
                Exact Executed SQL Query
              </h4>
              <div className="code-box" style={{ marginBottom: "18px" }}>
                {calculation.query}
              </div>

              <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "8px" }}>
                Raw Execution Result Table
              </h4>
              <div style={{
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                overflow: "hidden",
                marginBottom: "18px",
              }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
                  <thead style={{ background: "rgba(255, 255, 255, 0.04)" }}>
                    <tr>
                      {Object.keys(calculation.rawRows[0] || {}).map((header) => (
                        <th key={header} style={{ padding: "8px 12px", borderBottom: "1px solid var(--border-subtle)", color: "var(--text-secondary)" }}>
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {calculation.rawRows.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        {Object.values(row).map((val, cIdx) => (
                          <td key={cIdx} style={{ padding: "8px 12px", fontFamily: typeof val === "number" ? "var(--font-mono)" : "inherit" }}>
                            {typeof val === "number" ? val.toLocaleString() : String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "8px" }}>
                Arithmetic Derivation
              </h4>
              <div style={{
                background: "rgba(16, 185, 129, 0.06)",
                border: "1px solid rgba(16, 185, 129, 0.2)",
                borderRadius: "var(--radius-sm)",
                padding: "12px 14px",
                fontSize: "0.82rem",
                color: "#6ee7b7",
                fontFamily: "var(--font-mono)",
              }}>
                {calculation.derivation}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
