"use client";

import React from "react";
import { CitationData } from "../lib/mockData";

interface CitationViewerProps {
  citation: CitationData;
  onInspect?: (citation: CitationData) => void;
}

export default function CitationViewer({ citation, onInspect }: CitationViewerProps) {
  return (
    <div
      className="glass-card interactive-card"
      style={{ padding: "18px 20px", marginBottom: "14px", cursor: onInspect ? "pointer" : "default" }}
      onClick={() => onInspect?.(citation)}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px", flexWrap: "wrap", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: "28px",
            height: "28px",
            borderRadius: "6px",
            background: "rgba(6, 182, 212, 0.15)",
            color: "var(--accent-cyan)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)" }}>
              {citation.documentTitle}
            </div>
            {citation.department && (
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                {citation.department}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span className="badge badge-cyan" style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
            Page {citation.pageNumber}
          </span>
          <span className="badge badge-emerald" style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
            {(citation.similarityScore * 100).toFixed(1)}% Match
          </span>
        </div>
      </div>

      <p style={{
        fontSize: "0.85rem",
        color: "var(--text-secondary)",
        lineHeight: 1.6,
        background: "rgba(10, 15, 29, 0.6)",
        padding: "12px 14px",
        borderRadius: "var(--radius-sm)",
        borderLeft: "3px solid var(--accent-cyan)",
        fontStyle: "italic",
      }}>
        "{citation.excerpt}"
      </p>

      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginTop: "12px",
        fontSize: "0.72rem",
        color: "var(--text-muted)",
        fontFamily: "var(--font-mono)",
      }}>
        <span>Chunk ID: {citation.chunkId}</span>
        {onInspect && (
          <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>Click to Inspect Excerpt &rarr;</span>
        )}
      </div>
    </div>
  );
}
