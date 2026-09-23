"use client";

import React, { useState } from "react";
import Link from "next/link";
import DocumentCard from "./components/DocumentCard";
import DatasetCard from "./components/DatasetCard";
import InspectionDrawer from "./components/InspectionDrawer";
import {
  MOCK_DOCUMENTS,
  MOCK_DATASETS,
  MOCK_QUERY_SESSIONS,
  PRESET_QUESTIONS,
  CitationData,
  CalculationData,
} from "./lib/mockData";

export default function HomePage() {
  const activeSession = MOCK_QUERY_SESSIONS[0];
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState<"citation" | "calculation">("citation");
  const [activeCitation, setActiveCitation] = useState<CitationData | undefined>(activeSession.citations[0]);
  const [activeCalculation, setActiveCalculation] = useState<CalculationData | undefined>(activeSession.calculation);

  return (
    <div>
      {/* What is OpenCitizen AI? */}
      <section style={{ marginBottom: "36px" }}>
        <h1 style={{
          fontSize: "2.2rem",
          fontWeight: 800,
          lineHeight: 1.2,
          letterSpacing: "-0.03em",
          color: "var(--text-primary)",
          marginBottom: "16px",
        }}>
          What is OpenCitizen AI?
        </h1>
        <p style={{
          fontSize: "1.05rem",
          color: "var(--text-secondary)",
          lineHeight: 1.6,
          maxWidth: "700px",
        }}>
          OpenCitizen AI helps you understand public documents and datasets. 
          Ask questions and see the sources behind the answers.
        </p>
      </section>

      {/* How it works */}
      <section style={{ marginBottom: "36px" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "20px" }}>
          How it works
        </h2>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "16px",
        }}>
          <Link href="/documents" style={{ textDecoration: "none" }}>
            <div className="glass-card interactive-card" style={{ padding: "24px", height: "100%" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "8px" }}>
                1. Upload
              </h3>
              <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                Add a public report, budget, or dataset.
              </p>
            </div>
          </Link>

          <Link href="/query" style={{ textDecoration: "none" }}>
            <div className="glass-card interactive-card" style={{ padding: "24px", height: "100%" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-emerald)", marginBottom: "8px" }}>
                2. Ask
              </h3>
              <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                Ask a question about your documents in plain English.
              </p>
            </div>
          </Link>

          <Link href="/query" style={{ textDecoration: "none" }}>
            <div className="glass-card interactive-card" style={{ padding: "24px", height: "100%" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-purple)", marginBottom: "8px" }}>
                3. Check the source
              </h3>
              <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                See exactly which document and page the answer came from.
              </p>
            </div>
          </Link>
        </div>
      </section>

      {/* What can you ask? */}
      <section style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "20px" }}>
          What can you ask?
        </h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
          {PRESET_QUESTIONS.slice(0, 6).map((q) => (
            <Link key={q} href="/query" style={{ textDecoration: "none" }}>
              <div
                className="glass-card interactive-card"
                style={{
                  padding: "14px 20px",
                  fontSize: "0.95rem",
                  color: "var(--text-primary)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                {q}
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* What documents are available? */}
      <section style={{ marginBottom: "36px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
            What documents are available?
          </h2>
          <div style={{ display: "flex", gap: "16px" }}>
            <Link href="/documents" className="btn btn-secondary" style={{ fontSize: "0.9rem" }}>
              View all documents
            </Link>
            <Link href="/datasets" className="btn btn-secondary" style={{ fontSize: "0.9rem" }}>
              View all data
            </Link>
          </div>
        </div>

        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
          gap: "24px",
        }}>
          <div className="glass-card" style={{ padding: "22px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "16px" }}>
              Recent Documents
            </h3>
            <div>
              {MOCK_DOCUMENTS.slice(0, 3).map((doc) => (
                <DocumentCard key={doc.id} doc={doc} />
              ))}
            </div>
          </div>

          <div className="glass-card" style={{ padding: "22px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "16px" }}>
              Recent Data
            </h3>
            <div>
              {MOCK_DATASETS.slice(0, 3).map((dataset) => (
                <DatasetCard key={dataset.id} dataset={dataset} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Inspection Drawer (Kept for advanced view) */}
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
