import os
import json
import csv
import io
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.schemas import DocumentSchema, DocumentMetadata, SourceType
from app.services.hashing import compute_content_hash, extract_title_from_text
from app.services.crawler import fetch_web_page, determine_source_tier

class BaseParser:
    def parse(self, source_id: str, raw_data: Any, url_or_path: str, publisher: str = "Unknown") -> DocumentSchema:
        raise NotImplementedError

class WebParser(BaseParser):
    def parse(self, source_id: str, raw_data: Any, url_or_path: str, publisher: str = "Web Source") -> DocumentSchema:
        requested_url = url_or_path
        final_resolved_url = url_or_path
        was_redirected = False
        identity_mismatch = False
        source_tier = determine_source_tier(url_or_path, publisher)

        if isinstance(raw_data, str) and (raw_data.startswith("http://") or raw_data.startswith("https://")):
            crawled = fetch_web_page(raw_data)
            content = crawled["content"]
            title = crawled["title"]
            requested_url = crawled["requested_url"]
            final_resolved_url = crawled["final_resolved_url"]
            was_redirected = crawled["was_redirected"]
            identity_mismatch = crawled["identity_mismatch"]
            publisher = crawled["publisher"]
            source_tier = crawled["source_tier"]
        elif isinstance(raw_data, dict):
            content = raw_data.get("content", "")
            title = raw_data.get("title", "Web Document")
            requested_url = raw_data.get("requested_url", url_or_path)
            final_resolved_url = raw_data.get("final_resolved_url", url_or_path)
            was_redirected = raw_data.get("was_redirected", False)
            identity_mismatch = raw_data.get("identity_mismatch", False)
            source_tier = raw_data.get("source_tier", determine_source_tier(final_resolved_url, publisher))
        else:
            content = str(raw_data)
            title = extract_title_from_text(content, "Web Page")
            
        content_hash = compute_content_hash(content)
        doc_id = f"doc_{content_hash[:16]}"
        
        meta = DocumentMetadata(
            publisher=publisher,
            extra={
                "requested_url": requested_url,
                "final_resolved_url": final_resolved_url,
                "was_redirected": was_redirected,
                "identity_mismatch": identity_mismatch,
                "source_tier": source_tier,
                "format": "web"
            }
        )

        return DocumentSchema(
            document_id=doc_id,
            source_id=source_id,
            title=title,
            content=content,
            source_url=final_resolved_url,
            source_type=SourceType.WEB,
            publisher=publisher,
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            metadata=meta
        )

class CSVParser(BaseParser):
    def parse(self, source_id: str, raw_data: Any, url_or_path: str, publisher: str = "CSV Dataset") -> DocumentSchema:
        if isinstance(raw_data, str) and os.path.exists(raw_data):
            with open(raw_data, mode="r", encoding="utf-8", errors="replace") as f:
                content_str = f.read()
        elif isinstance(raw_data, bytes):
            content_str = raw_data.decode("utf-8", errors="replace")
        else:
            content_str = str(raw_data)
            
        reader = csv.DictReader(io.StringIO(content_str))
        rows = list(reader)
        
        formatted_blocks = []
        for idx, row in enumerate(rows, 1):
            fields = [f"{k.strip().replace('_', ' ').title()}: {v.strip()}" for k, v in row.items() if v and v.strip()]
            entity_title = row.get("company_name") or row.get("name") or row.get("title") or f"Record #{idx}"
            block = f"--- Record #{idx}: {entity_title} ---\n" + "\n".join(fields)
            formatted_blocks.append(block)
            
        full_content = "\n\n".join(formatted_blocks)
        content_hash = compute_content_hash(full_content)
        doc_id = f"doc_{content_hash[:16]}"
        file_name = os.path.basename(url_or_path)
        source_tier = determine_source_tier(url_or_path, publisher)

        meta = DocumentMetadata(
            publisher=publisher,
            extra={
                "requested_url": url_or_path,
                "final_resolved_url": url_or_path,
                "was_redirected": False,
                "identity_mismatch": False,
                "source_tier": source_tier,
                "record_count": len(rows),
                "file_name": file_name
            }
        )

        return DocumentSchema(
            document_id=doc_id,
            source_id=source_id,
            title=f"Dataset: {file_name}",
            content=full_content,
            source_url=url_or_path,
            source_type=SourceType.CSV,
            publisher=publisher,
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            metadata=meta
        )

class JSONParser(BaseParser):
    def parse(self, source_id: str, raw_data: Any, url_or_path: str, publisher: str = "JSON Dataset") -> DocumentSchema:
        if isinstance(raw_data, str) and os.path.exists(raw_data):
            with open(raw_data, mode="r", encoding="utf-8", errors="replace") as f:
                obj = json.load(f)
        elif isinstance(raw_data, (str, bytes)):
            obj = json.loads(raw_data)
        else:
            obj = raw_data
            
        formatted_blocks = []
        dataset_name = "JSON Dataset"
        
        if isinstance(obj, dict):
            dataset_name = obj.get("dataset") or obj.get("title") or dataset_name
            publisher = obj.get("publisher") or publisher
            records = obj.get("records") or obj.get("data") or [obj]
        elif isinstance(obj, list):
            records = obj
        else:
            records = [obj]
            
        for idx, rec in enumerate(records, 1):
            if isinstance(rec, dict):
                rec_name = rec.get("name") or rec.get("program_id") or rec.get("title") or f"Entry #{idx}"
                lines = [f"{k.replace('_', ' ').title()}: {json.dumps(v) if isinstance(v, (dict, list)) else v}" for k, v in rec.items()]
                formatted_blocks.append(f"--- Entity Record: {rec_name} ---\n" + "\n".join(lines))
            else:
                formatted_blocks.append(str(rec))
                
        full_content = "\n\n".join(formatted_blocks)
        content_hash = compute_content_hash(full_content)
        doc_id = f"doc_{content_hash[:16]}"
        file_name = os.path.basename(url_or_path)
        source_tier = determine_source_tier(url_or_path, publisher)

        meta = DocumentMetadata(
            publisher=publisher,
            extra={
                "requested_url": url_or_path,
                "final_resolved_url": url_or_path,
                "was_redirected": False,
                "identity_mismatch": False,
                "source_tier": source_tier,
                "record_count": len(records),
                "file_name": file_name
            }
        )

        return DocumentSchema(
            document_id=doc_id,
            source_id=source_id,
            title=f"Structured JSON: {dataset_name}",
            content=full_content,
            source_url=url_or_path,
            source_type=SourceType.JSON,
            publisher=publisher,
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            metadata=meta
        )

