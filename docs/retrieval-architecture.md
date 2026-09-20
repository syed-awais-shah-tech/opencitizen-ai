# OpenCitizen AI - Hybrid Document Retrieval Architecture

## 1. Overview & Motivation

OpenCitizen AI processes municipal and civic records, including annual financial audits, city council resolutions, zoning bylaws, municipal codes, and environmental inspection reports.

Civic information retrieval presents two conflicting demands:
1. **Semantic Understanding**: Citizens and analysts query documents using natural language, conceptual phrasing, or lay terminology (e.g., *"money spent fixing roads and potholes"*, *"children health clinics"*).
2. **Exact Identifier Precision**: Civic records rely heavily on exact alphanumeric identifiers, resolution numbers, project codes, and regulatory standards (e.g., `RES-2024-089`, `CTR-2023-142`, `ORD-2023-45`, `EPA-502.2`).

Dense embedding models (semantic retrieval) excel at conceptual mapping and synonymy, but frequently suffer from vector dilution, vocabulary mismatch, and numeric compression when dealing with arbitrary alphanumeric identifiers. Conversely, lexical keyword matching (BM25) provides exact identifier precision but fails when queries use paraphrases, synonyms, or conceptual generalizations.

To resolve this trade-off, **Stage 13** introduces a **Hybrid Retrieval Architecture** combining dense semantic vector search and sparse lexical BM25 retrieval, fused using **Reciprocal Rank Fusion (RRF)** while strictly preserving end-to-end document and chunk provenance.

```
                         +-----------------------------------+
                         |           User Query              |
                         +-----------------------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
                    v                                             v
       +-------------------------+                   +-------------------------+
       |   Dense Semantic Search |                   |   Sparse Lexical Index  |
       |  (Qdrant + Embeddings)  |                   |       (Okapi BM25)      |
       +-------------------------+                   +-------------------------+
                    |                                             |
                    | Top-K Candidate Pool                        | Top-K Candidate Pool
                    v                                             v
       +-----------------------------------------------------------------------+
       |                Reciprocal Rank Fusion (RRF) Reranker                  |
       |        RRF_score(d) = sum_m [ w_m / (k + rank_m(d)) ] (k=60)          |
       |             Calibrated Score Normalization [0.0, 1.0]                |
       |             Strict Metadata & Lineage Preservation                   |
       +-----------------------------------------------------------------------+
                                           |
                                           v
                         +-----------------------------------+
                         |    Fused & Reranked Candidates    |
                         |   (With Retrieval Provenance)     |
                         +-----------------------------------+
```

---

## 2. Retrieval Strategy

The hybrid retrieval pipeline operates via two complementary retrieval channels:

### 2.1. Dense Semantic Retrieval Channel
* **Underlying Store**: Qdrant vector database (`QdrantVectorStore`).
* **Embeddings**: Vector embeddings generated through the `BaseEmbeddingProvider` abstraction (e.g., Gemini text embeddings in production, deterministic embeddings in test environments).
* **Distance Metric**: Cosine similarity.
* **Role**: Captures high-level semantic intent, conceptual equivalence, and cross-lingual/thematic similarities where exact keywords are absent.

