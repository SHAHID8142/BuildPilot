# P7 Team Bootstrap — Mechanical Checklist

Schema: sps2.team-bootstrap/v1
Generated: 2026-10-05
Purpose: Mechanical checklist for fresh-agent onboarding. Based on repository state and authoritative sources. No generated runtime state.

## Steps

### Step 1: Read the memory layout

Load sps2/memory/memory-layout.json and verify its sha256 entries against the repository.

**Expected:** All sha256 hashes match the files they reference.

### Step 2: Verify phase index

Check sps2/decisions/ROADMAP-P3-DECISIONS.json completion block is APPROVED with User attribution.

**Expected:** P3 completion state is APPROVED, decided_by is User, decided_on is a date.

### Step 3: Verify capability registry

Load sps2/capability/registry.json and confirm 4 EVALUATED capabilities and CAP-P03-005 DEFERRED.

**Expected:** 4 EVALUATED, CAP-P03-005 DEFERRED / NOT_PROMOTED.

### Step 4: Verify P7 boundaries

Load sps2/decisions/P7-DECISIONS.json and confirm D-P7-IMPLEMENTATION is User-approved with named scope and forbidden scope.

**Expected:** D-P7-IMPLEMENTATION approved by User, scope and forbidden scope match G1-G8.

### Step 5: Verify no P7 implementation artefacts beyond authorised scope

Run validate-p7-readiness.py and confirm 0 P7 implementation artefacts outside the authorised set.

**Expected:** P7 READINESS RECORDED: 30 checks passed, 0 failed.

### Step 6: Verify CONF-001 and LCP/INP

Check sps2/research/cache.json for CONF-001 UNRESOLVED and LCP/INP NOT_OBSERVED.

**Expected:** CONF-001 UNRESOLVED; LCP/INP NOT_OBSERVED.

### Step 7: Run the full sequential validation suite

Run validate-sps2.sh, validate-p2.sh through validate-p6.py, validate-p7-readiness.py sequentially.

**Expected:** All phases pass; 0 failures.

## Boundaries

- no_generated_runtime_state: True
- project_local_only: True
- no_legacy_modification: True
- no_machine_global: True
