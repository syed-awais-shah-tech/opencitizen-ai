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

      {/* How it works Section */}
      <section style={{ 
        background: "rgba(10, 15, 29, 0.4)", 
        border: "1px solid var(--border-subtle)", 
        borderRadius: "var(--radius-lg)", 
        padding: "40px",
      }}>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "32px", textAlign: "center" }}>
          How it works
        </h2>
        
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "30px" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "12px" }}>
              ① Upload
            </div>
            <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Add a document or dataset.
            </p>
          </div>

          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-emerald)", marginBottom: "12px" }}>
              ② Ask
            </div>
            <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Ask your question in simple words.
            </p>
          </div>

          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-purple)", marginBottom: "12px" }}>
              ③ Check
            </div>
            <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              See the answer and the source.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
