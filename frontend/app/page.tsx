"use client";

import React from "react";
import Link from "next/link";

export default function HomePage() {
  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "40px 20px" }}>
      {/* Hero Section */}
      <section style={{ textAlign: "center", marginBottom: "60px" }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "12px" }}>
          Home
        </h2>
        <h1 style={{
          fontSize: "3rem",
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: "-0.03em",
          color: "var(--text-primary)",
          marginBottom: "24px",
        }}>
          OPEN CITIZEN AI
        </h1>
        <p style={{
          fontSize: "1.2rem",
          color: "var(--text-secondary)",
          fontWeight: 500,
          marginBottom: "16px",
        }}>
          Understand public information
        </p>
        <p style={{
          fontSize: "1rem",
          color: "var(--text-secondary)",
          lineHeight: 1.6,
          marginBottom: "40px",
        }}>
          Upload a document or dataset.<br/>
          Ask a question.<br/>
          See the answer and where it came from.
        </p>

        <div style={{ display: "flex", justifyContent: "center", gap: "20px", flexWrap: "wrap" }}>
          <Link href="/documents" className="btn btn-primary" style={{ padding: "12px 24px", fontSize: "1.05rem" }}>
            [ Upload a document ]
          </Link>
          <Link href="/query" className="btn btn-secondary" style={{ padding: "12px 24px", fontSize: "1.05rem" }}>
            [ Ask a question ]
          </Link>
        </div>
      </section>

      {/* What is OpenCitizen AI? Section */}
      <section style={{
        background: "rgba(10, 15, 29, 0.4)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "40px",
        marginBottom: "30px"
      }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "16px" }}>
          What is OpenCitizen AI?
        </h2>
        <p style={{ fontSize: "1.1rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
          OpenCitizen AI helps you understand public documents and datasets. Ask questions and see the sources behind the answers.
        </p>
      </section>

      {/* How it works Section */}
      <section style={{ 
        background: "rgba(10, 15, 29, 0.4)", 
        border: "1px solid var(--border-subtle)", 
        borderRadius: "var(--radius-lg)", 
        padding: "40px",
        marginBottom: "30px"
      }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "32px", textAlign: "center" }}>
          How it works
        </h2>
        
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "30px" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "12px" }}>
              1. Upload
            </div>
            <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Add a document or dataset.
            </p>
          </div>

          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-emerald)", marginBottom: "12px" }}>
              2. Ask
            </div>
            <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Ask your question in simple words.
            </p>
          </div>

          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-purple)", marginBottom: "12px" }}>
              3. Check the source
            </div>
            <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              See the answer and the source.
            </p>
          </div>
        </div>
      </section>

      {/* What can you ask? Section */}
      <section style={{
        background: "rgba(10, 15, 29, 0.4)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "40px",
        marginBottom: "30px"
      }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "24px" }}>
          What can you ask?
        </h2>
        <ul style={{ fontSize: "1.05rem", color: "var(--text-secondary)", lineHeight: 1.8, paddingLeft: "20px" }}>
          <li>What does this report say about housing?</li>
          <li>How much money was spent on public transport?</li>
          <li>What projects are planned for next year?</li>
          <li>What changed between these two years?</li>
          <li>What are the main findings in the budget?</li>
        </ul>
      </section>

      {/* What documents are available? Section */}
      <section style={{
        background: "rgba(10, 15, 29, 0.4)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "40px"
      }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "16px" }}>
          What documents are available?
        </h2>
        <p style={{ fontSize: "1.05rem", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: "16px" }}>
          You can upload and ask questions about public reports, budgets, planning datasets, and other public information.
        </p>
        <Link href="/documents" className="btn btn-secondary" style={{ padding: "8px 16px", fontSize: "0.95rem" }}>
          [ View your documents ]
        </Link>
      </section>

    </div>
  );
}
