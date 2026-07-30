# 05-guidelines · vitalia-fase2-lisa-doctores — builder enforceable guidelines

> Architect Opus 4.8 · 2026-05-31 · architecture_pattern: ADR-vitalia-004 (full).
> Consumed by `builder-backend` + `builder-frontend`. Enforced by `auditor-backend` + `auditor-frontend`.

## must_load_skills (per surface)

### builder-backend (Sonnet)
- `backend-expert` — Inside-Out DDD, SQLA 2.0, response_model, arch fitness.
- `tessl__fastapi` — router/DTO patterns.
- `tessl__pytest-api-testing` — endpoint tests.
- `tessl__graceful-degradation` — bio-gen LLM timeout/fallback.
- RULE `vitalia/.claude/rules/hipaa-lite.md` (FULL set — dual filter, audit sync, pgcrypto, RBAC, masking, channel guards).
- RULE `.claude/rules/backend-migrations.md` (idempotent raw SQL).
- RULE `.claude/rules/tenant-isolation.md` + `.claude/rules/backend-ddd.md`.
- PATTERN: consume `luana-core-assets` proxy upload (copy `nicolify/backend/src/main.py` wiring) + `python-dateutil.rrule` for recurrence.

### builder-frontend (Sonnet)
- `frontend-expert` — FSD-Lite, Server-First, React Query/Zustand split, runtime-quality-checklist.
- `vitalia-design-system` (★ brand FE SSoT) — shell-organism + tokens agent-lisa + SubSubTabsBar precedent + Valeria sidebar.
- `tessl__react-patterns` + `tessl__zod` + `tessl__shadcn-ui` + `tessl__tailwind` + `tessl__vitest` + `tessl__nextjs-app-router-modularization`.
- `playwright-expert` (for e2e/visual goldens — Clerk auth, POMs).
- RULE `.claude/rules/frontend-fsd.md` + `.claude/rules/frontend-visual-fidelity.md` + `.claude/rules/spanish-text.md` + `.claude/rules/form-runtime-array.md`.
- RULE `vitalia/.claude/rules/shell-mockup-per-component.md` (wrapper fidelity — port shell wrapper verbatim, don't reinvent).

### cross-cutting
- `brand-expert` (bio-gen tono anchor only — NOT writing brand aggregates).

## Patterns REQUIRED

- **Dual filter:** every PHI/clinics repo query carries `tenant_id` + `clinic_id`, inherits `PhiRepositoryBase`, calls `validate_dual_filter(...)`. Incl. `get_by_id`.
- **Audit sync write:** every mutation writes `AuditLogRepository.write(entry)` (awaited, same session, pre-response). Actions: `doctor.created/updated/deactivated`, `doctor.availability_block_created/deleted`, `cross_tenant_attempt`, `phi_access_granted/denied`.
- **pgcrypto:** PII columns (dni/email/phone/credential) stored BYTEA via `pgp_sym_encrypt(:v,:key)`; `dni_hash` deterministic for unique constraint. KEK via `KEKClient.from_env()`.
- **RBAC:** all doctor mutations gated by `require_phi_access(roles=["admin_clinic"], ...)` OR `require_brand_owner_access()` (admin_clinic). Public endpoint = no auth. FE hides/disables controls for non-admin + backend 403.
- **Masking:** lists + public use `phi_masking.mask_dni/mask_email/mask_phone`. Detail (admin only) unmasked.
- **response_model=:** mandatory every route. Public DTO = allow-list serializer (`to_public_dto`), physically no PHI fields.
- **Recurrence:** `dateutil.rrule` (WEEKLY interval 1/2, byweekday, until/count). NO hand-rolled recurrence math. `open_ended` -> 90d horizon.
- **Slots in UTC:** `DateTime(timezone=True)`, store UTC, FE display 24h via tenant tz.
- **React Query SSoT data, Zustand UI-only.** Keys `['lisa','staff',...]`. Mutations invalidate explicitly. SSR hydrate.
- **Autosave 600ms, NO save button** (Perfil/Horarios). Modal create = submit-driven.
- **Rutas-hoja reales** (NO Shadcn `<Tabs>`). `EntitySubNavBar` = N3-dynamic. Deep-link + back/forward work.
- **Spanish neutro** (microcopy table del spec § Microcopy authoritative). Tildes + ñ + ¿!.
- **Assets:** proxy upload (`POST /api/v1/vitalia/assets/upload`), 10MB + content-type allow-list. Storage swappable (LocalStorageStrategy in tests).
- **bio-gen:** extractive single-shot, guardrail "no inventes", timeout+fallback, output editable.

## Patterns FORBIDDEN

- ❌ Reimplementar recurrencia from scratch (usar dateutil.rrule).
- ❌ Llamar a `luana-core-commercial-calendar` para proyectar availability (NO hace recurrence — premisa errada del spec, ver 03-arch D-2).
- ❌ Construir presigned-upload nuevo o tocar `R2StorageStrategy` (engine change -> /pm-luana). Usar proxy upload.
- ❌ Crear `staff/` module (el dueño es `clinics`).
- ❌ Tocar `vitalia_doctor_extensions` model (se mantiene; FK lógica resuelta en app).
- ❌ Shadcn `<Tabs>` internas para Perfil/Horarios/Servicios (rutas-hoja + EntitySubNavBar).
- ❌ Modificar `SubSubTabsBar.tsx` (es N3-static; EntitySubNavBar es sibling nuevo).
- ❌ PHI en URL/searchParams. PHI sin sanitizar en logs/telemetría/traces.
- ❌ `session.query()` (SA 1.x). `class Config` Pydantic v1. `Any`/dict mágico. Hard delete.
- ❌ `op.create_table()` / `sa.Enum(create_type=True)`. Migration no idempotente.
- ❌ Botón "Guardar" en Perfil/Horarios (rompe autosave).
- ❌ Voseo en copy user-facing. `toLocaleDateString()`. Currency hardcoded.
- ❌ bio-gen como LangGraph node / copilot / sales_agent surface (NO es agentic).
- ❌ Cross-feature import (`features/lisa` ← otra feature). Cross-brand mirror.
- ❌ docker exec para lint/tests. Editar `core/luana-core-*/src/`.

## Files in scope (touch OK)

- `vitalia/backend/src/modules/vitalia/clinics/**` (domain/infra/app/api — NEW + dtos MODIFY)
- `vitalia/backend/alembic/versions/036_f2_s8_vitalia_lisa_staff.py` (NEW)
- `vitalia/backend/src/main.py` (MODIFY — 3 include_router)
- `vitalia/backend/tests/{architecture,modules/vitalia/clinics}/**` (NEW tests)
- `vitalia/frontend/src/features/lisa/**` (EXTEND — components/staff, api, hooks, store, types)
- `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/staff/**` (NEW routes)
- `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` (NEW)
- `vitalia/frontend/src/components/ui/dropzone.tsx` (INSTALL diragb/shadcn-dropzone)
- `vitalia/frontend/src/lib/shell-routes.ts` / `agent-catalog.ts` (MODIFY only if `staff` missing from `AGENT_SUBTABS[lisa]`)
- `vitalia/frontend/src/mocks/handlers/staff.ts` (NEW MSW)
- `vitalia/frontend/e2e/**` (NEW specs + POMs + goldens)

## Files NEVER touch

- `core/luana-core-*/src/**` (engine — read-only; changes -> /pm-luana promotion proposal)
- `vitalia/backend/src/modules/vitalia/infrastructure/models/doctor_extension_model.py` (existing extension — leave intact)
- `vitalia/backend/src/modules/vitalia/scheduling/**` (consume only, no edit — slots table is brand-local clinics)
- `components/shared/shell-organism/{SubSubTabsBar,Ribbon,SubTabsBar,ValeriaSidebar,TopBarGlobal}.tsx` (wrapper — port-reference only)
- `app/[tenantId]/(shell-organism)/lisa/marca/**` (sibling story)
- Other brands (`nicolify/`, `comunify/`, `lupulo/`) — read nicolify main.py as wiring reference ONLY, never edit.

## Quality gates (native, pre-commit + pre-spawn-auditor)

```bash
WS=$(git rev-parse --show-toplevel)
# BE
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/ tests/ && ${WS}/.venv/bin/ruff format --check src/ tests/
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/clinics/ -v
# FE
cd ${WS}/vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache
cd ${WS}/vitalia/frontend && npx vitest run src/features/lisa/ src/components/shared/shell-organism/
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke
```

## R2 provisioning (Chris manual — does NOT block code/tests)

Tests use LocalStorageStrategy. Before live E2E with real avatars:
1. Cloudflare -> R2 -> Manage R2 API Tokens -> S3 credentials (the `cfat_` token is CF API, NOT S3 key).
2. Create bucket `vitalia-assets` (+ optional `vitalia-assets-public`) + CORS for FE origin.
3. Load `R2_*` env in `vitalia/.env.dev` (gitignored). Rotate the chat-pasted `cfat_`.
