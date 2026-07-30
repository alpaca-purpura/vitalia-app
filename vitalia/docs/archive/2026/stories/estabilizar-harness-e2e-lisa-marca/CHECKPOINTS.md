<!-- voseo-allowed: doc interno de auditoría -->
# Story DoD CHECKPOINTS — vitalia/estabilizar-harness-e2e-lisa-marca

> Brand: vitalia
> Auditor: /auditor (orchestrator) + auditor-backend + auditor-frontend (×2 iter)
> Date: 2026-06-03
> Verdict: **APPROVED**

## C1 — Code
- [x] Tests RED → GREEN (TDD — logo storage, persist, delete, aggregateAutosave, TypographyEditor)
- [x] Coverage no regression (gate-runner: FE vitest 2525 passed; BE brand_studio passed)
- [x] Lint + format clean (ruff check + format; eslint --max-warnings 0)
- [x] Type-check clean (tsc --noEmit 0 errors). mypy: no instalado en venv → no gate (WARN W1 BE noted)

## C2 — Spec compliance
- [x] Cada Gherkin SC-1..SC-8 → test PASS (06-audit/gherkin-matrix.md). SC-1 PASS-con-retries (accepted Chris + HB-28)
- [x] Demo-bug fixes live-verified (logo 3 capas + delete + autosave + badge + typography)
- [x] demo_signoff Chris APPROVED 2026-06-03 (rule #37 §5)
- [x] Live-verify REAL (no GET-200): POST/DELETE /logos ejercidos + efecto observado en GET + R2

## C3 — Architecture
- [x] Arch fitness 0 violations (335 passed)
- [x] DDD boundaries (cross-module iam = sanctioned read; no forbidden imports)
- [x] Tenant isolation (queries filtran tenant_id; clerk_id lookup = identity resolution sobre columna unique)
- [x] Anti-duplication: logo consume engine `luana_core_assets` StorageStrategy (NO recrea, NO toca core/)
- [x] Cross-module audit: cero core/ editado; cero cross-brand
- [x] 05-guidelines "Files in scope" respetado

## C4 — Cross-cutting
- [x] Spanish neutro LatAm (auditores verificaron)
- [x] PII/HIPAA: audit actor real (clerk userId, no tenant_id); response_model en 21 routes
- [x] Master-data: n/a (sin monetary nuevo)
- [x] Migrations: n/a (sin migration nueva — logo usa storage, no DB schema)
- [x] Default flag flips: n/a
- [x] Security: RBAC brand_owner en mutaciones (DELETE sin rol → 403 verificado live)
- [x] Brand docs schema R1/R3 respetado

## C5 — Trace
- [ ] checkpoint.md state=done (lo setea /pm-vitalia en merge)
- [ ] BACKLOG regen post-merge (auto)
- [x] Capability `lisa-marca.yaml` re-cableado (T-4) + verified_real + presencia-web→partial
- [x] cap change_log entry de esta story (type=fix)
- [x] Learnings: avatar FK 500 latente (lisa-doctores) → nota /pm-vitalia; logo storage-direct pattern promotable
- [ ] Story folder ready for archive (R2 — /pm-vitalia git mv en commit del 07-merge)

## Findings summary
- C1: 4/4 ✅ (mypy no-gate documentado)
- C2: 4/4 ✅
- C3: 6/6 ✅
- C4: 7/7 ✅
- C5: 4/6 ✅ (2 los cierra /pm-vitalia en merge)

## WARNs no-bloqueantes (handoff /pm-vitalia + /pm-luana)
- W1 (BE Cat4): `get_trust_signals` sig `user_id: UUID` vs route puede pasar `None` — mypy arg-type. Runtime-safe (param sin uso). Pre-existente, no de esta story.
- W2 (BE Cat12): `user_resolver` re-query clerk_id→users.id; engine tiene `get_by_clerk_id` sync → async-lift candidate `/pm-luana`.
- Cross-story: avatares lisa-doctores usan mismo `AssetsService.upload_asset` → mismo FK 500 latente (mockeado) → bugfix story `/pm-vitalia`.

## Verdict
**APPROVED** — story ready for merge by /pm-vitalia.

## Notes for /pm-vitalia merge
- Capabilities to update: `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` (ya re-cableado en T-4 — verificar merge_sha al cerrar)
- modules MD: sin cambio narrativo
- Learnings sugeridos: (1) logo storage-direct (consume StorageStrategy, no AssetsService entity, evita FK assets→products) — promotable cross-brand; (2) avatar FK latente lisa-doctores
- Promotion candidate: user_resolver async `get_by_clerk_id` (W2) → ping /pm-luana
EOF
echo "CHECKPOINTS written"