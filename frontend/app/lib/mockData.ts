/**
 * Mock data repository for OpenCitizen AI (Stage 2 Frontend Shell).
 *
 * NOTE: This module contains isolated mock data and contract types.
 * In future stages, these interfaces will be backed by real FastAPI endpoints
 * and analytical services without needing UI refactoring.
 */

export interface DocumentItem {
  id: string;
  title: string;
  category: "Budget" | "Urban Planning" | "Public Safety" | "Council Minutes" | "Environment";
  pageCount: number;
  chunkCount: number;
  size: string;
  status: "ready" | "processing" | "pending";
  date: string;
  department: string;
  summary: string;
}

export interface DatasetColumn {
  name: string;
  type: "VARCHAR" | "DOUBLE" | "INTEGER" | "DATE" | "BOOLEAN";
}

export interface DatasetItem {
  id: string;
  name: string;
  category: "Expenditure" | "Procurement" | "Public Works" | "Demographics";
  format: "CSV" | "XLSX" | "PARQUET";
  rowCount: string;
  columnsCount: number;
  tableName: string;
  status: "active" | "registered";
  date: string;
  size: string;
  columns: DatasetColumn[];
  sampleRows: Record<string, string | number>[];
}

export interface CitationData {
  documentTitle: string;
  pageNumber: number;
  similarityScore: number;
  excerpt: string;
  chunkId: string;
  department?: string;
  highlightWords?: string[];
}

export interface CalculationData {
  query: string;
  executionTimeMs: number;
  rowsScanned: number;
  tableName: string;
  rawRows: Record<string, string | number>[];
  derivation: string;
}

export interface QuerySession {
  id: string;
  timestamp: string;
  question: string;
  answer: string;
  citations: CitationData[];
  calculation?: CalculationData;
  latencyMs: number;
  verified: boolean;
}

export interface SystemMetric {
  label: string;
  value: string | number;
  subtext: string;
  trend?: string;
  trendType?: "positive" | "neutral" | "negative";
  icon: "document" | "dataset" | "citation" | "calc" | "shield" | "activity";
}

// -----------------------------------------------------------------------------
// Mock Data Sets
// -----------------------------------------------------------------------------

export const MOCK_DOCUMENTS: DocumentItem[] = [
  {
    id: "doc-1",
    title: "City_Adopted_Budget_2024.pdf",
    category: "Budget",
    pageCount: 84,
    chunkCount: 210,
    size: "8.4 MB",
    status: "ready",
    date: "Sep 17, 2026",
    department: "Office of Management & Budget",
    summary: "Authorized fiscal year 2024 operational and capital expenditures, department ceilings, and funding allocations.",
  },
  {
    id: "doc-2",
    title: "Transportation_Master_Plan_2030.pdf",
    category: "Urban Planning",
    pageCount: 42,
    chunkCount: 98,
    size: "4.1 MB",
    status: "ready",
    date: "Sep 17, 2026",
    department: "Department of Transportation",
    summary: "Strategic transit corridors, bicycle master network expansions, and zero-emission fleet transition timelines.",
  },
  {
    id: "doc-3",
    title: "Parks_Recreation_Facilities_Audit_2023.pdf",
    category: "Budget",
    pageCount: 36,
    chunkCount: 88,
    size: "3.2 MB",
    status: "ready",
    date: "Sep 15, 2026",
    department: "Parks & Recreation",
    summary: "Community center retrofits, youth summer athletic programming, and deferred HVAC maintenance audits.",
  },
  {
    id: "doc-4",
    title: "City_Council_Resolution_2024_089.pdf",
    category: "Council Minutes",
    pageCount: 12,
    chunkCount: 28,
    size: "1.1 MB",
    status: "ready",
    date: "Sep 12, 2026",
    department: "City Clerk",
    summary: "Authorization for emergency storm drain infrastructure grants and procurement guidelines.",
  },
  {
    id: "doc-5",
    title: "Clean_Energy_Transition_Strategy_2025.pdf",
    category: "Environment",
    pageCount: 65,
    chunkCount: 145,
    size: "5.8 MB",
    status: "ready",
    date: "Sep 08, 2026",
    department: "Sustainability Office",
    summary: "Municipal solar rooftop array targets and civic building energy benchmarking data.",
  },
];

