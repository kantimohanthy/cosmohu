import re
from typing import List, Optional
from app.models.schemas import DocumentSchema, ChunkSchema
from app.services.hashing import compute_chunk_hash
from app.config import settings

def estimate_token_count(text: str) -> int:
    """Estimates token count by whitespace and punctuation splitting (~1.3 tokens per word)."""
    words = re.findall(r'\w+|\S', text)
    return max(1, int(len(words) * 1.1))

def chunk_document(
    doc: DocumentSchema,
    max_tokens: int = settings.DEFAULT_CHUNK_SIZE_TOKENS,
    overlap_tokens: int = settings.DEFAULT_CHUNK_OVERLAP_TOKENS
) -> List[ChunkSchema]:
    """
    Chunks document content into semantic chunks preserving heading context,
    character boundaries, and complete provenance metadata.
    """
    content = doc.content
    if not content or not content.strip():
        return []
        
    paragraphs = re.split(r'\n\s*\n', content)
    
    chunks: List[ChunkSchema] = []
    current_tokens = 0
    current_text_blocks = []
    current_heading: Optional[str] = doc.title
    start_char_idx = 0
    chunk_index = 0
    
    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue
            
        # Detect markdown heading
        if para_clean.startswith('#'):
            heading_line = para_clean.splitlines()[0]
            current_heading = re.sub(r'^[#\s]+', '', heading_line).strip()
            
        para_tokens = estimate_token_count(para_clean)
        
        # If single paragraph exceeds max size, split by sentences
        if para_tokens > max_tokens:
            sentences = re.split(r'(?<=[.!?])\s+', para_clean)
            for sent in sentences:
                sent_tokens = estimate_token_count(sent)
                if current_tokens + sent_tokens > max_tokens and current_text_blocks:
                    chunk_text = "\n\n".join(current_text_blocks)
                    end_char_idx = start_char_idx + len(chunk_text)
                    chunk_id = compute_chunk_hash(doc.document_id, chunk_index, chunk_text)
                    
                    chunks.append(ChunkSchema(
                        chunk_id=chunk_id,
                        document_id=doc.document_id,
                        source_id=doc.source_id,
                        chunk_index=chunk_index,
                        content=chunk_text,
                        heading_context=current_heading,
                        start_char=start_char_idx,
                        end_char=end_char_idx,
                        token_count=estimate_token_count(chunk_text),
                        source_url=doc.source_url,
                        publisher=doc.publisher,
                        published_at=doc.published_at,
                        metadata={"format": doc.source_type.value, "title": doc.title}
                    ))
                    
                    chunk_index += 1
                    start_char_idx = end_char_idx
                    # Keep overlap
                    if overlap_tokens > 0 and len(current_text_blocks) > 1:
                        current_text_blocks = current_text_blocks[-1:]
                        current_tokens = estimate_token_count(current_text_blocks[0])
                    else:
                        current_text_blocks = []
                        current_tokens = 0
                        
                current_text_blocks.append(sent)
                current_tokens += sent_tokens
        else:
            if current_tokens + para_tokens > max_tokens and current_text_blocks:
                chunk_text = "\n\n".join(current_text_blocks)
                end_char_idx = start_char_idx + len(chunk_text)
                chunk_id = compute_chunk_hash(doc.document_id, chunk_index, chunk_text)
                
                chunks.append(ChunkSchema(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    source_id=doc.source_id,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    heading_context=current_heading,
                    start_char=start_char_idx,
                    end_char=end_char_idx,
                    token_count=estimate_token_count(chunk_text),
                    source_url=doc.source_url,
                    publisher=doc.publisher,
                    published_at=doc.published_at,
                    metadata={"format": doc.source_type.value, "title": doc.title}
                ))
                
                chunk_index += 1
                start_char_idx = end_char_idx
                # Overlap
                if overlap_tokens > 0 and len(current_text_blocks) > 1:
                    current_text_blocks = current_text_blocks[-1:]
                    current_tokens = estimate_token_count(current_text_blocks[0])
                else:
                    current_text_blocks = []
                    current_tokens = 0
                    
            current_text_blocks.append(para_clean)
            current_tokens += para_tokens
            
    # Tail chunk
    if current_text_blocks:
        chunk_text = "\n\n".join(current_text_blocks)
        end_char_idx = start_char_idx + len(chunk_text)
        chunk_id = compute_chunk_hash(doc.document_id, chunk_index, chunk_text)
        
        chunks.append(ChunkSchema(
            chunk_id=chunk_id,
            document_id=doc.document_id,
            source_id=doc.source_id,
            chunk_index=chunk_index,
            content=chunk_text,
            heading_context=current_heading,
            start_char=start_char_idx,
            end_char=end_char_idx,
            token_count=estimate_token_count(chunk_text),
            source_url=doc.source_url,
            publisher=doc.publisher,
            published_at=doc.published_at,
            metadata={"format": doc.source_type.value, "title": doc.title}
        ))

    ent_attr = doc.metadata.extra.get("entity_id") if (doc.metadata and doc.metadata.extra) else ("pld" if "pld" in doc.document_id else ("isar" if "isar" in doc.document_id else "unknown"))

    # Post-process chunks to compute preceding and following context snippets
    for idx, chk in enumerate(chunks):
        chk.section_heading = current_heading or doc.title
        chk.entity_attribution = ent_attr
        chk.preceding_context = chunks[idx - 1].content[:200] if idx > 0 else f"Document: {doc.title}"
        chk.following_context = chunks[idx + 1].content[:200] if idx < len(chunks) - 1 else "End of document."

    return chunks
