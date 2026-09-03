"""
EVIDENCE GRAPH ENGINE & PROVENANCE GRAPH SERVICE (STAGE 4.8)
------------------------------------------------------------
Constructs a queryable Node-and-Edge evidence graph connecting Entities, Propositions, Claims,
Evidence passages, Chunks, Documents, Sources, Technologies, and Temporal States.

Invariants:
- NO UNSUPPORTED GRAPH EDGES MAY BE CREATED
- NO ENTAILMENT -> NO CLAIM -> NO GRAPH EDGE
- LLM -> ZERO GRAPH MUTATION
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class NodeType(str, Enum):
    ENTITY = "ENTITY"
    PROPOSITION = "PROPOSITION"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    CHUNK = "CHUNK"
    DOCUMENT = "DOCUMENT"
    SOURCE = "SOURCE"
    EVENT = "EVENT"
    TECHNOLOGY = "TECHNOLOGY"
    TEMPORAL_STATE = "TEMPORAL_STATE"

class EdgeType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CORROBORATES = "CORROBORATES"
    DERIVED_FROM = "DERIVED_FROM"
    MENTIONS = "MENTIONS"
    ABOUT = "ABOUT"
    OCCURRED_AT = "OCCURRED_AT"
    SUPERSEDES = "SUPERSEDES"
    REFINES = "REFINES"
    INVALIDATES = "INVALIDATES"

class GraphNode(BaseModel):
    id: str
    type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    type: EdgeType
    properties: Dict[str, Any] = Field(default_factory=dict)

class EvidenceGraph(BaseModel):
    proposition_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

def build_claim_evidence_graph(
    proposition_id: str,
    entity_id: str,
    entity_name: str,
    predicate: str,
    target_object: str,
    verification_result: Dict[str, Any],
    evidence_items: List[Dict[str, Any]]
) -> EvidenceGraph:
    """
    Constructs an immutable provenance graph for a verified proposition.
    """
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    node_ids = set()

    # 1. Entity Node
    ent_node_id = f"node_ent_{entity_id}"
    nodes.append(GraphNode(id=ent_node_id, type=NodeType.ENTITY, label=entity_name, properties={"entity_id": entity_id}))
    node_ids.add(ent_node_id)

    # 2. Proposition Node
    prop_node_id = f"node_prop_{proposition_id}"
    nodes.append(GraphNode(id=prop_node_id, type=NodeType.PROPOSITION, label=f"{entity_name} {predicate} {target_object}", properties={"proposition_id": proposition_id, "predicate": predicate, "object": target_object}))
    node_ids.add(prop_node_id)
    edges.append(GraphEdge(source=prop_node_id, target=ent_node_id, type=EdgeType.ABOUT))

    # 3. Evidence & Document Nodes
    status = verification_result.get("verification_status", "INSUFFICIENT_EVIDENCE")
    
    if status in ["SUPPORTED", "CORROBORATED"]:
        claim_node_id = f"node_claim_{proposition_id}"
        nodes.append(GraphNode(id=claim_node_id, type=NodeType.CLAIM, label=f"Verified Claim ({status})", properties={"status": status}))
        node_ids.add(claim_node_id)
        edges.append(GraphEdge(source=claim_node_id, target=prop_node_id, type=EdgeType.SUPPORTS))

        for idx, ev in enumerate(evidence_items, 1):
            ev_id = ev.get("evidence_id") or f"ev_{idx}"
            ev_node_id = f"node_ev_{ev_id}"
            nodes.append(GraphNode(id=ev_node_id, type=NodeType.EVIDENCE, label=f"Evidence {ev_id[:8]}", properties={"text": ev.get("evidence_text") or ev.get("text"), "source_url": ev.get("source_url")}))
            node_ids.add(ev_node_id)
            edges.append(GraphEdge(source=ev_node_id, target=claim_node_id, type=EdgeType.SUPPORTS))

            # Corroboration Edge between evidence items
            if idx > 1:
                prev_ev_node_id = f"node_ev_{evidence_items[0].get('evidence_id') or 'ev_1'}"
                edges.append(GraphEdge(source=ev_node_id, target=prev_ev_node_id, type=EdgeType.CORROBORATES))

            doc_id = ev.get("document_id")
            if doc_id:
                doc_node_id = f"node_doc_{doc_id}"
                if doc_node_id not in node_ids:
                    nodes.append(GraphNode(id=doc_node_id, type=NodeType.DOCUMENT, label=f"Document {doc_id[:12]}", properties={"document_id": doc_id, "publisher": ev.get("publisher"), "source_url": ev.get("source_url")}))
                    node_ids.add(doc_node_id)
                edges.append(GraphEdge(source=ev_node_id, target=doc_node_id, type=EdgeType.DERIVED_FROM))

    return EvidenceGraph(proposition_id=proposition_id, nodes=nodes, edges=edges)
