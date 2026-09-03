# STAGE 3.5.1 SEMANTIC ENTAILMENT HARDENING REPORT

---

## 1. ACTUAL SEMANTIC VERIFIER IMPLEMENTATION MODEL

The Semantic Verifier Engine evaluates evidence compositionally across **5 explicit dimensions**:
1. **Entity Attribution (`entity_attribution`):** Verifies that the passage explicitly references the canonical entity or an unambiguous alias.
2. **Predicate Support (`predicate_support`):** Verifies active development, R&D, manufacturing, or design predicates. Rejects operational-only or third-party supplier predicates.
3. **Object Support (`object_support`):** Verifies explicit reusable launch vehicle / recoverable first stage concept. Rejects expendable launchers.
4. **Temporal Support (`temporal_support`):** Verifies active `IN_DEVELOPMENT` scope. Rejects historical tests (`HISTORICAL`) or terminated programs (`CANCELLED`).
5. **Provenance Integrity (`provenance_valid`):** Verifies document hash integrity and checks for HTTP/soft redirect identity mismatches.

**Joint Semantic Completeness (`semantic_completeness`):** Succeeded **ONLY** when `Entity + Predicate + Object + Temporal + Provenance` are all satisfied simultaneously.


---

## 2. FIVE-DIMENSION VERIFICATION RESULTS TABLE

| Entity | Proposition | Entity Attrib | Predicate | Object | Temporal | Provenance | Semantic Completeness | Final Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PLD Space** (`pld`) | `pld -> develops_reusable` | `False` | `False` | `False` | `False` | `True` | **`False`** | **`INSUFFICIENT_EVIDENCE`** |
| **Isar Aerospace** (`isar`) | `isar -> develops_reusable` | `False` | `False` | `False` | `False` | `True` | **`False`** | **`INSUFFICIENT_EVIDENCE`** |
| **Rocket Factory Augsburg** (`rfa`) | `rfa -> develops_reusable` | `False` | `False` | `False` | `False` | `True` | **`False`** | **`INSUFFICIENT_EVIDENCE`** |
| **Orbex** (`orbex`) | `orbex -> develops_reusable` | `False` | `False` | `False` | `False` | `True` | **`False`** | **`NO_SOURCE_ROOT`** |
| **MaiaSpace** (`maia`) | `maia -> develops_reusable` | `False` | `False` | `False` | `False` | `False` | **`False`** | **`REDIRECT_MISMATCH`** |

---

## 3. ADVERSARIAL FIXTURES EVALUATION SUMMARY

| Fixture ID | Passage Text | Entity | Predicate | Object | Temporal | Semantic Result | Reason / Explanation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Fixture A** | *"Reusable launch vehicles are becoming increasingly impo..."* | `False` | `False` | `False` | `False` | **`NOT_ENTAILED`** | Missing entity attribution |
| **Fixture B** | *"PLD Space operates a reusable launch vehicle...."* | `True` | `False` | `False` | `False` | **`NOT_ENTAILED`** | Operational status without development predicate |
| **Fixture C** | *"PLD Space is developing a new orbital launch vehicle...."* | `True` | `True` | `False` | `False` | **`NOT_ENTAILED`** | Reusable property absent |
| **Fixture D** | *"PLD Space investigated reusable launch vehicle concepts..."* | `True` | `True` | `True` | `False` | **`NOT_ENTAILED`** | Historical temporal scope |
| **Fixture E** | *"PLD Space developed the reusable Miura 5 concept before..."* | `True` | `True` | `True` | `False` | **`NOT_ENTAILED`** | Cancelled program scope |
| **Fixture F** | *"PLD Space is not developing a reusable launch vehicle...."* | `True` | `False` | `False` | `False` | **`CONTRADICTED`** | Explicit negation |
| **Fixture G** | *"PLD Space develops launch vehicles. Reusable launch veh..."* | `True` | `False` | `True` | `False` | **`NOT_ENTAILED`** | Development predicate belongs to third party |
| **Fixture H** | *"PLD Space provides components used by companies develop..."* | `True` | `False` | `True` | `False` | **`NOT_ENTAILED`** | Component supplier relationship |
| **Fixture I** | *"Miura 5 is reusable. PLD Space has announced the vehicl..."* | `True` | `False` | `False` | `False` | **`NOT_ENTAILED`** | Announcement without development predicate |
| **Fixture J** | *"PLD Space is developing Miura 5, but the vehicle is exp..."* | `True` | `False` | `False` | `False` | **`CONTRADICTED`** | Explicit non-reusable refutation |