export const MOCK_DATASETS: DatasetItem[] = [
  {
    id: "data-1",
    name: "department_expenses_2023.csv",
    category: "Expenditure",
    format: "CSV",
    rowCount: "14,280",
    columnsCount: 6,
    tableName: "dept_expenses",
    status: "active",
    date: "Sep 16, 2026",
    size: "2.4 MB",
    columns: [
      { name: "department", type: "VARCHAR" },
      { name: "fiscal_year", type: "INTEGER" },
      { name: "amount", type: "DOUBLE" },
      { name: "vendor_name", type: "VARCHAR" },
      { name: "fund_source", type: "VARCHAR" },
      { name: "transaction_date", type: "DATE" },
    ],
    sampleRows: [
      { department: "Parks & Rec", fiscal_year: 2023, amount: 45000, vendor_name: "Apex Facility Services", fund_source: "General", transaction_date: "2023-04-12" },
      { department: "Parks & Rec", fiscal_year: 2023, amount: 12400, vendor_name: "Civic Turf & Landscape", fund_source: "Special", transaction_date: "2023-05-18" },
      { department: "Transportation", fiscal_year: 2023, amount: 89000, vendor_name: "Metro Asphalt Corp", fund_source: "Capital", transaction_date: "2023-06-01" },
      { department: "Public Safety", fiscal_year: 2023, amount: 32000, vendor_name: "Sentinel Telemetry", fund_source: "General", transaction_date: "2023-07-22" },
    ],
  },
  {
    id: "data-2",
    name: "municipal_vendor_contracts.xlsx",
    category: "Procurement",
    format: "XLSX",
    rowCount: "3,840",
    columnsCount: 7,
    tableName: "vendor_contracts",
    status: "registered",
    date: "Sep 14, 2026",
    size: "1.8 MB",
    columns: [
      { name: "contract_id", type: "VARCHAR" },
      { name: "vendor_name", type: "VARCHAR" },
      { name: "department", type: "VARCHAR" },
      { name: "contract_value", type: "DOUBLE" },
      { name: "award_date", type: "DATE" },
      { name: "end_date", type: "DATE" },
      { name: "is_active", type: "BOOLEAN" },
    ],
    sampleRows: [
      { contract_id: "CTR-2023-091", vendor_name: "Apex Facility Services", department: "Parks & Rec", contract_value: 1250000, award_date: "2023-01-15", end_date: "2025-01-15", is_active: 1 },
      { contract_id: "CTR-2023-142", vendor_name: "Metro Asphalt Corp", department: "Transportation", contract_value: 4800000, award_date: "2023-03-01", end_date: "2026-03-01", is_active: 1 },
      { contract_id: "CTR-2023-205", vendor_name: "CleanGrid Solutions", department: "Sustainability", contract_value: 2100000, award_date: "2023-05-10", end_date: "2025-12-31", is_active: 1 },
    ],
  },
  {
    id: "data-3",
    name: "capital_projects_status_2024.parquet",
    category: "Public Works",
    format: "PARQUET",
    rowCount: "920",
    columnsCount: 8,
    tableName: "capital_projects",
    status: "active",
    date: "Sep 10, 2026",
    size: "540 KB",
    columns: [
      { name: "project_id", type: "VARCHAR" },
      { name: "project_name", type: "VARCHAR" },
      { name: "budget_allocated", type: "DOUBLE" },
      { name: "spent_to_date", type: "DOUBLE" },
      { name: "completion_pct", type: "DOUBLE" },
      { name: "lead_agency", type: "VARCHAR" },
      { name: "target_quarter", type: "VARCHAR" },
      { name: "status", type: "VARCHAR" },
    ],
    sampleRows: [
      { project_id: "PRJ-011", project_name: "Downtown Bikeway Phase II", budget_allocated: 3400000, spent_to_date: 2100000, completion_pct: 62.5, lead_agency: "Transportation", target_quarter: "2024-Q3", status: "On Schedule" },
      { project_id: "PRJ-014", project_name: "Westside Community Pool Solar", budget_allocated: 950000, spent_to_date: 920000, completion_pct: 98.0, lead_agency: "Parks & Rec", target_quarter: "2024-Q2", status: "Finishing" },
      { project_id: "PRJ-019", project_name: "Harbor Storm Drain Retrofit", budget_allocated: 5200000, spent_to_date: 1400000, completion_pct: 27.0, lead_agency: "Public Works", target_quarter: "2025-Q1", status: "In Progress" },
    ],
  },
];

