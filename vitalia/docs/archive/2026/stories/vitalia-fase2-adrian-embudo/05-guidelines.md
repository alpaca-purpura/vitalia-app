---
story_id: vitalia-fase2-adrian-embudo
schema_version: v4.1
generated_by: /architect
generated_on: 2026-06-03
---

# 05-guidelines.md — Embudo de Adrián

> Patterns required/forbidden + files in scope + files NEVER touch + skills enforceable. Consumido por builders.

## Patterns REQUIRED

### Backend (`builder-backend`)
- **EXTEND crm, NO crear `sales_pipeline`** (Chris ratificó). Lead = non-PHI → single `tenant_id` filter; funnel repos NO heredan `PhiRepositoryBase`.
- **PII pgcrypto preservado** en `vitalia_leads.{name,email,phone,notes}` (encrypt on write, decrypt on read via KEK). Columnas funnel = plaintext NO-PII.
- **SA 2.0** `select(Model).where(...)` async. NUNCA `session.query()`.
- **Pydantic v2** `model_config = ConfigDict(from_attributes=True)`. Tipos explícitos, NO `Any`.
- **`response_model=` en cada route**. `X-Tenant-ID` mandatory (non-PHI → X-Clinic-ID opcional, `_resolve_context_sync`).
- **Optimistic lock** vía `version` (raw SQL `WHERE version = :expected` → rowcount 0 = 409).
- **Migration idempotent raw SQL** `IF NOT EXISTS`. NUNCA `op.create_table()` / `sa.Enum(create_type=True)`. Campo `reason TEXT` (NO `notes` → evita falso positivo arch test PHI).
- **Audit log sync write** en transiciones (`AuditLogRepository` existente; business event, no PHI dual-filter).
- **Stage machine determinista** (`funnel_machine.py` SSoT: allowed_next/SLA/freeze). Score glass-box SIN ML.
- **structlog** (no print/logging). Telemetry `vitalia_growth_studio_event` bucketed (no PHI).
- **Cross-module crm↔sales_agent vía domain event** (`lead_stage_overridden` outbox), NUNCA import directo.

### Frontend (`builder-frontend`)
- **REUSE > NEW**: EntitySubNavBar, TogglePill, EmptyState, PiiMaskedSpan, ChannelBadge(extend), @dnd-kit, fetchClient/hooks (ver `03-arch-fe.md § REUSE`).
- **Server Component default**; `"use client"` solo en root views + interactivos.
- **React Query** server data + **Zustand** UI state (NUNCA mezclar). RQ keys `[module,subtab,action,...filters]`.
- **RHF + Zod** forms. Toast `sonner`. NO `alert()`/`window.confirm()`.
- **Tokens de `globals.css`** — NUNCA hardcode HSL. Colores de canal/red social vía `channel-meta` registry (CSS vars).
- **Fidelidad mockup** `embudo-v3.html` + D.0–D.16. Wrapper shell portado verbatim (NO reinventar).
- **a11y**: ScoreDonut número visible, SLA texto `Xd`, EntitySubNavBar role=tablist, drag KeyboardSensor + aria-live, contraste ≥4.5:1.
- **`leadId` = UUID en URL** (RN-16, no PHI). `tenant_id` de `useTenantId()` (NUNCA `useAuth().orgId`).
- **base.ts anti-burbuja** en todo Playwright spec (NO `@playwright/test` directo).

### Agentic (`builder-agentic`, R23 Opus)
- **NO modificar `agent_state_checkpoints` schema** (§3 protected, engine-owned). `override_context` brand-local en `vitalia_lead_stage_transition.reason`.
- **NO crear tool nuevo** ni grafo nuevo. El wire es un **subscriber de domain event** (`lead_stage_overridden`) que escribe contexto donde el próximo turno del agente lo lee.
- **NO importar `crm/` desde `sales_agent/`** (cross-module). Recibir vía evento/port.
- Spanish neutro en harness; output del agente respeta voz tenant (excepción sales-agent).

## Patterns FORBIDDEN

