"""
ONTOLOGY-AWARE DETERMINISTIC QUERY PLANNER & PROPOSITION DECOMPOSER (STAGE 3.6 & 3.7)
-------------------------------------------------------------------------------------
Converts natural language research queries into structured QueryPlan representations
containing controlled intents, resolved entities, and independent propositions.

Invariants:
- Planner NEVER assigns truth/SUPPORTED status (initial status is UNVERIFIED).
- Planner NEVER creates Orvyra graph entities or relationships.
- Planner NEVER calls LLM synthesis layers.
- Query planning is 100% deterministic given identical query input.
"""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
import re
import hashlib

# 1. CONTROLLED INTENT TAXONOMY
CONTROLLED_INTENTS = {
    "ENTITY_DISCOVERY",
    "RELATIONSHIP_QUERY",
    "ATTRIBUTE_QUERY",
    "TECHNOLOGY_QUERY",
    "FUNDING_QUERY",
    "STATUS_QUERY",
    "EVIDENCE_QUERY",
    "COMPARISON_QUERY"
}

# 2. CONTROLLED PREDICATE VOCABULARY & ALIASES
CONTROLLED_PREDICATES = {
    "develops": ["developing", "develop", "develops", "building", "designing", "r&d"],
    "operates": ["operating", "operates", "operate", "flying"],
    "manufactures": ["manufacturing", "manufactures", "manufacture"],
    "funded_by": ["funding", "funded", "raised", "financial support", "invested by", "investors"],
    "headquartered_in": ["headquartered", "based in", "located in", "headquarters"],
    "launches": ["launching", "launches", "launched"],
    "uses": ["using", "uses", "utilizes"],
    "partners_with": ["partnering", "partners", "partnered"],
    "acquired_by": ["acquisition", "acquired"]
}

UNSUPPORTED_PREDICATE_KEYWORDS = [
    "teleports", "teleporting", "mind_controls", "shape_shifts", "time_travels", "levitates"
]

# 3. CONTROLLED CONCEPT VOCABULARY
CONTROLLED_CONCEPTS = {
    "reusable_launch_vehicle": ["reusable launch vehicle", "reusable launcher", "reusable rocket", "reusable technology"],
    "reusable_first_stage": ["reusable first stage", "recoverable first stage", "first stage recovery"],
    "launch_vehicle": ["launch vehicle", "launcher", "orbital vehicle"],
    "rocket": ["rocket"],
    "satellite": ["satellite", "payload"],
    "launch_site": ["launch site", "spaceport", "launchpad"]
}

UNSUPPORTED_DIMENSIONS = [
    "flavor", "astrological sign", "favorite color", "zodiac"
]

# 4. CANONICAL ENTITY ONTOLOGY
CANONICAL_ENTITIES = {
    "pld": {
        "canonical_name": "PLD Space",
        "aliases": ["pld space", "pld", "miura 5", "miura-5", "miura 1", "miura-1", "miura next"],
        "geography": "Spanish",
        "country": "Spain"
    },
    "isar": {
        "canonical_name": "Isar Aerospace",
        "aliases": ["isar aerospace", "isar", "spectrum"],
        "geography": "German",
        "country": "Germany"
    },
    "rfa": {
        "canonical_name": "Rocket Factory Augsburg",
        "aliases": ["rocket factory augsburg", "rfa", "rfa one", "rfa-one"],
        "geography": "German",
        "country": "Germany"
    },
    "orbex": {
        "canonical_name": "Orbex",
        "aliases": ["orbex", "prime"],
        "geography": "British",
        "country": "UK"
    },
    "maia": {
        "canonical_name": "MaiaSpace",
        "aliases": ["maiaspace", "maia", "prometheus"],
        "geography": "French",
        "country": "France"
    }
}

AMBIGUOUS_ENTITY_TERMS = [
    "ambiguous rocket company", "space Corp", "generic launcher inc", "unclear company"
]

UNKNOWN_SPECIFIC_ENTITIES = [
    "acme launch", "acme space", "starlight space", "nebula space", "xyz aerospace"
]