export const MOCK_SYSTEM_METRICS: SystemMetric[] = [
  {
    label: "Audited Documents",
    value: 5,
    subtext: "239 pages parsed & indexed",
    trend: "+2 this week",
    trendType: "positive",
    icon: "document",
  },
  {
    label: "Civic Datasets",
    value: 3,
    subtext: "19,040 tabular records in DuckDB",
    trend: "100% schema validated",
    trendType: "positive",
    icon: "dataset",
  },
  {
    label: "Evidence Citations",
    value: "100%",
    subtext: "Zero ungrounded hallucinations",
    trend: "Strict citation enforcement",
    trendType: "positive",
    icon: "shield",
  },
  {
    label: "Avg. Query Latency",
    value: "28ms",
    subtext: "FastAPI + DuckDB in-process",
    trend: "Sub-second verification",
    trendType: "positive",
    icon: "activity",
  },
];

export const MOCK_QUERY_SESSIONS: QuerySession[] = [
  {
    id: "qs-1",
    timestamp: "10 minutes ago",
    question: "What was the total expenditure for Parks & Rec in 2023, and what authorized it?",
    answer: "In fiscal year 2023, the Parks & Recreation department had an audited total expenditure of $4,250,000 across 412 transactions. This spending was authorized under Section 3.2 of the City Adopted Budget 2024, which approved a 6.2% adjustment specifically for community center energy retrofits and summer youth programming.",
    latencyMs: 34,
    verified: true,
    citations: [
      {
        documentTitle: "City_Adopted_Budget_2024.pdf",
        pageNumber: 14,
        similarityScore: 0.912,
        excerpt: "Section 3.2 - Parks, Recreation & Community Facilities: The authorized operational allocation for fiscal year 2023 was adjusted to $4,250,000, reflecting a 6.2% increase to accommodate community center energy efficiency retrofits and expanded summer youth programming.",
        chunkId: "chk_city_budget_p14_003",
        department: "Office of Management & Budget",
        highlightWords: ["$4,250,000", "6.2% increase", "summer youth programming"],
      },
      {
        documentTitle: "Parks_Recreation_Facilities_Audit_2023.pdf",
        pageNumber: 5,
        similarityScore: 0.884,
        excerpt: "Audit Summary: Operating expenditures reconciled against Treasury warrants matched the budgeted $4.25M ceiling with zero unauthorized variances detected in community athletics accounts.",
        chunkId: "chk_parks_audit_p5_001",
        department: "Parks & Recreation",
        highlightWords: ["$4.25M ceiling", "zero unauthorized variances"],
      },
    ],
    calculation: {
      query: "SELECT department, SUM(amount) AS total_spent, COUNT(*) AS transactions FROM dept_expenses WHERE department = 'Parks & Rec' AND fiscal_year = 2023 GROUP BY department;",
      executionTimeMs: 24,
      rowsScanned: 14280,
      tableName: "dept_expenses",
      rawRows: [
        { department: "Parks & Rec", total_spent: 4250000, transactions: 412 },
      ],
      derivation: "Result = SUM(amount) where department = 'Parks & Rec' and fiscal_year = 2023 -> Exactly $4,250,000 across 412 audited expenditure items.",
    },
  },
  {
    id: "qs-2",
    timestamp: "1 hour ago",
    question: "Which municipal vendors currently hold active contracts exceeding $2,000,000?",
    answer: "Based on the municipal vendor registry, two vendors hold active contracts exceeding $2,000,000: Metro Asphalt Corp holding contract CTR-2023-142 valued at $4,800,000 for Transportation, and CleanGrid Solutions holding CTR-2023-205 valued at $2,100,000 for the Sustainability Office.",
    latencyMs: 19,
    verified: true,
    citations: [
      {
        documentTitle: "Transportation_Master_Plan_2030.pdf",
        pageNumber: 22,
        similarityScore: 0.865,
        excerpt: "Capital Procurement Item: Multi-year arterial resurfacing contract awarded under CTR-2023-142 with guaranteed price cap of $4.8M through Q1 2026.",
        chunkId: "chk_trans_plan_p22_002",
        department: "Department of Transportation",
        highlightWords: ["CTR-2023-142", "$4.8M"],
      },
    ],
    calculation: {
      query: "SELECT vendor_name, contract_id, department, contract_value FROM vendor_contracts WHERE is_active = 1 AND contract_value > 2000000 ORDER BY contract_value DESC;",
      executionTimeMs: 12,
      rowsScanned: 3840,
      tableName: "vendor_contracts",
      rawRows: [
        { vendor_name: "Metro Asphalt Corp", contract_id: "CTR-2023-142", department: "Transportation", contract_value: 4800000 },
        { vendor_name: "CleanGrid Solutions", contract_id: "CTR-2023-205", department: "Sustainability", contract_value: 2100000 },
      ],
      derivation: "Filtered vendor_contracts where is_active = 1 and contract_value > 2,000,000. Found 2 qualifying vendor contracts.",
    },
  },
  {
    id: "qs-3",
    timestamp: "Yesterday",
    question: "What is the progress and budget status of the Downtown Bikeway Phase II capital project?",
    answer: "The Downtown Bikeway Phase II (Project ID PRJ-011) has an allocated budget of $3,400,000, with $2,100,000 spent to date. The project is currently 62.5% complete and remains on schedule for completion in 2024-Q3 under the Department of Transportation.",
    latencyMs: 22,
    verified: true,
    citations: [
      {
        documentTitle: "Transportation_Master_Plan_2030.pdf",
        pageNumber: 31,
        similarityScore: 0.899,
        excerpt: "Milestone 4: Downtown Bikeway Phase II active installation covers 4.2 miles of protected cycle track connecting the central railway terminal to university campus, with targeted delivery in Q3 2024.",
        chunkId: "chk_trans_plan_p31_004",
        department: "Department of Transportation",
        highlightWords: ["Downtown Bikeway Phase II", "Q3 2024"],
      },
    ],
    calculation: {
      query: "SELECT project_id, project_name, budget_allocated, spent_to_date, completion_pct, status FROM capital_projects WHERE project_id = 'PRJ-011';",
      executionTimeMs: 15,
      rowsScanned: 920,
      tableName: "capital_projects",
      rawRows: [
        { project_id: "PRJ-011", project_name: "Downtown Bikeway Phase II", budget_allocated: 3400000, spent_to_date: 2100000, completion_pct: 62.5, status: "On Schedule" },
      ],
      derivation: "Direct table lookup on capital_projects by project_id = 'PRJ-011'.",
    },
  },
];

export const PRESET_QUESTIONS = [
  "What was the total expenditure for Parks & Rec in 2023, and what authorized it?",
  "Which municipal vendors currently hold active contracts exceeding $2,000,000?",
  "What is the progress and budget status of the Downtown Bikeway Phase II capital project?",
  "What emergency authorizations were approved under City Council Resolution 2024-089?",
  "What are the municipal rooftop solar targets in the Clean Energy Transition Strategy?",
];
