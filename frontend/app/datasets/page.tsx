"use client";

import React, { useState } from "react";
import PageHeader from "../components/PageHeader";
import DatasetCard from "../components/DatasetCard";
import SqlTraceViewer from "../components/SqlTraceViewer";
import { MOCK_DATASETS, DatasetItem, CalculationData } from "../lib/mockData";

export default function DatasetsPage() {
  const [datasets] = useState<DatasetItem[]>(MOCK_DATASETS);
  const [selectedDataset, setSelectedDataset] = useState<DatasetItem>(MOCK_DATASETS[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  // Sample custom SQL Sandbox state
  const [sqlInput, setSqlInput] = useState(
    `SELECT department, SUM(amount) AS total_spent, COUNT(*) AS count\nFROM dept_expenses\nGROUP BY department\nORDER BY total_spent DESC;`
  );
  const [activeCalculation, setActiveCalculation] = useState<CalculationData>({
    query: `SELECT department, SUM(amount) AS total_spent, COUNT(*) AS count FROM dept_expenses GROUP BY department ORDER BY total_spent DESC;`,
    executionTimeMs: 18,
    rowsScanned: 14280,
    tableName: "dept_expenses",
    rawRows: [
      { department: "Transportation", total_spent: 8450000, count: 612 },
      { department: "Parks & Rec", total_spent: 4250000, count: 412 },
      { department: "Public Safety", total_spent: 3100000, count: 280 },
      { department: "Civic IT", total_spent: 1850000, count: 95 },
    ],
    derivation: "Aggregated 14,280 rows across all departments using in-process DuckDB columnar execution.",
  });

  const filteredDatasets = datasets.filter((ds) => {
    const matchesSearch =
      ds.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ds.tableName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === "All" || ds.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const categories = ["All", "Expenditure", "Procurement", "Public Works"];

  const handleRunSql = () => {
    // Mock execution for interactive feel
    setActiveCalculation({
      query: sqlInput.trim(),
      executionTimeMs: Math.floor(Math.random() * 15) + 10,
      rowsScanned: parseInt(selectedDataset.rowCount.replace(",", ""), 10) || 1000,
      tableName: selectedDataset.tableName,
      rawRows: selectedDataset.sampleRows,
      derivation: `Executed DuckDB SQL against ${selectedDataset.tableName} with instantaneous columnar scan.`,
    });
  };

  return (
    <div>
      <PageHeader
        title="Tabular Datasets & DuckDB Engine"
        description="Audit structured municipal ledgers with sub-second in-process DuckDB SQL analytics. Eliminates LLM arithmetic hallucination by performing verified computations directly on column data."
        badge="DuckDB Columnar Engine"
        badgeColor="emerald"
        actions={
          <button
            onClick={() => setUploadModalOpen(true)}
            className="btn btn-primary"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Register Dataset
          </button>
        }
      />

      {/* Filter and Search Bar */}
      <div className="glass-card" style={{ padding: "16px 20px", marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ flex: "1 1 300px" }}>
            <input
              type="text"
              placeholder="Filter datasets by name or table identifier..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-control"
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginRight: "4px" }}>
              Category:
            </span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`btn ${categoryFilter === cat ? "btn-primary" : "btn-secondary"}`}
                style={{ padding: "6px 12px", fontSize: "0.78rem" }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
        gap: "24px",
        marginBottom: "36px",
      }}>
        {/* Left: Registered Datasets List */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Registered Tables ({filteredDatasets.length})
            </h2>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Click table to inspect schema
            </span>
          </div>

          <div>
            {filteredDatasets.map((ds) => (
              <div
                key={ds.id}
                style={{
                  border: selectedDataset.id === ds.id ? "2px solid var(--accent-cyan)" : "none",
                  borderRadius: "var(--radius-lg)",
                  marginBottom: "8px",
                }}
              >
                <DatasetCard dataset={ds} onClick={setSelectedDataset} />
              </div>
            ))}
          </div>
        </div>

        {/* Right: Selected Dataset Detail & Schema */}
        <div>
          <div className="glass-card" style={{ padding: "22px", marginBottom: "24px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "16px" }}>
              <div>
                <span className="badge badge-purple" style={{ marginBottom: "6px" }}>
                  {selectedDataset.category}
                </span>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  {selectedDataset.name}
                </h3>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  Registered as: <span style={{ color: "var(--accent-cyan)" }}>{selectedDataset.tableName}</span>
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-emerald)" }}>
                  {selectedDataset.rowCount} rows
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {selectedDataset.columnsCount} columns • {selectedDataset.size}
                </div>
              </div>
            </div>

            {/* Schema Table */}
            <div style={{ marginBottom: "20px" }}>
              <h4 style={{ fontSize: "0.82rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "8px" }}>
                Column Definitions & Schema
              </h4>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Inferred Type</th>
                      <th>Storage Role</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedDataset.columns.map((col) => (
                      <tr key={col.name}>
                        <td style={{ fontWeight: 600, fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>
                          {col.name}
                        </td>
                        <td>
                          <span className="badge badge-cyan" style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem" }}>
                            {col.type}
                          </span>
                        </td>
                        <td style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                          {col.type === "DOUBLE" || col.type === "INTEGER"
                            ? "Calculable Metric (SQL Aggregation)"
                            : col.type === "DATE"
                            ? "Temporal Dimension"
                            : "Categorical Attribute"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Sample Records Table */}
            <div>
              <h4 style={{ fontSize: "0.82rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "8px" }}>
                Sample Ingested Rows
              </h4>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      {selectedDataset.columns.map((col) => (
                        <th key={col.name}>{col.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {selectedDataset.sampleRows.map((row, idx) => (
                      <tr key={idx}>
                        {selectedDataset.columns.map((col) => (
                          <td key={col.name} style={{ fontFamily: typeof row[col.name] === "number" ? "var(--font-mono)" : "inherit" }}>
                            {typeof row[col.name] === "number" ? Number(row[col.name]).toLocaleString() : String(row[col.name])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive DuckDB SQL Sandbox */}
      <section style={{ marginBottom: "36px" }}>
        <div className="glass-card" style={{ padding: "24px", border: "1px solid rgba(16, 185, 129, 0.3)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
            <div>
              <span className="badge badge-emerald" style={{ marginBottom: "6px" }}>
                <span className="badge-dot" /> Live Analytical Sandbox
              </span>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-primary)" }}>
                DuckDB SQL Query Executor
              </h2>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <button
                onClick={() => setSqlInput(`SELECT department, COUNT(*) AS count, AVG(amount) AS avg_spent FROM dept_expenses GROUP BY department;`)}
                className="btn btn-secondary"
                style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              >
                Preset: Avg by Dept
              </button>
              <button
                onClick={() => setSqlInput(`SELECT vendor_name, SUM(amount) AS total FROM dept_expenses GROUP BY vendor_name ORDER BY total DESC LIMIT 3;`)}
                className="btn btn-secondary"
                style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              >
                Preset: Top Vendors
              </button>
            </div>
          </div>

          <div style={{ marginBottom: "14px" }}>
            <textarea
              rows={3}
              value={sqlInput}
              onChange={(e) => setSqlInput(e.target.value)}
              className="input-control"
              style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", lineHeight: 1.5 }}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "18px" }}>
            <button onClick={handleRunSql} className="btn btn-primary">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Execute In-Memory Query
            </button>
          </div>

          {/* Results Output */}
          <SqlTraceViewer calculation={activeCalculation} />
        </div>
      </section>

      {/* Mock Upload Modal */}
      {uploadModalOpen && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.7)",
          backdropFilter: "blur(6px)",
          zIndex: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "20px",
        }}>
          <div className="glass-card" style={{ maxWidth: "520px", width: "100%", padding: "28px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Register Civic Dataset
              </h3>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="btn-ghost"
                style={{ border: "none", cursor: "pointer", padding: "4px" }}
              >
                &times;
              </button>
            </div>

            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "20px" }}>
              Stage 2 Mock Environment: In Milestone 1, uploading CSV or Parquet files will automatically initialize a typed table in DuckDB with automatic schema inference.
            </p>

            <div style={{
              border: "2px dashed var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "36px 20px",
              textAlign: "center",
              marginBottom: "20px",
              background: "rgba(10, 15, 29, 0.4)",
            }}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ margin: "0 auto 10px" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "4px" }}>
                Drag and drop CSV, XLSX, or Parquet
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Files up to 100MB supported for local DuckDB querying
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setUploadModalOpen(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={() => setUploadModalOpen(false)} className="btn btn-primary">
                Confirm & Register
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
