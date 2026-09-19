"use client";

import React, { useState } from "react";
import Link from "next/link";
import PageHeader from "./components/PageHeader";
import MetricCard from "./components/MetricCard";
import DocumentCard from "./components/DocumentCard";
import DatasetCard from "./components/DatasetCard";
import InspectionDrawer from "./components/InspectionDrawer";
import {
  MOCK_DOCUMENTS,
  MOCK_DATASETS,
  MOCK_SYSTEM_METRICS,
  MOCK_QUERY_SESSIONS,
  CitationData,
  CalculationData,
} from "./lib/mockData";

export default function DashboardPage() {
  const activeSession = MOCK_QUERY_SESSIONS[0];
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState<"citation" | "calculation">("citation");
  const [activeCitation, setActiveCitation] = useState<CitationData | undefined>(activeSession.citations[0]);
  const [activeCalculation, setActiveCalculation] = useState<CalculationData | undefined>(activeSession.calculation);

  const openCitationInspector = (cit?: CitationData) => {
    if (cit) setActiveCitation(cit);
    setDrawerTab("citation");
    setDrawerOpen(true);
  };

  const openCalculationInspector = () => {
    setActiveCalculation(activeSession.calculation);
    setDrawerTab("calculation");
    setDrawerOpen(true);
  };

  return (
    <div>
      {/* Page Header */}
      <PageHeader
        title="Civic Intelligence Executive Dashboard"
        description="Ground every municipal answer in verifiable evidence. Query city budgets, transportation master plans, and financial ledgers with source citations and DuckDB arithmetic audit trails."
        badge="Zero-Hallucination Framework"
        badgeColor="cyan"
        actions={
          <>
            <Link href="/query" className="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
              </svg>
              New AI Query
            </Link>
            <Link href="/documents" className="btn btn-secondary">
              Upload Documents
            </Link>
          </>
        }
      />

      {/* Metrics Row */}
      <section style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
        gap: "16px",
        marginBottom: "32px",
      }}>
        {MOCK_SYSTEM_METRICS.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      {/* Interactive Evidence Spotlight Banner */}
      <section className="glass-card" style={{ padding: "26px", marginBottom: "36px", border: "1px solid rgba(6, 182, 212, 0.3)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span className="badge badge-cyan">
              <span className="badge-dot" /> Verified Audit Spotlight
            </span>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Latency: {activeSession.latencyMs}ms • Dual Verified (Qdrant + DuckDB)
            </span>
          </div>

          <Link href="/query" style={{ fontSize: "0.82rem", color: "var(--accent-cyan)", textDecoration: "none", fontWeight: 600 }}>
            Open Interactive Query Studio &rarr;
          </Link>
        </div>

        {/* Question */}
        <div style={{
          fontSize: "1.1rem",
          fontWeight: 600,
          color: "var(--text-primary)",
          marginBottom: "12px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}>
          <span style={{ color: "var(--accent-cyan)" }}>Q:</span>
          <span>{activeSession.question}</span>
        </div>

        {/* Answer Box */}
        <div style={{
          background: "rgba(10, 15, 29, 0.7)",
          padding: "18px 20px",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border-subtle)",
          lineHeight: 1.7,
          fontSize: "0.95rem",
          color: "var(--text-primary)",
          marginBottom: "18px",
        }}>
          In fiscal year 2023, the Parks & Recreation department had an audited total expenditure of{" "}
          <button
            onClick={openCalculationInspector}
            className="calc-badge"
            title="Inspect DuckDB SQL arithmetic derivation"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="7" y1="8" x2="17" y2="8"/>
              <line x1="7" y1="12" x2="17" y2="12"/>
            </svg>
            $4,250,000 [DuckDB: 412 rows]
          </button>
          . This spending was authorized under Section 3.2 of the City Adopted Budget 2024, which approved a 6.2% adjustment specifically for community center energy retrofits and summer youth programming{" "}
          <button
            onClick={() => openCitationInspector(activeSession.citations[0])}
            className="citation-pill"
            title="Inspect document excerpt"
          >
            [Doc 1, p.14 &bull; 91.2%]
          </button>
          , reconciled with zero variances against municipal warrant audits{" "}
          <button
            onClick={() => openCitationInspector(activeSession.citations[1])}
            className="citation-pill"
            title="Inspect audit report excerpt"
          >
            [Doc 3, p.5 &bull; 88.4%]
          </button>
          .
        </div>

        {/* Verification Controls */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              onClick={() => openCitationInspector(activeSession.citations[0])}
              className="btn btn-secondary"
              style={{ fontSize: "0.8rem", padding: "6px 14px" }}
            >
              Inspect Source Citations ({activeSession.citations.length})
            </button>
            <button
              onClick={openCalculationInspector}
              className="btn btn-secondary"
              style={{ fontSize: "0.8rem", padding: "6px 14px" }}
            >
              Inspect SQL Trace & Derivation
            </button>
          </div>

          <span style={{ fontSize: "0.78rem", color: "var(--accent-emerald)", fontWeight: 500 }}>
            &#10003; Provenance 100% Auditable
          </span>
        </div>
      </section>

      {/* Two Column Grid: Documents & Datasets */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
        gap: "24px",
        marginBottom: "36px",
      }}>
        {/* Recent Ingested Documents */}
        <div className="glass-card" style={{ padding: "22px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Audited Document Repository
              </h2>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                PDFs chunked, vectorized, and citation-indexed
              </p>
            </div>
            <Link href="/documents" className="btn btn-ghost" style={{ fontSize: "0.8rem" }}>
              View All ({MOCK_DOCUMENTS.length}) &rarr;
            </Link>
          </div>

          <div>
            {MOCK_DOCUMENTS.slice(0, 3).map((doc) => (
              <DocumentCard key={doc.id} doc={doc} />
            ))}
          </div>
        </div>

        {/* Registered Civic Datasets */}
        <div className="glass-card" style={{ padding: "22px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Civic Tabular Datasets
              </h2>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                In-process DuckDB tables ready for SQL analytics
              </p>
            </div>
            <Link href="/datasets" className="btn btn-ghost" style={{ fontSize: "0.8rem" }}>
              View All ({MOCK_DATASETS.length}) &rarr;
            </Link>
          </div>

          <div>
            {MOCK_DATASETS.map((dataset) => (
              <DatasetCard key={dataset.id} dataset={dataset} />
            ))}
          </div>
        </div>
      </div>

      {/* System Engine Architecture Banner */}
      <section className="glass-card" style={{ padding: "24px" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "14px" }}>
          Stage 2 Architecture: Zero-Hallucination Pipeline
        </h3>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
        }}>
          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-cyan)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              1. Unstructured Ingestion
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
              FastAPI parses PDF pages with absolute page numbering preserved into Qdrant vectors.
            </div>
          </div>

          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-emerald)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              2. Structured Analytics
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
              Tabular CSV/Parquet ingested into DuckDB. Pure SQL calculations prevent LLM arithmetic hallucination.
            </div>
          </div>

          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-purple)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              3. Dual-Retrieval Orchestrator
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
              Natural language queries simultaneously execute vector search and generate verified SQL queries.
            </div>
          </div>

          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-amber)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              4. Complete Provenance
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
              Every response links to exact chunk text and SQL query traces accessible through the inspection drawer.
            </div>
          </div>
        </div>
      </section>

      {/* Inspection Drawer */}
      <InspectionDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        tab={drawerTab}
        onTabChange={setDrawerTab}
        citation={activeCitation}
        calculation={activeCalculation}
      />
    </div>
  );
}