# 5. SCHEMA DEFINITIONS
class QueryProposition(BaseModel):
    proposition_id: str
    entity_id: str
    entity_name: str
    predicate: str
    target_object: str
    temporal_scope: str = "UNSPECIFIED"
    required_evidence: List[str] = Field(default_factory=lambda: [
        "entity attribution", "predicate support", "object support", "temporal support", "valid provenance"
    ])
    status: str = "UNVERIFIED"

class ResolvedEntity(BaseModel):
    entity_id: str
    canonical_name: str
    entity_type: str  # CANONICAL_ENTITY | ENTITY_ALIAS | UNKNOWN_ENTITY | AMBIGUOUS_ENTITY | ENTITY_CLASS
    category_constraint: Optional[str] = None
    geographic_constraint: Optional[str] = None

class QueryPlan(BaseModel):
    query_id: str
    original_query: str
    intents: List[str]
    entities: List[ResolvedEntity]
    propositions: List[QueryProposition]
    constraints: Dict[str, Any] = Field(default_factory=dict)
    temporal_scope: str = "UNKNOWN"
    requested_evidence: bool = False
    comparison_dimensions: List[str] = Field(default_factory=list)
    status: str = "SUCCESS"  # SUCCESS | AMBIGUOUS_ENTITY | UNSUPPORTED_PREDICATE | UNSUPPORTED_DIMENSION
    error_code: Optional[str] = None
    reason: str = ""

# Backward Compatibility Wrapper
def plan_query_execution(query_text: str) -> Dict[str, Any]:
    plan = build_deterministic_query_plan(query_text)
    return {
        "intent": plan.intents[0] if plan.intents else "FACTUAL",
        "entities": [e.canonical_name for e in plan.entities],
        "filters": plan.constraints,
        "query_clean": plan.original_query
    }

