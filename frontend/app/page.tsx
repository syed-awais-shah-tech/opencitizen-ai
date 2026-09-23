"use client";

import React, { useState } from "react";
import Link from "next/link";
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

export default function HomePage() {
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
      {/* Hero Section */}
      <section style={{ marginBottom: "36px" }}>
        <div style={{ marginBottom: "10px" }}>
          <span className="badge badge-cyan">
            <span className="badge-dot" /> Welcome to OpenCitizen AI
          </span>
        </div>
        <h1 style={{
          fontSize: "2.2rem",
          fontWeight: 800,
          lineHeight: 1.2,
          letterSpacing: "-0.03em",
          color: "var(--text-primary)",
          marginBottom: "10px",
        }}>
          Get answers from your city&apos;s<br />
          documents and data
        </h1>
        <p style={{
          fontSize: "1rem",
          color: "var(--text-secondary)",
          lineHeight: 1.6,
          maxWidth: "640px",
        }}>
          Upload budgets, reports, and spreadsheets. Ask questions in plain English.
          Get verified answers with sources you can inspect.
        </p>
      </section>

      {/* Three Action Cards */}
      <section style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        gap: "16px",
        marginBottom: "36px",
      }}>
        <Link href="/documents" style={{ textDecoration: "none" }}>
          <div className="glass-card interactive-card" style={{ padding: "24px", height: "100%" }}>
            <div style={{
              width: "48px",
              height: "48px",
              borderRadius: "12px",
              background: "rgba(6, 182, 212, 0.12)",
              border: "1px solid rgba(6, 182, 212, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-cyan)",
              marginBottom: "16px",
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <line x1="9" y1="15" x2="15" y2="15"/>
              </svg>
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
              Upload a Document
            </h3>
            <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Add a PDF report, budget, or plan. We&apos;ll read it so you can ask questions about it.
            </p>
          </div>
        </Link>

        <Link href="/datasets" style={{ textDecoration: "none" }}>
          <div className="glass-card interactive-card" style={{ padding: "24px", height: "100%" }}>
            <div style={{
              width: "48px",
              height: "48px",
              borderRadius: "12px",
              background: "rgba(16, 185, 129, 0.12)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-emerald)",
              marginBottom: "16px",
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="3" y1="15" x2="21" y2="15"/>
                <line x1="9" y1="3" x2="9" y2="21"/>
                <line x1="15" y1="3" x2="15" y2="21"/>
              </svg>
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
              Upload Data
            </h3>
            <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Add a CSV or Excel spreadsheet. Ask questions about the numbers and see the calculations.
            </p>
          </div>
        </Link>

        <Link href="/query" style={{ textDecoration: "none" }}>
          <div className="glass-card interactive-card" style={{ padding: "24px", height: "100%" }}>
            <div style={{
              width: "48px",
              height: "48px",
              borderRadius: "12px",
              background: "rgba(139, 92, 246, 0.12)",
              border: "1px solid rgba(139, 92, 246, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-purple)",
              marginBottom: "16px",
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
              </svg>
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
              Ask a Question
            </h3>
            <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Get an answer with source citations. See exactly where every fact came from.
            </p>
          </div>
        </Link>
      </section>

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

      {/* Example Q&A Spotlight */}
      <section className="glass-card" style={{ padding: "26px", marginBottom: "36px", border: "1px solid rgba(6, 182, 212, 0.3)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span className="badge badge-cyan">
              <span className="badge-dot" /> Example: See How It Works
            </span>
          </div>

          <Link href="/query" style={{ fontSize: "0.82rem", color: "var(--accent-cyan)", textDecoration: "none", fontWeight: 600 }}>
            Try it yourself &rarr;
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
            title="See how this number was calculated"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="7" y1="8" x2="17" y2="8"/>
              <line x1="7" y1="12" x2="17" y2="12"/>
            </svg>
            $4,250,000
          </button>
          . This spending was authorized under Section 3.2 of the City Adopted Budget 2024, which approved a 6.2% adjustment specifically for community center energy retrofits and summer youth programming{" "}
          <button
            onClick={() => openCitationInspector(activeSession.citations[0])}
            className="citation-pill"
            title="See the source document"
          >
            [Source 1, p.14]
          </button>
          , reconciled with zero variances against municipal warrant audits{" "}
          <button
            onClick={() => openCitationInspector(activeSession.citations[1])}
            className="citation-pill"
            title="See the source document"
          >
            [Source 2, p.5]
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
              See where this came from ({activeSession.citations.length})
            </button>
            <button
              onClick={openCalculationInspector}
              className="btn btn-secondary"
              style={{ fontSize: "0.8rem", padding: "6px 14px" }}
            >
              See the calculation
            </button>
          </div>

          <span style={{ fontSize: "0.78rem", color: "var(--accent-emerald)", fontWeight: 500 }}>
            &#10003; Every fact verified with sources
          </span>
        </div>
      </section>

      {/* How It Works */}
      <section className="glass-card" style={{ padding: "24px", marginBottom: "36px" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "14px" }}>
          How It Works
        </h3>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
        }}>
          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-cyan)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              1. Upload
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Upload your document or data file. We accept PDFs, CSVs, and Excel spreadsheets.
            </div>
          </div>

          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-emerald)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              2. We Read It
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Our system reads and understands every page, every row, every number in your files.
            </div>
          </div>

          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-purple)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              3. Ask Anything
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Type your question in plain English. Get a verified answer that links to the exact source.
            </div>
          </div>

          <div style={{ padding: "14px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--accent-amber)", fontWeight: 700, fontSize: "0.88rem", marginBottom: "4px" }}>
              4. Verify It
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Every answer shows exactly which document, page, and calculation it came from. No guessing.
            </div>
          </div>
        </div>
      </section>

      {/* Two Column Grid: Recent Documents & Recent Data */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
        gap: "24px",
        marginBottom: "36px",
      }}>
        {/* Recent Documents */}
        <div className="glass-card" style={{ padding: "22px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Recent Documents
              </h2>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                Your uploaded files
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

        {/* Recent Data */}
        <div className="glass-card" style={{ padding: "22px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Recent Data
              </h2>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                Your uploaded spreadsheets
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
