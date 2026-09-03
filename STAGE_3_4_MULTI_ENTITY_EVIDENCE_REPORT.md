# STAGE 3.4 MULTI-ENTITY EVIDENCE EXPANSION & PROPOSITION ISOLATION REPORT

---

## 1. SUMMARY OF EVALUATED PROPOSITIONS

| Entity | Proposition | Status | Evidence Count | Source Tier | Temporal Scope | Relationship Created |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **PLD Space** (`pld`) | `pld -> develops_reusable_launch_vehicle` | **`SUPPORTED`** | 1 | `TIER_1` | `PLANNED` | YES (`RE-0001`) |
| **Isar Aerospace** (`isar`) | `isar -> develops_reusable_launch_vehicle` | **`INSUFFICIENT_EVIDENCE`** | 0 | `N/A` | `UNSPECIFIED` | NO (`0`) |
| **Rocket Factory Augsburg** (`rfa`) | `rfa -> develops_reusable_launch_vehicle` | **`INSUFFICIENT_EVIDENCE`** | 0 | `N/A` | `UNSPECIFIED` | NO (`0`) |
| **Orbex** (`orbex`) | `orbex -> develops_reusable_launch_vehicle` | **`NO_SOURCE_ROOT`** | 0 | `N/A` | `UNSPECIFIED` | NO (`0`) |
| **MaiaSpace** (`maia`) | `maia -> develops_reusable_launch_vehicle` | **`REDIRECT_MISMATCH`** | 0 | `TIER_4` | `UNSPECIFIED` | NO (`0`) |

---

## 2. COMPLETE EVIDENCE CHAINS FOR SUPPORTED PROPOSITIONS

### Entity: PLD Space (`pld`)

```text
ENTITY
  PLD Space (ID: pld)

PROPOSITION
  "PLD Space is developing reusable launch vehicle technology."

EVIDENCE ID
  ev_chk_9b26bd44

DOCUMENT ID
  doc_c185acc3848c7f61

CHUNK ID
  chk_f28a9201

RUN ID
  run_stage3_4_1788388736

CONTENT HASH
  c185acc3848c7f615e62f76e11f70c65b99b94228e387879095b357b59af99f0

SOURCE URL
  https://www.pldspace.com/en/miura-5-2.html

EXACT PASSAGE
  "Miura 5 Reusable | PLD Space
R&D PROGRAM
Features & Specs
Renewable Fuel
Long-term environmental benefit.
Zero Debris
De..."

VERIFICATION
  SUPPORTED (Heuristic Conf: 0.89, Evidence Strength: 0.89, Corroboration Count: 1)

ORVYRA CLAIM
  CL-0001 (Statement: "PLD Space is developing reusable launch vehicle technology.")

ORVYRA RELATIONSHIP
  RE-0001 (Edge: pld --develops--> reusable, Evidence IDs: ['ev_chk_9b26bd44'])
```


---

## 3. NON-SUPPORTED PROPOSITION EXPLANATIONS

### Isar Aerospace (`isar`): **`INSUFFICIENT_EVIDENCE`**
- **Reason:** No non-mismatched retrieved text passage establishes reusable launcher development for Isar Aerospace.

### Rocket Factory Augsburg (`rfa`): **`INSUFFICIENT_EVIDENCE`**
- **Reason:** No non-mismatched retrieved text passage establishes reusable launcher development for Rocket Factory Augsburg.

### Orbex (`orbex`): **`NO_SOURCE_ROOT`**
- **Reason:** NO_SOURCE_ROOT: No registered or discovered authoritative source root exists for Orbex.

### MaiaSpace (`maia`): **`REDIRECT_MISMATCH`**
- **Reason:** REDIRECT_MISMATCH: Source 'https://en.wikipedia.org/wiki/MaiaSpace' redirected to 'https://en.wikipedia.org/wiki/MaiaSpace'. Redirected article rejected as direct evidence for MaiaSpace.


---

## 4. MULTI-SOURCE CORROBORATION & CONFIDENCE MODEL ANALYSIS

- **Independent Source Document Counting:** Standardized deduplication ensures that duplicate text copies across identical URLs are not counted as independent corroborating evidence.
- **Separation of Calibration Fields:**
  - `verification_status`: Deterministic outcome (`SUPPORTED`, `INSUFFICIENT_EVIDENCE`, `REDIRECT_MISMATCH`, `NO_SOURCE_ROOT`).
  - `evidence_strength`: Uncalibrated raw passage score multiplied by source tier factor.
  - `source_tier`: Explicit source quality tier (`TIER_1` to `TIER_5`).
  - `corroboration_count`: Number of distinct independent source URLs containing matching proposition passages.
  - `confidence`: Explicitly labeled as **Heuristic Confidence** (`is_heuristic_confidence = True`).

---

## 5. AUTOMATED TEST SUITE EXECUTION SUMMARY

Executed `tests/test_stage3_4_suite.py` (**10/10 PASSED**):
- **Test A (PLD evidence cannot support Isar):** `PASSED`
- **Test B (Isar evidence cannot support RFA):** `PASSED`
- **Test C (RFA evidence cannot support Orbex):** `PASSED`
- **Test D (Generic statement cannot become entity proposition):** `PASSED`
- **Test E (Multi-company mention sentence attribution):** `PASSED`
- **Test F (No source root returns NO_SOURCE_ROOT):** `PASSED`
- **Test G (Historical evidence cannot satisfy operational):** `PASSED`
- **Test H (Redirect mismatch rejected):** `PASSED`
- **Test I (Stale documents rejected):** `PASSED`
- **Test J (Unsupported proposition creates 0 relationships):** `PASSED` (Invariants 1 & 2 strictly enforced)

---

## 6. FINAL AUDIT METRICS SUMMARY

- **Entities Evaluated:** 5
- **Propositions Evaluated:** 5
- **Supported Propositions:** 1
- **Insufficient Propositions:** 2
- **Redirect Mismatches:** 1
- **No Source Roots:** 1
- **Conflicts:** 0
- **Invalid Provenance Cases:** 0
- **Orvyra Relationships Created:** 1
- **Cross-Entity Contamination Tests:** 5/5 PASSED
- **Stale-Evidence Tests:** 2/2 PASSED
- **Total Automated Tests & Pass Rate:** 10/10 PASSED (100%)
- **Remaining Limitations:** Single Page Applications require headless browser DOM rendering for dynamic navigation; local provider fallbacks active.