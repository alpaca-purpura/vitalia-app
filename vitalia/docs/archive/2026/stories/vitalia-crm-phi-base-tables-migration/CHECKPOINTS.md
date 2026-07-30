# Story DoD CHECKPOINTS — vitalia/vitalia-crm-phi-base-tables-migration

> Brand: vitalia · Auditor: auditor-backend (Opus) + orchestrator Phase D
> Date: 2026-05-30 · Verdict: APPROVED

## C1 — Code
- [x] Tests RED → GREEN (TDD; T-1 idempotency RED-first, T-2 roundtrip, fix regression unit test)
- [x] Coverage no regression (nuevos tests agregados; 0 borrados)
- [x] Lint + format clean (ruff check + ruff format --check — auditor independiente GREEN)
- [x] Type-check clean (scope crm)

## C2 — Spec compliance
- [x] Cada Gherkin SC-1..SC-5 con test/evidencia GREEN (06-audit/gherkin-matrix.md, 5/5 PASS)
- [x] Verificación live real (god-matrix JWT Clerk + conteos DB) — VERIFICATION-godmatrix-live.md
- [x] N/A Playwright (service-story BE, sin UI)
- [x] N/A voice fidelity

## C3 — Architecture
- [x] Arch fitness 0 violations (330 arch tests GREEN, incl. test_pgcrypto_phi_columns extendido)
- [x] DDD boundaries (cifrado en infra, dominio sin cambio; repos infra)
- [x] Tenant isolation (patient dual filter tenant+clinic incl get_by_id; leads tenant; decrypt projection-only no bypassa WHERE)
- [x] Anti-duplication (KEKClient EXTENDIDO, no recreado; pgcrypto pattern reusado; cero mirror cross-brand)
- [x] Engine boundary (cero edit core/luana-core-*/src/; cero cross-brand)
- [x] Files in scope respetados (crm + db.py aditivo + migración + seed + env + tests)

## C4 — Cross-cutting
- [x] N/A Spanish neutro (sin UI; seed data LatAm neutro)
- [x] PII: PatientResponse allowlist (name/email/phone/marketing_opt_out_at) — NO dni/dob/address (verificado live: fields response)
- [x] PHI cifrado at-rest pgcrypto BYTEA (hipaa-lite § Encryption at rest) — verificado raw ciphertext 0xc3
- [x] KEK secrecy: nunca logueada (grep AV-kek-not-logged GREEN); nunca impresa en verificación
- [x] Audit log sync write pre-response — ★ corregido (fix 62b068ac): ahora commitea + persiste (rows 0→1 live)
- [x] Migración idempotente (IF NOT EXISTS; sin sa.Enum; downgrade preserva 016 + pgcrypto)
- [x] No default flag flips (N/A)
- [x] Security: sin SQL injection (bound params), sin PII leak en response/logs
- [x] Brand docs schema R1/R3 respetados (sin .md sueltos en docs/ raíz; sin edit a auto-gen)

## C5 — Trace
- [x] checkpoint.md → /pm-vitalia setea done en merge
- [x] BACKLOG regen post-merge (auto)
- [x] Capability ledger: cap_change_type=fix → append change_log a target (iam-scaffold-slice-1 o crm-consent-optout — /pm decide en F.3)
- [x] modules/crm.md auto-list refresh post-merge
- [x] learnings: candidato — Content-Type fix en god-matrix mint (actualizar learning 2026-05-30) + lección anti-teatro commit-gap
- [x] Story folder lista para archive (R2 git mv en commit del 07-merge)

## Findings summary
- C1: 4/4 ✅ · C2: 5/5 ✅ (2 N/A) · C3: 6/6 ✅ · C4: 9/9 ✅ · C5: 6/6 ✅
- WARN no-bloqueantes: W-1 (api/conftest.py patchea get_async_session ahora no usado por crm → dead patch; follow-up builder, cero impacto actual) · W-2 (SC-4 cross-clinic 404 vs 403, sin leak, resolver pre-existente Slice 2)

## Verdict
APPROVED — story ready for merge by /pm-vitalia

## Notes for /pm-vitalia merge
- cap_change_type: fix → append change_log entry al cap target. Confirmar target real: el checkpoint cita `iam-scaffold-slice-1` pero los repos llevan `# cap: crm.crm-consent-optout` → /pm decide el dueño semántico en Fase F.3 (probablemente crm-consent-optout, o ambos: el fix habilita endpoints PHI que el cap iam scaffolding esperaba).
- Cross-cutting finding ESCALADO (NO en esta story): 18 módulos usan get_async_session sin commit explícito → posible gap unit-of-work en otros módulos que escriben. Recomendación: abrir story de plataforma (/pm-luana o /pm-vitalia) que audite el commit de cada endpoint que escribe. Stake-asimétrico, blast radius — fuera de scope acá.
- Follow-ups ADR-007 ya registrados: trigger+GUC 025 roto, blind index, KMS prod, legacy tree.
- W-1 follow-up: actualizar api/conftest.py para patchear get_async_session_committing (o eliminar el patch muerto).
- Promotion candidate cross-brand: el dependency `get_async_session_committing` (unit-of-work pattern) + el learning Content-Type del god-matrix mint son candidatos de lift/learning cross-brand → ping /pm-luana.
