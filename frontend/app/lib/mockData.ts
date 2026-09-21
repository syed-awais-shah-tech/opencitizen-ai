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
  status: "ready" | "processing" | "pending" | "queued" | "completed" | "failed";
  date: string;
  department: string;
  summary: string;
  jobId?: string;
  stage?: "queued" | "extraction" | "chunking" | "embedding" | "vector_storage" | "completed" | "failed";
  progressPct?: number;
  errorMessage?: string;
}

export interface DatasetColumn {
  name: string;
  type: "VARCHAR" | "DOUBLE" | "INTEGER" | "DATE" | "BOOLEAN";
  missingCount?: number;
  nullPercentage?: number;
}

export interface DatasetPreviewData {
  datasetId: string;
  name: string;
  format: string;
  rowCount: number;
  columnsCount: number;
  columns: string[];
  inferredTypes: Record<string, string>;
  missingValueCounts: Record<string, number>;
  sampleRows: Record<string, any>[];
}

export interface GeographicMetadataData {
  crs: string;
  hasGeospatial: boolean;
  bbox?: [number, number, number, number];
  center?: [number, number];
  featureCount: number;
  validFeatures: number;
  invalidFeatures: number;
  latitudeColumn?: string;
  longitudeColumn?: string;
  geometryTypes?: string[];
}

export interface GeoJSONGeometryData {
  type: string;
  coordinates: any;
}

export interface GeoJSONFeatureData {
  type: "Feature";
  id?: string | number;
  geometry: GeoJSONGeometryData;
  properties: Record<string, any>;
}

export interface GeoJSONFeatureCollectionData {
  type: "FeatureCollection";
  bbox?: [number, number, number, number];
  features: GeoJSONFeatureData[];
  metadata?: GeographicMetadataData;
}

