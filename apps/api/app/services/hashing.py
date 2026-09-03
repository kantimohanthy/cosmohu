import hashlib
import re

def compute_content_hash(content: str) -> str:
    """Computes a canonical SHA-256 hash of text content normalized for whitespace."""
    normalized = re.sub(r'\s+', ' ', content.strip()).lower()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def compute_chunk_hash(doc_id: str, chunk_index: int, content: str) -> str:
    """Computes unique chunk ID deterministically."""
    raw = f"{doc_id}:{chunk_index}:{content[:100]}"
    return "chk_" + hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

def extract_title_from_text(content: str, default: str = "Untitled Document") -> str:
    """Extracts the first heading or non-empty line as title."""
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        return default
    first_line = lines[0]
    first_line = re.sub(r'^[#*=\-\s]+', '', first_line).strip()
    return first_line[:120] if first_line else default
