# Story DoD CHECKPOINTS — vitalia/vitalia-fase2-adrian-inbox

> Brand: vitalia
> Auditor: /auditor (autónomo) + auditor-backend (Opus, independiente)
> Date: 2026-06-04
> Model: 2-modos (amendment 2026-06-04)
> Verdict: **APPROVED** — story ready for merge by /pm-vitalia

## C1 — Code
- [x] Tests RED → GREEN — golden e2e `adrian-inbox-modes.spec.ts` es la regresión del commit-fix (botón pausa flippea solo si commitea+refetchea); BE inbox 103 tests verdes
- [x] Coverage no regression — BE inbox 103 passed · FE `features/adrian` 344 passed (50 files)
- [x] Lint + format clean — `ruff check` + `ruff format --check` clean (BE) · `eslint src/features/adrian` exit 0 (FE)
- [x] Type-check clean — `tsc --noEmit` exit 0 (FE) · mypy (BE auditor pass)

## C2 — Spec compliance
- [x] Each Gherkin scenario has GREEN test — gherkin-matrix 17/17 reglas PASS, 0 MISSING (`06-audit/gherkin-matrix.md`)
- [x] Playwright E2E passes — golden `adrian-inbox-modes.spec.ts` **7 passed** contra dev-app (backend real, base.ts anti-burbuja); writes DB-verified
- [x] Agentic eval — N/A justificado (inbox CONSUME runtime read-only; `04-validators § agentic_eval skip`)
- [x] Screenshots/mockups — ADR-003 mockup-per-component **WAIVED** (story de migración; ratificación visual = live-verify dev-app, más fuerte). Ver `checkpoint::ratified_visual_waiver`
- [x] Voice fidelity grader — N/A (no toca sales_agent voice runtime)

## C3 — Architecture
- [x] Arch fitness 0 violations (en scope) — BE 3 PHI/contract arch tests pass (response_model + dual-filter + contract-parity) · FE no-hardcoded-colors 2/2 + no-clerk-organizations 16/16. (Reds fsd_boundaries/no_cross_feature = pre-existentes, otras sesiones — ver § Pre-existentes)
- [x] DDD boundaries — inbox NO importa sales_agent directo (`av-no-sales-agent-import` green); commit-fix es inbox-local
- [x] Tenant isolation — dual filter `tenant_id`+`clinic_id` intacto (auditor-backend confirmó); cross-tenant 404
- [x] Anti-duplication — sin mirror; `set_pause_until` REUSADO (crm), no recreado; sesión committing = la MISMA que CRM ya usaba
- [x] Cross-module audit (R3) — el commit-fix usa el patrón session compartido; sin nuevos cross-imports
- [x] 05-guidelines scope respetado — cambios SOLO en `inbox/api/router.py` + e2e + docs (NO core/, NO otra brand, NO crm repo)

## C4 — Cross-cutting
- [x] Spanish neutro — copy del inbox sin cambios user-facing (solo lógica BE + e2e + docs)
- [x] PII sanitization — `response_model=` intacto en mutation handlers + `sanitize_payload` (auditor confirmó); el fix RESTAURA una obligación HIPAA-lite (audit-log antes se perdía sin commit)
- [x] Currency/master-data — N/A (sin campos monetarios en el inbox chrome)
- [x] Migrations idempotentes — N/A (esta work no toca migrations/models)
- [x] Default flag flips — N/A
- [x] Security — sin SQL injection/XSS/prompt injection; el fix corrige un write silenciosamente perdido (mejora de integridad)
- [x] Brand docs R1 — sin `.md` suelto en `vitalia/docs/` raíz
- [x] Brand docs R3 — BACKLOG no editado manual

## C5 — Trace
- [ ] checkpoint.md final state=done — lo setea /pm-vitalia al merge
- [ ] BACKLOG regenerado post-merge — auto (R33 hook) en /pm-vitalia
- [x] Capability migration ready — cap `adrian.inbox` v3.2 (scenarios + access + business_rules) lista para poblar por /pm-vitalia Fase F.3 (`cap_change_type: fix`)
- [x] modules MD refresh ready — `inbox` module
- [x] learnings entry — HB-50 capturado (`docs/process/harness-backlog.md`); **promotable cross-brand** (3ra instancia verificación-≠-200 + missing-commit) → ping /pm-luana
- [x] Story folder ready for archive — R2 `git mv` a `vitalia/docs/archive/2026/stories/` en MISMO commit del 07-merge

## Findings summary
- C1: 4/4 ✅
- C2: 5/5 ✅
- C3: 6/6 ✅
- C4: 8/8 ✅
- C5: 4/6 ✅ (2 pending = acciones de /pm-vitalia al merge)

## Verdict
**APPROVED** — story ready for merge by /pm-vitalia.

Hallazgo del auditor (Carril R, ya resuelto): `_get_retract_service` tenía el mismo bug HB-50 (commit-fix omitió retract) → arreglado por auditor-backend + gates re-corridos (103 inbox tests verdes). Detalle: `T-reconcile-be-review.md`.

## Notes for /pm-vitalia merge
- Capabilities to update: `adrian.inbox` (cap_change_type: fix → change_log entry type=fix; el amendment 2-modos toca behavior → considerar `extend` con scenarios SC-mode/SC-4/SC-composer/SC-privacy. /pm-vitalia decide fix vs extend en Fase F.3).
- modules/inbox.md auto-list refresh.
- learnings entry suggested: SÍ — HB-50 (verification-≠-200 + missing-commit systemic). Promotable → /pm-luana.
- Follow-ups (NO bloquean done, ya en `06-tickets.yaml § follow_ups`): FU-1..FU-6 + FU-7 (live-verify del retract — su commit-fix está gate-cubierto por 103 tests pero el efecto en DB no se ejerció live; retract NO es un scenario de esta story).
- demo_signoff: APPROVED_WITH_NOTES (Chris 2026-06-04) presente en checkpoint + demo-script.md.