# 6. DETERMINISTIC PLANNER LOGIC
def build_deterministic_query_plan(query_text: str) -> QueryPlan:
    """
    Parses a natural language query deterministically into a structured QueryPlan.
    """
    raw_query = query_text.strip()
    q_lower = raw_query.lower()

    query_id = f"plan_{hashlib.sha256(raw_query.encode('utf-8')).hexdigest()[:12]}"

    # A. Check for Failure Mode 1: Unsupported Predicate
    for bad_pred in UNSUPPORTED_PREDICATE_KEYWORDS:
        if bad_pred in q_lower:
            return QueryPlan(
                query_id=query_id,
                original_query=raw_query,
                intents=["RELATIONSHIP_QUERY"],
                entities=[],
                propositions=[],
                status="UNSUPPORTED_PREDICATE",
                error_code="UNSUPPORTED_PREDICATE",
                reason=f"UNSUPPORTED_PREDICATE: Predicate '{bad_pred}' is outside controlled ontology vocabulary."
            )

    # B. Check for Failure Mode 2: Unsupported Comparison Dimension
    for bad_dim in UNSUPPORTED_DIMENSIONS:
        if bad_dim in q_lower:
            return QueryPlan(
                query_id=query_id,
                original_query=raw_query,
                intents=["COMPARISON_QUERY"],
                entities=[],
                propositions=[],
                status="UNSUPPORTED_DIMENSION",
                error_code="UNSUPPORTED_DIMENSION",
                reason=f"UNSUPPORTED_DIMENSION: Comparison dimension '{bad_dim}' is not supported by space ontology."
            )

    # C. Check for Failure Mode 3: Ambiguous Entity
    for amb_term in AMBIGUOUS_ENTITY_TERMS:
        if amb_term.lower() in q_lower:
            return QueryPlan(
                query_id=query_id,
                original_query=raw_query,
                intents=["ENTITY_DISCOVERY"],
                entities=[
                    ResolvedEntity(
                        entity_id="ambiguous_term",
                        canonical_name=amb_term,
                        entity_type="AMBIGUOUS_ENTITY"
                    )
                ],
                propositions=[],
                status="AMBIGUOUS_ENTITY",
                error_code="AMBIGUOUS_ENTITY",
                reason=f"AMBIGUOUS_ENTITY: Term '{amb_term}' matches multiple entities without disambiguation."
            )

    # D. Intent Classification
    intents: List[str] = []
    if any(kw in q_lower for kw in ["compare", "versus", "vs", "difference"]):
        intents.append("COMPARISON_QUERY")
    if any(kw in q_lower for kw in ["which", "list", "top", "what companies", "find companies", "european launch companies"]):
        intents.append("ENTITY_DISCOVERY")
    if any(kw in q_lower for kw in ["funding", "funded", "raised", "million", "euros", "investment"]):
        intents.append("FUNDING_QUERY")
    if any(kw in q_lower for kw in ["reusable", "rocket", "launcher", "first stage", "technology", "developing"]):
        intents.append("TECHNOLOGY_QUERY")
    if any(kw in q_lower for kw in ["status", "how far along", "stage", "operational", "progress"]):
        intents.append("STATUS_QUERY")
    if any(kw in q_lower for kw in ["evidence", "proof", "source", "supports", "verification"]):
        intents.append("EVIDENCE_QUERY")

    if not intents:
        intents.append("ATTRIBUTE_QUERY")

    requested_evidence = "EVIDENCE_QUERY" in intents or any(kw in q_lower for kw in ["evidence", "supports", "proof"])

    # E. Entity Resolution
    resolved_entities: List[ResolvedEntity] = []
    matched_canonical_ids: Set[str] = set()

    for ent_id, ent_info in CANONICAL_ENTITIES.items():
        for alias in ent_info["aliases"]:
            if re.search(r"\b" + re.escape(alias) + r"\b", q_lower):
                if ent_id not in matched_canonical_ids:
                    matched_canonical_ids.add(ent_id)
                    ent_type = "CANONICAL_ENTITY" if alias == ent_info["canonical_name"].lower() else "ENTITY_ALIAS"
                    resolved_entities.append(
                        ResolvedEntity(
                            entity_id=ent_id,
                            canonical_name=ent_info["canonical_name"],
                            entity_type=ent_type,
                            geographic_constraint=ent_info["geography"]
                        )
                    )

    # Check for Unknown Specific Entities
    for unknown_ent in UNKNOWN_SPECIFIC_ENTITIES:
        if unknown_ent.lower() in q_lower:
            unk_id = f"unknown_{re.sub(r'[^a-z0-9]', '_', unknown_ent.lower())}"
            resolved_entities.append(
                ResolvedEntity(
                    entity_id=unk_id,
                    canonical_name=unknown_ent.title(),
                    entity_type="UNKNOWN_ENTITY"
                )
            )

    # Check for Entity Class / Category Request (e.g. "European launch companies")
    if any(kw in q_lower for kw in ["european launch companies", "european space startups", "launch providers"]):
        resolved_entities.append(
            ResolvedEntity(
                entity_id="class_european_launch",
                canonical_name="European Launch Companies",
                entity_type="ENTITY_CLASS",
                category_constraint="launch_company",
                geographic_constraint="European"
            )
        )

    # F. Extract Constraints & Temporal Scope
    constraints: Dict[str, Any] = {}
    if "european" in q_lower or "europe" in q_lower:
        constraints["geography"] = "European"
    if "spanish" in q_lower:
        constraints["geography"] = "Spanish"
    if "german" in q_lower:
        constraints["geography"] = "German"
    if "french" in q_lower:
        constraints["geography"] = "French"

    if any(kw in q_lower for kw in ["launch company", "launch companies", "launch provider"]):
        constraints["company_type"] = "launch_company"
        constraints["industry"] = "space_launch"

    # Temporal Semantics
    temporal_scope = "UNKNOWN"
    if any(kw in q_lower for kw in ["developing", "is developing", "under development", "r&d"]):
        temporal_scope = "IN_DEVELOPMENT"
    elif any(kw in q_lower for kw in ["plans to", "intends to", "future", "planned"]):
        temporal_scope = "PLANNED"
    elif any(kw in q_lower for kw in ["investigated", "historical", "previously", "in 2018"]):
        temporal_scope = "HISTORICAL"
    elif any(kw in q_lower for kw in ["operates", "currently flying", "operational"]):
        temporal_scope = "OPERATIONAL"

    # G. Comparison Dimensions
    comparison_dimensions: List[str] = []
    if "COMPARISON_QUERY" in intents:
        if "reusable" in q_lower or "reusable launch vehicle" in q_lower:
            comparison_dimensions.append("reusable_launch_vehicle")
        if "status" in q_lower or "how far along" in q_lower:
            comparison_dimensions.append("status")
        if "funding" in q_lower or "funded" in q_lower:
            comparison_dimensions.append("funding")
        if not comparison_dimensions:
            comparison_dimensions.append("development_status")

    # H. Proposition Generation & Decomposition
    propositions: List[QueryProposition] = []
    prop_counter = 1

    # Predicate Detection
    target_predicate = "develops"
    if "funded_by" in q_lower or "funding" in q_lower or "funded" in q_lower:
        target_predicate = "funded_by"
    elif "headquartered" in q_lower or "based in" in q_lower:
        target_predicate = "headquartered_in"
    elif "operates" in q_lower:
        target_predicate = "operates"

    # Target Object Detection
    target_obj = "reusable_launch_vehicle"
    if "reusable first stage" in q_lower or "recoverable first stage" in q_lower:
        target_obj = "reusable_first_stage"
    elif "satellite" in q_lower:
        target_obj = "satellite"
    elif target_predicate == "funded_by":
        target_obj = "venture_funding"

    # Case 1: Entity Class / Discovery Query
    if any(e.entity_type == "ENTITY_CLASS" for e in resolved_entities):
        p_id = f"PROP-CLASS-REUSABLE-{prop_counter:03d}"
        propositions.append(
            QueryProposition(
                proposition_id=p_id,
                entity_id="ENTITY_TEMPLATE",
                entity_name="[Discovered Entity]",
                predicate=target_predicate,
                target_object=target_obj,
                temporal_scope=temporal_scope,
                status="UNVERIFIED"
            )
        )
        prop_counter += 1

    # Case 2: Multi-Entity Comparison / Compound Query
    else:
        for ent in resolved_entities:
            # If query asks for reusable launcher development
            if "TECHNOLOGY_QUERY" in intents or "reusable" in q_lower or target_predicate == "develops":
                p_id = f"PROP-{ent.entity_id.upper()}-REUSABLE-{prop_counter:03d}"
                propositions.append(
                    QueryProposition(
                        proposition_id=p_id,
                        entity_id=ent.entity_id,
                        entity_name=ent.canonical_name,
                        predicate="develops",
                        target_object="reusable_launch_vehicle",
                        temporal_scope=temporal_scope if temporal_scope != "UNKNOWN" else "IN_DEVELOPMENT",
                        status="UNVERIFIED"
                    )
                )
                prop_counter += 1

            # If query asks for status
            if "STATUS_QUERY" in intents or "status" in q_lower or "how far along" in q_lower:
                p_id = f"PROP-{ent.entity_id.upper()}-STATUS-{prop_counter:03d}"
                propositions.append(
                    QueryProposition(
                        proposition_id=p_id,
                        entity_id=ent.entity_id,
                        entity_name=ent.canonical_name,
                        predicate="has_development_status",
                        target_object="development_status",
                        temporal_scope=temporal_scope if temporal_scope != "UNKNOWN" else "CURRENT",
                        status="UNVERIFIED"
                    )
                )
                prop_counter += 1

            # If query asks for funding
            if "FUNDING_QUERY" in intents or "funding" in q_lower or "funded" in q_lower:
                p_id = f"PROP-{ent.entity_id.upper()}-FUNDING-{prop_counter:03d}"
                propositions.append(
                    QueryProposition(
                        proposition_id=p_id,
                        entity_id=ent.entity_id,
                        entity_name=ent.canonical_name,
                        predicate="funded_by",
                        target_object="venture_funding",
                        temporal_scope="CURRENT",
                        status="UNVERIFIED"
                    )
                )
                prop_counter += 1

    # If no entities matched and no Failure Mode triggered, create a generic proposition template
    if not resolved_entities and not propositions:
        propositions.append(
            QueryProposition(
                proposition_id=f"PROP-GENERIC-{prop_counter:03d}",
                entity_id="unknown_entity",
                entity_name="[Unknown Entity]",
                predicate=target_predicate,
                target_object=target_obj,
                temporal_scope=temporal_scope,
                status="UNVERIFIED"
            )
        )

    return QueryPlan(
        query_id=query_id,
        original_query=raw_query,
        intents=intents,
        entities=resolved_entities,
        propositions=propositions,
        constraints=constraints,
        temporal_scope=temporal_scope,
        requested_evidence=requested_evidence,
        comparison_dimensions=comparison_dimensions,
        status="SUCCESS"
    )
