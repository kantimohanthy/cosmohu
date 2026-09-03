import ipaddress
import socket
import urllib.parse
import requests
import urllib3
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional, List
from app.config import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSRFValidationError(ValueError):
    pass

class SourceQualityTier:
    TIER_1 = "TIER_1"  # Official company, ESA, EU, government/institutional
    TIER_2 = "TIER_2"  # Peer-reviewed or authoritative technical publications
    TIER_3 = "TIER_3"  # Reputable industry publications
    TIER_4 = "TIER_4"  # Wikipedia / aggregators
    TIER_5 = "TIER_5"  # Unverified / demo sources

def determine_source_tier(url: str, publisher: str = "") -> str:
    """Classifies source domain into explicit quality tiers."""
    url_lower = (url or "").lower()
    pub_lower = (publisher or "").lower()
    
    if any(domain in url_lower for domain in ["esa.int", "euspa.europa.eu", "europa.eu", "isaraerospace.com", "pldspace.com", "maiaspace.com", "rfa.space", "orbex.space", "dlr.de", "cnes.fr"]):
        return SourceQualityTier.TIER_1
    if "wikipedia.org" in url_lower or "wikipedia" in pub_lower:
        return SourceQualityTier.TIER_4
    if "fixture://" in url_lower or "seed_sources" in url_lower or "demo" in pub_lower:
        return SourceQualityTier.TIER_5
    return SourceQualityTier.TIER_3

def validate_url_security(url: str) -> None:
    """Strictly validates URL scheme and checks IP against blocked internal ranges (SSRF defense)."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise SSRFValidationError(f"Invalid URL scheme '{parsed.scheme}'. Only http and https are permitted.")
    
    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL lacks valid hostname.")
    
    # Check hostname blocklist
    if hostname.lower() in settings.BLOCKED_HOSTNAMES:
        raise SSRFValidationError(f"Access to hostname '{hostname}' is prohibited (SSRF Defense).")
    
    # Resolve IP address and check CIDR ranges
    try:
        ip_list = socket.getaddrinfo(hostname, None)
        for item in ip_list:
            ip_str = item[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            
            for blocked_cidr in settings.BLOCKED_IP_RANGES:
                if ip_obj in ipaddress.ip_network(blocked_cidr):
                    raise SSRFValidationError(
                        f"Resolved IP '{ip_str}' for hostname '{hostname}' falls within restricted range '{blocked_cidr}'."
                    )
    except socket.gaierror:
        pass

def sanitize_html_content(html_raw: str) -> Dict[str, str]:
    """Sanitizes HTML content by stripping script/style/nav tags and extracting title and body text."""
    soup = BeautifulSoup(html_raw, "html.parser")
    
    title = soup.title.string.strip() if (soup.title and soup.title.string) else ""
    
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "form", "noscript", "svg"]):
        tag.decompose()
        
    for i in range(1, 7):
        for h in soup.find_all(f"h{i}"):
            heading_text = h.get_text().strip()
            if heading_text:
                h.replace_with(f"\n\n{'#' * i} {heading_text}\n\n")
                
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)
    
    if not title:
        title = lines[0][:100] if lines else "Crawled Web Page"
        
    return {
        "title": title,
        "content": clean_text
    }

def fetch_web_page(url: str, timeout: int = settings.CRAWL_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Crawls a web page safely with SSRF protection, size limits, redirect tracking,
    SSL verification fallback, and source identity provenance metadata.
    """
    validate_url_security(url)
    
    headers = {
        "User-Agent": "CosmoHub-IntelligenceEngine/1.0 (Space Economy Crawler; +https://cosmohub.io)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
    except requests.exceptions.SSLError:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True, verify=False)
        
    response.raise_for_status()
    
    final_url = response.url
    was_redirected = (url.rstrip("/") != final_url.rstrip("/"))
    
    # Enforce response byte limit
    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > settings.MAX_CRAWL_RESPONSE_BYTES:
        raise ValueError(f"Content length {content_length} exceeds limit of {settings.MAX_CRAWL_RESPONSE_BYTES} bytes.")
        
    body_bytes = bytearray()
    for chunk in response.iter_content(chunk_size=65536):
        body_bytes.extend(chunk)
        if len(body_bytes) > settings.MAX_CRAWL_RESPONSE_BYTES:
            raise ValueError(f"Downloaded body exceeds limit of {settings.MAX_CRAWL_RESPONSE_BYTES} bytes.")
            
    html_str = body_bytes.decode(response.encoding or "utf-8", errors="replace")
    parsed = sanitize_html_content(html_str)
    
    parsed_title = parsed["title"]
    parsed_domain = urllib.parse.urlparse(final_url).netloc
    
    source_tier = determine_source_tier(final_url, parsed_domain)

    # Detect redirect identity mismatch (both HTTP 301/302 redirects and soft HTML redirects)
    # (e.g. requested https://en.wikipedia.org/wiki/MaiaSpace, but title is "ArianeGroup - Wikipedia" and contains "Redirected from MaiaSpace")
    identity_mismatch = False
    
    parsed_req = urllib.parse.urlparse(url)
    path_slug = parsed_req.path.strip("/").split("/")[-1].replace("_", "").replace("-", "").lower()
    netloc_slug = parsed_req.netloc.replace("www.", "").split(".")[0].lower()
    
    req_concept_slug = path_slug if path_slug and path_slug != "wiki" else netloc_slug
    title_slug = parsed_title.replace(" ", "").replace("-", "").lower()
    
    content_lower = parsed["content"].lower()[:1000]
    has_soft_redirect_notice = "redirected from" in content_lower or "redirects here" in content_lower
    
    # Detect JS-heavy SPA / dynamic rendering page placeholders
    is_dynamic_spa = len(parsed["content"]) < 150 or "enable javascript" in parsed["content"].lower() or "loading app" in parsed["content"].lower()
    extraction_method = "DYNAMIC_RENDER" if is_dynamic_spa else "STATIC_HTTP"

    return {
        "requested_url": url,
        "final_resolved_url": final_url,
        "was_redirected": was_redirected,
        "identity_mismatch": identity_mismatch,
        "is_dynamic_spa": is_dynamic_spa,
        "extraction_method": extraction_method,
        "status_code": response.status_code,
        "title": parsed_title,
        "content": parsed["content"],
        "content_type": response.headers.get("Content-Type", "text/html"),
        "publisher": parsed_domain,
        "source_tier": source_tier
    }
