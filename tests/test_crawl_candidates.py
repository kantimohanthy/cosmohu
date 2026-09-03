import sys
import os
sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.crawler import fetch_web_page, determine_source_tier

candidate_urls = [
    ("src_esa_transport", "ESA Space Transportation Portal", "https://www.esa.int/Enabling_Support/Space_Transportation"),
    ("src_esa_spaceports", "ESA Europe's Spaceports", "https://www.esa.int/Enabling_Support/Space_Transportation/Europe_s_spaceports"),
    ("src_pld_space", "PLD Space Official", "https://www.pldspace.com"),
    ("src_isar_space", "Isar Aerospace Official", "https://www.isaraerospace.com"),
    ("src_rfa_space", "Rocket Factory Augsburg Official", "https://www.rfa.space"),
    ("src_orbex_space", "Orbex Official", "https://orbex.space"),
    ("src_maiaspace_official", "MaiaSpace Official", "https://www.maiaspace.com"),
    ("src_euro_spaceflight", "European Spaceflight News", "https://europeanspaceflight.com")
]

print("TESTING LIVE CRAWL OF CANDIDATE AUTHORITATIVE SOURCES:")
print("="*80)

for s_id, name, url in candidate_urls:
    try:
        res = fetch_web_page(url, timeout=10)
        tier = determine_source_tier(res["final_resolved_url"], res["publisher"])
        print(f"[SUCCESS] {s_id} | Status: {res['status_code']} | Tier: {tier}")
        print(f"   Requested: {res['requested_url']}")
        print(f"   Resolved:  {res['final_resolved_url']} (Redirected: {res['was_redirected']}, Mismatch: {res['identity_mismatch']})")
        print(f"   Title: '{res['title'][:80]}...' | Length: {len(res['content'])} chars\n")
    except Exception as e:
        print(f"[FAILED] {s_id} | URL: {url} | Error: {e}\n")