- ❌ Crear `sales_pipeline` module (EXTEND crm).
- ❌ Funnel repo heredando `PhiRepositoryBase` (Lead non-PHI).
- ❌ Renderizar datos clínicos del paciente en el Historial del embudo (RN-2 firewall; el link al Inbox PHI-gated abre la conversación real allá).
- ❌ Montar el router engine `closer_studio` (sync/auth mismatch). Reimplementar brand-local sobre read-model.
- ❌ Añadir columna a `agent_state_checkpoints` (engine lift = `/pm-luana`, fuera de scope).
- ❌ Mirror cross-brand (no existe en comunify/nicolify/lupulo — no recrear allá).
- ❌ Hardcode HSL / `'USD'` / `datetime.utcnow()` / `op.create_table()`.
- ❌ `→reservado` por drag/manual (RN-4/5 → 403). Reservado = webhook depósito.
- ❌ Drag reordena dentro de columna (RN-17: drag solo cambia columna; orden = antigüedad-en-etapa).
- ❌ Shadcn `Tabs` internas en body para Resumen/Historial (vistas en EntitySubNavBar, opción C).
- ❌ Modal (`Dialog`) para nuevo lead (ruta-hoja `/nuevo`). `OverrideReasonDialog` SÍ usa overlay (es transitorio, no navegable).
- ❌ e2e que mockea el backend presentado como live-verify (DoD #37 — falso verde).

## Files IN scope (brand-scoped vitalia/)

### BE
`vitalia/backend/src/modules/vitalia/crm/{domain,application,infrastructure,api}/**` (extend lead, new funnel) + `vitalia/backend/alembic/versions/{rev}_adrian_embudo_funnel.py` + `vitalia/backend/tests/modules/vitalia/crm/**` + `vitalia/backend/tests/architecture/` (EXTEND ratchet).
### FE
`vitalia/frontend/src/features/adrian/{components/embudo,components/recuperar,api,hooks,store,types}/**` + `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/{embudo,recuperar}/**` + `vitalia/frontend/src/components/shared/score/ScoreDonut.tsx` + `vitalia/frontend/src/lib/channels/channel-meta.ts` + `vitalia/frontend/src/components/shared/shell-organism/ChannelBadge.tsx` (EXTEND) + `vitalia/frontend/src/lib/shell-routes.ts` (agregar subtabs si falta) + `vitalia/frontend/src/features/adrian/index.ts` + `vitalia/frontend/src/features/crm-shared/types.ts` (extend Lead) + `vitalia/frontend/src/mocks/handlers/embudo.ts` + `vitalia/frontend/e2e/shell-organism/embudo-*.spec.ts` + `recuperar.spec.ts` + `e2e/pages/{EmbudoBoardPage,LeadWorkspacePage,NewLeadPage,RecuperarPage}.ts`.
### AGENTIC
`vitalia/backend/src/modules/vitalia/sales_agent/application/services/override_context_wire.py` + subscriber + `vitalia/backend/tests/modules/vitalia/sales_agent/test_manual_override_feeds_agent_context.py`.

## Files NEVER touch

- ❌ `core/luana-core-*/src/**` (engine — read-only; modificar = `/pm-luana` promotion). Incluye `agent_state_checkpoints`, `closer_studio`, `lifecycle_transitions`.
- ❌ `vitalia/backend/src/modules/vitalia/sales_agent/` runtime/LangGraph/prompts/specialists (salvo el wire/subscriber brand-extension nuevo — production_code R23 Opus, ticket T-AG-1).
- ❌ `vitalia/frontend/src/components/ui/**` (Shadcn primitives — copy-paste, no editar).
- ❌ `vitalia/frontend/src/components/shared/shell-organism/{EntitySubNavBar,TopBarGlobal,Ribbon,SubTabsBar,ValeriaSidebar}.tsx` (reuse verbatim; bug → `vitalia/docs/observed-bugs/`).
- ❌ Otros brands (`comunify/`, `nicolify/`, `lupulo/`).
- ❌ Otras features (`features/{lisa,mateo,valeria,lucas,camila}/**`).

## must_load_skills (enforceable per ticket)

| Ticket surface | must_load_skills |
|---|---|
| BE funnel | `backend-expert` + rules `{tenant-isolation, backend-ddd, backend-migrations}` + `vitalia/.claude/rules/hipaa-lite.md` (Lead non-PHI → solo tenant+audit) |
| FE | `frontend-expert` + **`vitalia-design-system`** (SSoT shell+átomos+tokens — OBLIGATORIO) + rules `{frontend-fsd, frontend-visual-fidelity}` |
| AGENTIC | `sales-agent-expert` + rule `anti-duplication` (consumo engine, no recrear) + R23 Opus |
| E2E | `playwright-expert` (Clerk auth, base.ts, POMs) |
| Cross-cutting (todos) | `definition-of-done-live-verify`, `test-design-doctrine`, `anti-orphan-integration`, `anti-duplication` |
