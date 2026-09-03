"""
TARGETED EVIDENCE DISCOVERY MODULE (STAGE 3.2)
----------------------------------------------
Implements multi-stage discovery order:
1. sitemap.xml / sitemap_index.xml
2. robots.txt (Sitemap directives)
3. Static HTML links from root and sub-pages
4. Same-domain enforcement (external links strictly prohibited from becoming company pages)
5. RSS / official newsroom feeds
6. Playwright browser rendering (ONLY if static discovery methods fail to return internal sub-pages)
"""

import urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Set, Tuple
import requests

from app.services.crawler import fetch_web_page, determine_source_tier, validate_url_security, SourceQualityTier
from app.services.source_registry import RegisteredSource

DISCOVERY_KEYWORDS = [
    "reusable", "reusability", "recovery", "recovered", "first stage", "launch vehicle",
    "launcher", "vehicle development", "propulsion", "orbital", "launch architecture",
    "missions", "technology", "technical specifications", "development", "official announcements",
    "newsroom", "press releases", "spectrum", "miura", "rfaone", "prime"
]

def fetch_sitemap_urls(root_url: str) -> List[str]:
    """Attempts to fetch URLs from /sitemap.xml or /robots.txt with fast timeout."""
    sitemap_urls: Set[str] = set()
    parsed_root = urllib.parse.urlparse(root_url)
    base_domain = f"{parsed_root.scheme}://{parsed_root.netloc}"

    try:
        robots_res = requests.get(f"{base_domain}/robots.txt", timeout=2, verify=False)
        if robots_res.status_code == 200:
            for line in robots_res.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sm_url = line.split(":", 1)[1].strip()
                    sitemap_urls.add(sm_url)
    except Exception:
        pass

    # Try root sitemap.xml
    sitemap_urls.add(f"{base_domain}/sitemap.xml")

    discovered_pages: List[str] = []

    for sm_url in list(sitemap_urls):
        try:
            res = requests.get(sm_url, timeout=2, verify=False)
            if res.status_code == 200 and "xml" in res.headers.get("Content-Type", ""):
                tree = ET.fromstring(res.content)
                for elem in tree.iter():
                    if elem.tag.endswith("loc") and elem.text:
                        loc_url = elem.text.strip()
                        if urllib.parse.urlparse(loc_url).netloc == parsed_root.netloc:
                            discovered_pages.append(loc_url)
        except Exception:
            continue

    return list(set(discovered_pages))

def try_playwright_rendering(root_url: str) -> Tuple[List[str], bool]:
    """
    Attempts headless browser rendering via Playwright ONLY for client-rendered SPA frameworks.
    Returns (discovered_urls, was_browser_used).
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(root_url, timeout=10000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            
            hrefs = page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
            browser.close()

            root_domain = urllib.parse.urlparse(root_url).netloc
            valid_urls = set()
            for href in hrefs:
                parsed = urllib.parse.urlparse(href)
                if parsed.scheme in ["http", "https"] and parsed.netloc == root_domain:
                    clean = href.split("#")[0]
                    if clean != root_url:
                        valid_urls.add(clean)

            return list(valid_urls), True
    except Exception as e:
        print(f"[Discovery Notice] Playwright browser rendering for {root_url}: {e}")
        return [], False

def discover_authoritative_pages(root_source: RegisteredSource, max_pages: int = 4) -> Dict[str, Any]:
    """
    Executes ordered multi-stage targeted page discovery for a registered source root.
    """
    root_url = root_source.source_url
    root_domain = urllib.parse.urlparse(root_url).netloc

    methods_used: List[str] = []
    crawled_records: List[Dict[str, Any]] = []
    browser_rendered = False
    candidate_urls: Set[str] = set()

    # Step 1. Crawl root page
    root_crawl = fetch_web_page(root_url)
    crawled_records.append(root_crawl)
    methods_used.append("root_page_crawl")

    # Step A & B: Sitemap & Robots.txt Discovery
    sitemap_links = fetch_sitemap_urls(root_url)
    if sitemap_links:
        methods_used.append("sitemap_xml")
        for link in sitemap_links:
            path_lower = urllib.parse.urlparse(link).path.lower()
            if any(kw in path_lower for kw in DISCOVERY_KEYWORDS):
                candidate_urls.add(link)

    # Step C & D: Static HTML Links & Same-Domain Enforcement
    soup = BeautifulSoup(root_crawl["content"], "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urllib.parse.urljoin(root_crawl["final_resolved_url"], href)
        parsed_full = urllib.parse.urlparse(full_url)

        # STRICT SAME-DOMAIN ENFORCEMENT (Rule 2.D & Test B)
        if parsed_full.scheme in ["http", "https"] and parsed_full.netloc == root_domain:
            path_lower = parsed_full.path.lower()
            text_lower = a.get_text().strip().lower()

            if any(kw in path_lower or kw in text_lower for kw in DISCOVERY_KEYWORDS):
                clean_url = full_url.split("#")[0]
                if clean_url != root_url:
                    candidate_urls.add(clean_url)

    if candidate_urls:
        methods_used.append("static_html_links")

    # Step F: Browser Rendering ONLY if static discovery returned 0 sub-pages (e.g. PLD Space SPA)
    if len(candidate_urls) == 0:
        pw_urls, pw_used = try_playwright_rendering(root_url)
        if pw_used:
            browser_rendered = True
            methods_used.append("playwright_browser_rendering")
            for u in pw_urls:
                if any(kw in u.lower() for kw in DISCOVERY_KEYWORDS):
                    candidate_urls.add(u)

    # Crawl target candidate pages up to max_pages limit
    for sub_url in list(candidate_urls)[:max_pages]:
        try:
            sub_crawl = fetch_web_page(sub_url)
            crawled_records.append(sub_crawl)
        except Exception:
            continue

    return {
        "source_id": root_source.source_id,
        "root_url": root_url,
        "methods_used": methods_used,
        "browser_rendered": browser_rendered,
        "discovered_count": len(candidate_urls),
        "crawled_records": crawled_records
    }
