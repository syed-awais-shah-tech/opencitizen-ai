"use client";

import React from "react";

export default function Header() {
  return (
    <header style={{
      borderBottom: "1px solid var(--border-subtle)",
      background: "rgba(7, 10, 18, 0.8)",
      backdropFilter: "blur(12px)",
      position: "sticky",
      top: 0,
      zIndex: 40,
    }}>
      <div className="container" style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "70px",
      }}>
        {/* Logo and Branding */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div style={{
            width: "38px",
            height: "38px",
            borderRadius: "10px",
            background: "linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 16px rgba(6, 182, 212, 0.4)",
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <circle cx="12" cy="11" r="3"/>
            </svg>
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "1.2rem", fontWeight: 700, letterSpacing: "-0.02em" }}>
                OpenCitizen <span style={{ color: "var(--accent-cyan)" }}>AI</span>
              </span>
              <span className="badge badge-cyan" style={{ fontSize: "0.68rem" }}>
                Stage 1: Foundation
              </span>
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Evidence-Grounded Civic Intelligence
            </div>
          </div>
        </div>

        {/* Status Indicators & Navigation */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "6px 12px",
            background: "rgba(16, 185, 129, 0.08)",
            border: "1px solid rgba(16, 185, 129, 0.25)",
            borderRadius: "var(--radius-full)",
            fontSize: "0.8rem",
            color: "#34d399",
          }}>
            <span className="badge-dot" style={{ backgroundColor: "#10b981", boxShadow: "0 0 8px #10b981" }} />
            <span>FastAPI Core: Ready (Port 8000)</span>
          </div>

          <a
            href="https://github.com/syed-awais-shah-tech/opencitizen-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ fontSize: "0.8rem", padding: "8px 14px" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
            </svg>
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
