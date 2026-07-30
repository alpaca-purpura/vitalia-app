# 05-guidelines · vitalia-fase2-config-cuenta — code style + skills enforceables

> Guía de construcción para builders. SSoT de estilo vitalia + skills obligatorias por surface.
> Consumido por `/dev-team` (carga `must_load_skills` por ticket) + `/auditor`.

## must_load_skills (enforceable · por surface)

### T-1 — Frontend (`builder-frontend`, Sonnet)
```yaml
must_load_skills:
  - frontend-expert            # FSD-Lite, Server-First, React Query, RHF+Zod, runtime-quality-checklist
  - vitalia-design-system      # ★ HARD overlay: shell-organism + átomos + tokens + @luana/ui-kit canon
  - playwright-expert          # E2E live-verify + Clerk auth + anti-burbuja fixture
must_load_artifacts:
  - 03-arch.md                 # § 4 (routes) · § 5 (TS types) · § 10 (file structure) · § Integration design
  - 04-validators.yaml         # test_construction_plan.frontend + playwright_visual_scope
  - mockups/cuenta.html        # mockup ratificado (3 sub-sub-tabs)
  - docs/architecture/luana-platform/design-system-canon.md   # binding HARD (Select/Group/autosave/page-primitives)
  - vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md  # patrón 9 secciones
forbidden_to_touch:
  - "vitalia/backend/**"                         # T-2 owna el BE
  - "core/@luana/ui-kit/**"                       # consumir, NO editar (engine TS → /pm-luana)
  - "vitalia/frontend/src/components/shared/shell-organism/**"  # chrome shipped — usar verbatim
  - "config/conexiones, config/avanzado"          # otras stories
```

### T-2 — Backend (`builder-backend`, Sonnet)
```yaml
must_load_skills:
  - backend-expert             # DDD Inside-Out, SQLA 2.0, Pydantic v2, migration idempotente, runtime-quality-checklist
  - brand-expert               # specialties viven en tenant.config_json.clinic_config (NO en Clinic entity)
must_load_artifacts:
  - 03-arch.md                 # § 1-9 (entities/models/DTOs/routes/repos/services/migration) · § Architecture Decisions
  - 04-validators.yaml         # test_construction_plan.backend + business_rules
  - vitalia/.claude/rules/hipaa-lite.md           # audit log sync + tenant scope (clinic = non-PHI, documentado)
forbidden_to_touch:
  - "vitalia/frontend/**"                         # T-1 owna el FE
  - "core/luana-core-tenant-profile/**"           # engine — config_json se escribe vía brand service, NO column nueva
  - "core/luana-core-iam/**"                       # consumir read-only (TenantModel.config_json)
  - "clinics/api/router.py"                        # CRUD admin existente — account_router es archivo NUEVO
  - "clinics/application/credential_validator.py"  # validador médico (doctor) — NO reusar para fiscal
```

## Code style — Backend

- **DDD Inside-Out:** domain (puro, sin sqlalchemy/fastapi) → infrastructure → application → api (thin).
- **SQLA 2.0:** `select(Model).where(...)`. NUNCA `session.query()`. Async (`AsyncSession`).
- **Modelo clinic_model.py:** mantener estilo `Column()` existente (NO mezclar `mapped_column` en el mismo archivo).
- **Pydantic v2:** `model_config = ConfigDict(from_attributes=True)`. Sin `class Config` interno. Sin `Any`/dicts mágicos.
- **response_model=** en CADA route (arch test bloquea). Errores: `{"field": ..., "message": ...}` Spanish neutro.
- **tenant_id** filtra TODA query (incl. get_active_for_tenant). Cross-tenant → 404.
- **Audit log:** `AsyncAuditWriter.write(...)` SYNC pre-response en PATCH. payload sin PHI (solo identity fields cambiados).
- **Migration:** raw SQL `IF NOT EXISTS`. `down_revision` vía `alembic current` (HB-37 — NO hardcodear de memoria). NO `op.add_column`/`sa.Enum`.
- **structlog**, no `print`/`logging`.
- **Transaction boundary:** clinic fields + config_json specialties en mismo commit (atomic). Event best-effort `try/except`.

## Code style — Frontend

- **Server-First:** `page.tsx` Server Components (SSR initial state). `"use client"` línea 1 SOLO en views hoja (`AccountDataView`, `PreferencesView`).
- **N3-static:** `config/cuenta` usa SubSubTabsBar (`AGENT_SUBSUBTABS["config.cuenta"]` en `shell-routes.ts`). NUNCA Shadcn `<Tabs>` body para las 3 vistas (Nivel 4 anti-pattern, ADR-vitalia-004 v1.1).
- **Design canon HARD (`@luana/ui-kit`):**
  - `Select` canónico (timezone via `timezone-select`, currency via `currency-selector`). ❌ `<select>` nativo.
  - `Group` + `FloatingAutosaveIndicator` (UNA por página). ❌ badge por-grupo.
  - `PageContainer`/`PageContentStack`/`PageHeader`. ❌ `<div p-4/p-6>` sueltos.
  - Franjas N3 full-bleed (no card redondeada). Tokens, ❌ arbitrary-values (hex/spacing).
- **Autosave:** `use-autosave` (hook existente) 600ms + coalesce. ❌ botón "Guardar".
- **tenant_id:** `useTenantId()`. ❌ `useAuth().orgId` (`test-no-clerk-organizations` enforce).
- **camelCase exact mirror:** los TS types = mirror EXACTO de los Pydantic DTOs (§ 5). Camelizar en fetch boundary. ❌ campos imaginados (lección embudo HB-42).
- **React Query** server data + **Zustand** UI state (sin mezclar). **RHF + Zod** forms.
- **Spanish neutro LatAm** (sin voseo). Strings centralizados (`test_no_hardcoded_strings`).
- **No `any`** (`unknown` + type guards). No default exports (excepto Next pages).

## Live-verify gate (DoD #37 — mandatory antes de done)

Ninguna parte llega a `done` sin ejercer la acción real en dev-app:
- Admin autenticado edita CUIT válido → autosave → POST 200 → reload → persiste + audit_log row en logs.
- Admin edita especialidad → config_json.primary_specialties actualizado + reload observa valor.
- `dod_evidence` poblado en checkpoint (writes ejercidos + efecto + backend_log).

## Anti-patterns prohibidos (esta story)

- ❌ Agregar columna `specialties`/`clinic_type` a `vitalia_clinic_branches` (SSoT es `tenant.config_json` — drift).
- ❌ Hacer `ClinicRepository` heredar `PhiRepositoryBase` (clinic = non-PHI; rationale en 03-arch § Architecture Decisions).
- ❌ Reusar `credential_validator.py` (médico) para fiscal-id (semántica distinta — NEW acotado).
- ❌ Mount/editar router engine tenant-profile (consumir read-only; write brand-local).
- ❌ Shadcn `<Tabs>` body para las 3 sub-sub-tabs (usar SubSubTabsBar N3-static).
- ❌ `<select>` nativo / arbitrary-values / `<div>` de layout (canon HARD).
- ❌ FE type con campo que el BE no emite (registrar CONTRACT_PAIR primero).
- ❌ e2e que mockea el BE del surface (falso verde — lección lisa-marca).
