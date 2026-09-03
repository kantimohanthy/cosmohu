import sys
import os
import requests
import urllib.parse
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath("apps/api"))
from app.services.crawler import fetch_web_page, determine_source_tier

target_roots = [
    ("esa", "https://www.esa.int/Enabling_Support/Space_Transportation"),
    ("isar", "https://isaraerospace.com"),
    ("pld", "https://www.pldspace.com"),
    ("rfa", "https://www.rfa.space"),
    ("euroflight", "https://europeanspaceflight.com")
]

keywords = ["vehicle", "spectrum", "miura", "rfa", "one", "maia", "reusab", "recover", "propulsion", "press", "news", "technology", "launch", "about"]

print("TESTING AUTHORITATIVE DOMAIN PAGE DISCOVERY:")
print("="*80)

for entity_id, root_url in target_roots:
    print(f"\n--- Root: {root_url} ({entity_id}) ---")
    try:
        crawled = fetch_web_page(root_url, timeout=10)
        soup = BeautifulSoup(requests.get(crawled["final_resolved_url"], headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=10).text, "html.parser")
        
        discovered_urls = set()
        root_domain = urllib.parse.urlparse(crawled["final_resolved_url"]).netloc
        
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urllib.parse.urljoin(crawled["final_resolved_url"], href)
            parsed_full = urllib.parse.urlparse(full_url)
            
            if parsed_full.scheme in ["http", "https"] and parsed_full.netloc == root_domain:
                path_lower = parsed_full.path.lower()
                link_text = a.get_text().strip().lower()
                
                if any(kw in path_lower or kw in link_text for kw in keywords):
                    if full_url != root_url and not full_url.endswith("#"):
                        discovered_urls.add(full_url)
                        
        print(f"Discovered {len(discovered_urls)} relevant sub-pages:")
        for url in list(discovered_urls)[:6]:
            print(f"  * {url}")
            
    except Exception as e:
        print(f"Error discovering links for {root_url}: {e}")