---

## 4. POSITIVE ENTAILMENT EVIDENCE EVALUATION

### Positive 1: *"PLD Space is developing MIURA 5, an orbital reusable launch vehicle."*
- **Entity Attribution:** `True`
- **Predicate Support:** `True`
- **Object Support:** `True`
- **Temporal Support:** `True` (`IN_DEVELOPMENT`)
- **Semantic Completeness:** `True`
- **Entailment Result:** **`ENTAILED`**

### Positive 2: *"Spanish launch provider PLD Space is currently designing and building a recoverable first stage launcher."*
- **Entity Attribution:** `True`
- **Predicate Support:** `True`
- **Object Support:** `True`
- **Temporal Support:** `True` (`IN_DEVELOPMENT`)
- **Semantic Completeness:** `True`
- **Entailment Result:** **`ENTAILED`**

### Positive 3: *"PLD Space R&D programme is actively manufacturing a reusable launch vehicle for commercial satellite missions."*
- **Entity Attribution:** `True`
- **Predicate Support:** `True`
- **Object Support:** `True`
- **Temporal Support:** `True` (`IN_DEVELOPMENT`)
- **Semantic Completeness:** `True`
- **Entailment Result:** **`ENTAILED`**


---

## 5. CURRENT LIVE PLD EVIDENCE AUDIT

PLD Space Live Evidence Status: **`INSUFFICIENT_EVIDENCE`** (No semantically entailed text passage establishes reusable launcher development for PLD Space.)


---

## 6. EVIDENCE FRAGMENT VS SURROUNDING CONTEXT ANALYSIS

- **`DIRECT_ENTAILMENT`:** The extracted passage itself compositionally establishes `Entity + Predicate + Object + Temporal Scope` without requiring external text.
- **`CONTEXTUAL_ENTAILMENT`:** A short header fragment (e.g. *"Discover Miura Next | PLD Space"*) combined with surrounding chunk context (*"R&D PROGRAM features recoverable first stage"*) compositionally establishes entailment.
- **`INSUFFICIENT_FRAGMENT`:** Isolated fragments containing keywords without compositional predicate support are rejected.

---

## 7. ANTI-HARDCODING VERIFICATION

- **Source Code Audit:** Codebase inspection confirms ZERO entity-specific shortcuts (e.g. `if entity == 'pld'` or `if 'miura' in text`).
- **Fictitious Entity Test:** Fictitious entity `custom_ent` (*"Aether Dynamics"*) with unknown vehicle (*"Prometheus"*) evaluated compositionally and returned `ENTAILED` without any entity shortcuts.

---

## 8. AUTOMATED TEST SUITE SUMMARY

Executed `tests/test_stage3_5_1_hardening.py` (**25/25 PASSED** in 0.029s):
- **10 Adversarial Negative Fixtures (Fixtures A-J):** `10/10 PASSED`
- **3 Positive Entailment Fixtures:** `3/3 PASSED`
- **3 Temporal Scope Fixtures:** `3/3 PASSED`
- **3 Contradiction / Conflict Fixtures:** `3/3 PASSED`
- **2 Context-vs-Fragment Fixtures:** `2/2 PASSED`
- **2 Anti-Hardcoding Tests:** `2/2 PASSED`
- **2 Provenance Integrity Tests:** `2/2 PASSED`

---

## 9. REMAINING LIMITATIONS & FINAL INVARIANTS

### Invariants Enforced:
- `NO EVIDENCE -> NO CLAIM`
- `NO ENTAILMENT -> NO CLAIM`
- `NO VERIFIED CLAIM -> NO ORVYRA RELATIONSHIP`

### Remaining Limitations:
- Single Page Applications require headless browser DOM rendering for dynamic sub-page discovery.
- Local provider fallbacks active for embeddings and reranking.