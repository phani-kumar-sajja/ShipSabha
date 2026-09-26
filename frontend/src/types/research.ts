// Keep in sync with backend/app/models/schemas.py

export type ResearchStage =
  | "submitted"
  | "domain_validation"
  | "research_planning"
  | "literature_review"
  | "existing_approaches"
  | "research_gap"
  | "hypothesis_formation"
  | "experiment_design"
  | "experiment_execution"
  | "result_analysis"
  | "comparison"
  | "hypothesis_refinement"
  | "findings"
  | "report";

export const STAGE_ORDER: ResearchStage[] = [
  "submitted",
  "domain_validation",
  "research_planning",
  "literature_review",
  "existing_approaches",
  "research_gap",
  "hypothesis_formation",
  "experiment_design",
  "experiment_execution",
  "result_analysis",
  "comparison",
  "hypothesis_refinement",
  "findings",
  "report",
];

export const STAGE_LABELS: Record<ResearchStage, string> = {
  submitted: "Research question received",
  domain_validation: "CSE domain validated",
  research_planning: "Research planning",
  literature_review: "Literature review",
  existing_approaches: "Existing approaches analyzed",
  research_gap: "Research gap identified",
  hypothesis_formation: "Hypothesis formulated",
  experiment_design: "Experiment designed",
  experiment_execution: "Experiment executed",
  result_analysis: "Results analyzed",
  comparison: "Compared with prior work",
  hypothesis_refinement: "Hypothesis refined",
  findings: "Findings generated",
  report: "Report generated",
};

export type StageStatus = "pending" | "running" | "complete" | "failed" | "skipped";

export type SessionStatus =
  | "initialized"
  | "running"
  | "paused"
  | "stopped"
  | "rejected"
  | "completed"
  | "error";

export interface StageRecord {
  stage: ResearchStage;
  status: StageStatus;
  message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  error?: string | null;
}

export interface DomainValidationResult {
  is_cse_related: boolean;
  domain?: string | null;
  subdomain?: string | null;
  confidence: number;
  rationale: string;
  suggested_reformulation?: string | null;
}

export interface ResearchSession {
  session_id: string;
  created_at: string;
  updated_at: string;
  research_question: string;
  constraints: string[];
  datasets: string[];
  preferred_language?: string | null;
  computational_constraints?: string | null;
  research_objectives: string[];
  domain?: string | null;
  subdomain?: string | null;
  domain_validation?: DomainValidationResult | null;
  status: SessionStatus;
  current_stage: ResearchStage;
  stages: StageRecord[];
  literature: unknown[];
  existing_approaches: unknown[];
  research_gaps: unknown[];
  hypotheses: unknown[];
  experiments: unknown[];
  results: unknown[];
  comparisons: unknown[];
  findings: unknown[];
  artifacts: unknown[];
}

export interface ResearchQuestionInput {
  research_question: string;
  constraints: string[];
  datasets: string[];
  preferred_language?: string | null;
  computational_constraints?: string | null;
  research_objectives: string[];
}

export interface AgentEvent {
  type: string;
  session_id: string;
  stage?: ResearchStage | null;
  status?: StageStatus | null;
  message: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export type WsMessage = AgentEvent | { type: "snapshot"; session: ResearchSession } | { type: "error"; message: string };
