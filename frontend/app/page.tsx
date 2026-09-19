"use client";

import React, { useState } from "react";
import Header from "./components/Header";
import DocumentCard, { DocumentItem } from "./components/DocumentCard";
import DatasetCard, { DatasetItem } from "./components/DatasetCard";
import InspectionDrawer, {
  CitationData,
  CalculationData,
} from "./components/InspectionDrawer";

const INITIAL_DOCUMENTS: DocumentItem[] = [
  {
    id: "doc-1",
    title: "City_Adopted_Budget_2024.pdf",
    pageCount: 84,
    chunkCount: 210,
    size: "8.4 MB",
    status: "ready",
    date: "Sep 17, 2026",
  },
  {
    id: "doc-2",
    title: "Transportation_Master_Plan.pdf",
    pageCount: 42,
    chunkCount: 98,
    size: "4.1 MB",
    status: "ready",
    date: "Sep 17, 2026",
  },
];

const INITIAL_DATASETS: DatasetItem[] = [
  {
    id: "data-1",
    name: "department_expenses_2023.csv",
    format: "CSV",
    rowCount: "14,280",
    columnsCount: 12,
    tableName: "dept_expenses",
    status: "active",
  },
  {
    id: "data-2",
    name: "municipal_vendor_contracts.xlsx",
    format: "XLSX",
    rowCount: "3,840",
    columnsCount: 8,
    tableName: "vendor_contracts",
    status: "registered",
  },
];

const SAMPLE_CITATION: CitationData = {
  documentTitle: "City_Adopted_Budget_2024.pdf",
  pageNumber: 14,
  similarityScore: 0.912,
  excerpt:
    "Section 3.2 - Parks, Recreation & Community Facilities: The authorized operational allocation for fiscal year 2023 was adjusted to $4,250,000, reflecting a 6.2% increase to accommodate community center energy efficiency retrofits and expanded summer youth programming.",
  chunkId: "chk_city_budget_p14_003",
};

const SAMPLE_CALCULATION: CalculationData = {
  query:
    "SELECT department, SUM(amount) AS total_spent, COUNT(*) AS transactions FROM dept_expenses WHERE department = 'Parks & Rec' AND fiscal_year = 2023 GROUP BY department;",
  executionTimeMs: 24,
  rowsScanned: 14280,
  tableName: "dept_expenses",
  rawRows: [
    { department: "Parks & Rec", total_spent: 4250000, transactions: 412 },
  ],
  derivation:
    "Result = SUM(amount) where department = 'Parks & Rec' and fiscal_year = 2023 -> Exactly $4,250,000 across 412 audited expenditure items.",
};