export interface DatasetItem {
  id: string;
  name: string;
  category: "Expenditure" | "Procurement" | "Public Works" | "Demographics" | "Grants";
  format: "CSV" | "XLSX" | "JSON" | "PARQUET";
  rowCount: string;
  columnsCount: number;
  tableName: string;
  status: "active" | "registered" | "ready";
  date: string;
  size: string;
  columns: DatasetColumn[];
  sampleRows: Record<string, string | number | boolean | null>[];
  missingValueCounts?: Record<string, number>;
  sourceUrl?: string;
  sourceName?: string;
  retrievalDate?: string;
  originalFormat?: string;
  processingMetadata?: Record<string, any>;
  hasGeospatial?: boolean;
  geographicMetadata?: GeographicMetadataData;
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

export interface SourceDocumentData {
  documentTitle: string;
  pageNumbers: number[];
  chunkCount: number;
  department?: string;
}

export interface EvidenceSnippetData {
  snippetId: string;
  documentTitle: string;
  pageNumber: number;
  text: string;
  similarityScore: number;
  rank: number;
  department?: string;
}

export interface RetrievalMetadataData {
  vectorStore: string;
  topK: number;
  scoreThreshold: number;
  totalRetrievedChunks: number;
  searchLatencyMs: number;
}

export interface MeasuredConfidenceData {
  isGrounded: boolean;
  evidenceCount: number;
  meanSimilarityScore?: number;
  minSimilarityScore?: number;
  maxSimilarityScore?: number;
  scoreMetric: string;
  verifiabilityRating: "high" | "moderate" | "insufficient";
  explanation: string;
  evaluationBasis: string;
}

export interface TrustReportData {
  answer: string;
  sourceDocuments: SourceDocumentData[];
  pageNumbers: number[];
  evidenceSnippets: EvidenceSnippetData[];
  retrievalMetadata: RetrievalMetadataData;
  modelIdentifier: string;
  limitations: string[];
  confidence: MeasuredConfidenceData;
}

export type ChartType = "bar" | "line" | "pie" | "table";
export type FormatType = "currency" | "number" | "percent" | "integer" | "string";

export interface ChartSeriesData {
  key: string;
  label: string;
  color?: string;
  formatType?: FormatType;
}

export interface ChartConfigData {
  chartType: ChartType;
  title: string;
  description?: string;
  xKey?: string;
  xLabel?: string;
  yLabel?: string;
  series: ChartSeriesData[];
  data: Record<string, any>[];
  selectionReason: string;
  isEmpty?: boolean;
  errorMessage?: string;
}

export interface CalculationData {
  query: string;
  executionTimeMs: number;
  rowsScanned: number;
  tableName: string;
  rawRows: Record<string, string | number | boolean | null>[];
  derivation: string;
  chart?: ChartConfigData;
}

export interface QuerySession {
  id: string;
  timestamp: string;
  question: string;
  answer: string;
  citations: CitationData[];
  trust?: TrustReportData;
  calculation?: CalculationData;
  chart?: ChartConfigData;
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
  {
    id: "doc-6",
    title: "Green_Infrastructure_Stormwater_Report_2025.pdf",
    category: "Environment",
    pageCount: 28,
    chunkCount: 64,
    size: "3.7 MB",
    status: "processing",
    stage: "embedding",
    progressPct: 70,
    jobId: "job_green_infra_001",
    date: "Sep 21, 2026",
    department: "Public Works & Water Management",
    summary: "Bioswale performance assessments, urban stormwater retention metrics, and permeable pavement rollout.",
  },
  {
    id: "doc-7",
    title: "Housing_Affordability_Incentive_Study_2026.pdf",
    category: "Urban Planning",
    pageCount: 52,
    chunkCount: 0,
    size: "6.2 MB",
    status: "queued",
    stage: "queued",
    progressPct: 0,
    jobId: "job_housing_study_002",
    date: "Sep 21, 2026",
    department: "Community Development",
    summary: "Incentive zoning frameworks, density bonuses, and affordable housing trust fund projections.",
  },
  {
    id: "doc-8",
    title: "Corrupted_Zoning_Map_Addendum_Draft.pdf",
    category: "Urban Planning",
    pageCount: 4,
    chunkCount: 0,
    size: "1.8 MB",
    status: "failed",
    stage: "extraction",
    progressPct: 20,
    jobId: "job_corrupted_addendum_003",
    errorMessage: "ExtractionError: PDF page 1 text stream was unreadable or malformed.",
    date: "Sep 20, 2026",
    department: "Zoning Board",
    summary: "Draft amendment for commercial district rezoning and set-back boundaries.",
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
      { name: "department", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "fiscal_year", type: "INTEGER", missingCount: 0, nullPercentage: 0.0 },
      { name: "amount", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "vendor_name", type: "VARCHAR", missingCount: 14, nullPercentage: 0.1 },
      { name: "fund_source", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "transaction_date", type: "DATE", missingCount: 0, nullPercentage: 0.0 },
    ],
    missingValueCounts: {
      department: 0,
      fiscal_year: 0,
      amount: 0,
      vendor_name: 14,
      fund_source: 0,
      transaction_date: 0,
    },
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
      { name: "contract_id", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "vendor_name", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "department", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "contract_value", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "award_date", type: "DATE", missingCount: 0, nullPercentage: 0.0 },
      { name: "end_date", type: "DATE", missingCount: 8, nullPercentage: 0.2 },
      { name: "is_active", type: "BOOLEAN", missingCount: 0, nullPercentage: 0.0 },
    ],
    missingValueCounts: {
      contract_id: 0,
      vendor_name: 0,
      department: 0,
      contract_value: 0,
      award_date: 0,
      end_date: 8,
      is_active: 0,
    },
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
      { name: "project_id", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "project_name", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "budget_allocated", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "spent_to_date", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "completion_pct", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "lead_agency", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "target_quarter", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "status", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
    ],
    missingValueCounts: {
      project_id: 0,
      project_name: 0,
      budget_allocated: 0,
      spent_to_date: 0,
      completion_pct: 0,
      lead_agency: 0,
      target_quarter: 0,
      status: 0,
    },
    sampleRows: [
      { project_id: "PRJ-011", project_name: "Downtown Bikeway Phase II", budget_allocated: 3400000, spent_to_date: 2100000, completion_pct: 62.5, lead_agency: "Transportation", target_quarter: "2024-Q3", status: "On Schedule" },
      { project_id: "PRJ-014", project_name: "Westside Community Pool Solar", budget_allocated: 950000, spent_to_date: 920000, completion_pct: 98.0, lead_agency: "Parks & Rec", target_quarter: "2024-Q2", status: "Finishing" },
      { project_id: "PRJ-019", project_name: "Harbor Storm Drain Retrofit", budget_allocated: 5200000, spent_to_date: 1400000, completion_pct: 27.0, lead_agency: "Public Works", target_quarter: "2025-Q1", status: "In Progress" },
    ],
  },
  {
    id: "data-4",
    name: "civic_grants_registry_2024.json",
    category: "Grants",
    format: "JSON",
    rowCount: "1,240",
    columnsCount: 6,
    tableName: "civic_grants",
    status: "ready",
    date: "Sep 20, 2026",
    size: "680 KB",
    columns: [
      { name: "grant_id", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "recipient", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "grant_amount", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "disbursed", type: "BOOLEAN", missingCount: 0, nullPercentage: 0.0 },
      { name: "approval_date", type: "DATE", missingCount: 12, nullPercentage: 1.0 },
      { name: "program_name", type: "VARCHAR", missingCount: 5, nullPercentage: 0.4 },
    ],
    missingValueCounts: {
      grant_id: 0,
      recipient: 0,
      grant_amount: 0,
      disbursed: 0,
      approval_date: 12,
      program_name: 5,
    },
    sampleRows: [
      { grant_id: "GRN-2024-001", recipient: "Westside Youth Arts", grant_amount: 45000, disbursed: true, approval_date: "2024-01-15", program_name: "Community Cultural Fund" },
      { grant_id: "GRN-2024-002", recipient: "Harbor Clean Waters", grant_amount: 120000, disbursed: true, approval_date: "2024-02-20", program_name: "Environmental Resilience" },
      { grant_id: "GRN-2024-003", recipient: "Downtown Urban Greenery", grant_amount: 35000, disbursed: false, approval_date: "2024-03-05", program_name: null },
      { grant_id: "GRN-2024-004", recipient: "Elder Transit Link", grant_amount: 78000, disbursed: true, approval_date: null, program_name: "Civic Mobility Grant" },
    ],
  },
  {
    id: "data-5",
    name: "austin_capital_improvement_projects.csv",
    category: "Public Works",
    format: "CSV",
    rowCount: "2,840",
    columnsCount: 6,
    tableName: "austin_capital_projects",
    status: "ready",
    date: "Sep 21, 2026",
    size: "1.4 MB",
    sourceUrl: "https://data.austintexas.gov/resource/capital_projects.csv",
    sourceName: "City of Austin Open Data Portal",
    retrievalDate: "2026-09-21T05:45:00Z",
    originalFormat: "CSV",
    processingMetadata: {
      content_sha256: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
      http_status_code: 200,
      content_type: "text/csv; charset=utf-8",
      fetch_elapsed_ms: 142.6,
      connector_id: "civic_open_data",
      transformations: [
        "parsed_csv",
        "normalized_column_identifiers",
        "trimmed_cells_standardized_nulls",
        "inferred_column_types",
      ],
    },
    hasGeospatial: true,
    geographicMetadata: {
      crs: "EPSG:4326",
      hasGeospatial: true,
      bbox: [-97.770, 30.263, -97.740, 30.274],
      center: [-97.7515, 30.2685],
      featureCount: 3,
      validFeatures: 3,
      invalidFeatures: 0,
      latitudeColumn: "latitude",
      longitudeColumn: "longitude",
      geometryTypes: ["Point"],
    },
    columns: [
      { name: "project_id", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "department", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "project_name", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "allocated_budget", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "expenditure_to_date", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "completion_rate", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "latitude", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "longitude", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
    ],
    missingValueCounts: {
      project_id: 0,
      department: 0,
      project_name: 0,
      allocated_budget: 0,
      expenditure_to_date: 0,
      completion_rate: 0,
      latitude: 0,
      longitude: 0,
    },
    sampleRows: [
      { project_id: "CIP-801", department: "Transportation", project_name: "Bikeway & Urban Trail Expansion", allocated_budget: 1200000, expenditure_to_date: 1020000, completion_rate: 0.85, latitude: 30.2672, longitude: -97.7431 },
      { project_id: "CIP-802", department: "Parks & Rec", project_name: "Urban Greenway Canopy Renewal", allocated_budget: 450000, expenditure_to_date: 450000, completion_rate: 1.0, latitude: 30.2740, longitude: -97.7400 },
      { project_id: "CIP-803", department: "Public Works", project_name: "Barton Springs Drainage Upgrade", allocated_budget: 2300000, expenditure_to_date: 920000, completion_rate: 0.40, latitude: 30.2630, longitude: -97.7700 },
    ],
  },
  {
    id: "data-6",
    name: "public_development_projects.csv",
    category: "Public Works",
    format: "CSV",
    rowCount: "8",
    columnsCount: 10,
    tableName: "public_development_projects",
    status: "active",
    date: "Sep 21, 2026",
    size: "340 KB",
    sourceUrl: "https://data.austintexas.gov/resource/public_facilities_development.csv",
    sourceName: "Austin Municipal Capital Development Agency",
    retrievalDate: "2026-09-21T06:00:00Z",
    originalFormat: "CSV",
    hasGeospatial: true,
    geographicMetadata: {
      crs: "EPSG:4326",
      hasGeospatial: true,
      bbox: [-97.784, 30.231, -97.705, 30.345],
      center: [-97.7445, 30.288],
      featureCount: 8,
      validFeatures: 8,
      invalidFeatures: 0,
      latitudeColumn: "latitude",
      longitudeColumn: "longitude",
      geometryTypes: ["Point"],
    },
    processingMetadata: {
      content_sha256: "7e502b48e6bf1ad935cbb64b85c165ef9447432d665f8a0ef93bf81d1b32d659",
      http_status_code: 200,
      content_type: "text/csv; charset=utf-8",
      fetch_elapsed_ms: 98.4,
      connector_id: "civic_open_data",
      transformations: [
        "parsed_csv",
        "normalized_column_identifiers",
        "validated_geographic_coordinates",
        "wgs84_bounding_box_calculated",
      ],
    },
    columns: [
      { name: "project_id", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "project_name", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "category", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "status", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "budget", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "spent_to_date", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "completion_pct", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "lead_agency", type: "VARCHAR", missingCount: 0, nullPercentage: 0.0 },
      { name: "latitude", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
      { name: "longitude", type: "DOUBLE", missingCount: 0, nullPercentage: 0.0 },
    ],
    missingValueCounts: {
      project_id: 0,
      project_name: 0,
      category: 0,
      status: 0,
      budget: 0,
      spent_to_date: 0,
      completion_pct: 0,
      lead_agency: 0,
      latitude: 0,
      longitude: 0,
    },
    sampleRows: [
      {
        project_id: "DEV-101",
        project_name: "East Riverside Transit Hub & Affordable Housing",
        category: "Transportation",
        status: "In Progress",
        budget: 4200000,
        spent_to_date: 2730000,
        completion_pct: 65.0,
        lead_agency: "Transportation & Public Works",
        latitude: 30.2450,
        longitude: -97.7280,
      },
      {
        project_id: "DEV-102",
        project_name: "Barton Creek Greenbelt Ecological Restoration",
        category: "Parks & Environment",
        status: "Completed",
        budget: 1850000,
        spent_to_date: 1850000,
        completion_pct: 100.0,
        lead_agency: "Parks & Rec",
        latitude: 30.2580,
        longitude: -97.7840,
      },
      {
        project_id: "DEV-103",
        project_name: "Zilker Park Community Solar & Rec Facility",
        category: "Parks & Environment",
        status: "In Progress",
        budget: 950000,
        spent_to_date: 285000,
        completion_pct: 30.0,
        lead_agency: "Sustainability Office",
        latitude: 30.2670,
        longitude: -97.7710,
      },
      {
        project_id: "DEV-104",
        project_name: "Airport Boulevard Corridor Modernization",
        category: "Transportation",
        status: "Planned",
        budget: 6800000,
        spent_to_date: 0,
        completion_pct: 0.0,
        lead_agency: "Transportation Dept",
        latitude: 30.3120,
        longitude: -97.7150,
      },
      {
        project_id: "DEV-105",
        project_name: "Pleasant Valley Civic Health Clinic",
        category: "Healthcare",
        status: "In Progress",
        budget: 3100000,
        spent_to_date: 1550000,
        completion_pct: 50.0,
        lead_agency: "Public Health",
        latitude: 30.2310,
        longitude: -97.7120,
      },
      {
        project_id: "DEV-106",
        project_name: "Mueller Branch Library & Community Center",
        category: "Public Facilities",
        status: "Completed",
        budget: 2400000,
        spent_to_date: 2400000,
        completion_pct: 100.0,
        lead_agency: "Library Dept",
        latitude: 30.3010,
        longitude: -97.7050,
      },
      {
        project_id: "DEV-107",
        project_name: "North Lamar Stormwater & Bioswale Project",
        category: "Infrastructure",
        status: "In Progress",
        budget: 1600000,
        spent_to_date: 1280000,
        completion_pct: 80.0,
        lead_agency: "Watershed Protection",
        latitude: 30.3450,
        longitude: -97.7210,
      },
      {
        project_id: "DEV-108",
        project_name: "South Congress Pedestrian Safety Corridor",
        category: "Transportation",
        status: "Planned",
        budget: 890000,
        spent_to_date: 120000,
        completion_pct: 15.0,
        lead_agency: "Transportation Dept",
        latitude: 30.2480,
        longitude: -97.7530,
      },
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
    trust: {
      answer: "In fiscal year 2023, the Parks & Recreation department had an audited total expenditure of $4,250,000 across 412 transactions. This spending was authorized under Section 3.2 of the City Adopted Budget 2024, which approved a 6.2% adjustment specifically for community center energy retrofits and summer youth programming.",
      sourceDocuments: [
        {
          documentTitle: "City_Adopted_Budget_2024.pdf",
          pageNumbers: [14],
          chunkCount: 1,
          department: "Office of Management & Budget",
        },
        {
          documentTitle: "Parks_Recreation_Facilities_Audit_2023.pdf",
          pageNumbers: [5],
          chunkCount: 1,
          department: "Parks & Recreation",
        },
      ],
      pageNumbers: [5, 14],
      evidenceSnippets: [
        {
          snippetId: "chk_city_budget_p14_003",
          documentTitle: "City_Adopted_Budget_2024.pdf",
          pageNumber: 14,
          similarityScore: 0.912,
          rank: 1,
          department: "Office of Management & Budget",
          text: "Section 3.2 - Parks, Recreation & Community Facilities: The authorized operational allocation for fiscal year 2023 was adjusted to $4,250,000, reflecting a 6.2% increase to accommodate community center energy efficiency retrofits and expanded summer youth programming.",
        },
        {
          snippetId: "chk_parks_audit_p5_001",
          documentTitle: "Parks_Recreation_Facilities_Audit_2023.pdf",
          pageNumber: 5,
          similarityScore: 0.884,
          rank: 2,
          department: "Parks & Recreation",
          text: "Audit Summary: Operating expenditures reconciled against Treasury warrants matched the budgeted $4.25M ceiling with zero unauthorized variances detected in community athletics accounts.",
        },
      ],
      retrievalMetadata: {
        vectorStore: "Qdrant HNSW",
        topK: 5,
        scoreThreshold: 0.65,
        totalRetrievedChunks: 2,
        searchLatencyMs: 14.8,
      },
      modelIdentifier: "gemini-2.5-flash",
      limitations: [
        "Grounding Boundary: Synthesized exclusively from retrieved municipal records. Content not present in the indexed document repository cannot be attested.",
        "Temporal Scope: Factual information reflects document publication dates and may not reflect subsequent legislative actions, emergency resolutions, or revised budget amendments.",
        "Advisory Notice: Automated civic analysis is intended for public transparency and research assistance and does not constitute formal legal counsel or official certified municipal audit.",
        "Evidence Inspection: Citizens can independently verify each claim by inspecting the exact verbatim excerpts and page citations in the provenance drawer.",
      ],
      confidence: {
        isGrounded: true,
        evidenceCount: 2,
        meanSimilarityScore: 0.898,
        minSimilarityScore: 0.884,
        maxSimilarityScore: 0.912,
        scoreMetric: "cosine_similarity",
        verifiabilityRating: "high",
        explanation: "Answer is backed by 2 verified excerpt(s) across 2 source document(s) with an average cosine similarity of 0.8980 (range: 0.8840 - 0.9120).",
        evaluationBasis: "Empirical vector cosine similarity and source evidence coverage without statistical inflation",
      },
    },
    calculation: {
      query: "SELECT department, SUM(amount) AS total_spent, COUNT(*) AS transactions FROM dept_expenses WHERE fiscal_year = 2023 GROUP BY department ORDER BY total_spent DESC LIMIT 5;",
      executionTimeMs: 24,
      rowsScanned: 14280,
      tableName: "dept_expenses",
      rawRows: [
        { department: "Transportation", total_spent: 8400000, transactions: 814 },
        { department: "Public Works", total_spent: 6100000, transactions: 652 },
        { department: "Parks & Rec", total_spent: 4250000, transactions: 412 },
        { department: "Health & Social", total_spent: 3900000, transactions: 388 },
        { department: "Library System", total_spent: 1950000, transactions: 195 },
      ],
      derivation: "Result = SUM(amount) grouped by department for fiscal_year = 2023 -> Top 5 municipal departments by total expenditure.",
      chart: {
        chartType: "bar",
        title: "Departmental Expenditure Comparison (FY 2023)",
        description: "Comparative expenditure across top municipal departments in DuckDB table 'dept_expenses'",
        xKey: "department",
        xLabel: "Department",
        yLabel: "Total Spent ($)",
        series: [
          { key: "total_spent", label: "Total Spent", color: "#06b6d4", formatType: "currency" }
        ],
        data: [
          { department: "Transportation", total_spent: 8400000 },
          { department: "Public Works", total_spent: 6100000 },
          { department: "Parks & Rec", total_spent: 4250000 },
          { department: "Health & Social", total_spent: 3900000 },
          { department: "Library System", total_spent: 1950000 },
        ],
        selectionReason: "Selected bar chart for discrete categorical comparison of total expenditure across 5 departments.",
        isEmpty: false,
      },
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
    trust: {
      answer: "Based on the municipal vendor registry, two vendors hold active contracts exceeding $2,000,000: Metro Asphalt Corp holding contract CTR-2023-142 valued at $4,800,000 for Transportation, and CleanGrid Solutions holding CTR-2023-205 valued at $2,100,000 for the Sustainability Office.",
      sourceDocuments: [
        {
          documentTitle: "Transportation_Master_Plan_2030.pdf",
          pageNumbers: [22],
          chunkCount: 1,
          department: "Department of Transportation",
        },
      ],
      pageNumbers: [22],
      evidenceSnippets: [
        {
          snippetId: "chk_trans_plan_p22_002",
          documentTitle: "Transportation_Master_Plan_2030.pdf",
          pageNumber: 22,
          similarityScore: 0.865,
          rank: 1,
          department: "Department of Transportation",
          text: "Capital Procurement Item: Multi-year arterial resurfacing contract awarded under CTR-2023-142 with guaranteed price cap of $4.8M through Q1 2026.",
        },
      ],
      retrievalMetadata: {
        vectorStore: "Qdrant HNSW",
        topK: 5,
        scoreThreshold: 0.65,
        totalRetrievedChunks: 1,
        searchLatencyMs: 11.2,
      },
      modelIdentifier: "gemini-2.5-flash",
      limitations: [
        "Grounding Boundary: Synthesized exclusively from retrieved municipal records. Content not present in the indexed document repository cannot be attested.",
        "Temporal Scope: Factual information reflects document publication dates and may not reflect subsequent legislative actions, emergency resolutions, or revised budget amendments.",
        "Advisory Notice: Automated civic analysis is intended for public transparency and research assistance and does not constitute formal legal counsel or official certified municipal audit.",
        "Evidence Inspection: Citizens can independently verify each claim by inspecting the exact verbatim excerpts and page citations in the provenance drawer.",
      ],
      confidence: {
        isGrounded: true,
        evidenceCount: 1,
        meanSimilarityScore: 0.865,
        minSimilarityScore: 0.865,
        maxSimilarityScore: 0.865,
        scoreMetric: "cosine_similarity",
        verifiabilityRating: "moderate",
        explanation: "Answer is backed by 1 verified excerpt(s) across 1 source document(s) with an average cosine similarity of 0.8650 (range: 0.8650 - 0.8650).",
        evaluationBasis: "Empirical vector cosine similarity and source evidence coverage without statistical inflation",
      },
    },
    calculation: {
      query: "SELECT department, SUM(contract_value) AS total_value FROM vendor_contracts WHERE is_active = 1 GROUP BY department ORDER BY total_value DESC LIMIT 4;",
      executionTimeMs: 12,
      rowsScanned: 3840,
      tableName: "vendor_contracts",
      rawRows: [
        { department: "Transportation", total_value: 4800000 },
        { department: "Sustainability", total_value: 2100000 },
        { department: "Information Tech", total_value: 1750000 },
        { department: "Facilities", total_value: 1250000 },
      ],
      derivation: "Aggregated active vendor contract values grouped by municipal department across top 4 allocations.",
      chart: {
        chartType: "pie",
        title: "Active Contract Allocation Share by Department",
        description: "Compositional share of active contracts exceeding major thresholds in table 'vendor_contracts'",
        xKey: "department",
        xLabel: "Department",
        yLabel: "Contract Value ($)",
        series: [
          { key: "total_value", label: "Contract Value", color: "#10b981", formatType: "currency" }
        ],
        data: [
          { department: "Transportation", total_value: 4800000 },
          { department: "Sustainability", total_value: 2100000 },
          { department: "Information Tech", total_value: 1750000 },
          { department: "Facilities", total_value: 1250000 },
        ],
        selectionReason: "Selected pie chart because result represents a compositional breakdown across 4 discrete departments with strictly positive values.",
        isEmpty: false,
      },
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
    trust: {
      answer: "The Downtown Bikeway Phase II (Project ID PRJ-011) has an allocated budget of $3,400,000, with $2,100,000 spent to date. The project is currently 62.5% complete and remains on schedule for completion in 2024-Q3 under the Department of Transportation.",
      sourceDocuments: [
        {
          documentTitle: "Transportation_Master_Plan_2030.pdf",
          pageNumbers: [31],
          chunkCount: 1,
          department: "Department of Transportation",
        },
      ],
      pageNumbers: [31],
      evidenceSnippets: [
        {
          snippetId: "chk_trans_plan_p31_004",
          documentTitle: "Transportation_Master_Plan_2030.pdf",
          pageNumber: 31,
          similarityScore: 0.899,
          rank: 1,
          department: "Department of Transportation",
          text: "Milestone 4: Downtown Bikeway Phase II active installation covers 4.2 miles of protected cycle track connecting the central railway terminal to university campus, with targeted delivery in Q3 2024.",
        },
      ],
      retrievalMetadata: {
        vectorStore: "Qdrant HNSW",
        topK: 5,
        scoreThreshold: 0.65,
        totalRetrievedChunks: 1,
        searchLatencyMs: 13.5,
      },
      modelIdentifier: "gemini-2.5-flash",
      limitations: [
        "Grounding Boundary: Synthesized exclusively from retrieved municipal records. Content not present in the indexed document repository cannot be attested.",
        "Temporal Scope: Factual information reflects document publication dates and may not reflect subsequent legislative actions, emergency resolutions, or revised budget amendments.",
        "Advisory Notice: Automated civic analysis is intended for public transparency and research assistance and does not constitute formal legal counsel or official certified municipal audit.",
        "Evidence Inspection: Citizens can independently verify each claim by inspecting the exact verbatim excerpts and page citations in the provenance drawer.",
      ],
      confidence: {
        isGrounded: true,
        evidenceCount: 1,
        meanSimilarityScore: 0.899,
        minSimilarityScore: 0.899,
        maxSimilarityScore: 0.899,
        scoreMetric: "cosine_similarity",
        verifiabilityRating: "moderate",
        explanation: "Answer is backed by 1 verified excerpt(s) across 1 source document(s) with an average cosine similarity of 0.8990 (range: 0.8990 - 0.8990).",
        evaluationBasis: "Empirical vector cosine similarity and source evidence coverage without statistical inflation",
      },
    },
    calculation: {
      query: "SELECT fiscal_year, SUM(spent_to_date) AS total_spent, SUM(budget_allocated) AS total_budget FROM capital_projects GROUP BY fiscal_year ORDER BY fiscal_year ASC;",
      executionTimeMs: 15,
      rowsScanned: 920,
      tableName: "capital_projects",
      rawRows: [
        { fiscal_year: "2021", total_spent: 8500000, total_budget: 10200000 },
        { fiscal_year: "2022", total_spent: 11400000, total_budget: 13000000 },
        { fiscal_year: "2023", total_spent: 14800000, total_budget: 16500000 },
        { fiscal_year: "2024", total_spent: 17200000, total_budget: 18900000 },
      ],
      derivation: "Aggregated annual capital expenditures across consecutive fiscal years 2021-2024.",
      chart: {
        chartType: "line",
        title: "Capital Projects Expenditure Trajectory (2021-2024)",
        description: "Multi-year capital budget and spending progression across municipal infrastructure cycles",
        xKey: "fiscal_year",
        xLabel: "Fiscal Year",
        yLabel: "Capital Budget ($)",
        series: [
          { key: "total_spent", label: "Spent to Date", color: "#8b5cf6", formatType: "currency" },
          { key: "total_budget", label: "Allocated Budget", color: "#06b6d4", formatType: "currency" },
        ],
        data: [
          { fiscal_year: "2021", total_spent: 8500000, total_budget: 10200000 },
          { fiscal_year: "2022", total_spent: 11400000, total_budget: 13000000 },
          { fiscal_year: "2023", total_spent: 14800000, total_budget: 16500000 },
          { fiscal_year: "2024", total_spent: 17200000, total_budget: 18900000 },
        ],
        selectionReason: "Selected line chart because dimension 'fiscal_year' represents a chronological temporal sequence across 4 annual periods.",
        isEmpty: false,
      },
    },
  },
  {
    id: "qs-4",
    timestamp: "2 days ago",
    question: "Show emergency flood relief allocations for Ward 9 in fiscal year 2020",
    answer: "No matching emergency flood relief expenditure records were found for Ward 9 in the 2020 fiscal dataset. All emergency flood disbursements recorded in that period were allocated to Ward 3 and Ward 7.",
    latencyMs: 14,
    verified: true,
    citations: [],
    calculation: {
      query: "SELECT ward, grant_name, amount FROM civic_grants WHERE ward = 'Ward 9' AND program = 'Flood Relief' AND fiscal_year = 2020;",
      executionTimeMs: 9,
      rowsScanned: 2400,
      tableName: "civic_grants",
      rawRows: [],
      derivation: "Filtered civic_grants where ward = 'Ward 9' and program = 'Flood Relief' and fiscal_year = 2020 -> 0 rows returned.",
      chart: {
        chartType: "table",
        title: "Emergency Flood Relief Allocations (Ward 9 - 2020)",
        description: "Zero records match the requested criteria in table 'civic_grants'",
        xKey: "grant_name",
        series: [],
        data: [],
        selectionReason: "Result set contains 0 records; defaulting to empty table view.",
        isEmpty: true,
        errorMessage: "No analytical records match the specified query filters in the selected fiscal year.",
      },
    },
  },
];

export const PRESET_QUESTIONS = [
  "What was the total expenditure for Parks & Rec in 2023, and what authorized it?",
  "Which municipal vendors currently hold active contracts exceeding $2,000,000?",
  "What is the progress and budget status of the Downtown Bikeway Phase II capital project?",
  "Show emergency flood relief allocations for Ward 9 in fiscal year 2020",
  "What emergency authorizations were approved under City Council Resolution 2024-089?",
  "What are the municipal rooftop solar targets in the Clean Energy Transition Strategy?",
];
