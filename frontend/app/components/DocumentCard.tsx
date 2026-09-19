"use client";

import React from "react";
import { DocumentItem } from "../lib/mockData";

export type { DocumentItem };

interface DocumentCardProps {
  doc: DocumentItem;
  onClick?: (doc: DocumentItem) => void;
}

export default function DocumentCard({ doc, onClick }: DocumentCardProps) {
  return (
    <div
      className="glass-card interactive-card"
      style={{
        padding: "18px",
        marginBottom: "12px",
        cursor: onClick ? "pointer" : "default",
      }}
      onClick={() => onClick?.(doc)}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "38px",
            height: "38px",
            borderRadius: "8px",
            background: "rgba(6, 182, 212, 0.12)",
            border: "1px solid rgba(6, 182, 212, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--accent-cyan)",
            flexShrink: 0,
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: "0.94rem", fontWeight: 600, color: "var(--text-primary)" }}>
              {doc.title}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
              {doc.department} • {doc.size}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span className="badge badge-purple" style={{ fontSize: "0.68rem" }}>
            {doc.category}
          </span>
          <span className="badge badge-emerald" style={{ fontSize: "0.68rem" }}>
            <span className="badge-dot" />
            {doc.status.toUpperCase()}
          </span>
        </div>
      </div>

      <p style={{
        fontSize: "0.82rem",
        color: "var(--text-secondary)",
        marginTop: "10px",
        lineHeight: 1.5,
        display: "-webkit-box",
        WebkitLineClamp: 2,
        WebkitBoxOrient: "vertical",
        overflow: "hidden",
      }}>
        {doc.summary}
      </p>

      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginTop: "12px",
        paddingTop: "10px",
        borderTop: "1px solid var(--border-subtle)",
        fontSize: "0.75rem",
        color: "var(--text-secondary)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div>
            <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>{doc.pageCount}</span> pages
          </div>
          <span>•</span>
          <div>
            <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>{doc.chunkCount}</span> indexed chunks
          </div>
        </div>

        <div style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
          Added {doc.date}
        </div>
      </div>
    </div>
  );
}
