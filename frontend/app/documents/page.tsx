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
      case "queued": return "Waiting to be prepared";
      case "extraction": return "Step 1: Uploading your file";
      case "chunking": return "Step 2: Reading the document";
      case "embedding": return "Step 3: Preparing it for questions";
      case "vector_storage": return "Step 3: Preparing it for questions";
      case "completed": return "Ready";
      case "failed": return "Could not process";
      default: return stage;
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto", padding: "40px 20px" }}>
      <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "12px" }}>
        Upload
      </h2>
      <h1 style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: "16px" }}>
        Add a document
      </h1>
      <p style={{ fontSize: "1.1rem", color: "var(--text-secondary)", marginBottom: "40px" }}>
        Upload a public report, budget, plan, or dataset.
      </p>

      {!activeJob ? (
        <div 
          onClick={() => {
            // Simulate selecting a file
            runSimulatedJob("city_budget_2024.pdf", "4.5 MB");
          }}
          style={{
            border: "2px dashed var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "60px 20px",
            textAlign: "center",
            cursor: "pointer",
            background: "rgba(10, 15, 29, 0.4)",
            marginBottom: "20px"
          }}
        >
          <div style={{ fontSize: "1.2rem", color: "var(--text-primary)", marginBottom: "20px" }}>
            Drop your file here
          </div>
          <button className="btn btn-secondary">
            [ Choose a file ]
          </button>
        </div>
      ) : (
        <div style={{
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "30px",
          background: "rgba(10, 15, 29, 0.6)",
          marginBottom: "20px"
        }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>
            Processing
          </h3>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "24px" }}>
            Preparing your document
          </h2>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "32px", fontSize: "1.1rem", color: "var(--text-secondary)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", color: activeJob.progressPct >= 25 ? "var(--text-primary)" : "var(--text-muted)" }}>
              {activeJob.progressPct >= 25 ? "✓" : "○"} Uploading
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", color: activeJob.progressPct >= 50 ? "var(--text-primary)" : "var(--text-muted)" }}>
              {activeJob.progressPct >= 50 ? "✓" : "○"} Reading
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", color: activeJob.progressPct >= 75 ? "var(--accent-cyan)" : "var(--text-muted)" }}>
              {activeJob.progressPct >= 75 ? (activeJob.progressPct >= 100 ? "✓" : "●") : "○"} Preparing
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", color: activeJob.progressPct >= 100 ? "var(--accent-emerald)" : "var(--text-muted)" }}>
              {activeJob.progressPct >= 100 ? "✓ Ready" : "○ Ready"}
            </div>
          </div>

          <p style={{ fontSize: "0.95rem", color: "var(--text-muted)", marginBottom: "8px" }}>
            This may take a little while.
          </p>
          <p style={{ fontSize: "0.95rem", color: "var(--text-muted)" }}>
            You can continue when it is ready.
          </p>
        </div>
      )}

      {!activeJob && (
        <div style={{ textAlign: "center", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          PDF • CSV • Excel • JSON • Parquet
        </div>
      )}
    </div>
  );
}
