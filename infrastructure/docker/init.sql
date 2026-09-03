-- Enable pgvector extension for PostgreSQL vector search
CREATE EXTENSION IF NOT EXISTS vector;

-- Sources Registry Table
CREATE TABLE IF NOT EXISTS sources (
    source_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    url_or_path TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    crawl_frequency VARCHAR(32),
    trust_level FLOAT DEFAULT 0.9,
    last_crawled_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_content_hash VARCHAR(64),
    document_count INT DEFAULT 0,
    configuration JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents Provenance Table
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) REFERENCES sources(source_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    publisher VARCHAR(255),
    language VARCHAR(10) DEFAULT 'en',
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB,
    version INT DEFAULT 1
);

-- Chunks & Vector Store Table (384 Dimensions)
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) REFERENCES documents(document_id) ON DELETE CASCADE,
    source_id VARCHAR(64) REFERENCES sources(source_id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    heading_context TEXT,
    start_char INT,
    end_char INT,
    token_count INT,
    source_url TEXT,
    publisher VARCHAR(255),
    published_at TIMESTAMP,
    metadata JSONB,
    embedding vector(384)
);

-- Vector Cosine Similarity Index
CREATE INDEX IF NOT EXISTS chunks_embedding_cosine_idx ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Space Entities Table
CREATE TABLE IF NOT EXISTS entities (
    entity_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    country VARCHAR(100),
    funding_raised_eur_m FLOAT,
    key_technologies JSONB,
    description TEXT,
    sources_count INT DEFAULT 0
);

-- Ingestion Jobs Table
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) REFERENCES sources(source_id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    documents_discovered INT DEFAULT 0,
    documents_processed INT DEFAULT 0,
    chunks_created INT DEFAULT 0,
    bytes_ingested BIGINT DEFAULT 0,
    content_changed BOOLEAN DEFAULT FALSE,
    error_message TEXT
);
