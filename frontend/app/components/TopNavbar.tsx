"use client";

import React from "react";
import { usePathname } from "next/navigation";

interface TopNavbarProps {
  onToggleSidebar: () => void;
}

const PAGE_TITLES: Record<string, { title: string; category: string }> = {
  "/": { title: "Executive Dashboard", category: "Civic Intelligence" },
  "/documents": { title: "Document Repository", category: "Ingestion & Chunks" },
  "/datasets": { title: "Tabular Datasets", category: "DuckDB Engine" },
  "/query": { title: "Evidence-Grounded Query", category: "Audited Intelligence" },
  "/evidence": { title: "Sources & Provenance", category: "Zero-Hallucination Audit" },
};

export default function TopNavbar({ onToggleSidebar }: TopNavbarProps) {
  const pathname = usePathname();
  const pageInfo = PAGE_TITLES[pathname] || { title: "OpenCitizen AI", category: "Platform" };

  return (
    <header className="app-topbar">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <button
          onClick={onToggleSidebar}
          className="mobile-toggle-btn btn btn-ghost"
          style={{
            padding: "8px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border-subtle)",
            display: "none",
          }}
          aria-label="Toggle navigation menu"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.72rem", color: "var(--text-muted)" }}>
            <span>OpenCitizen</span>
            <span>/</span>
            <span style={{ color: "var(--text-secondary)" }}>{pageInfo.category}</span>
          </div>
          <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
            {pageInfo.title}
          </div>
        </div>
      </div>

      {/* Right: Status and Quick Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {/* Mock Mode / Stage 2 Indicator */}
        <span className="badge badge-cyan" style={{ fontSize: "0.7rem" }}>
          <span className="badge-dot" /> Stage 2: UI Shell
        </span>

        {/* Backend Ready Pill */}
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 12px",
          background: "rgba(16, 185, 129, 0.08)",
          border: "1px solid rgba(16, 185, 129, 0.25)",
          borderRadius: "var(--radius-full)",
          fontSize: "0.75rem",
          color: "#34d399",
        }}>
          <span className="badge-dot" style={{ backgroundColor: "#10b981", boxShadow: "0 0 8px #10b981" }} />
          <span className="hide-mobile">FastAPI Core: Ready (:8000)</span>
        </div>

        {/* GitHub link */}
        <a
          href="https://github.com/syed-awais-shah-tech/opencitizen-ai"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{ fontSize: "0.8rem", padding: "8px 12px" }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
          </svg>
          <span className="hide-mobile">GitHub</span>
        </a>
      </div>
    </header>
  );
}
