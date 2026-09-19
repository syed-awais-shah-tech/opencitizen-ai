"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  {
    href: "/",
    label: "Dashboard",
    badge: undefined,
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
  },
  {
    href: "/documents",
    label: "Documents",
    badge: "5",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
  },
  {
    href: "/datasets",
    label: "Datasets",
    badge: "3",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="3" y1="9" x2="21" y2="9"/>
        <line x1="3" y1="15" x2="21" y2="15"/>
        <line x1="9" y1="3" x2="9" y2="21"/>
        <line x1="15" y1="3" x2="15" y2="21"/>
      </svg>
    ),
  },
  {
    href: "/query",
    label: "AI Query",
    badge: "Audited",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
      </svg>
    ),
  },
  {
    href: "/evidence",
    label: "Sources & Evidence",
    badge: "Zero-Hallucination",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <circle cx="12" cy="11" r="3"/>
      </svg>
    ),
  },
];

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile Drawer Overlay */}
      <div
        className={`sidebar-overlay ${isOpen ? "open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Main Sidebar */}
      <aside className={`app-sidebar ${isOpen ? "open" : ""}`}>
        {/* Brand Header */}
        <div style={{
          padding: "20px 20px 18px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <Link
            href="/"
            onClick={onClose}
            style={{ display: "flex", alignItems: "center", gap: "12px", textDecoration: "none" }}
          >
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 16px rgba(6, 182, 212, 0.4)",
              flexShrink: 0,
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <circle cx="12" cy="11" r="3"/>
              </svg>
            </div>
            <div>
              <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
                OpenCitizen <span style={{ color: "var(--accent-cyan)" }}>AI</span>
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                Civic Intelligence
              </div>
            </div>
          </Link>

          {/* Close button on mobile */}
          <button
            onClick={onClose}
            className="mobile-toggle-btn btn-ghost"
            style={{
              padding: "6px",
              borderRadius: "var(--radius-sm)",
              border: "none",
              cursor: "pointer",
              display: "none",
            }}
            aria-label="Close navigation"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Navigation Links */}
        <div style={{ padding: "16px 14px", flex: 1, overflowY: "auto" }}>
          <div style={{
            fontSize: "0.7rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "var(--text-muted)",
            padding: "0 10px 8px",
          }}>
            Platform Navigation
          </div>

          <nav>
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={`nav-link ${isActive ? "active" : ""}`}
                >
                  <span style={{ color: isActive ? "var(--accent-cyan)" : "inherit" }}>
                    {item.icon}
                  </span>
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.badge && (
                    <span
                      className={`badge ${isActive ? "badge-cyan" : "badge-purple"}`}
                      style={{ fontSize: "0.65rem", padding: "2px 6px" }}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Engine Architecture & Status Card */}
        <div style={{
          padding: "16px",
          margin: "12px",
          background: "rgba(15, 23, 42, 0.7)",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border-subtle)",
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)" }}>
              Engine Status
            </span>
            <span className="badge badge-emerald" style={{ fontSize: "0.62rem", padding: "2px 6px" }}>
              <span className="badge-dot" /> Live
            </span>
          </div>

          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: "6px" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Backend API</span>
              <span style={{ color: "var(--accent-emerald)", fontFamily: "var(--font-mono)" }}>FastAPI :8000</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Analytics</span>
              <span style={{ color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>DuckDB In-Proc</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Vector Store</span>
              <span style={{ color: "var(--accent-purple)", fontFamily: "var(--font-mono)" }}>Qdrant Ready</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
