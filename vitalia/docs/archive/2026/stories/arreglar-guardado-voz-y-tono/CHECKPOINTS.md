# Story DoD CHECKPOINTS — vitalia/arreglar-guardado-voz-y-tono

> Brand: vitalia · Auditor: auditor-backend + auditor-frontend (independientes) · Date: 2026-05-31
> Type: bugfix (lite) · Verdict: **APPROVED** (1 WARN non-blocking diferido)

## C1 — Code
- [x] Tests RED → GREEN (TDD) — test_audit_writer_sanitize + test_patch_personality_audit (BE) + e2e real-backend (FE)
- [x] Coverage no regression
- [x] Lint + format clean (ruff check + ruff format · eslint)
- [x] Type-check clean (mypy/ruff BE · tsc --noEmit FE)

## C2 — Spec compliance
- [x] Cada scenario con test GREEN o quarantine-pointed (ver 06-audit/gherkin-matrix.md) — 6/8 determinístico, 2 quarantined → harness story
- [x] Playwright E2E real-backend: arquetipo autosave + bloque no-422 PASS (determinista 2x, `--workers=1` confirmado)
- [x] Persistencia verificada REAL (curl PATCH→GET round-trip) — no mock
- n/a Agentic eval / voice fidelity (no aplica)

## C3 — Architecture
- [x] Arch fitness 0 violations
- [x] DDD boundaries (no import cycle audit→compliance · auditor-be confirmó)
- [x] Tenant isolation (cross-tenant 403/404 test)
- [x] Anti-duplication: consume engine `sanitize_payload` vía wrapper brand-local `sanitize_phi_payload` (cero recreación)
- [x] Cross-module: sin downstream regression (auditor-be confirmó CAST/alias scoped)
- [x] Files in scope respetados (sin engine, sin cross-brand)

## C4 — Cross-cutting
- [x] Spanish neutro (UI sin voseo · chris-input magic comment para conversación interna)
- [x] PHI sanitization RESTAURADA (sanitize_phi_payload — el bug la tenía muerta · HIPAA-lite)
- [x] Migrations: n/a (sin DDL nuevo)
- [x] Security: tenant isolation OK · sin nuevos vectores
- [x] Brand docs R1/R3 respetados
- [ ] **WARN (diferido):** audit-actor `X-User-ID: tenantId` en marca-voice-api.ts (debería ser Clerk userId) — HIPAA-lite fidelity. Non-blocking · stake-asimétrico → `estabilizar-harness-e2e-lisa-marca` § Sub-bug #2

## C5 — Trace
- [x] checkpoint.md → reviewing (será done por /pm al merge)
- [x] Capability `brand_studio.lisa-marca` cap_change_type=fix · change_log entry al merge
- [x] e2e_test wire del scenario voz-y-tono → al merge (mueve cap hacia verified-live; restante quarantined → harness story)
- [x] Story folder lista para archive (git mv en commit del 07-merge)
- [x] Follow-up story `estabilizar-harness-e2e-lisa-marca` creada (race auth-readiness + prohibited-phrases + audit-actor + contraste)

## Findings summary
- C1: 4/4 ✅ · C2: 3/3 ✅ (+2 quarantined pointed) · C3: 6/6 ✅ · C4: 5/6 ✅ (1 WARN diferido) · C5: 5/5 ✅

## Verdict
**APPROVED** — story ready for merge by /pm-vitalia. El WARN de audit-actor es non-blocking y queda trackeado en la harness story.

## Notes for /pm-vitalia merge
- Cap a actualizar: `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` — change_log entry type=fix · wire `e2e_test` del scenario `admin-define-voz-y-tono` (hoy null) → `voz-arquetipo-autosave.spec.ts`.
- Learnings sugeridos: (1) verificación-real destapó 5 bugs apilados que el E2E mockeado nunca vio; (2) el harness lisa-marca estaba mockeado+testids-fantasma+tenant-ficticio (= verde-falso) — promotable cross-brand. → ping /pm-luana opcional.
- Follow-up: `estabilizar-harness-e2e-lisa-marca` (creada).
