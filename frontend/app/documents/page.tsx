"use client";

import React, { useState, useEffect } from "react";
import PageHeader from "../components/PageHeader";
import DocumentCard from "../components/DocumentCard";
import { MOCK_DOCUMENTS, DocumentItem } from "../lib/mockData";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>(MOCK_DOCUMENTS);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem>(MOCK_DOCUMENTS[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState<"All" | "ready" | "processing" | "queued" | "failed">("All");

  // Upload modal & job tracking state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [department, setDepartment] = useState("Office of Management & Budget");
  const [category, setCategory] = useState<DocumentItem["category"]>("Budget");
  const [summary, setSummary] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Active tracked job state
  const [activeJob, setActiveJob] = useState<{
    id: string;
    documentId: string;
    title: string;
    status: "queued" | "processing" | "completed" | "failed";
    stage: string;
    progressPct: number;
    totalPages: number;
    totalChunks: number;
    errorMessage?: string;
  } | null>(null);

  const categories = ["All", "Budget", "Urban Planning", "Council Minutes", "Environment"];
  const statuses: ("All" | "ready" | "processing" | "queued" | "failed")[] = [
    "All",
    "ready",
    "processing",
    "queued",
    "failed",
  ];

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.summary.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === "All" || doc.category === categoryFilter;
    const matchesStatus =
      statusFilter === "All"
        ? true
        : statusFilter === "ready"
        ? doc.status === "ready" || doc.status === "completed"
        : doc.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  // Mock chunks for ready documents
  const mockChunks = Array.from({ length: 4 }).map((_, i) => ({
    id: `chk_${selectedDoc.id}_p${i + 1}_00${i + 1}`,
    pageNumber: i + 1,
    characterCount: 420 + i * 45,
    excerpt: `Section ${i + 1}.0 - Municipal Record Excerpt from ${selectedDoc.title}: Page ${i + 1} encompasses authorized allocations, statutory guidelines, and executive summaries regarding ${selectedDoc.department} programmatic activities for the audited period.`,
    isEmbedded: true,
  }));

  // Handle document upload with non-blocking background job creation
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsSubmitting(true);
    const fileName = selectedFile.name;
    const fileSizeMb = (selectedFile.size / (1024 * 1024)).toFixed(1) + " MB";

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("department", department);
      formData.append("category", category);
      formData.append("summary", summary || `Municipal report regarding ${department} operational policies.`);
      formData.append("sync", "false"); // Explicit non-blocking upload

      // Attempt live API upload
      const response = await fetch("http://localhost:8000/api/v1/documents/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const newDoc: DocumentItem = {
          id: data.document.id,
          title: data.document.title,
          category: category,
          pageCount: 0,
          chunkCount: 0,
          size: fileSizeMb,
          status: "queued",
          stage: "queued",
          progressPct: 0,
          jobId: data.job_id,
          date: "Just now",
          department: department,
          summary: summary || `Municipal report regarding ${department} operational policies.`,
        };

        setDocuments((prev) => [newDoc, ...prev]);
        setSelectedDoc(newDoc);
        setActiveJob({
          id: data.job_id,
          documentId: newDoc.id,
          title: newDoc.title,
          status: "queued",
          stage: "queued",
          progressPct: 0,
          totalPages: 0,
          totalChunks: 0,
        });

        // Start live polling for job status
        pollJobStatus(data.job_id, newDoc.id);
      } else {
        // Fallback simulation if backend API is not locally running
        runSimulatedJob(fileName, fileSizeMb);
      }
    } catch {
      // Offline fallback simulation
      runSimulatedJob(fileName, fileSizeMb);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Poll backend for real background job lifecycle transitions
  const pollJobStatus = async (jobId: string, documentId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/documents/jobs/${jobId}`);
        if (!res.ok) return;
        const jobData = await res.json();

        setActiveJob((prev) =>
          prev
            ? {
                ...prev,
                status: jobData.status,
                stage: jobData.stage,
                progressPct: jobData.progress_pct,
                totalPages: jobData.total_pages,
                totalChunks: jobData.total_chunks,
                errorMessage: jobData.error_message,
              }
            : null
        );

        // Update document state
        setDocuments((prev) =>
          prev.map((d) =>
            d.id === documentId
              ? {
                  ...d,
                  status: jobData.status,
                  stage: jobData.stage,
                  progressPct: jobData.progress_pct,
                  pageCount: jobData.total_pages || d.pageCount,
                  chunkCount: jobData.total_chunks || d.chunkCount,
                  errorMessage: jobData.error_message,
                }
              : d
          )
        );

        if (jobData.status === "completed" || jobData.status === "failed") {
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
      }
    }, 900);
  };

  // Simulated fallback job lifecycle for local browser demonstration
  const runSimulatedJob = (fileName: string, fileSizeMb: string) => {
    const tempDocId = `doc_${Math.random().toString(36).substring(2, 9)}`;
    const tempJobId = `job_${Math.random().toString(36).substring(2, 9)}`;

    const newDoc: DocumentItem = {
      id: tempDocId,
      title: fileName,
      category: category,
      pageCount: 0,
      chunkCount: 0,
      size: fileSizeMb,
      status: "queued",
      stage: "queued",
      progressPct: 0,
      jobId: tempJobId,
      date: "Just now",
      department: department,
      summary: summary || `Municipal report regarding ${department} operational policies.`,
    };

    setDocuments((prev) => [newDoc, ...prev]);
    setSelectedDoc(newDoc);
    setActiveJob({
      id: tempJobId,
      documentId: tempDocId,
      title: fileName,
      status: "queued",
      stage: "queued",
      progressPct: 5,
      totalPages: 0,
      totalChunks: 0,
    });

    // Simulate lifecycle: queued -> extraction -> chunking -> embedding -> vector_storage -> completed
    const stages: { stage: any; progressPct: number; delay: number }[] = [
      { stage: "extraction", progressPct: 25, delay: 1000 },
      { stage: "chunking", progressPct: 50, delay: 2000 },
      { stage: "embedding", progressPct: 75, delay: 3200 },
      { stage: "vector_storage", progressPct: 90, delay: 4400 },
      { stage: "completed", progressPct: 100, delay: 5600 },
    ];

    stages.forEach(({ stage, progressPct, delay }) => {
      setTimeout(() => {
        const isDone = stage === "completed";
        setActiveJob((prev) =>
          prev
            ? {
                ...prev,
                status: isDone ? "completed" : "processing",
                stage,
                progressPct,
                totalPages: progressPct >= 50 ? 18 : 0,
                totalChunks: progressPct >= 75 ? 42 : 0,
              }
            : null
        );

        setDocuments((prev) =>
          prev.map((d) =>
            d.id === tempDocId
              ? {
                  ...d,
                  status: isDone ? "completed" : "processing",
                  stage,
                  progressPct,
                  pageCount: progressPct >= 50 ? 18 : 0,
                  chunkCount: progressPct >= 75 ? 42 : 0,
                }
              : d
          )
        );
      }, delay);
    });
  };

  const getStageLabel = (stage: string) => {
    switch (stage) {
      case "queued":
        return "Job Queued in Worker Queue";
      case "extraction":
        return "Stage 1/4: Text & Page Boundary Extraction";
      case "chunking":
        return "Stage 2/4: Traceable Context Chunking";
      case "embedding":
        return "Stage 3/4: Computing Semantic Embeddings";
      case "vector_storage":
        return "Stage 4/4: Vector Indexing & BM25 Storage";
      case "completed":
        return "Ingestion Complete & Vector Indexed";
      case "failed":
        return "Ingestion Pipeline Failed";
      default:
        return stage.toUpperCase();
    }
  };

  return (
    <div>
      <PageHeader
        title="Audited Document Repository"
        description="Municipal PDFs processed through asynchronous background worker jobs. Ingestion coordinates text extraction, chunking with page-level integrity, dense embedding generation, and Qdrant vector storage without blocking HTTP requests."
        badge="Stage 16: Background Ingestion"
        badgeColor="cyan"
        actions={
          <button
            onClick={() => {
              setActiveJob(null);
              setSelectedFile(null);
              setUploadModalOpen(true);
            }}
            className="btn btn-primary"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload Document (Async Job)
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

          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginRight: "4px" }}>
              Status:
            </span>
            {statuses.map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`btn ${statusFilter === st ? "btn-primary" : "btn-secondary"}`}
                style={{ padding: "6px 12px", fontSize: "0.78rem" }}
              >
                {st.toUpperCase()}
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
              Select document to inspect status & vector chunks
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

        {/* Right: Selected Document Lifecycle & Inspection */}
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

              {/* Status Badge */}
              {selectedDoc.status === "completed" || selectedDoc.status === "ready" ? (
                <span className="badge badge-emerald">
                  <span className="badge-dot" /> Ready & Audited
                </span>
              ) : selectedDoc.status === "processing" ? (
                <span className="badge badge-cyan">
                  <span className="badge-dot-pulsing" /> Processing ({selectedDoc.stage || "Pipeline"})
                </span>
              ) : selectedDoc.status === "queued" ? (
                <span className="badge badge-amber">
                  <span className="badge-dot" /> Queued in Worker
                </span>
              ) : (
                <span className="badge badge-rose">
                  <span className="badge-dot" /> Ingestion Failed
                </span>
              )}
            </div>

            {/* Lifecycle Status Views */}
            {selectedDoc.status === "queued" && (
              <div style={{
                padding: "20px",
                borderRadius: "var(--radius-md)",
                background: "rgba(245, 158, 11, 0.08)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                marginBottom: "20px",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                  <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#fbbf24" }}>
                    Job Queued in Background Worker
                  </h4>
                </div>
                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  This document upload was registered non-blockingly. An asynchronous background task has been created ({selectedDoc.jobId || "job_queue"}) and is awaiting worker thread pickup for text extraction, chunking, and Qdrant embedding.
                </p>
              </div>
            )}

            {selectedDoc.status === "processing" && (
              <div style={{
                padding: "20px",
                borderRadius: "var(--radius-md)",
                background: "rgba(6, 182, 212, 0.08)",
                border: "1px solid rgba(6, 182, 212, 0.3)",
                marginBottom: "20px",
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{
                      width: "12px",
                      height: "12px",
                      borderRadius: "50%",
                      background: "var(--accent-cyan)",
                      boxShadow: "0 0 10px var(--accent-cyan)",
                      animation: "pulse-badge-dot 1.2s infinite ease-in-out",
                    }} />
                    <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
                      {getStageLabel(selectedDoc.stage || "processing")}
                    </h4>
                  </div>
                  <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
                    {selectedDoc.progressPct || 45}%
                  </span>
                </div>

                {/* Progress Bar */}
                <div style={{
                  width: "100%",
                  height: "8px",
                  borderRadius: "var(--radius-full)",
                  background: "rgba(255, 255, 255, 0.1)",
                  overflow: "hidden",
                  marginBottom: "12px",
                }}>
                  <div style={{
                    width: `${selectedDoc.progressPct || 45}%`,
                    height: "100%",
                    background: "linear-gradient(90deg, var(--accent-cyan), var(--accent-blue))",
                    borderRadius: "var(--radius-full)",
                    transition: "width 0.4s ease",
                  }} />
                </div>

                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(4, 1fr)",
                  gap: "6px",
                  fontSize: "0.7rem",
                  color: "var(--text-muted)",
                  textAlign: "center",
                }}>
                  <div style={{ color: selectedDoc.stage === "extraction" ? "var(--accent-cyan)" : "inherit" }}>
                    1. Extraction
                  </div>
                  <div style={{ color: selectedDoc.stage === "chunking" ? "var(--accent-cyan)" : "inherit" }}>
                    2. Chunking
                  </div>
                  <div style={{ color: selectedDoc.stage === "embedding" ? "var(--accent-cyan)" : "inherit" }}>
                    3. Embedding
                  </div>
                  <div style={{ color: selectedDoc.stage === "vector_storage" ? "var(--accent-cyan)" : "inherit" }}>
                    4. Vector Store
                  </div>
                </div>
              </div>
            )}

            {selectedDoc.status === "failed" && (
              <div style={{
                padding: "20px",
                borderRadius: "var(--radius-md)",
                background: "rgba(244, 63, 94, 0.08)",
                border: "1px solid rgba(244, 63, 94, 0.3)",
                marginBottom: "20px",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fb7185" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#fb7185" }}>
                    Ingestion Pipeline Failure
                  </h4>
                </div>
                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: "10px" }}>
                  The worker encountered an error while processing this document:
                </p>
                <div className="code-box" style={{ color: "#fb7185", background: "rgba(0,0,0,0.4)", fontSize: "0.75rem" }}>
                  {selectedDoc.errorMessage || "ExtractionError: PDF stream corrupted or contained unsupported font encoding."}
                </div>
              </div>
            )}

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
            {(selectedDoc.status === "ready" || selectedDoc.status === "completed") && (
              <div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                  <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
                    Extracted Text Chunks & Page Offsets
                  </h4>
                  <span style={{ fontSize: "0.72rem", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                    Qdrant Vector Size: 384-dim (Dense) + BM25 (Lexical)
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
            )}
          </div>
        </div>
      </div>

      {/* Upload Modal with Non-Blocking Background Job Tracking */}
      {uploadModalOpen && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.75)",
          backdropFilter: "blur(6px)",
          zIndex: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "20px",
        }}>
          <div className="glass-card" style={{ maxWidth: "560px", width: "100%", padding: "28px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span className="badge badge-cyan" style={{ fontSize: "0.7rem" }}>
                  Stage 16
                </span>
                <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Upload Municipal PDF Document
                </h3>
              </div>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="btn-ghost"
                style={{ border: "none", cursor: "pointer", padding: "4px" }}
              >
                &times;
              </button>
            </div>

            {!activeJob ? (
              <form onSubmit={handleUploadSubmit}>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
                  Uploads are handled non-blockingly via background worker jobs. The HTTP request returns immediately with a tracking job ID while text extraction, chunking, embedding, and vector storage execute asynchronously.
                </p>

                {/* File Dropzone */}
                <div
                  style={{
                    border: "2px dashed var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "24px 20px",
                    textAlign: "center",
                    marginBottom: "16px",
                    background: "rgba(10, 15, 29, 0.4)",
                    cursor: "pointer",
                  }}
                  onClick={() => document.getElementById("pdf-file-input")?.click()}
                >
                  <input
                    id="pdf-file-input"
                    type="file"
                    accept=".pdf"
                    style={{ display: "none" }}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                      }
                    }}
                  />
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ margin: "0 auto 8px" }}>
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="12" y1="18" x2="12" y2="12"/>
                    <line x1="9" y1="15" x2="12" y2="12"/>
                    <line x1="15" y1="15" x2="12" y2="12"/>
                  </svg>
                  <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "4px" }}>
                    {selectedFile ? selectedFile.name : "Select or drag & drop PDF document"}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                    {selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB` : "Strict magic-byte validation, max 25 MB"}
                  </div>
                </div>

                {/* Form fields */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                      Municipal Department
                    </label>
                    <input
                      type="text"
                      className="input-control"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                      Document Category
                    </label>
                    <select
                      className="input-control"
                      value={category}
                      onChange={(e) => setCategory(e.target.value as any)}
                    >
                      <option value="Budget">Budget</option>
                      <option value="Urban Planning">Urban Planning</option>
                      <option value="Public Safety">Public Safety</option>
                      <option value="Council Minutes">Council Minutes</option>
                      <option value="Environment">Environment</option>
                    </select>
                  </div>
                </div>

                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                    Executive Summary / Notes
                  </label>
                  <textarea
                    className="input-control"
                    rows={2}
                    placeholder="Brief description of the document topic or audit scope..."
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                  />
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button type="button" onClick={() => setUploadModalOpen(false)} className="btn btn-secondary">
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!selectedFile || isSubmitting}
                  >
                    {isSubmitting ? "Queueing Job..." : "Queue Background Ingestion"}
                  </button>
                </div>
              </form>
            ) : (
              /* Live Ingestion Job Tracker */
              <div>
                <div style={{
                  padding: "16px",
                  borderRadius: "var(--radius-md)",
                  background: "rgba(10, 15, 29, 0.6)",
                  border: "1px solid var(--border-subtle)",
                  marginBottom: "18px",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                      Job ID: {activeJob.id}
                    </span>
                    <span className={`badge ${
                      activeJob.status === "completed"
                        ? "badge-emerald"
                        : activeJob.status === "failed"
                        ? "badge-rose"
                        : activeJob.status === "processing"
                        ? "badge-cyan"
                        : "badge-amber"
                    }`}>
                      {activeJob.status.toUpperCase()}
                    </span>
                  </div>

                  <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
                    {activeJob.title}
                  </h4>

                  <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: "14px" }}>
                    {getStageLabel(activeJob.stage)}
                  </div>

                  {/* Progress bar */}
                  <div style={{
                    width: "100%",
                    height: "8px",
                    borderRadius: "var(--radius-full)",
                    background: "rgba(255, 255, 255, 0.1)",
                    overflow: "hidden",
                    marginBottom: "10px",
                  }}>
                    <div style={{
                      width: `${activeJob.progressPct}%`,
                      height: "100%",
                      background: activeJob.status === "failed"
                        ? "var(--accent-rose, #fb7185)"
                        : "linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald))",
                      borderRadius: "var(--radius-full)",
                      transition: "width 0.4s ease",
                    }} />
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", color: "var(--text-muted)" }}>
                    <span>Progress: {activeJob.progressPct}%</span>
                    <span>Pages: {activeJob.totalPages} • Chunks: {activeJob.totalChunks}</span>
                  </div>
                </div>

                {activeJob.status === "completed" && (
                  <div style={{
                    padding: "12px",
                    borderRadius: "var(--radius-sm)",
                    background: "rgba(16, 185, 129, 0.1)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    color: "var(--accent-emerald)",
                    fontSize: "0.82rem",
                    marginBottom: "16px",
                  }}>
                    ✓ Ingestion complete! The document is fully vector-indexed and ready for RAG inquiries.
                  </div>
                )}

                {activeJob.status === "failed" && (
                  <div style={{
                    padding: "12px",
                    borderRadius: "var(--radius-sm)",
                    background: "rgba(244, 63, 94, 0.1)",
                    border: "1px solid rgba(244, 63, 94, 0.3)",
                    color: "#fb7185",
                    fontSize: "0.82rem",
                    marginBottom: "16px",
                  }}>
                    ✕ Job failed: {activeJob.errorMessage || "Unknown error during ingestion."}
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    onClick={() => {
                      setUploadModalOpen(false);
                      setActiveJob(null);
                    }}
                    className="btn btn-primary"
                  >
                    {activeJob.status === "completed" ? "Done & View Chunks" : "Close Tracker"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
