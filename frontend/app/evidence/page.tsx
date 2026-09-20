"use client";

import React, { useState } from "react";
import PageHeader from "../components/PageHeader";
import CitationViewer from "../components/CitationViewer";
import SqlTraceViewer from "../components/SqlTraceViewer";
import InspectionDrawer from "../components/InspectionDrawer";
import {
  MOCK_QUERY_SESSIONS,
  CitationData,
  CalculationData,
} from "../lib/mockData";

export default function EvidencePage() {
  const [filterType, setFilterType] = useState<"all" | "citations" | "sql">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState<"citation" | "calculation">("citation");
  const [activeCitation, setActiveCitation] = useState<CitationData | undefined>(MOCK_QUERY_SESSIONS[0].citations[0]);
  const [activeCalculation, setActiveCalculation] = useState<CalculationData | undefined>(MOCK_QUERY_SESSIONS[0].calculation);

  const openCitationInspector = (cit: CitationData) => {
    setActiveCitation(cit);
    setDrawerTab("citation");
    setDrawerOpen(true);
  };

  const openCalculationInspector = (calc: CalculationData) => {
    setActiveCalculation(calc);
    setDrawerTab("calculation");
    setDrawerOpen(true);
  };

  return (
    <div>
      <PageHeader
        title="Sources & Evidence Provenance Explorer"
        description="Inspect the exact mathematical derivations and verbatim text citations behind every OpenCitizen answer. Every query preserves its cryptographic audit trail to eliminate hallucinations."
        badge="100% Auditable Provenance"
        badgeColor="cyan"
      />

      {/* Trust & Provenance Summary Metrics */}
      <section style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "16px",
        marginBottom: "28px",
      }}>
        <div className="glass-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "6px" }}>
            Total Verified Citations
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent-cyan)" }}>
            4 Audited
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--accent-emerald)", marginTop: "4px" }}>
            100% Page Boundary Validated
          </div>
        </div>

        <div className="glass-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "6px" }}>
            SQL Calculations Executed
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent-emerald)" }}>
            3 Verified
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            DuckDB Columnar Proofs
          </div>
        </div>

        <div className="glass-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "6px" }}>
            Grounding Status
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent-emerald)" }}>
            Verified
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            Ungrounded claims rejected
          </div>
        </div>

        <div className="glass-card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "6px" }}>
            Vector Matching Algorithm
          </div>
          <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--accent-purple)", marginTop: "4px" }}>
            Cosine &gt; 0.85
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "6px" }}>
            Qdrant HNSW Index
          </div>
        </div>
      </section>

      {/* Filter and Search Bar */}
      <div className="glass-card" style={{ padding: "16px 20px", marginBottom: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ flex: "1 1 300px" }}>
            <input
              type="text"
              placeholder="Search evidence traces by document title, query, or SQL snippet..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-control"
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              onClick={() => setFilterType("all")}
              className={`btn ${filterType === "all" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.78rem", padding: "6px 14px" }}
            >
              All Evidence
            </button>
            <button
              onClick={() => setFilterType("citations")}
              className={`btn ${filterType === "citations" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.78rem", padding: "6px 14px" }}
            >
              PDF Citations Only
            </button>
            <button
              onClick={() => setFilterType("sql")}
              className={`btn ${filterType === "sql" ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.78rem", padding: "6px 14px" }}
            >
              SQL Calculations Only
            </button>
          </div>
        </div>
      </div>

      {/* Evidence Audit Stream */}
      <div style={{ display: "flex", flexDirection: "column", gap: "28px", marginBottom: "36px" }}>
        {MOCK_QUERY_SESSIONS.map((session) => {
          const matches =
            session.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
            session.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
            session.citations.some((c) => c.documentTitle.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (session.calculation && session.calculation.query.toLowerCase().includes(searchQuery.toLowerCase()));

          if (!matches) return null;

          return (
            <div key={session.id} className="glass-card" style={{ padding: "26px" }}>
              {/* Inquiry Header */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span className="badge badge-cyan">
                    <span className="badge-dot" /> Audit Session #{session.id}
                  </span>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    Executed {session.timestamp}
                  </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span className="badge badge-emerald" style={{ fontSize: "0.7rem" }}>
                    Verified Integrity
                  </span>
                </div>
              </div>

              {/* Inquiry Question & Answer Summary */}
              <div style={{ marginBottom: "20px" }}>
                <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
                  Q: {session.question}
                </div>
                <div style={{
                  fontSize: "0.9rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                  padding: "12px 16px",
                  background: "rgba(10, 15, 29, 0.5)",
                  borderRadius: "var(--radius-sm)",
                  borderLeft: "3px solid var(--accent-cyan)",
                }}>
                  {session.answer}
                </div>
              </div>

              {/* Citations Section */}
              {(filterType === "all" || filterType === "citations") && session.citations.length > 0 && (
                <div style={{ marginBottom: "20px" }}>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "10px" }}>
                    Underlying Document Citations ({session.citations.length})
                  </div>
                  <div>
                    {session.citations.map((cit, idx) => (
                      <CitationViewer
                        key={idx}
                        citation={cit}
                        onInspect={openCitationInspector}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* SQL Calculation Section */}
              {(filterType === "all" || filterType === "sql") && session.calculation && (
                <div>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "10px" }}>
                    Underlying DuckDB Columnar Calculation
                  </div>
                  <SqlTraceViewer calculation={session.calculation} />
                </div>
              )}
            </div>
          );
        })}
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
