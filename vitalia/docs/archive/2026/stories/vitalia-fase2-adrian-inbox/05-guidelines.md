---
story_id: vitalia-fase2-adrian-inbox
brand: vitalia
architecture_pattern: ADR-vitalia-004
---

# 05-guidelines — vitalia-fase2-adrian-inbox

> Guía enforceable para builders. Esta story es **MIGRACIÓN + consolidación + un-stub**, no build virgen. La disciplina nº 1: **no dejar dos sets de inbox conviviendo** y **no tocar el engine ni el runtime sales_agent**.

## must_load_skills (por surface — enforceable)

| Surface | Skills obligatorios (cargar ANTES de codear) |
|---|---|
| BE (`inbox/`) | `backend-expert` + (consultar) `sales-agent-expert` § anti-duplication (consume tool, no import) + `copilot-expert` (activity-stream consume trace, no recorder nuevo) |
| FE (`features/adrian/`, `app/.../adrian/inbox/`, `ChannelBadge`) | `frontend-expert` + **`vitalia-design-system`** (★ SSoT shell/tokens/splitter — sin esto el wrapper se reinventa) |

## Files in scope (TOCAR)

```
BE:
  vitalia/backend/src/modules/vitalia/inbox/api/router.py                      MODIFY (wire ComplianceService real + nudge endpoint)
  vitalia/backend/src/modules/vitalia/inbox/application/services/nudge_service.py   NEW
  vitalia/backend/src/modules/vitalia/inbox/application/policies/phi_channel_policy.py  NEW
  vitalia/backend/src/modules/vitalia/inbox/application/dto/nudge_dto.py        NEW
  vitalia/backend/tests/modules/vitalia/inbox/**                               NEW + fill stubs + regression_guard

FE:
  vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx    NEW
  vitalia/frontend/src/features/adrian/components/inbox/**                       MIGRATE+MERGE+NEW
  vitalia/frontend/src/features/adrian/{api,hooks,store,types}/**               MIGRATE+NEW
  vitalia/frontend/src/features/adrian/index.ts                                 MODIFY (barrel)
  vitalia/frontend/src/components/shared/shell-organism/ChannelBadge.tsx        NEW
  vitalia/frontend/src/lib/agent-catalog.ts                                     MODIFY (SHIPPED_STATIC_SUBTABS += adrian.inbox)
  vitalia/frontend/src/features/inbox/                                          DELETE (todo el directorio)
  vitalia/frontend/e2e/shell-organism/adrian-inbox-*.spec.ts                    NEW
  vitalia/frontend/e2e/pages/AdrianInboxPage.ts                                 NEW
```

## NEVER touch (HARD)

- ❌ `core/luana-core-*/src/**` — engine read-only. Necesidad genuina → `/pm-luana` promotion proposal (NO ticket).
- ❌ `vitalia/backend/src/modules/vitalia/sales_agent/**` (runtime/domain/tools/prompts) — CONSUME vía service resolver. Necesidad de tocar un tool/prompt → `/pm-vitalia` (NO ticket).
- ❌ `vitalia/backend/src/modules/vitalia/copilot/**` runtime.
- ❌ `vitalia/frontend/src/components/ui/**` (Shadcn primitives — copy-paste local existente).
- ❌ `vitalia/frontend/src/components/shared/shell-organism/{ShellOrganismLayout,ValeriaSidebar,Ribbon,SubTabsBar,EmptyState,SubSubTabsBar}.tsx` (wrapper — REUSE, solo consumir/montar).
- ❌ `vitalia/frontend/src/stores/shell-store.ts` (consume `setValeriaState`, NO modifica el store).
- ❌ `vitalia_conversations` schema (modelo cubre 3-modos; sin migración).

## Patterns REQUIRED

### BE
- Consume `ComplianceService.check()` del engine (`core/luana-core-compliance`). `PhiChannelPolicy` implementa el `CompliancePolicy` Protocol — extensión, NO mirror.
- `NudgeService` consume `send_proactive_reengagement` vía **service resolver** (mismo patrón que el tool), nunca `import` de `sales_agent/`.
- Dual filter `tenant_id + clinic_id` en toda query (`CompoundScopeRepositoryBase`). Audit sync write pre-response. `response_model=` en el endpoint nudge. SA 2.0 (`select().where()`). Soft delete. `structlog` (no print/logging).
- Idempotency: nudge con `idempotency_key` + dedup natural key `(tenant, conv, 'nudge', day)`.
- Pydantic v2 `model_config = ConfigDict(...)`. Sin `Any`.

