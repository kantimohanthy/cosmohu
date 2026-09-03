export type AnswerStatus = "supported" | "partially_supported" | "conflicting" | "insufficient_evidence";

export interface PropositionDTO {
  proposition_id: string;
  entity_id: string;
  entity_name: string;
  predicate: string;
  object: string;
  status: string; // SUPPORTED | INSUFFICIENT_EVIDENCE | CONTRADICTED | CONFLICT | REDIRECT_MISMATCH | NO_SOURCE_ROOT
  temporal_scope: string;
  evidence_strength: number;
  evidence_ids: string[];
  claim_id?: string;
  relationship_id?: string;
}

export interface ClaimDTO {
  claim_id: string;
  text: string;
  entity_id: string;
  evidence_ids: string[];
  verification_status: string;
}

export interface EvidenceDTO {
  evidence_id: string;
  claim_id?: string;
  document_id: string;
  chunk_id: string;
  source_url: string;
  publisher: string;
  source_tier: string;
  published_at?: string;
  observed_at?: string;
  temporal_scope: string;
  exact_text: string;
  provenance_status: string;
  content_hash: string;
  run_id: string;
}

export interface InsufficientDTO {
  proposition_id: string;
  entity_id: string;
  entity_name: string;
  reason: string;
}

export interface SourceDTO {
  source_id: string;
  publisher: string;
  source_url: string;
  source_tier: string;
}

export interface ResearchQueryResponse {
  query: string;
  status: string;
  run_id: string;
  answer: string;
  propositions: PropositionDTO[];
  claims: ClaimDTO[];
  evidence: EvidenceDTO[];
  insufficient: InsufficientDTO[];
  conflicts: any[];
  withheld: any[];
  sources: SourceDTO[];
  metadata: {
    planning_ms: number;
    retrieval_ms: number;
    reranking_ms: number;
    verification_ms: number;
    orchestration_ms: number;
    synthesis_ms: number | string;
    validation_ms: number;
    total_ms: number;
    provider_type: string;
  };
}

export interface EvidenceChainItem {
  step: number;
  type: string; // PROPOSITION | CLAIM | EVIDENCE | CHUNK | DOCUMENT | SOURCE
  id: string;
  label?: string;
  text?: string;
  source_tier?: string;
  document_id?: string;
  title?: string;
  content_hash?: string;
  publisher?: string;
  url?: string;
}

export interface EvidenceChainResponse {
  proposition_id: string;
  entity_id: string;
  entity_name: string;
  predicate: string;
  object: string;
  status: string;
  temporal_scope?: string;
  evidence_strength?: number;
  evidence_chain: EvidenceChainItem[];
  evidence_records?: EvidenceDTO[];
  rejected_records?: any[];
  conflicts?: any[];
  corroboration_count?: number;
  provenance_summary?: {
    entity_attribution: boolean;
    predicate_support: boolean;
    object_support: boolean;
    temporal_support: boolean;
    provenance_valid: boolean;
  };
  searched_count?: number;
  verified_count?: number;
}

export interface EvidencePassage {
  passage_id: string;
  chunk_id: string;
  document_id: string;
  source_id: string;
  title: string;
  publisher: string;
  source_url: string;
  published_at?: string;
  retrieved_at?: string;
  text: string;
  relevance_score: number;
  confidence_score: number;
  why_relevant: string;
}

export interface ClaimItem {
  claim_id: string;
  text: string;
  confidence: number;
  status: string;
  evidence_ids: string[];
}

export interface WhyCategory {
  code: string;
  title: string;
  summary: string;
  evidence_snippets: string[];
}

export interface ReasoningStep {
  step_number: number;
  label: string;
  description: string;
  timestamp: string;
}

export interface AnswerResponse {
  query: string;
  answer: string;
  status: AnswerStatus;
  confidence: number;
  why: WhyCategory[];
  claims: ClaimItem[];
  sources: EvidencePassage[];
  reasoning_steps: ReasoningStep[];
  retrieval_stats: {
    dense_results?: number;
    keyword_results?: number;
    fused_results?: number;
    reranked_results?: number;
  };
  generated_at: string;
}

export interface Source {
  source_id: string;
  name: string;
  source_type: string;
  url_or_path: string;
  status: string;
  crawl_frequency: string;
  trust_level: number;
  last_crawled_at?: string;
  last_success_at?: string;
  last_content_hash?: string;
  document_count: number;
  configuration: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Entity {
  entity_id: string;
  name: string;
  entity_type: string;
  country?: string;
  funding_raised_eur_m?: number;
  key_technologies: string[];
  description: string;
  sources_count: number;
}

export interface IngestionJob {
  job_id: string;
  source_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  documents_discovered: number;
  documents_processed: number;
  chunks_created: number;
  bytes_ingested: number;
  content_changed: boolean;
  error_message?: string;
}

export interface ResearchSessionQueryItem {
  query_id: string;
  query_text: string;
  executed_at: string;
  run_id: string;
  answer: string;
  status: string;
}

export interface ResearchSessionMetadata {
  total_queries: number;
  total_entities: number;
  total_propositions: number;
  supported_count: number;
  insufficient_count: number;
  conflict_count: number;
  evidence_count: number;
  source_count: number;
  evidence_density: number;
  corroboration_count: number;
  tier1_source_count: number;
}

export interface ResearchSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  queries: ResearchSessionQueryItem[];
  entities: Array<{ entity_id: string; entity_name: string }>;
  propositions: PropositionDTO[];
  supported_claims: ClaimDTO[];
  insufficient_propositions: InsufficientDTO[];
  contradictions: any[];
  conflicts: any[];
  evidence_references: EvidenceDTO[];
  source_references: SourceDTO[];
  withheld_items: any[];
  metadata: ResearchSessionMetadata;
}