class MarkdownParser(BaseParser):
    def parse(self, source_id: str, raw_data: Any, url_or_path: str, publisher: str = "Markdown Source") -> DocumentSchema:
        if isinstance(raw_data, str) and os.path.exists(raw_data):
            with open(raw_data, mode="r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        else:
            content = str(raw_data)
            
        title = extract_title_from_text(content, os.path.basename(url_or_path))
        content_hash = compute_content_hash(content)
        doc_id = f"doc_{content_hash[:16]}"
        source_tier = determine_source_tier(url_or_path, publisher)

        meta = DocumentMetadata(
            publisher=publisher,
            extra={
                "requested_url": url_or_path,
                "final_resolved_url": url_or_path,
                "was_redirected": False,
                "identity_mismatch": False,
                "source_tier": source_tier,
                "format": "markdown"
            }
        )

        return DocumentSchema(
            document_id=doc_id,
            source_id=source_id,
            title=title,
            content=content,
            source_url=url_or_path,
            source_type=SourceType.MARKDOWN,
            publisher=publisher,
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            metadata=meta
        )

class PDFParser(BaseParser):
    def parse(self, source_id: str, raw_data: Any, url_or_path: str, publisher: str = "PDF Document") -> DocumentSchema:
        content = ""
        if isinstance(raw_data, str) and os.path.exists(raw_data):
            try:
                import pypdf
                reader = pypdf.PdfReader(raw_data)
                text_runs = []
                for page_num, page in enumerate(reader.pages, 1):
                    txt = page.extract_text()
                    if txt:
                        text_runs.append(f"--- Page {page_num} ---\n{txt}")
                content = "\n\n".join(text_runs)
            except Exception as e:
                content = f"PDF content extraction fallback: {os.path.basename(url_or_path)} ({e})"
        else:
            content = str(raw_data)
            
        title = extract_title_from_text(content, os.path.basename(url_or_path))
        content_hash = compute_content_hash(content)
        doc_id = f"doc_{content_hash[:16]}"
        source_tier = determine_source_tier(url_or_path, publisher)

        meta = DocumentMetadata(
            publisher=publisher,
            extra={
                "requested_url": url_or_path,
                "final_resolved_url": url_or_path,
                "was_redirected": False,
                "identity_mismatch": False,
                "source_tier": source_tier,
                "format": "pdf"
            }
        )

        return DocumentSchema(
            document_id=doc_id,
            source_id=source_id,
            title=title,
            content=content,
            source_url=url_or_path,
            source_type=SourceType.PDF,
            publisher=publisher,
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            metadata=meta
        )

class DOCXParser(BaseParser):
    def parse(self, source_id: str, raw_data: Any, url_or_path: str, publisher: str = "Word Document") -> DocumentSchema:
        content = ""
        if isinstance(raw_data, str) and os.path.exists(raw_data):
            try:
                import docx
                doc = docx.Document(raw_data)
                paras = [p.text for p in doc.paragraphs if p.text.strip()]
                content = "\n\n".join(paras)
            except Exception as e:
                content = f"DOCX extraction fallback: {os.path.basename(url_or_path)} ({e})"
        else:
            content = str(raw_data)
            
        title = extract_title_from_text(content, os.path.basename(url_or_path))
        content_hash = compute_content_hash(content)
        doc_id = f"doc_{content_hash[:16]}"
        source_tier = determine_source_tier(url_or_path, publisher)

        meta = DocumentMetadata(
            publisher=publisher,
            extra={
                "requested_url": url_or_path,
                "final_resolved_url": url_or_path,
                "was_redirected": False,
                "identity_mismatch": False,
                "source_tier": source_tier,
                "format": "docx"
            }
        )

        return DocumentSchema(
            document_id=doc_id,
            source_id=source_id,
            title=title,
            content=content,
            source_url=url_or_path,
            source_type=SourceType.DOCX,
            publisher=publisher,
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            metadata=meta
        )

PARSER_REGISTRY: Dict[SourceType, BaseParser] = {
    SourceType.WEB: WebParser(),
    SourceType.CSV: CSVParser(),
    SourceType.JSON: JSONParser(),
    SourceType.MARKDOWN: MarkdownParser(),
    SourceType.PDF: PDFParser(),
    SourceType.DOCX: DOCXParser(),
}

def parse_document(source_id: str, source_type: SourceType, raw_data: Any, url_or_path: str, publisher: str = "Unknown") -> DocumentSchema:
    parser = PARSER_REGISTRY.get(source_type, WebParser())
    return parser.parse(source_id, raw_data, url_or_path, publisher)