### 2.2. Sparse Lexical BM25 Channel
* **Underlying Store**: `BM25Index`, a pure-Python in-memory inverted index implementing the Okapi BM25 probabilistic ranking algorithm ($k_1=1.5, b=0.75$).
* **Civic-Aware Tokenization**: Standard whitespace/punctuation tokenizers break alphanumeric identifiers with hyphens and underscores into meaningless sub-tokens (e.g., turning `RES-2024-089` into `RES`, `2024`, `089`). Our custom tokenizer uses the regex:
  $$\b[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*\b$$
  This ensures codes like `RES-2024-089`, `CTR-2023-142`, `PRJ-011`, and `EPA-502.2` remain intact single tokens.
* **Stopword Handling**: Standard English stopwords are filtered to prevent term frequency saturation, with an automatic fallback preserving tokens if a query consists entirely of stopwords.
* **Role**: Guarantees exact-match precision for municipal identifiers, ordinance numbers, contract codes, and proper civic entity names.

### 2.3. Candidate Pool Expansion
Before merging, each channel retrieves an expanded candidate pool:
$$\text{pool\_k} = \max(\text{top\_k} \times \text{candidate\_pool\_multiplier}, 10)$$
This ensures that documents highly relevant in one channel are not prematurely dropped before rank fusion.

---

## 3. Ranking Strategy: Reciprocal Rank Fusion (RRF)

### 3.1. RRF Formula
Because dense cosine similarity scores (bounded $[-1.0, 1.0]$) and BM25 scores (unbounded positive floats) have fundamentally different scale distributions, linear score combination without complex calibration often produces channel domination.

We utilize **Reciprocal Rank Fusion (RRF)**, a consensus ranking algorithm that operates on the positional ranks of items rather than their raw scores:

$$\text{RRF\_score}(d) = \sum_{m \in \{\text{semantic}, \text{lexical}\}} \frac{w_m}{k + \text{rank}_m(d)}$$

Where:
* $k = 60$: Standard smoothing constant that dampens the penalty difference between top-ranking items (e.g. rank 1 vs rank 2) while ensuring tail results do not dominate.
* $\text{rank}_m(d)$: 1-indexed position of document chunk $d$ in the results of retrieval channel $m$.
* $w_m$: Channel weight factor ($w_{\text{semantic}} = 0.6$, $w_{\text{lexical}} = 0.4$), giving primary priority to semantic context while heavily rewarding exact lexical confirmation.

### 3.2. Calibrated Score & Thresholding
For downstream thresholding (e.g. `score_threshold`) and user-facing confidence calculation in the Trust Layer, we compute a calibrated normalized score in the range $[0.0, 1.0]$:

$$\text{calibrated\_score}(d) = w_{\text{sem}} \cdot \max(0, s_{\text{sem}}) + w_{\text{lex}} \cdot \frac{\max(0, s_{\text{lex}})}{\max_{i}(s_{\text{lex}, i})}$$

Candidates originating solely from semantic retrieval with non-positive cosine similarity ($\le 0$) and zero lexical matches are discarded as non-relevant noise.

### 3.3. Complete Metadata Preservation
All 5 required metadata fields and arbitrary provenance attributes are preserved without loss or mutation:
* `chunk_id`
* `document_id`
* `page_number`
* `source_filename`
* `original_text`
* `metadata`: augmented with retrieval provenance:
  * `retrieval_method`: `"hybrid"`, `"semantic_only"`, or `"lexical_only"`
  * `retrieval_meta`: structured audit dict containing `rrf_score`, `calibrated_score`, `semantic_rank`, `lexical_rank`, `semantic_score`, and `lexical_score`.

---

## 4. Empirical Evaluation & Performance Comparison

To objectively evaluate the hybrid retrieval architecture against the original semantic-only approach, we executed an empirical benchmark using a realistic municipal civic document evaluation corpus.

### 4.1. Evaluation Dataset
* **Corpus**: 10 distinct chunks across 5 municipal documents:
  1. `doc-budget-2024`: City budget audit, capital allocations, resolution codes (`RES-2024-089`).
  2. `doc-health-2024`: Pediatric wellness clinic programs, adult screenings (`CWI-24`).
  3. `doc-zoning-2023`: Commercial height setbacks (`ORD-2023-45`), residential zoning (`R-1`).
  4. `doc-transit-2024`: Fleet bus electrification (`CTR-2023-142`), route infrastructure (`Line-42`).
  5. `doc-water-2024`: Compliance testing standards (`EPA-502.2`), reservoir turbidity monitoring.
* **Queries**: 10 representative civic queries categorised into:
  * **Exact Code Queries** (Q1–Q4): queries containing exact alphanumeric codes (e.g. `RES-2024-089`, `CTR-2023-142`, `ORD-2023-45`, `EPA-502.2`).
  * **Conceptual Queries** (Q5–Q7): natural language questions with thematic synonyms and paraphrases.
  * **Mixed Queries** (Q8–Q10): combinations of conceptual terms with specific municipal identifiers.

### 4.2. Empirical Results Table

| Metric | Semantic (Original) | Lexical (BM25) | Hybrid (RRF) |
|:---|:---:|:---:|:---:|
| **Hit@1** | 80.0% | 100.0% | **100.0%** |
| **Hit@3** | 80.0% | 100.0% | **100.0%** |
| **Hit@5** | 90.0% | 100.0% | **100.0%** |
| **MRR (Mean Reciprocal Rank)** | 0.8200 | 1.0000 | **1.0000** |
| **Recall@5** | 90.0% | 100.0% | **100.0%** |

### 4.3. Analysis of Empirical Gains

1. **Elimination of False Negative Misses (Recall@5: 90% $\to$ 100%)**:
   - In Query **Q7** (*"reservoir water clarity purity contaminant monitoring"*), the original semantic-only search failed to include the target chunk (`chk_water_02`) within its top 5 candidates due to vector dilution with broader environmental chunks.
   - Lexical retrieval accurately matched the distinctive tokens (`clarity`, `purity`, `reservoir`), and Hybrid RRF promoted the correct chunk directly to **Rank 1**.
2. **Top-Rank Elevation on Conceptual Queries (Hit@1: 80% $\to$ 100%, MRR: 0.8200 $\to$ 1.0000)**:
   - In Query **Q5** (*"children healthcare free immunizations"*), the original semantic-only approach ranked the relevant chunk (`chk_health_01`) at **Rank 5** (MRR = 0.20), diluted by other general municipal health entries.
   - The hybrid architecture elevated this candidate to **Rank 1** (MRR = 1.00), demonstrating how keyword presence acts as an anchor to disambiguate semantically similar candidates.
3. **Consistency on Exact Identifiers**:
   - Across all exact identifier queries (Q1, Q2, Q3, Q4), Hybrid retrieval preserved the 100% Hit@1 rate.

---

## 5. Known Limitations

While the Stage 13 hybrid retrieval architecture significantly outperforms the baseline, the following limitations are documented for future milestones:

1. **In-Memory BM25 Volatility**:
   - The current `BM25Index` is maintained in-process memory. While fully integrated with `VectorSearchService.index_chunks()` and `delete_document()`, the index must be rebuilt or synchronized upon cold application restarts. Future iterations will back the inverted index with persistent storage (e.g. PostgreSQL `tsvector` / GIN indexes or SQLite FTS5).
2. **Static Channel Weighting**:
   - The RRF weights ($w_{\text{sem}}=0.6, w_{\text{lex}}=0.4$) and smoothing constant ($k=60$) are static across all queries. Queries consisting purely of an alphanumeric code could benefit from dynamic weight biasing towards lexical retrieval ($w_{\text{lex}}=0.8$), while highly conversational questions could lean towards semantic retrieval ($w_{\text{sem}}=0.8$).
3. **Lack of Morphological Lemmatization**:
   - The current lexical tokenizer uses case-insensitive alphanumeric matching without Porter or Snowball stemming. While this deliberately prevents corruption of municipal code numbers and legal acronyms, it does not conflate inflected forms (e.g., *"inspecting"* vs *"inspection"*, *"bylaws"* vs *"bylaw"*).
4. **Vocabulary Mismatch without Synonym Expansion**:
   - If a citizen query uses colloquial terminology that shares zero lexical overlap with formal legislative text (e.g., *"pothole fixing"* vs *"asphalt resurfacing"*), lexical BM25 assigns a score of 0.0, leaving retrieval entirely dependent on the semantic channel.