export default function DashboardPage() {
  const [documents] = useState<DocumentItem[]>(INITIAL_DOCUMENTS);
  const [datasets] = useState<DatasetItem[]>(INITIAL_DATASETS);
  const [queryInput, setQueryInput] = useState(
    "What was the total expenditure for Parks & Rec in 2023, and what authorized it?"
  );
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState<"citation" | "calculation">("citation");

  const openCitationInspector = () => {
    setDrawerTab("citation");
    setDrawerOpen(true);
  };

  const openCalculationInspector = () => {
    setDrawerTab("calculation");
    setDrawerOpen(true);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Header />

      <main className="container" style={{ flex: 1, padding: "36px 24px 64px" }}>
        {/* Hero Section */}
        <section style={{ marginBottom: "36px" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
            <span className="badge badge-cyan">
              <span className="badge-dot" />
              Open Source Civic Intelligence
            </span>
            <span className="badge badge-emerald">Stage 1 Foundation Active</span>
          </div>

          <h1 style={{
            fontSize: "2.6rem",
            fontWeight: 800,
            lineHeight: 1.2,
            letterSpacing: "-0.03em",
            marginBottom: "14px",
            background: "linear-gradient(135deg, #ffffff 30%, #94a3b8 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>
            Auditable Answers from Civic Documents & Data
          </h1>

          <p style={{
            fontSize: "1.05rem",
            color: "var(--text-secondary)",
            maxWidth: "820px",
            lineHeight: 1.6,
          }}>
            OpenCitizen AI grounds every answer in verifiable evidence. Upload municipal reports, budgets, and tabular datasets, ask natural language questions, and inspect the exact page citations and DuckDB calculations behind every claim.
          </p>

          {/* Metric Bar */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px",
            marginTop: "24px",
          }}>
            <div className="glass-card" style={{ padding: "16px 20px" }}>
              <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
                100%
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Grounded Citations
              </div>
            </div>

            <div className="glass-card" style={{ padding: "16px 20px" }}>
              <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--accent-emerald)" }}>
                0%
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Hallucinated Math (DuckDB)
              </div>
            </div>

            <div className="glass-card" style={{ padding: "16px 20px" }}>
              <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--accent-purple)" }}>
                &lt; 300 ms
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Vector Search Latency
              </div>
            </div>

            <div className="glass-card" style={{ padding: "16px 20px" }}>
              <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--accent-blue)" }}>
                Dual-Path
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                PDF Text + Tabular SQL
              </div>
            </div>
          </div>
        </section>

        {/* Dashboard Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "340px 1fr",
          gap: "28px",
          alignItems: "start",
        }}>
          {/* Left Column: Document & Dataset Ingestion Hub */}
          <aside style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Civic Documents Section */}
            <div className="glass-card" style={{ padding: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <h3 style={{ fontSize: "0.95rem", fontWeight: 700 }}>Civic Documents (PDF)</h3>
                </div>
                <span className="badge badge-cyan" style={{ fontSize: "0.7rem" }}>
                  {documents.length} Indexed
                </span>
              </div>

              {/* Upload Dropzone */}
              <div style={{
                border: "2px dashed var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "20px 16px",
                textAlign: "center",
                marginBottom: "16px",
                background: "rgba(255, 255, 255, 0.01)",
                cursor: "pointer",
                transition: "border-color 0.2s ease",
              }}>
                <div style={{ color: "var(--accent-cyan)", marginBottom: "6px" }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ margin: "0 auto" }}>
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <div style={{ fontSize: "0.82rem", fontWeight: 600 }}>Drop PDF documents here</div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "2px" }}>
                  Page-preserving text extraction & vector indexing
                </div>
              </div>

              {/* Document List */}
              {documents.map((doc) => (
                <DocumentCard key={doc.id} doc={doc} />
              ))}
            </div>

            {/* Civic Datasets Section */}
            <div className="glass-card" style={{ padding: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-emerald)" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="3" y1="9" x2="21" y2="9"/>
                    <line x1="9" y1="3" x2="9" y2="21"/>
                  </svg>
                  <h3 style={{ fontSize: "0.95rem", fontWeight: 700 }}>Civic Datasets</h3>
                </div>
                <span className="badge badge-emerald" style={{ fontSize: "0.7rem" }}>
                  DuckDB Ready
                </span>
              </div>

              {/* Upload Dropzone */}
              <div style={{
                border: "2px dashed var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "20px 16px",
                textAlign: "center",
                marginBottom: "16px",
                background: "rgba(255, 255, 255, 0.01)",
                cursor: "pointer",
                transition: "border-color 0.2s ease",
              }}>
                <div style={{ color: "var(--accent-emerald)", marginBottom: "6px" }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ margin: "0 auto" }}>
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <div style={{ fontSize: "0.82rem", fontWeight: 600 }}>Drop CSV or XLSX datasets here</div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "2px" }}>
                  Auto schema inference & SQL query registration
                </div>
              </div>

              {/* Dataset List */}
              {datasets.map((ds) => (
                <DatasetCard key={ds.id} dataset={ds} />
              ))}
            </div>
          </aside>

          {/* Right Area: Interactive Query & Audit Workspace */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Query Prompt Box */}
            <div className="glass-card" style={{ padding: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span className="badge badge-blue">Interactive Workspace</span>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    Natural language querying across documents & data
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                  Dual-Retrieval Router: Enabled
                </div>
              </div>

              <div style={{ position: "relative" }}>
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="Ask a question about municipal budgets, policy reports, or civic datasets..."
                  style={{
                    width: "100%",
                    padding: "16px 120px 16px 20px",
                    background: "rgba(11, 15, 25, 0.9)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--text-primary)",
                    fontSize: "0.95rem",
                    outline: "none",
                    transition: "border-color 0.2s ease, box-shadow 0.2s ease",
                  }}
                />
                <button
                  className="btn btn-primary"
                  style={{ position: "absolute", right: "8px", top: "8px", bottom: "8px" }}
                >
                  Query
                </button>
              </div>

              {/* Prompt Suggestions */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "14px" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", alignSelf: "center" }}>
                  Try asking:
                </span>
                <button
                  onClick={() =>
                    setQueryInput(
                      "What was the total expenditure for Parks & Rec in 2023, and what authorized it?"
                    )
                  }
                  className="btn btn-secondary"
                  style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                >
                  Parks & Rec 2023 Spending
                </button>
                <button
                  onClick={() =>
                    setQueryInput(
                      "What are the key priorities outlined in the Transportation Plan?"
                    )
                  }
                  className="btn btn-secondary"
                  style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                >
                  Transportation Priorities
                </button>
              </div>
            </div>

            {/* Evidence-Grounded Response Preview */}
            <div className="glass-card" style={{ padding: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "6px",
                    background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                  </div>
                  <span style={{ fontSize: "0.95rem", fontWeight: 700 }}>OpenCitizen Grounded Answer</span>
                </div>

                <div style={{ display: "flex", gap: "10px" }}>
                  <button onClick={openCitationInspector} className="citation-pill">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    [City Budget 2024, p. 14]
                  </button>

                  <button onClick={openCalculationInspector} className="calc-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    DuckDB: $4,250,000 (24ms)
                  </button>
                </div>
              </div>

              {/* Answer Content */}
              <div style={{
                fontSize: "0.95rem",
                lineHeight: 1.7,
                color: "#e2e8f0",
                background: "rgba(7, 10, 18, 0.6)",
                padding: "20px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}>
                <p style={{ marginBottom: "12px" }}>
                  According to the audited municipal records, the total operational expenditure for the <strong>Parks & Recreation</strong> department in fiscal year 2023 was{" "}
                  <strong style={{ color: "#34d399" }}>$4,250,000</strong> across 412 audited transactions{" "}
                  <button onClick={openCalculationInspector} className="calc-badge" style={{ padding: "2px 8px", fontSize: "0.75rem" }}>
                    Inspect Calculation
                  </button>
                  .
                </p>

                <p>
                  This expenditure was formally authorized under Section 3.2 of the adopted municipal budget{" "}
                  <button onClick={openCitationInspector} className="citation-pill">
                    City Budget 2024, p. 14
                  </button>
                  , which reflects an authorized 6.2% operational adjustment dedicated toward municipal community center energy retrofits and youth programming.
                </p>
              </div>

              {/* Inspection Prompt Bar */}
              <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginTop: "16px",
                padding: "12px 16px",
                background: "rgba(6, 182, 212, 0.06)",
                border: "1px solid rgba(6, 182, 212, 0.18)",
                borderRadius: "var(--radius-sm)",
                fontSize: "0.8rem",
              }}>
                <div style={{ color: "var(--text-secondary)" }}>
                  Want to audit this claim? Inspect the exact source text chunk or the executed DuckDB SQL query.
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={openCitationInspector} className="btn btn-secondary" style={{ fontSize: "0.78rem", padding: "6px 12px" }}>
                    View Citation
                  </button>
                  <button onClick={openCalculationInspector} className="btn btn-primary" style={{ fontSize: "0.78rem", padding: "6px 12px" }}>
                    View SQL Trace
                  </button>
                </div>
              </div>
            </div>

            {/* Core Capabilities Showcase */}
            <div className="glass-card" style={{ padding: "24px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: "16px" }}>
                MVP Core Capabilities (10 Architectural Pillars)
              </h3>

              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "12px",
              }}>
                {[
                  { num: "1", title: "PDF Document Upload", desc: "Digital text PDF parsing with page-level integrity." },
                  { num: "2", title: "CSV/XLSX Tabular Upload", desc: "Automated schema detection & DuckDB table creation." },
                  { num: "3", title: "Page-Preserving Processing", desc: "500-800 token chunking with page number attribution." },
                  { num: "4", title: "Semantic Retrieval", desc: "Qdrant vector similarity indexing with similarity thresholds." },
                  { num: "5", title: "Grounded Question Answering", desc: "Zero hallucination guarantee using strict bounded context." },
                  { num: "6", title: "DuckDB SQL Analytics", desc: "Safe read-only execution for sums, averages, and group-bys." },
                  { num: "7", title: "Dynamic Recharts Visualizations", desc: "Visualizations strictly derived from actual SQL results." },
                  { num: "8", title: "In-Text Source Citations", desc: "Interactive pills linking claims directly to original pages." },
                  { num: "9", title: "Inspectable Evidence Drawer", desc: "Audit full retrieved text excerpts & relevance scores." },
                  { num: "10", title: "Calculation Lineage Trace", desc: "Complete transparency into executed SQL & raw rows." },
                ].map((cap) => (
                  <div
                    key={cap.num}
                    style={{
                      padding: "12px 14px",
                      background: "rgba(255, 255, 255, 0.02)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-sm)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span style={{
                        width: "20px",
                        height: "20px",
                        borderRadius: "50%",
                        background: "rgba(6, 182, 212, 0.15)",
                        color: "var(--accent-cyan)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.7rem",
                        fontWeight: 700,
                      }}>
                        {cap.num}
                      </span>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                        {cap.title}
                      </span>
                    </div>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "28px" }}>
                      {cap.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Slide-out Inspector Drawer */}
      <InspectionDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        tab={drawerTab}
        onTabChange={setDrawerTab}
        citation={SAMPLE_CITATION}
        calculation={SAMPLE_CALCULATION}
      />
    </div>
  );
}
