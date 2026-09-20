"use client";

import React from "react";
import {
  CitationData,
  CalculationData,
  EvidenceSnippetData,
  SourceDocumentData,
} from "../lib/mockData";

export type { CitationData, CalculationData, EvidenceSnippetData, SourceDocumentData };

interface InspectionDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  tab?: string;
  onTabChange?: (tab: any) => void;
  citation?: CitationData;
  snippet?: EvidenceSnippetData;
  sourceDoc?: SourceDocumentData;
  calculation?: CalculationData;
  modelIdentifier?: string;
}

export default function InspectionDrawer({
  isOpen,
  onClose,
  tab = "evidence",
  onTabChange,
  citation,
  snippet,
  sourceDoc,
  calculation,
  modelIdentifier = "gemini-2.5-flash",
}: InspectionDrawerProps) {
  if (!isOpen) return null;

  // Normalize snippet from either snippet or citation
  const activeSnippet: EvidenceSnippetData | undefined =
    snippet ||
    (citation
      ? {
          snippetId: citation.chunkId,
          documentTitle: citation.documentTitle,
          pageNumber: citation.pageNumber,
          text: citation.excerpt,
          similarityScore: citation.similarityScore,
          rank: 1,
          department: citation.department,
        }
      : undefined);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(6px)",
        zIndex: 50,
        display: "flex",
        justifyContent: "flex-end",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "560px",
          background: "#0c1220",
          borderLeft: "1px solid var(--border-subtle)",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          boxShadow: "-12px 0 36px rgba(0,0,0,0.75)",
        }}
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span className="badge badge-cyan" style={{ fontSize: "0.68rem" }}>
                Trust Layer Inspector
              </span>
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                {modelIdentifier}
              </span>
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "4px" }}>
              Evidence & Provenance Inspector
            </h3>
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
              Verifiable source excerpt and empirical retrieval metadata
            </p>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{ padding: "6px", borderRadius: "8px" }}
            aria-label="Close drawer"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Drawer Body */}
        <div style={{ padding: "24px", overflowY: "auto", flex: 1 }}>
          {activeSnippet ? (
            <div>
              {/* Document Header Card */}
              <div
                style={{
                  background: "rgba(6, 182, 212, 0.08)",
                  border: "1px solid rgba(6, 182, 212, 0.25)",
                  borderRadius: "var(--radius-md)",
                  padding: "16px 18px",
                  marginBottom: "20px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
                  <div>
                    <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--accent-cyan)", display: "block" }}>
                      {activeSnippet.documentTitle}
                    </span>
                    {activeSnippet.department && (
                      <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px", display: "block" }}>
                        Attribution: {activeSnippet.department}
                      </span>
                    )}
                  </div>
                  <span className="badge badge-cyan" style={{ fontSize: "0.72rem", whiteSpace: "nowrap" }}>
                    Page {activeSnippet.pageNumber}
                  </span>
                </div>

                {/* Empirical Metadata Grid */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "8px",
                    marginTop: "14px",
                    paddingTop: "12px",
                    borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                    fontSize: "0.75rem",
                  }}
                >
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Cosine Similarity:</span>{" "}
                    <strong style={{ color: "var(--accent-emerald)", fontFamily: "var(--font-mono)" }}>
                      {activeSnippet.similarityScore.toFixed(4)}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Retrieval Rank:</span>{" "}
                    <strong style={{ color: "var(--text-primary)" }}>#{activeSnippet.rank}</strong>
                  </div>
                  <div style={{ gridColumn: "span 2" }}>
                    <span style={{ color: "var(--text-muted)" }}>Chunk ID:</span>{" "}
                    <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
                      {activeSnippet.snippetId}
                    </span>
                  </div>
                </div>
              </div>

              {/* Verbatim Excerpt */}
              <div style={{ marginBottom: "22px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "10px",
                  }}
                >
                  <h4
                    style={{
                      fontSize: "0.82rem",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      color: "var(--text-muted)",
                      margin: 0,
                    }}
                  >
                    Verbatim Document Passage
                  </h4>
                  <span className="badge badge-emerald" style={{ fontSize: "0.68rem" }}>
                    Unmodified Text
                  </span>
                </div>

                <div
                  style={{
                    background: "#080c16",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "18px",
                    fontSize: "0.92rem",
                    lineHeight: "1.7",
                    color: "#f1f5f9",
                    fontStyle: "normal",
                    borderLeft: "4px solid var(--accent-cyan)",
                  }}
                >
                  &ldquo;{activeSnippet.text}&rdquo;
                </div>
              </div>

              {/* Trust Evaluation & Grounding Policy */}
              <div
                style={{
                  background: "rgba(15, 23, 42, 0.6)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "16px",
                  marginBottom: "20px",
                }}
              >
                <h5 style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
                  Grounding & Citation Policy
                </h5>
                <ul
                  style={{
                    margin: 0,
                    paddingLeft: "16px",
                    fontSize: "0.78rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                  }}
                >
                  <li>Every factual assertion must map directly to an excerpt extracted from the municipal document.</li>
                  <li>Cosine similarity measures mathematical vector distance between query and chunk embeddings.</li>
                  <li>No synthetic confidence percentages are fabricated.</li>
                </ul>
              </div>

              {/* Civic Notice */}
              <div style={{ fontSize: "0.74rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                Advisory Notice: Automated civic analysis is provided for transparency and research assistance and does not constitute formal legal or financial counsel.
              </div>
            </div>
          ) : sourceDoc ? (
            <div>
              <div
                style={{
                  background: "rgba(6, 182, 212, 0.08)",
                  border: "1px solid rgba(6, 182, 212, 0.25)",
                  borderRadius: "var(--radius-md)",
                  padding: "16px 18px",
                  marginBottom: "20px",
                }}
              >
                <h4 style={{ fontSize: "1rem", color: "var(--accent-cyan)", margin: "0 0 6px 0" }}>
                  {sourceDoc.documentTitle}
                </h4>
                {sourceDoc.department && (
                  <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "8px" }}>
                    Department: {sourceDoc.department}
                  </div>
                )}
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                  Total Cited Chunks: <strong>{sourceDoc.chunkCount}</strong>
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  Cited Page Boundaries:{" "}
                  {sourceDoc.pageNumbers.map((p) => (
                    <span key={p} className="badge badge-cyan" style={{ marginLeft: "4px", fontSize: "0.68rem" }}>
                      Page {p}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--text-muted)" }}>
              No evidence snippet selected for inspection.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