### FE
- Ruta `adrian/inbox/page.tsx` = mirror de `mateo/agenda/page.tsx` (RSC, async params, `getInitialInboxState` SSR, graceful degradation, `initialData` props).
- 3-pane = `ResizablePanelGroup` (Shadcn `resizable.tsx` REUSE). 100% del panel, sin `max-width`.
- 3-modos = segmented control / `RadioGroup` (NUNCA Shadcn `<Tabs>` — anti-pattern N3/N4). Mapping `{decide→ai+false, consulta→ai+true, manual→human+false}`.
- Modo conversación: guarda `priorValeriaState` en `inbox-store` + `useShellStore.setValeriaState('collapsed')` / restore. `useShellStore` = SSoT REUSE.
- React Query = server data (keys `['adrian','inbox',...]`). Zustand `inbox-store` = UI. `useSearchParams` = conv/filter. Split estricto.
- Polling: lista 10s, activity-stream 5s (solo expandido).
- ChannelBadge → `shared/shell-organism/` (reusable). Tokens `--agent-adrian`/`--agent-adrian-soft` (sin colores hardcoded).
- PHI: `PiiMaskedSpan` + `RequireRole` en ContactSidebar. PHI nunca en URL (solo `conv` UUID).
- Spanish neutro en chrome (microcopy SSoT spec § Microcopy). Output Adrián = voz tenant.
- TDD RED-first. e2e importan `e2e/fixtures/base.ts` (anti-burbuja). NO `@playwright/test` directo en specs autenticados.

## Patterns FORBIDDEN

- ❌ Crear un layer de compliance/llm/cache/router nuevo (NO-NEW-LAYER — consume engine).
- ❌ Dos sets de inbox coexistiendo (DELETE `features/inbox/` en T-4, mismo PR de consolidación).
- ❌ `import` cross-feature (`features/adrian` ← `features/lisa`/`mateo`) ni cross-brand.
- ❌ Reinventar el wrapper shell (port verbatim / REUSE).
- ❌ Shadcn `<Tabs>` para 3-modos o sub-secciones.
- ❌ Colores hardcoded / voseo en chrome / PHI en URL / `datetime.utcnow()`.
- ❌ Endpoint sin `response_model=` / sin dual filter / sin audit sync.
- ❌ Flipear defaults de feature flags (no aplica).
- ❌ Olvidar `SHIPPED_STATIC_SUBTABS += adrian.inbox` (→ ruta isla).
- ❌ e2e que mockea el backend del surface presentado como live-verify (DoD #37 — falso verde).
- ❌ Tocar `core/` o `sales_agent/` runtime (escalar, no ticketear).

## Consolidation discipline (★ lo más importante)

1. MIGRATE la lógica rica de `features/inbox/` → `features/adrian/components/inbox/` (ver 03-arch.md § 9.1).
2. MERGE con la versión parity (`features/adrian/.../inbox/`) — quedarse con la más rica, preservar API pública que el shell consume (ver § 9.2).
3. Crear las piezas NEW (§ 9.4).
4. DELETE `features/inbox/` en el MISMO PR (§ 9.3) — el gate `av-no-orphan-inbox` valida que el directorio NO exista.
5. Mover los Vitest co-located junto a su componente (regression_guard — mantener verdes).

## DoD (Critical Rule #37) — live-verify

- Demo manual obligatorio (`demo_required: true`). Producir `demo-script.md` (SETUP/HAPPY/EDGE/TEARDOWN) derivado de los SC.
- Live-verify contra dev-app vitalia (`make dev-app-vitalia` → dev-app.vitalialat.com, Chrome DevTools MCP) o localhost:3002: ejercer 3-modos (PATCH real + audit row), nudge (outbound + activity row), modo conversación (Valeria colapsa), PHI block (SC-3) — leer Console (0 errores) + Network + backend logs (sin traceback) + efecto en DB.
- `dod_evidence` en checkpoint.md. `demo_signoff` (Chris) = gate `reviewing → done`.
