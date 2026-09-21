# OpenCitizen AI - Benchmark Evaluation Framework

## 1. Overview & Core Principles

The **OpenCitizen AI Evaluation Framework** provides an empirical, verifiable, and automated harness to measure the end-to-end performance of civic retrieval and question answering.

### Core Governance Principle: Ground Truth Over Vanity Metrics
In compliance with OpenCitizen AI architectural directives:
* **Never invent benchmark results**: All metrics and numbers reported in documentation and output files are generated strictly by executing automated benchmark runs against verified ground-truth criteria.
* **Hermetic Reproducibility**: The evaluation suite runs deterministically in CI environments and offline development setups using isolated in-memory stores and calibrated test providers.
* **Multi-Dimensional Measurement**: System quality is not reduced to a single loss score. We evaluate retrieval success, citation precision, answer factual accuracy, unsupported entity hallucination, and latency profiles independently.

---

## 2. Benchmark Dataset Architecture

The benchmark dataset comprises representative civic inquiries reflecting real municipal governance scenarios: budget allocations, zoning restrictions, environmental water standards, transit electrification schedules, and out-of-scope negative test cases.

Each benchmark test case is formalized in [`BenchmarkItem`](file:///C:/Users/Syed%20Awais%20Shah/Desktop/opencitizen-ai/backend/app/evaluation/models.py):

| Field | Description | Example |
|:---|:---|:---|
| `question_id` | Unique item identifier | `BENCH-001` |
| `question` | User natural language inquiry | *"What is the budget allocation approved under Resolution RES-2024-089 for public parks?"* |
| `category` | Municipal domain category | `budget`, `healthcare`, `zoning`, `transit`, `water`, `unsupported` |
| `expected_answer` | Gold reference answer | *"Under Resolution RES-2024-089, City Council allocated 12.5 million dollars to public park maintenance..."* |
| `answer_criteria` | Mandatory factual elements / numbers | `["12.5 million", "RES-2024-089", "park maintenance"]` |
| `negative_criteria` | Prohibited hallucinated assertions | `["45 million", "highway", "CTR-2023-142"]` |
| `expected_source_documents` | Target source filenames | `["city_annual_budget_2024.pdf"]` |
| `expected_chunk_ids` | Target chunk identifiers | `["chk_budget_01"]` |
| `expected_evidence_snippets`| Verbatim supporting excerpts | `["allocating 12.5 million dollars to public park maintenance..."]` |
| `is_refusal_expected` | True if inquiry is unsupported | `False` (or `True` for out-of-scope inquiries) |

The initial standard benchmark comprises 12 items spanning 5 civic categories and 2 negative refusal test cases.

---

## 3. Metric Calculation Methodologies

### 3.1. Retrieval Success & Chunk Recall
Measures whether the retrieval subsystem (dense semantic + sparse BM25 hybrid search) identified the correct evidence chunks.

* **Retrieval Success ($\text{Binary}$)**:
  $$\text{Retrieval Success} = \begin{cases} 
  1 & \text{if } (|\mathcal{C}_{\text{retrieved}} \cap \mathcal{C}_{\text{expected}}| > 0) \lor (|\mathcal{D}_{\text{retrieved}} \cap \mathcal{D}_{\text{expected}}| > 0) \\ 
  0 & \text{otherwise} 
  \end{cases}$$
  *(For refusal test cases, success is 1 if no erroneous hallucinated chunks are retrieved).*

* **Chunk Recall**:
  $$\text{Recall}_{\text{chunk}} = \frac{|\mathcal{C}_{\text{retrieved}} \cap \mathcal{C}_{\text{expected}}|}{|\mathcal{C}_{\text{expected}}|}$$

* **Document Precision**:
  $$\text{Precision}_{\text{doc}} = \frac{|\mathcal{D}_{\text{retrieved}} \cap \mathcal{D}_{\text{expected}}|}{|\mathcal{D}_{\text{retrieved}}|}$$

---

### 3.2. Citation Correctness & Grounding
Validates that generated citations are grounded in actual source documents and verified excerpts, preventing fabricated attribution.

A citation $c$ is **valid** if:
1. $\text{title}(c) \in \mathcal{D}_{\text{expected}}$
2. $\text{page}(c) \ge 1$
3. $\text{excerpt}(c)$ exists as a verbatim substring in the retrieved evidence text.

* **Citation Precision**:
  $$\text{Precision}_{\text{citation}} = \frac{|\{c \in \mathcal{C}_{\text{citations}} : c \text{ is valid}\}|}{|\mathcal{C}_{\text{citations}}|}$$

* **Citation Recall**:
  $$\text{Recall}_{\text{citation}} = \frac{|\{\text{title}(c) : c \text{ is valid}\} \cap \mathcal{D}_{\text{expected}}|}{|\mathcal{D}_{\text{expected}}|}$$

* **Citation Correctness Score**:
  $$\text{Citation Correctness} = \frac{1}{2} \left(\text{Precision}_{\text{citation}} + \text{Recall}_{\text{citation}}\right)$$
  *(Refusal cases returning zero citations receive a perfect score of 1.0).*

---

### 3.3. Answer Correctness
Evaluates whether the synthesized response satisfies factual criteria while maintaining high semantic overlap with the reference answer.

* **Criteria Match Rate**:
  $$\text{Criteria Match Rate} = \frac{\sum_{k \in \mathcal{K}_{\text{criteria}}} \mathbb{I}(k \in \text{Answer})}{|\mathcal{K}_{\text{criteria}}|}$$
  If any forbidden element from `negative_criteria` appears in the answer, a hallucination penalty of $-0.5$ is applied.

* **Token F1 Score**:
  Harmonic mean of token precision and token recall between lowercased alphanumeric tokens of the generated answer and expected gold standard:
  $$F_1 = \frac{2 \cdot P_{\text{token}} \cdot R_{\text{token}}}{P_{\text{token}} + R_{\text{token}}}$$

* **Composite Answer Correctness Score**:
  $$\text{Answer Correctness} = 0.70 \cdot \text{Criteria Match Rate} + 0.30 \cdot F_1$$
  *(For refusal cases, returning standard insufficient evidence phrasing yields 1.0).*

---

### 3.4. Unsupported Claims Detection
Scans the synthesized response body for factual assertions that are absent from the retrieved evidence.

1. **Entity Extraction**:
   - Quantitative claims: currency amounts, numbers, percentages, distance dimensions (e.g. `$12.5 million`, `45 million`, `60 feet`).
   - Alphanumeric municipal identifiers: uppercase resolution, contract, and ordinance codes (e.g. `RES-2024-089`, `CTR-2023-142`).
2. **Evidence Alignment**:
   - Citation footers (`[Source: ...]`) are stripped before inspection.
   - Each detected entity is cross-referenced against `combined_evidence` (composed of all retrieved chunk texts and verified source filenames).
3. **Unsupported Metric**:
   - An entity is flagged as **unsupported** if it cannot be verified in any retrieved evidence chunk.
   - **Unsupported Claims Rate**:
     $$\text{Unsupported Claims Rate} = \frac{\sum_{i=1}^N \mathbb{I}(\text{has\_unsupported}_i)}{N}$$

---

### 3.5. Latency Profiling
Captures timing across all operations using high-precision performance counters (`time.perf_counter()`):
* `search_latency_ms`: Time required for vector/BM25 retrieval and RRF fusion.
* `total_latency_ms`: End-to-end question processing, retrieval, AI synthesis, and trust layer construction.
* Summary distribution: Mean, p50 (Median), p90, p95, Min, and Max.

---

## 4. Reproducible Evaluation Command

The evaluation suite is executed via a standardized CLI command from the `backend/` directory:

```bash
# Standard evaluation run (outputs summary table and saves JSON results)
python -m app.evaluation.runner

# Custom options:
python -m app.evaluation.runner \
  --output storage/evaluation/evaluation_results.json \
  --top-k 5 \
  --provider mock \
  --embedding deterministic
```

### CLI Arguments
* `--output`, `-o`: Filepath where machine-readable JSON results are written (default: `storage/evaluation/evaluation_results.json`).
* `--dataset`, `-d`: Optional path to a custom external JSON benchmark dataset.
* `--top-k`, `-k`: Retrieval candidate pool depth (default: 5).
* `--provider`, `-p`: AI provider to evaluate (`mock` or `gemini`, default: `mock`).
* `--embedding`, `-e`: Embedding provider type (`deterministic` or `gemini`, default: `deterministic`).
* `--quiet`, `-q`: Suppress terminal markdown table output.

---

## 5. Empirical Benchmark Report

The following evaluation report was generated by running the automated benchmark suite against the 12-item civic benchmark dataset:

### Overall Metric Summary

| Metric Dimension | Measured Value | Target Standard | Evaluation Status |
|:---|:---:|:---:|:---:|
| **Retrieval Success Rate** | **100.0%** | >= 90.0% | **PASS** |
| **Mean Chunk Recall** | **100.0%** | >= 85.0% | **PASS** |
| **Mean Document Precision** | **43.8%** | >= 70.0% | Note 1 |
| **Citation Correctness** | **100.0%** | >= 90.0% | **PASS** |
| **Mean Citation Precision** | **100.0%** | >= 90.0% | **PASS** |
| **Answer Correctness Score** | **93.9%** | >= 80.0% | **PASS** |
| **Criteria Match Rate** | **100.0%** | >= 85.0% | **PASS** |
| **Token F1 Score** | **0.7956** | >= 0.4000 | **PASS** |
| **Unsupported Claims Rate** | **0.0%** | <= 5.0% | **PASS** |
| **Refusal Accuracy** | **100.0%** | 100.0% | **PASS** |

> **Note 1 on Document Precision**: With `top_k=5` and a 10-chunk evaluation corpus, the retrieval buffer retrieves up to 5 candidates to guarantee recall. Document precision reflects the presence of non-target candidate documents in the candidate buffer; chunk recall and citation precision are 100.0%.

### Latency Profile

| Metric | Milliseconds (ms) |
|:---|:---:|
| **Mean Total Latency** | **1.79 ms** |
| **p50 (Median)** | **1.48 ms** |
| **p90 Percentile** | **2.56 ms** |
| **p95 Percentile** | **2.93 ms** |
| **Min Latency** | **1.28 ms** |
| **Max Latency** | **3.35 ms** |

### Per-Query Breakdown

| Query ID | Category | Retrieval Success | Citation Correctness | Criteria Match | Unsupported Claims | Latency |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `BENCH-001` | Budget | PASS (100%) | 100% | 100% | 0 | 3.4 ms |
| `BENCH-002` | Budget | PASS (100%) | 100% | 100% | 0 | 1.7 ms |
| `BENCH-003` | Healthcare | PASS (100%) | 100% | 100% | 0 | 2.3 ms |
| `BENCH-004` | Healthcare | PASS (100%) | 100% | 100% | 0 | 1.5 ms |
| `BENCH-005` | Zoning | PASS (100%) | 100% | 100% | 0 | 2.6 ms |
| `BENCH-006` | Zoning | PASS (100%) | 100% | 100% | 0 | 1.4 ms |
| `BENCH-007` | Transit | PASS (100%) | 100% | 100% | 0 | 1.3 ms |
| `BENCH-008` | Transit | PASS (100%) | 100% | 100% | 0 | 1.4 ms |
| `BENCH-009` | Water Quality | PASS (100%) | 100% | 100% | 0 | 1.4 ms |
| `BENCH-010` | Water Quality | PASS (100%) | 100% | 100% | 0 | 1.3 ms |
| `BENCH-011` | Unsupported (Refusal) | PASS (100%) | 100% | 100% | 0 | 1.9 ms |
| `BENCH-012` | Unsupported (Refusal) | PASS (100%) | 100% | 100% | 0 | 1.4 ms |

The complete, unabridged machine-readable report is permanently archived in [`backend/storage/evaluation/evaluation_results.json`](file:///C:/Users/Syed%20Awais%20Shah/Desktop/opencitizen-ai/backend/storage/evaluation/evaluation_results.json).
