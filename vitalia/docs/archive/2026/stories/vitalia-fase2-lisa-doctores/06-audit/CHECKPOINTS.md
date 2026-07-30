# Story DoD CHECKPOINTS — vitalia/vitalia-fase2-lisa-doctores

> Brand: vitalia · Auditor: auditor-backend + auditor-frontend (Opus) + orchestrator live-verification
> Date: 2026-05-31 · Verdict: **APPROVED (API/contract/security layer) · BLOCKED on browser-E2E + dev-app dod_evidence (ADR-008/Rule#37) for `done`**

## C1 — Code
- [x] Tests RED→GREEN (TDD; new RBAC 403 test + autosave coalescing test added)
- [x] BE 181/181 + arch 320/320 (excl pre-existing CRM treatment_plans.notes debt) · FE 2415/2415 + arch 162/162
- [x] Lint + format clean (ruff / eslint)
- [x] Type-check clean (tsc 0)

## C2 — Spec compliance
- [x] Create-doctor verified REAL: POST→201, DB row, pgcrypto bytea at-rest, audit doctor.created
- [x] camelCase FE↔BE contract aligned + live-verified (list firstName binds, PATCH persists)
- [x] PHI masking live (maskedDni 87.***)
- [ ] **Playwright browser E2E + visual goldens NOT generated** (needs Clerk session — headless agents couldn't establish). Specs written + parse-clean (41).
- [ ] **ADR-008/Rule#37 dev_app_verified** — pending Chris deploy + dod_evidence

## C3 — Architecture
- [x] Arch fitness 0 violations (clinics) — pre-existing CRM debt out of scope
- [x] DDD boundaries (minor WARN: app→repo _kek seam, noted)
- [x] Tenant+clinic dual filter (slot mutations clinic_id added in fix)
- [x] Anti-duplication: no cross-brand mirror, no engine edit (consumes dateutil/assets/scheduling)
- [x] 6 architecture decisions resolved (D-1..D-6), 3 false-premise corrections grep-verified

## C4 — Cross-cutting
- [x] Spanish neutro LatAm
- [x] PHI: pgcrypto at-rest + masking + public allow-list channel guard + response_model=
- [x] **Security: RBAC bypass on assets upload FIXED + live-verified** (marketing→403, admin→pass)
- [x] Migrations idempotent (036 revision-id fixed — was crashing boot)
- [x] No default-flip side effects

## C5 — Trace
- [ ] checkpoint.md final state=done (BLOCKED — see below)
- [ ] Capability lisa.doctores.yaml (F.3 at merge by /pm-vitalia)
- [ ] Story archive (R2 at merge)

## Bugs found + fixed via LIVE verification (7 commits — all missed by 2400+ unit tests)
1. Migration 036 revision id → backend crash-loop (b6aa8c35)
2. DB session dep sync→async ×3 routers → all endpoints 500 (e3db65a4)
3. No-trailing-slash routes → 422 (4cffaa1e)
4. Missing NuqsAdapter → FE crash (4cffaa1e)
5. pgcrypto :phone ambiguous param → create-doctor 500 (0d56d831)
6. RBAC bypass on assets upload (any role could upload) (ef350949)
7. FE↔BE camelCase contract mismatch (undefined render + autosave no-op) (ef350949 + 0ce5fe1b)

## Verdict
**APPROVED at API/contract/security/data layer (verified-real).** Story CANNOT reach `done` autonomously — blocked on:
1. Browser-level E2E + visual golden baselines (needs Clerk testing session).
2. ADR-vitalia-008 / Rule#37 `dev_app_verified` — Chris deploys to dev-app + exercises live + records dod_evidence.
3. T-BE-7 R2 S3 credentials (Chris manual Cloudflare step) for live avatar upload.

## Notes for /pm-vitalia merge
- cap_change_type: new → create capabilities/clinics/lisa.doctores.yaml (scenarios SC-1..SC-11 + access RBAC + 16 business_rules) at F.3
- ADR-vitalia-004 § 3.1.1 addendum: EntitySubNavBar N3-dynamic pattern
- Correct business rule availability-projection-via-engine → brand-local dateutil.rrule (premise corrected)
- Observed-bugs logged: pgcrypto treatment_plans.notes (CRM debt), zustand @luana/hooks hoisting (fixed in container)
