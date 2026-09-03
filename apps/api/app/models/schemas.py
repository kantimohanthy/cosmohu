from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class SourceType(str, Enum):
    WEB = "web"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    DOCX = "docx"

class SourceStatus(str, Enum):
    ACTIVE = "active"
    CRAWLING = "crawling"
    FAILED = "failed"
    IDLE = "idle"

class AnswerStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONFLICTING = "conflicting"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

class SourceBase(BaseModel):
    name: str
    source_type: SourceType
    url_or_path: str
    crawl_frequency: str = "daily"
    trust_level: float = Field(default=0.9, ge=0.0, le=1.0)
    configuration: Dict[str, Any] = Field(default_factory=dict)

class SourceCreate(SourceBase):
    pass

class Source(SourceBase):
    source_id: str
    status: SourceStatus = SourceStatus.IDLE
    last_crawled_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_content_hash: Optional[str] = None
    document_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentMetadata(BaseModel):
    publisher: Optional[str] = None
    published_at: Optional[str] = None
    language: str = "en"
    author: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

class DocumentSchema(BaseModel):
    document_id: str
    source_id: str
    title: str
    content: str
    source_url: str
    source_type: SourceType
    publisher: str = "Unknown"
    language: str = "en"
    retrieved_at: str
    published_at: Optional[str] = None
    content_hash: str
    metadata: DocumentMetadata
    version: int = 1

class ChunkSchema(BaseModel):
    chunk_id: str
    document_id: str
    source_id: str
    chunk_index: int
    content: str
    heading_context: Optional[str] = None
    section_heading: Optional[str] = None
    preceding_context: Optional[str] = None
    following_context: Optional[str] = None
    entity_attribution: Optional[str] = None
    start_char: int
    end_char: int
    token_count: int
    source_url: str
    publisher: str
    published_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EvidencePassage(BaseModel):
    passage_id: str
    chunk_id: str
    document_id: str
    source_id: str
    title: str
    publisher: str
    source_url: str
    published_at: Optional[str] = None
    retrieved_at: Optional[str] = None
    text: str
    relevance_score: float
    confidence_score: float
    why_relevant: str

class ClaimItem(BaseModel):
    claim_id: str
    text: str
    confidence: float
    status: str = "supported"
    evidence_ids: List[str]

class WhyCategory(BaseModel):
    code: str  # e.g., "01 — CAPITAL"
    title: str
    summary: str
    evidence_snippets: List[str]

class ReasoningStep(BaseModel):
    step_number: int
    label: str  # e.g., "UNDERSTANDING QUERY"
    description: str
    timestamp: str

class AnswerResponse(BaseModel):
    query: str
    answer: str
    status: AnswerStatus
    confidence: float
    why: List[WhyCategory]
    claims: List[ClaimItem]
    sources: List[EvidencePassage]
    reasoning_steps: List[ReasoningStep]
    retrieval_stats: Dict[str, Any]
    generated_at: str

class IngestionJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class IngestionJob(BaseModel):
    job_id: str
    source_id: str
    status: IngestionJobStatus
    started_at: str
    completed_at: Optional[str] = None
    documents_discovered: int = 0
    documents_processed: int = 0
    chunks_created: int = 0
    bytes_ingested: int = 0
    content_changed: bool = False
    error_message: Optional[str] = None

class Entity(BaseModel):
    entity_id: str
    name: str
    entity_type: str  # Company, Agency, Mission, Platform, Investor
    country: Optional[str] = None
    funding_raised_eur_m: Optional[float] = None
    key_technologies: List[str] = Field(default_factory=list)
    description: str
    sources_count: int = 0
