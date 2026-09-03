import sqlite3
import json
import os
import re
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.models.schemas import Source, DocumentSchema, ChunkSchema, Entity, IngestionJob, SourceStatus, IngestionJobStatus

class VectorStore:
    def __init__(self, db_path: str = settings.SQLITE_FALLBACK_DB):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def reset_store(self):
        """Clears all records from SQLite storage tables for clean isolated runs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM sources")
            cursor.execute("DELETE FROM entities")
            cursor.execute("DELETE FROM research_sessions")
            conn.commit()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Research Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    data_json TEXT NOT NULL
                )
            """)
            # Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    url_or_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    crawl_frequency TEXT,
                    trust_level REAL,
                    last_crawled_at TEXT,
                    last_success_at TEXT,
                    last_content_hash TEXT,
                    document_count INTEGER DEFAULT 0,
                    configuration TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    publisher TEXT,
                    language TEXT,
                    retrieved_at TEXT,
                    published_at TEXT,
                    content_hash TEXT NOT NULL,
                    metadata TEXT,
                    version INTEGER DEFAULT 1,
                    FOREIGN KEY(source_id) REFERENCES sources(source_id)
                )
            """)
            # Chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    heading_context TEXT,
                    start_char INTEGER,
                    end_char INTEGER,
                    token_count INTEGER,
                    source_url TEXT,
                    publisher TEXT,
                    published_at TEXT,
                    metadata TEXT,
                    embedding_json TEXT,
                    FOREIGN KEY(document_id) REFERENCES documents(document_id)
                )
            """)
            # Entities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    country TEXT,
                    funding_raised_eur_m REAL,
                    key_technologies TEXT,
                    description TEXT,
                    sources_count INTEGER DEFAULT 0
                )
            """)
            # Ingestion Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    job_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    documents_discovered INTEGER DEFAULT 0,
                    documents_processed INTEGER DEFAULT 0,
                    chunks_created INTEGER DEFAULT 0,
                    bytes_ingested INTEGER DEFAULT 0,
                    content_changed INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
            conn.commit()

    # Source operations
    def save_source(self, source: Source) -> Source:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sources (
                    source_id, name, source_type, url_or_path, status, crawl_frequency,
                    trust_level, last_crawled_at, last_success_at, last_content_hash,
                    document_count, configuration, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source.source_id, source.name, source.source_type.value, source.url_or_path,
                source.status.value, source.crawl_frequency, source.trust_level,
                source.last_crawled_at.isoformat() if source.last_crawled_at else None,
                source.last_success_at.isoformat() if source.last_success_at else None,
                source.last_content_hash, source.document_count,
                json.dumps(source.configuration),
                source.created_at.isoformat(), source.updated_at.isoformat()
            ))
            conn.commit()
        return source

    def get_source(self, source_id: str) -> Optional[Source]:
        with self._get_connection() as conn:
            row = conn.cursor().execute("SELECT * FROM sources WHERE source_id = ?", (source_id,)).fetchone()
            if not row:
                return None
            return Source(
                source_id=row["source_id"],
                name=row["name"],
                source_type=row["source_type"],
                url_or_path=row["url_or_path"],
                status=SourceStatus(row["status"]),
                crawl_frequency=row["crawl_frequency"],
                trust_level=row["trust_level"],
                last_crawled_at=datetime.fromisoformat(row["last_crawled_at"]) if row["last_crawled_at"] else None,
                last_success_at=datetime.fromisoformat(row["last_success_at"]) if row["last_success_at"] else None,
                last_content_hash=row["last_content_hash"],
                document_count=row["document_count"],
                configuration=json.loads(row["configuration"]) if row["configuration"] else {},
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow()
            )

    def list_sources(self) -> List[Source]:
        with self._get_connection() as conn:
            rows = conn.cursor().execute("SELECT * FROM sources ORDER BY created_at DESC").fetchall()
            sources = []
            for row in rows:
                sources.append(Source(
                    source_id=row["source_id"],
                    name=row["name"],
                    source_type=row["source_type"],
                    url_or_path=row["url_or_path"],
                    status=SourceStatus(row["status"]),
                    crawl_frequency=row["crawl_frequency"],
                    trust_level=row["trust_level"],
                    last_crawled_at=datetime.fromisoformat(row["last_crawled_at"]) if row["last_crawled_at"] else None,
                    last_success_at=datetime.fromisoformat(row["last_success_at"]) if row["last_success_at"] else None,
                    last_content_hash=row["last_content_hash"],
                    document_count=row["document_count"],
                    configuration=json.loads(row["configuration"]) if row["configuration"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow()
                ))
            return sources

    # Document & Chunk operations
    def save_document(self, doc: DocumentSchema) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    document_id, source_id, title, content, source_url, source_type,
                    publisher, language, retrieved_at, published_at, content_hash, metadata, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.document_id, doc.source_id, doc.title, doc.content, doc.source_url,
                doc.source_type.value, doc.publisher, doc.language, doc.retrieved_at,
                doc.published_at, doc.content_hash, json.dumps(doc.metadata.model_dump()), doc.version
            ))
            conn.commit()

    def get_document(self, doc_id: str) -> Optional[DocumentSchema]:
        with self._get_connection() as conn:
            row = conn.cursor().execute("SELECT * FROM documents WHERE document_id = ?", (doc_id,)).fetchone()
            if not row:
                return None
            return DocumentSchema(
                document_id=row["document_id"],
                source_id=row["source_id"],
                title=row["title"],
                content=row["content"],
                source_url=row["source_url"],
                source_type=row["source_type"],
                publisher=row["publisher"],
                language=row["language"],
                retrieved_at=row["retrieved_at"],
                published_at=row["published_at"],
                content_hash=row["content_hash"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                version=row["version"]
            )

    def list_documents(self) -> List[DocumentSchema]:
        with self._get_connection() as conn:
            rows = conn.cursor().execute("SELECT * FROM documents ORDER BY retrieved_at DESC").fetchall()
            res = []
            for row in rows:
                res.append(DocumentSchema(
                    document_id=row["document_id"],
                    source_id=row["source_id"],
                    title=row["title"],
                    content=row["content"],
                    source_url=row["source_url"],
                    source_type=row["source_type"],
                    publisher=row["publisher"],
                    language=row["language"],
                    retrieved_at=row["retrieved_at"],
                    published_at=row["published_at"],
                    content_hash=row["content_hash"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    version=row["version"]
                ))
            return res

    def save_chunks(self, chunks: List[ChunkSchema], embeddings: List[List[float]]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for chk, emb in zip(chunks, embeddings):
                cursor.execute("""
                    INSERT OR REPLACE INTO chunks (
                        chunk_id, document_id, source_id, chunk_index, content,
                        heading_context, start_char, end_char, token_count, source_url,
                        publisher, published_at, metadata, embedding_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chk.chunk_id, chk.document_id, chk.source_id, chk.chunk_index, chk.content,
                    chk.heading_context, chk.start_char, chk.end_char, chk.token_count,
                    chk.source_url, chk.publisher, chk.published_at,
                    json.dumps(chk.metadata), json.dumps(emb)
                ))
            conn.commit()

    def search_vector_dense(
        self, query_embedding: List[float], top_k: int = 20, source_filter: Optional[str] = None
    ) -> List[Tuple[ChunkSchema, float]]:
        """Performs dense vector similarity search (cosine similarity)."""
        with self._get_connection() as conn:
            query = "SELECT * FROM chunks"
            params = []
            if source_filter:
                query += " WHERE source_id = ?"
                params.append(source_filter)
                
            rows = conn.cursor().execute(query, params).fetchall()
            if not rows:
                return []
                
            q_vec = np.array(query_embedding, dtype=np.float32)
            q_norm = np.linalg.norm(q_vec)
            if q_norm == 0:
                return []
                
            scored_chunks = []
            for row in rows:
                emb_list = json.loads(row["embedding_json"]) if row["embedding_json"] else []
                if not emb_list:
                    continue
                c_vec = np.array(emb_list, dtype=np.float32)
                c_norm = np.linalg.norm(c_vec)
                score = 0.0
                if c_norm > 0:
                    score = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                    
                chk = ChunkSchema(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    source_id=row["source_id"],
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    heading_context=row["heading_context"],
                    start_char=row["start_char"],
                    end_char=row["end_char"],
                    token_count=row["token_count"],
                    source_url=row["source_url"],
                    publisher=row["publisher"],
                    published_at=row["published_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                )
                scored_chunks.append((chk, score))
                
            scored_chunks.sort(key=lambda x: x[1], reverse=True)
            return scored_chunks[:top_k]

    def search_keyword_sparse(
        self, query_text: str, top_k: int = 20, source_filter: Optional[str] = None
    ) -> List[Tuple[ChunkSchema, float]]:
        """Performs sparse keyword matching (BM25 token overlap score)."""
        with self._get_connection() as conn:
            query = "SELECT * FROM chunks"
            params = []
            if source_filter:
                query += " WHERE source_id = ?"
                params.append(source_filter)
                
            rows = conn.cursor().execute(query, params).fetchall()
            if not rows:
                return []
                
            query_terms = set(re.findall(r'\w+', query_text.lower()))
            if not query_terms:
                return []
                
            scored_chunks = []
            for row in rows:
                content = row["content"].lower()
                doc_terms = re.findall(r'\w+', content)
                match_count = sum(1 for t in query_terms if t in doc_terms)
                score = match_count / (len(query_terms) + 0.1)
                
                if score > 0:
                    chk = ChunkSchema(
                        chunk_id=row["chunk_id"],
                        document_id=row["document_id"],
                        source_id=row["source_id"],
                        chunk_index=row["chunk_index"],
                        content=row["content"],
                        heading_context=row["heading_context"],
                        start_char=row["start_char"],
                        end_char=row["end_char"],
                        token_count=row["token_count"],
                        source_url=row["source_url"],
                        publisher=row["publisher"],
                        published_at=row["published_at"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                    )
                    scored_chunks.append((chk, float(score)))
                    
            scored_chunks.sort(key=lambda x: x[1], reverse=True)
            return scored_chunks[:top_k]

    # Ingestion Job Operations
    def save_job(self, job: IngestionJob) -> IngestionJob:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ingestion_jobs (
                    job_id, source_id, status, started_at, completed_at,
                    documents_discovered, documents_processed, chunks_created,
                    bytes_ingested, content_changed, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.source_id, job.status.value, job.started_at,
                job.completed_at, job.documents_discovered, job.documents_processed,
                job.chunks_created, job.bytes_ingested, 1 if job.content_changed else 0,
                job.error_message
            ))
            conn.commit()
        return job

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        with self._get_connection() as conn:
            row = conn.cursor().execute("SELECT * FROM ingestion_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return IngestionJob(
                job_id=row["job_id"],
                source_id=row["source_id"],
                status=IngestionJobStatus(row["status"]),
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                documents_discovered=row["documents_discovered"],
                documents_processed=row["documents_processed"],
                chunks_created=row["chunks_created"],
                bytes_ingested=row["bytes_ingested"],
                content_changed=bool(row["content_changed"]),
                error_message=row["error_message"]
            )

    # Entities operations
    def save_entity(self, entity: Entity) -> Entity:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO entities (
                    entity_id, name, entity_type, country, funding_raised_eur_m,
                    key_technologies, description, sources_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.entity_id, entity.name, entity.entity_type, entity.country,
                entity.funding_raised_eur_m, json.dumps(entity.key_technologies),
                entity.description, entity.sources_count
            ))
            conn.commit()
        return entity

    def list_entities(self) -> List[Entity]:
        with self._get_connection() as conn:
            rows = conn.cursor().execute("SELECT * FROM entities ORDER BY name ASC").fetchall()
            entities = []
            for row in rows:
                entities.append(Entity(
                    entity_id=row["entity_id"],
                    name=row["name"],
                    entity_type=row["entity_type"],
                    country=row["country"],
                    funding_raised_eur_m=row["funding_raised_eur_m"],
                    key_technologies=json.loads(row["key_technologies"]) if row["key_technologies"] else [],
                    description=row["description"],
                    sources_count=row["sources_count"]
                ))
            return entities

    # Research session operations
    def save_research_session(self, session_id: str, title: str, created_at: str, updated_at: str, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO research_sessions (session_id, title, created_at, updated_at, data_json)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, title, created_at, updated_at, json.dumps(data)))
            conn.commit()
        return data

    def get_research_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.cursor().execute("SELECT * FROM research_sessions WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                data = json.loads(row["data_json"])
                return data
            return None

    def list_research_sessions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.cursor().execute("SELECT * FROM research_sessions ORDER BY updated_at DESC").fetchall()
            sessions = []
            for row in rows:
                data = json.loads(row["data_json"])
                sessions.append(data)
            return sessions

    def delete_research_session(self, session_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM research_sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0

# Singleton vector store instance
store = VectorStore()
