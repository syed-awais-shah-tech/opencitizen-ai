"use client";

import React, { useState } from "react";
import PageHeader from "../components/PageHeader";
import CitationViewer from "../components/CitationViewer";
import SqlTraceViewer from "../components/SqlTraceViewer";
import InspectionDrawer from "../components/InspectionDrawer";
import {
  MOCK_QUERY_SESSIONS,
  PRESET_QUESTIONS,
  QuerySession,
  CitationData,
  CalculationData,
} from "../lib/mockData";

export default function QueryPage() {
  const [sessions] = useState<QuerySession[]>(MOCK_QUERY_SESSIONS);
  const [activeSession, setActiveSession] = useState<QuerySession>(MOCK_QUERY_SESSIONS[0]);
  const [queryInput, setQueryInput] = useState(MOCK_QUERY_SESSIONS[0].question);
  const [isSearching, setIsSearching] = useState(false);
  const [activeTab, setActiveTab] = useState<"answer" | "citations" | "sql">("answer");

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState<"citation" | "calculation">("citation");
  const [activeCitation, setActiveCitation] = useState<CitationData | undefined>(activeSession.citations[0]);
  const [activeCalculation, setActiveCalculation] = useState<CalculationData | undefined>(activeSession.calculation);

  const handleSelectPreset = (questionText: string) => {
    setQueryInput(questionText);
    const found = sessions.find((s) => s.question.toLowerCase() === questionText.toLowerCase());
    if (found) {
      setActiveSession(found);
    }
  };

  const handleRunQuery = () => {
    setIsSearching(true);
    setTimeout(() => {
      // Pick matching session or default
      const matched = sessions.find((s) =>
        s.question.toLowerCase().includes(queryInput.toLowerCase()) ||
        queryInput.toLowerCase().includes(s.question.toLowerCase())
      ) || sessions[0];
      setActiveSession({
        ...matched,
        question: queryInput,
      });
      setIsSearching(false);
    }, 450);
  };

  const openCitationInspector = (cit: CitationData) => {
    setActiveCitation(cit);
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
      <PageHeader
        title="Evidence-Grounded AI Query"
        description="Query complex municipal records with automatic dual retrieval: Qdrant semantic search retrieves exact PDF paragraph citations, while DuckDB computes verified aggregates over tabular data."
        badge="Zero-Hallucination Query Engine"
        badgeColor="purple"
      />

      {/* Query Studio Input Box */}
      <section className="glass-card" style={{ padding: "24px", marginBottom: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            Civic Query Prompt:
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="badge badge-cyan" style={{ fontSize: "0.68rem" }}>
              Dual Orchestration: Qdrant + DuckDB
            </span>
          </div>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <textarea
            rows={3}
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="Ask a question regarding city budgets, departmental spending, or public works..."
            className="input-control"
            style={{ fontSize: "1rem", lineHeight: 1.6 }}
          />
        </div>

        {/* Preset Questions Chips */}
        <div style={{ marginBottom: "18px" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "8px" }}>
            Suggested Civic Inquiries:
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {PRESET_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => handleSelectPreset(q)}
                className="btn btn-secondary"
                style={{
                  fontSize: "0.78rem",
                  padding: "6px 12px",
                  background: queryInput === q ? "rgba(6, 182, 212, 0.15)" : "rgba(30, 41, 59, 0.5)",
                  borderColor: queryInput === q ? "var(--accent-cyan)" : "var(--border-subtle)",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Action Controls */}
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderTop: "1px solid var(--border-subtle)",
          paddingTop: "16px",
          flexWrap: "wrap",
          gap: "12px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "0.78rem", color: "var(--text-muted)" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
              <input type="checkbox" defaultChecked disabled />
              <span>Vector Search (Qdrant)</span>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
              <input type="checkbox" defaultChecked disabled />
              <span>SQL Calculation (DuckDB)</span>
            </label>
          </div>

          <button
            onClick={handleRunQuery}
            disabled={isSearching}
            className="btn btn-primary"
            style={{ padding: "10px 22px" }}
          >
            {isSearching ? (
              <span>Orchestrating Dual Search...</span>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Ask OpenCitizen AI
              </>
            )}
          </button>
        </div>
      </section>

      {/* Answer & Inspection Tabs */}
      <section className="glass-card" style={{ padding: "26px", marginBottom: "36px" }}>
        {/* Tab Controls */}
        <div className="tab-bar">
          <button
            onClick={() => setActiveTab("answer")}
            className={`tab-item ${activeTab === "answer" ? "active" : ""}`}
          >
            Audited Answer & In-Line Citations
          </button>
          <button
            onClick={() => setActiveTab("citations")}
            className={`tab-item ${activeTab === "citations" ? "active" : ""}`}
          >
            Source Citations ({activeSession.citations.length})
          </button>
          {activeSession.calculation && (
            <button
              onClick={() => setActiveTab("sql")}
              className={`tab-item ${activeTab === "sql" ? "active" : ""}`}
            >
              DuckDB SQL Trace ({activeSession.calculation.rowsScanned.toLocaleString()} rows)
            </button>
          )}
        </div>

        {/* Tab 1: Answer Content */}
        {activeTab === "answer" && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span className="badge badge-emerald">
                  <span className="badge-dot" /> Evidence Grounded
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Resolved in {activeSession.latencyMs}ms
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <button
                  onClick={() => openCitationInspector(activeSession.citations[0])}
                  className="btn btn-secondary"
                  style={{ fontSize: "0.78rem", padding: "6px 12px" }}
                >
                  Open Provenance Drawer
                </button>
              </div>
            </div>

            <div style={{
              background: "rgba(10, 15, 29, 0.7)",
              padding: "22px 24px",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
              lineHeight: 1.8,
              fontSize: "1.05rem",
              color: "var(--text-primary)",
              marginBottom: "24px",
            }}>
              {activeSession.answer}
            </div>

            {/* Quick In-Line Evidence Previews */}
            <div>
              <div style={{ fontSize: "0.82rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "12px" }}>
                Supporting Evidence & Derivation
              </div>

              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                gap: "14px",
              }}>
                {activeSession.citations.map((cit, idx) => (
                  <div
                    key={idx}
                    onClick={() => openCitationInspector(cit)}
                    className="glass-card interactive-card"
                    style={{ padding: "14px 16px", cursor: "pointer", border: "1px solid rgba(6, 182, 212, 0.25)" }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                        {cit.documentTitle}
                      </span>
                      <span className="badge badge-cyan" style={{ fontSize: "0.68rem" }}>
                        Page {cit.pageNumber}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.5, fontStyle: "italic" }}>
                      "{cit.excerpt.slice(0, 140)}..."
                    </div>
                  </div>
                ))}

                {activeSession.calculation && (
                  <div
                    onClick={openCalculationInspector}
                    className="glass-card interactive-card"
                    style={{ padding: "14px 16px", cursor: "pointer", border: "1px solid rgba(16, 185, 129, 0.25)" }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                        DuckDB SQL Trace
                      </span>
                      <span className="badge badge-emerald" style={{ fontSize: "0.68rem" }}>
                        {activeSession.calculation.executionTimeMs}ms
                      </span>
                    </div>
                    <div style={{ fontSize: "0.78rem", color: "var(--accent-emerald)", fontFamily: "var(--font-mono)", lineHeight: 1.5 }}>
                      {activeSession.calculation.derivation}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Full Citations */}
        {activeTab === "citations" && (
          <div>
            <div style={{ marginBottom: "16px", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              All matched text segments retrieved by Qdrant vector semantic search for the active query prompt:
            </div>
            {activeSession.citations.map((cit, idx) => (
              <CitationViewer
                key={idx}
                citation={cit}
                onInspect={openCitationInspector}
              />
            ))}
          </div>
        )}

        {/* Tab 3: SQL Execution Details */}
        {activeTab === "sql" && activeSession.calculation && (
          <div>
            <div style={{ marginBottom: "16px", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              The arithmetic for this response was calculated via native in-process DuckDB queries to eliminate numerical hallucination:
            </div>
            <SqlTraceViewer calculation={activeSession.calculation} />
          </div>
        )}
      </section>

      {/* Drawer */}
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
