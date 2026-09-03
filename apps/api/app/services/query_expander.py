"""
QUERY EXPANSION ENGINE & TECHNICAL TERMINOLOGY REGISTRY (STAGE 4.6)
---------------------------------------------------------------------
Provides deterministic, ontology-backed query expansion for multi-query retrieval.
Expands search formulations ONLY to improve candidate recall (Recall@1), without
altering proposition semantics or semantic verifier truth rules.
"""

import re
from typing import List, Dict, Set, Optional

# Technical Terminology Registry
TECHNICAL_VOCABULARY_REGISTRY: Dict[str, Dict[str, List[str]]] = {
    "REUSABLE_LAUNCH_VEHICLE": {
        "positive": [
            "reusable launcher", "reusable launch system", "recoverable launcher",
            "recoverable first stage", "first stage recovery", "propulsive recovery", "reusability"
        ],
        "negative": ["expendable", "non-reusable", "one-time use"]
    },
    "DEVELOPMENT": {
        "positive": [
            "developing", "development program", "R&D", "research and development",
            "designing", "under development", "manufacturing"
        ],
        "negative": ["cancelled", "abandoned", "retired"]
    },
    "PROPULSION": {
        "positive": [
            "staged combustion engine", "Helix engine", "Colibri engine",
            "bio-propane engine", "liquid oxygen engine", "rocket propulsion"
        ],
        "negative": []
    },
    "LAUNCH_SITE": {
        "positive": [
            "Andøya Spaceport", "SaxaVord Spaceport", "Sutherland Spaceport",
            "El Arenosillo", "Kourou launch pad"
        ],
        "negative": []
    }
}

ENTITY_ALIAS_MAP: Dict[str, List[str]] = {
    "pld": ["PLD Space", "MIURA 5", "MIURA 1"],
    "isar": ["Isar Aerospace", "Spectrum"],
    "rfa": ["Rocket Factory Augsburg", "RFA ONE", "RFA"],
    "orbex": ["Orbex", "Orbex Prime"],
    "maia": ["MaiaSpace", "Colibri"]
}

def expand_search_terms(concept_key: str) -> List[str]:
    """Returns positive expanded terms for a concept key."""
    concept = TECHNICAL_VOCABULARY_REGISTRY.get(concept_key, {})
    return concept.get("positive", [])

def generate_expanded_queries(query_text: str, entity_id: Optional[str] = None) -> List[str]:
    """
    Generates 3 to 4 deterministic multi-query formulations combining canonical entity
    aliases, domain terms, and program identifiers to improve retrieval Recall@1.
    """
    q_lower = query_text.lower()
    expanded_queries: List[str] = [query_text]

    # Detect entity if not explicitly provided
    target_entity = entity_id
    if not target_entity:
        for eid, aliases in ENTITY_ALIAS_MAP.items():
            if any(alias.lower() in q_lower for alias in aliases):
                target_entity = eid
                break

    if target_entity and target_entity in ENTITY_ALIAS_MAP:
        aliases = ENTITY_ALIAS_MAP[target_entity]
        canonical_name = aliases[0]

        # Concept-specific expansions
        if "reusable" in q_lower or "recovery" in q_lower or "reusability" in q_lower:
            expanded_queries.append(f"{canonical_name} reusable launch vehicle development")
            expanded_queries.append(f"{canonical_name} first stage recovery reusability")
            if len(aliases) > 1:
                expanded_queries.append(f"{aliases[1]} reusable launcher recovery")
        elif "engine" in q_lower or "propulsion" in q_lower:
            expanded_queries.append(f"{canonical_name} rocket engine propulsion tech")
            expanded_queries.append(f"{canonical_name} staged combustion engine testing")
        elif "site" in q_lower or "spaceport" in q_lower or "pad" in q_lower:
            expanded_queries.append(f"{canonical_name} launch site spaceport qualification")
        else:
            expanded_queries.append(f"{canonical_name} orbital launch vehicle development")
            if len(aliases) > 1:
                expanded_queries.append(f"{aliases[1]} orbital rocket stage")

    # Fallback multi-term expansion
    if len(expanded_queries) == 1:
        if "reusable" in q_lower:
            expanded_queries.append("European reusable launch vehicle development program")
            expanded_queries.append("recoverable first stage rocket launcher")

    # Deduplicate while preserving order
    unique_queries = []
    for q in expanded_queries:
        if q not in unique_queries:
            unique_queries.append(q)

    return unique_queries[:4]
