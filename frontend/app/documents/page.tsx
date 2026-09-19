"use client";

import React, { useState } from "react";
import PageHeader from "../components/PageHeader";
import DocumentCard from "../components/DocumentCard";
import { MOCK_DOCUMENTS, DocumentItem } from "../lib/mockData";

export default function DocumentsPage() {
  const [documents] = useState<DocumentItem[]>(MOCK_DOCUMENTS);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem>(MOCK_DOCUMENTS[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  const categories = ["All", "Budget", "Urban Planning", "Council Minutes", "Environment"];

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.summary.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === "All" || doc.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  // Mock chunk generation for the selected document
  const mockChunks = Array.from({ length: 4 }).map((_, i) => ({
    id: `chk_${selectedDoc.id}_p${i + 1}_00${i + 1}`,
    pageNumber: i + 1,
    characterCount: 420 + i * 45,
    excerpt: `Section ${i + 1}.0 - Municipal Record Excerpt from ${selectedDoc.title}: Page ${i + 1} encompasses authorized allocations, statutory guidelines, and executive summaries regarding ${selectedDoc.department} programmatic activities for the audited period.`,
    isEmbedded: true,
  }));

  return (
    <div>
      <PageHeader
        title="Audited Document Repository"
        description="Municipal PDFs parsed with strict page-boundary preservation. Text chunks are indexed into the Qdrant vector database so that every generated insight can cite exact page numbers and verbatim excerpts."
        badge="Qdrant Vector Indexing"
        badgeColor="cyan"
        actions={
          <button
            onClick={() => setUploadModalOpen(true)}
            className="btn btn-primary"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload Document
          </button>
        }
      />

      {/* Filter and Search Bar */}
      <div className="glass-card" style={{ padding: "16px 20px", marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ flex: "1 1 300px" }}>
            <input
              type="text"
              placeholder="Search documents by title, department, or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-control"
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginRight: "4px" }}>
              Category:
            </span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`btn ${categoryFilter === cat ? "btn-primary" : "btn-secondary"}`}
                style={{ padding: "6px 12px", fontSize: "0.78rem" }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
        gap: "24px",
        marginBottom: "36px",
      }}>
        {/* Left: Document List */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Ingested PDF Documents ({filteredDocs.length})
            </h2>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Select document to inspect chunks
            </span>
          </div>

          <div>
            {filteredDocs.map((doc) => (
              <div
                key={doc.id}
                style={{
                  border: selectedDoc.id === doc.id ? "2px solid var(--accent-cyan)" : "none",
                  borderRadius: "var(--radius-lg)",
                  marginBottom: "8px",
                }}
              >
                <DocumentCard doc={doc} onClick={setSelectedDoc} />
              </div>
            ))}
          </div>
        </div>

        {/* Right: Selected Document Chunks & Vector Breakdown */}
        <div>
          <div className="glass-card" style={{ padding: "22px", marginBottom: "24px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "16px" }}>
              <div>
                <span className="badge badge-cyan" style={{ marginBottom: "6px" }}>
                  {selectedDoc.category}
                </span>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  {selectedDoc.title}
                </h3>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                  {selectedDoc.department} • Uploaded {selectedDoc.date}
                </div>
              </div>

              <span className="badge badge-emerald">
                <span className="badge-dot" /> Ready & Audited
              </span>
            </div>

            {/* Document Statistics Summary */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "12px",
              padding: "12px",
              background: "rgba(10, 15, 29, 0.6)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
              marginBottom: "20px",
              textAlign: "center",
            }}>
              <div>
                <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
                  {selectedDoc.pageCount}
                </div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Total Pages</div>
              </div>
              <div>
                <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-purple)" }}>
                  {selectedDoc.chunkCount}
                </div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Vector Chunks</div>
              </div>
              <div>
                <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-emerald)" }}>
                  {selectedDoc.size}
                </div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Storage Footprint</div>
              </div>
            </div>

            {/* Chunk Inspector */}
            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
                  Extracted Text Chunks & Page Offsets
                </h4>
                <span style={{ fontSize: "0.72rem", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                  Qdrant Vector Size: 1536-dim
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {mockChunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    style={{
                      background: "rgba(255, 255, 255, 0.02)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-sm)",
                      padding: "12px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                        {chunk.id}
                      </span>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span className="badge badge-purple" style={{ fontSize: "0.65rem" }}>
                          Page {chunk.pageNumber}
                        </span>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                          {chunk.characterCount} chars
                        </span>
                      </div>
                    </div>
                    <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                      "{chunk.excerpt}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mock Upload Modal */}
      {uploadModalOpen && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.7)",
          backdropFilter: "blur(6px)",
          zIndex: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "20px",
        }}>
          <div className="glass-card" style={{ maxWidth: "520px", width: "100%", padding: "28px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Upload Municipal PDF Document
              </h3>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="btn-ghost"
                style={{ border: "none", cursor: "pointer", padding: "4px" }}
              >
                &times;
              </button>
            </div>

            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "20px" }}>
              Stage 2 Mock Environment: In Milestone 1, uploading PDF documents will trigger Python PyPDF text extraction, chunking with overlap, and vector embedding into Qdrant.
            </p>

            <div style={{
              border: "2px dashed var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "36px 20px",
              textAlign: "center",
              marginBottom: "20px",
              background: "rgba(10, 15, 29, 0.4)",
            }}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ margin: "0 auto 10px" }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <line x1="9" y1="15" x2="12" y2="12"/>
                <line x1="15" y1="15" x2="12" y2="12"/>
              </svg>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "4px" }}>
                Drag and drop PDF report
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Municipal budgets, audit reports, or ordinances up to 50MB
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setUploadModalOpen(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={() => setUploadModalOpen(false)} className="btn btn-primary">
                Process & Vectorize
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
