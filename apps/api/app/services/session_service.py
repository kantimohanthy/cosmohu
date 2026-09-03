import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from app.services.grounded_synthesizer import GroundedSynthesizer
from app.services.research_pipeline import execute_research_pipeline
from app.services.answer_assembler import assemble_evidence_answer
from app.services.store import store

class SessionService:
    @staticmethod
    def create_session(title: Optional[str] = None) -> Dict[str, Any]:
        session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        now = datetime.utcnow().isoformat()
        session_title = title.strip() if (title and title.strip()) else "New Space Intelligence Investigation"

        session_data = {
            "session_id": session_id,
            "title": session_title,
            "created_at": now,
            "updated_at": now,
            "queries": [],
            "entities": [],
            "propositions": [],
            "supported_claims": [],
            "insufficient_propositions": [],
            "contradictions": [],
            "conflicts": [],
            "evidence_references": [],
            "source_references": [],
            "withheld_items": [],
            "metadata": {
                "total_queries": 0,
                "total_entities": 0,
                "total_propositions": 0,
                "supported_count": 0,
                "insufficient_count": 0,
                "conflict_count": 0,
                "evidence_count": 0,
                "source_count": 0,
                "evidence_density": 0.0,
                "corroboration_count": 0,
                "tier1_source_count": 0
            }
        }
        store.save_research_session(session_id, session_title, now, now, session_data)
        return session_data

    @staticmethod
    def list_sessions() -> List[Dict[str, Any]]:
        return store.list_research_sessions()

    @staticmethod
    def get_session(session_id: str) -> Dict[str, Any]:
        session_data = store.get_research_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"RESEARCH_SESSION_NOT_FOUND: {session_id}")
        return session_data

    @staticmethod
    def delete_session(session_id: str) -> bool:
        deleted = store.delete_research_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"RESEARCH_SESSION_NOT_FOUND: {session_id}")
        return True

    @staticmethod
    def add_query_to_session(session_id: str, query_text: str) -> Dict[str, Any]:
        session = SessionService.get_session(session_id)
        now = datetime.utcnow().isoformat()

        # Execute end-to-end pipeline
        e2e_res = GroundedSynthesizer.execute_end_to_end_grounded_research(query_text)
        structured_ans = e2e_res.final_grounded_answer.structured_answer

        query_item = {
            "query_id": f"q_{len(session['queries']) + 1}",
            "query_text": query_text,
            "executed_at": now,
            "run_id": e2e_res.run_id,
            "answer": e2e_res.final_grounded_answer.answer_text,
            "status": "COMPLETED"
        }
        session["queries"].append(query_item)

        if session["title"] == "New Space Intelligence Investigation" and len(query_text) > 2:
            session["title"] = query_text[:60]

        # Extract & accumulate artifacts
        if structured_ans:
            for p in structured_ans.propositions:
                # Deduplicate proposition by proposition_id
                if not any(existing["proposition_id"] == p.proposition_id for existing in session["propositions"]):
                    ev_ids = [ev.evidence_id for ev in p.evidence]
                    prop_dict = {
                        "proposition_id": p.proposition_id,
                        "entity_id": p.entity_id,
                        "entity_name": p.entity_name,
                        "predicate": p.predicate,
                        "object": p.target_object,
                        "status": p.status,
                        "temporal_scope": p.temporal_scope,
                        "evidence_strength": p.evidence_strength,
                        "evidence_ids": ev_ids,
                        "claim_id": f"clm_{p.entity_id}_{p.target_object}" if p.status == "SUPPORTED" else None,
                        "relationship_id": f"rel_{p.entity_id}_{p.target_object}" if p.status == "SUPPORTED" else None
                    }
                    session["propositions"].append(prop_dict)

                    # Discover entity
                    ent_obj = {"entity_id": p.entity_id, "entity_name": p.entity_name}
                    if not any(e["entity_id"] == p.entity_id for e in session["entities"]):
                        session["entities"].append(ent_obj)

                    # Categorize claims and insufficiency
                    if p.status == "SUPPORTED":
                        clm_obj = {
                            "claim_id": f"clm_{p.entity_id}_{p.target_object}",
                            "text": f"{p.entity_name} {p.predicate} {p.target_object.replace('_', ' ')}",
                            "entity_id": p.entity_id,
                            "entity_name": p.entity_name,
                            "evidence_ids": ev_ids,
                            "verification_status": "SUPPORTED"
                        }
                        if not any(c["claim_id"] == clm_obj["claim_id"] for c in session["supported_claims"]):
                            session["supported_claims"].append(clm_obj)

                        # Save evidence objects
                        for ev in p.evidence:
                            ev_ref = {
                                "evidence_id": ev.evidence_id,
                                "proposition_id": p.proposition_id,
                                "document_id": ev.document_id,
                                "chunk_id": ev.chunk_id,
                                "source_url": ev.source_url,
                                "publisher": ev.publisher,
                                "source_tier": ev.source_tier,
                                "exact_passage": getattr(ev, 'exact_passage', getattr(ev, 'exact_text', '')),
                                "provenance_status": "VERIFIED",
                                "content_hash": ev.content_hash,
                                "run_id": e2e_res.run_id
                            }
                            if not any(e["evidence_id"] == ev.evidence_id for e in session["evidence_references"]):
                                session["evidence_references"].append(ev_ref)

                            # Save source object
                            src_ref = {
                                "source_id": f"src_{ev.document_id}",
                                "publisher": ev.publisher,
                                "source_url": ev.source_url,
                                "source_tier": ev.source_tier
                            }
                            if not any(s["source_url"] == ev.source_url for s in session["source_references"]):
                                session["source_references"].append(src_ref)

                    elif p.status == "INSUFFICIENT_EVIDENCE":
                        insuff_obj = {
                            "proposition_id": p.proposition_id,
                            "entity_id": p.entity_id,
                            "entity_name": p.entity_name,
                            "reason": f"INSUFFICIENT_EVIDENCE: No verified evidence found for {p.entity_name}."
                        }
                        if not any(i["proposition_id"] == p.proposition_id for i in session["insufficient_propositions"]):
                            session["insufficient_propositions"].append(insuff_obj)

                    elif p.status in ("CONTRADICTED", "CONFLICT"):
                        conf_obj = {
                            "proposition_id": p.proposition_id,
                            "entity_id": p.entity_id,
                            "entity_name": p.entity_name,
                            "reason": f"CONFLICT: Opposing or contradictory evidence identified for {p.entity_name}."
                        }
                        if not any(c["proposition_id"] == p.proposition_id for c in session["conflicts"]):
                            session["conflicts"].append(conf_obj)

            # Record withheld disclosures
            withheld_list = getattr(e2e_res, 'withheld_disclosures', getattr(e2e_res.pipeline_result, 'withheld_disclosures', []))
            for w in withheld_list:
                w_obj = {"entity": getattr(w, 'entity_id', 'unknown'), "reason": getattr(w, 'reason', '')}
                if not any(existing.get("reason") == w_obj["reason"] for existing in session["withheld_items"]):
                    session["withheld_items"].append(w_obj)

        # Update Session Metrics & Evidence Density
        total_p = len(session["propositions"])
        supported_p = len([p for p in session["propositions"] if p["status"] == "SUPPORTED"])
        insuff_p = len([p for p in session["propositions"] if p["status"] == "INSUFFICIENT_EVIDENCE"])
        conflict_p = len([p for p in session["propositions"] if p["status"] in ("CONTRADICTED", "CONFLICT")])
        tier1_src = len([s for s in session["source_references"] if s.get("source_tier") == "TIER_1"])
        corroborated_p = len([p for p in session["propositions"] if len(p.get("evidence_ids", [])) > 1])

        session["updated_at"] = now
        session["metadata"] = {
            "total_queries": len(session["queries"]),
            "total_entities": len(session["entities"]),
            "total_propositions": total_p,
            "supported_count": supported_p,
            "insufficient_count": insuff_p,
            "conflict_count": conflict_p,
            "evidence_count": len(session["evidence_references"]),
            "source_count": len(session["source_references"]),
            "evidence_density": round((supported_p / total_p * 100), 1) if total_p > 0 else 0.0,
            "corroboration_count": corroborated_p,
            "tier1_source_count": tier1_src
        }

        store.save_research_session(session_id, session["title"], session["created_at"], now, session)
        return session
