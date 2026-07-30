---
story_id: vitalia-fase2-adrian-inbox
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
architect_run_on: 2026-06-03
state: ready
autonomous_mode: true
---

# 03-arch — vitalia-fase2-adrian-inbox (MIGRACIÓN + consolidación)

> **Naturaleza confirmada por exploración de código real (2026-06-03):** esto es una **migración + consolidación + un-stub + cableado**, NO un build virgen. El backend inbox YA tiene 8 endpoints shipped (slice-1), el modelo de datos `vitalia_conversations` con `handler_mode`/OCC/`pause_until` YA existe, el `ConversationRepository.list_for_inbox()` con dual filter YA existe, y ~40 componentes FE shipped viven huérfanos en `features/inbox/`. El trabajo real: (1) un-stub la `ComplianceService` real en el path de envío (RN-7/AC-9/SC-3), (2) agregar el endpoint **nudge** (gap genuino), (3) consolidar `features/inbox/` → `features/adrian/components/inbox/` + borrar el huérfano, (4) crear las piezas NEW (`AdrianInboxView` 3-pane, `ConversationModeButton`, `ChannelBadge`, `ToolCallCard`, `NudgeButton`, Valeria-reacciona), (5) crear la ruta real `adrian/inbox/page.tsx` + registrar `adrian.inbox` en los catálogos shell.

---

## § 0. Context Summary

- **Story:** F2-S3 · `vitalia-fase2-adrian-inbox` · release F3 · módulo `inbox` · cap_target `adrian.inbox` (NEW) · map zone `agentes` → box `adrian`.
- **Architect run on:** 2026-06-03 (`date -u +%Y-%m-%d`).
- **Knowledge cutoff disclosure:** Opus 4.8 cutoff = enero 2026. Patrones SSR/React-Query/Next-16 verificados live vía WebSearch 2026-06-03 (ver § 15). LangGraph/sales_agent/copilot = **consume-only** (no se diseñan acá; runtime vive en `core/`).
- **Módulos tocados:** `vitalia/backend/src/modules/vitalia/inbox/` (un-stub + nudge), `vitalia/frontend/src/features/adrian/` (consolidación + piezas NEW), `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/inbox/` (ruta NEW), `vitalia/frontend/src/lib/{shell-routes.ts, agent-catalog.ts}` (registro), `vitalia/frontend/src/features/inbox/` (DELETE), `vitalia/frontend/src/components/shared/shell-organism/ChannelBadge.tsx` (NEW reusable).

### Surface → builder → auditor mapping (★ /dev-team usa esto para spawnear)

| Surface | Builder | Auditor |
|---|---|---|
| `backend/src/modules/vitalia/inbox/{application,api}/**` (un-stub ComplianceService + nudge endpoint + tests) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `frontend/src/features/adrian/**` + `app/.../adrian/inbox/**` + `components/shared/shell-organism/ChannelBadge.tsx` + `lib/{shell-routes,agent-catalog}.ts` MODIFY + `features/inbox/` DELETE | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| **Agentic** (`copilot/`, `sales_agent/` runtime) | **NINGUNO** — consume-only (read-only). Sin AGENTIC production code en esta story. | n/a |

> **No hay superficie agéntica de producción.** El inbox CONSUME: (a) el runtime sales_agent vía el flujo de mensajes ya cableado, (b) el tool `send_proactive_reengagement` (brand, shipped) vía el endpoint nudge, (c) `copilot_trace_event` + `sanitize_payload` (observability engine) vía el activity-stream ya shipped. **Cero tickets editan `core/` o `sales_agent/` runtime.** Si surge necesidad genuina de tocar un tool/prompt sales_agent → escalar a `/pm-vitalia` (NO meterlo en un ticket).

### Skills consultados (decisión tomada, no contenido pegado)

- **backend-expert** — el módulo inbox ya es DDD Inside-Out correcto; un-stub = swap del `_NoOpComplianceService` por wiring real de `ComplianceService.check()` (engine), no nuevo layer. Nudge = nuevo service+endpoint reusando `ProactiveOutboundService` patrón.
- **frontend-expert** + **vitalia-design-system** (★ SSoT shell/tokens/splitter — CARGADO) — hogar canónico `features/adrian/components/inbox/`; reusar `useShellStore` (`valeriaState`), `resizable.tsx` (ResizablePanel), tokens `--agent-adrian`/`--agent-adrian-soft`. Wrapper shell = REUSE (no tocar).
- **sales-agent-expert** — `personality_profiles.system_instruction` = SSoT de voz (output de Adrián respeta voz tenant; el chrome del inbox = neutro). `send_proactive_reengagement` tool = consume vía servicio, NUNCA importar `sales_agent/` desde `inbox/`. §3 surfaces protegidas NO se tocan.
- **copilot-expert** — activity-stream consume `copilot_trace_event` + `sanitize_payload` (ya wired en `ActivityEventService`). Glass-box = read del trace, no recorder nuevo.
- **brand-expert / offer-expert / metrics-expert** — no aplican (sin cambios de brand/offer/analytics).

### CONTEXT-BRIEF source

- **Self-ran greps (Path B)** — no se generó `CONTEXT-BRIEF.md` (dispatch directo). Prior-art scan ya estaba en checkpoint.md § Prior art scan; lo extendí con exploración de código real (ver § Prior art audit).

### capability YAML + modules MD afectados (post-merge, /pm-vitalia Fase F.3)

- `vitalia/docs/product/capabilities/inbox/adrian.inbox.yaml` — **NEW** (cap_change_type=new): poblar `scenarios[]` (SC-1..SC-10) + `access` (RBAC doctor/nurse/admin_clinic) + `business_rules` (RN-1..RN-14) + `dev_preview` apuntando a `adrian/inbox/page.tsx`.
- `vitalia/docs/product/modules/inbox.md` — actualizar narrativa: inbox re-hogareado en shell-organism + 3-modos + nudge.

### Architecture gates que deben seguir verdes

- BE: `vitalia/backend/tests/architecture/{test_phi_dual_filter.py, test_audit_log_sync_write.py, test_response_model_required.py, test_growth_studio_event_no_phi.py}` + suite inbox existente (`tests/modules/vitalia/inbox/`).
- FE: `vitalia/frontend/src/__tests__/architecture/{test_no_hardcoded_strings_inbox.test.ts, test_no_hardcoded_colors.test.ts, test_no_phi_in_url_params (whitelist), test_no_cross_feature_imports.test.ts, test_fsd_boundaries.test.ts, test-agent-catalog-ssot.test.ts, test-no-cross-brand-shell-mirror.test.ts, test_server_first.test.ts, test-ribbon-no-shadcn-tabs.test.ts, test_phi_pii_components_used.test.ts}`.

---

## § 1. Surfaces

| Surface | Hoy | Esta story |
|---|---|---|
| BE inbox endpoints | 8 shipped (send, revert, **PATCH mode/OCC**, pause, tools, **activity-stream**, proactive-outbound, transcribe) con `_NoOp` stubs de compliance/rate-limiter | un-stub `ComplianceService.check()` real en send path (SC-3) + **nudge endpoint NEW** |
| BE conversation list | `GET /api/v1/vitalia/crm/conversations` + `/{id}` shipped (filtros + dual filter) | REUSE (verificar filtros faltantes: `unread`, `help_needed`, búsqueda) |
| Datos | `vitalia_conversations` (`handler_mode`, `proposal_required`, `pause_until`, `help_needed`, OCC `updated_at`) shipped | REUSE — sin migración nueva (modelo cubre 3-modos) |
| FE inbox rico | `features/inbox/` (~40 comps + hooks RQ + store) huérfano (page borrado) | MIGRATE → `features/adrian/components/inbox/` + DELETE huérfano |
| FE inbox parity | `features/adrian/components/inbox/` (8 comps simples) | MERGE con la versión rica |
| FE ruta | genérico `[agent]/[subtab]/page.tsx` → `InboxPlaceholder` | NEW `adrian/inbox/page.tsx` (mirror de `mateo/agenda/page.tsx`) |
| FE catálogo shell | `agent-catalog.ts` ya tiene `adrian.inbox` subtab; falta en `SHIPPED_STATIC_SUBTABS` | MODIFY: registrar `adrian.inbox` |
| Agentic runtime | `core/luana-core-sales-agent` + brand tools shipped | CONSUME read-only (cero edición) |

---

## § 2. FE arch (detalle en `03-arch-fe.md`)

Resumen (full en `03-arch-fe.md`):

- **Ruta:** `app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx` (RSC) — mirror exacto de `mateo/agenda/page.tsx`: `await params/searchParams`, resuelve `conv`+`filter`, llama `getInitialInboxState()` SSR (graceful degradation), pasa `initialData` a `AdrianInboxView` (client root).
- **Deep-link primario = `?conv={id}` searchParam** (RN-14). El thread es el panel central siempre-visible del 3-pane (NO un overlay/drawer interceptado como embudo — la naturaleza 3-pane lo distingue). `[conv-id]/page.tsx` N3-dyn es **opcional/diferido** (el searchParam cubre AC-3/RN-14; declararlo solo si el equipo decide ruta directa-a-conv). PHI nunca en URL — solo `conv_id` (UUID, no datos).
- **Client root** `AdrianInboxView.tsx` (`"use client"` línea 1): compone `ResizablePanelGroup` 3-cols (`InboxConvList 320` · `InboxThread 1fr` · `ContactSidebar 320`), integra modo conversación vía `useShellStore`, monta `useInboxConversations`/`useConversationDetail`/`useActivityStream` (React Query, hidratados con `initialData`).
- **3-modos → backend mapping** (★ clave de la consolidación): el modelo BE tiene `handler_mode ∈ {ai, human}` + `proposal_required: bool`. El toggle UI de 3 estados mapea así:
  - `decide` → `handler_mode='ai'`, `proposal_required=false`
  - `consulta` → `handler_mode='ai'`, `proposal_required=true`
  - `manual` ("Yo escribo") → `handler_mode='human'`, `proposal_required=false`
  - La mutación `useSetMode` envía `PATCH /mode` con `{mode, proposal_required, expected_updated_at}` (OCC) — endpoint shipped. Optimistic update + rollback en 409 (SC-4).
- **Modo conversación (`ConversationModeButton`):** al pulsar full → guarda `priorValeriaState = useShellStore.valeriaState` (en `inbox-store` Zustand) + `setValeriaState('collapsed')`; al re-pulsar → `setValeriaState(priorValeriaState)`. Inbox al 100% sin `max-width` (RN-11/RN-12). El botón en sí es local al inbox; el `useShellStore` es el SSoT (REUSE, no modificar).
- **Valeria-reacciona (básica):** hook `useValeriaReaccion(convId)` en `AdrianInboxView` que, al abrir conv, hace un POST best-effort al chat de Valeria con contexto del lead + recibe 1-2 acciones sugeridas que se pintan en `ValeriaChat`/sidebar. MVP: degradación graciosa (si falla, no rompe el thread).
- **Polling:** lista refetch 10s (`refetchInterval`); activity-stream 5s solo cuando expandido. WebSocket diferido post-MVP.
- **Estado:** React Query = server data (SSoT). Zustand `inbox-store` = UI state (sidebar abierto, activity expanded, `priorValeriaState`, attach queue). `useShellStore` = valeriaState (REUSE). Nunca mezclar.
- **ChannelBadge** → `components/shared/shell-organism/ChannelBadge.tsx` (NEW, reusable cross-feature; lift candidate brand-local; escalar `/pm-luana` solo si aparece en ≥2 brands — NO ahora).
- **Anti-burbuja:** todos los e2e importan de `e2e/fixtures/base.ts` (existe). Runtime-error gate obligatorio.

---

## § 3. BE arch (detalle en `03-arch-be.md`)

Resumen (full en `03-arch-be.md`):

- **NO hay migración nueva.** `vitalia_conversations` cubre los 3-modos (`handler_mode` + `proposal_required` + `pause_until`). Verificado en `conversation_model.py`.
- **Un-stub ComplianceService (SC-3/AC-9/RN-7) — el trabajo BE central:**
  - Hoy `SendMessageService` recibe (vía `ProactiveOutboundService`) un `_NoOpComplianceService.validate_outbound_message(...)` que deja pasar todo.
  - El engine real es `core/luana-core-compliance` `ComplianceService.check(...)` → `CheckResult(allowed: bool, failed_policy)` con short-circuit de policies (WABA24h → OptIn → Blacklist → CountryBlock). **Consumir, no recrear** (anti-duplication).
  - **Diseño:** una `PhiChannelPolicy` (brand-local en `vitalia/.../compliance/` o `inbox/application/policies/`) que implementa el `CompliancePolicy` Protocol del engine: detecta intención de resultados clínicos por canal no-encriptado (WhatsApp free/SMS) → `CheckResult(allowed=False, failed_policy='phi_unencrypted_channel')`. El send path llama `ComplianceService.check(...)`; si `allowed=False` → reemplaza el outbound por el redirect a portal (microcopy SSoT) + escribe activity event `compliance_block_outbound_phi` + audit row `compliance_block_outbound_phi`.
  - **Wiring DI:** `_get_send_service` / `_get_proactive_service` inyectan el `ComplianceService` real (lista de policies que incluye `PhiChannelPolicy`) en vez del `_NoOp`.
- **Nudge endpoint (gap genuino):**
  - `POST /api/v1/vitalia/inbox/conversations/{conv_id}/nudge` → `NudgeService.nudge(...)`.
  - Consume el patrón de `ProactiveOutboundService` pero scoped a UNA conv viva estancada (RN-13). NO crea conv nueva. NO reactiva lead frío. El re-enganche respeta voz del tenant (consume `send_proactive_reengagement` vía resolver de servicio — NUNCA import directo de `sales_agent/`).
  - Escribe activity event `nudge_sent` + audit row. Dual filter `tenant_id+clinic_id`. `response_model=` mandatorio. PHI-gated (doctor/nurse/admin_clinic).
- **Conversation list filters:** verificar contra `ConversationListFilters` (existe: `status`, `channel`, `handler_mode`, `help_needed`, `unread_media`, `limit/offset`). Gaps a cubrir si faltan para AC-2: filtro "Sin leer" (`unread_media`/`unread_count`), "Asignadas a mí" (requiere `assigned_user_id` — si no existe, diferir o derivar), "Esperando humano" (`proposal_required=true` + sin respuesta humana > 2min → derivable en query). Búsqueda (`search` por nombre masked/snippet) — agregar si falta.
- **Activity stream:** `ActivityEventService.get_stream()` shipped, sirve sanitizado vía `sanitize_payload`. REUSE. Verificar que el nudge + compliance-block emitan activity events legibles (descriptions_es).
- **Idempotencia:** `send_message` ya recibe `idempotency_key`. El nudge debe aceptar `idempotency_key` (header o body) — dedup por `(tenant, conv, 'nudge', day)` natural key para evitar doble-empujón.
- **Outbox:** mode/nudge/compliance-block emiten eventos vía `adapter_bus` (outbox pattern, ya cableado). NO flipear defaults (ver § 9.5 — no aplica).

---

## § 4. Cross-cutting concerns

- **Tenant isolation + HIPAA-lite dual filter:** TODA query inbox filtra `tenant_id` AND `clinic_id` (`ConversationRepository` hereda `CompoundScopeRepositoryBase scope_field='clinic_id'`). Cross-tenant → 404 (SC-10). Cross-clinic → 403.
- **Audit log sync write:** todo cambio de modo, takeover, pause, nudge, compliance-block escribe `audit_log` row ANTES de la response (RN-2). Ya implementado en `SetModeService`/`PauseAdrianService`; nudge + compliance-block deben replicar.
- **PII / PHI:** `response_model=` en cada endpoint (gate). ContactSidebar usa `PiiMaskedSpan` + `RequireRole` (RN-8). Activity stream vía `sanitize_payload` (RN-10). PHI nunca en URL (RN-14, searchParams whitelist). Lead = comercial (non-PHI); identidad de paciente = PHI (firewall).
- **Currency / master-data:** sin campos monetarios directos en el inbox chrome (los montos viven en propuestas/pagos, link-out). Fechas display vía `formatTenantDate*()` (timestamps relativos). UTC store.
- **Spanish neutro LatAm:** chrome del inbox = neutro (microcopy SSoT en spec § Microcopy). **Excepción:** output de Adrián (mensajes al paciente) respeta `personality_profiles.system_instruction` (voz tenant, puede ser voseo AR).
- **Native-first:** todos los gates corren native Linux host. FE :3002 / BE :8002. Nunca `docker exec` para lint/tests.

---

## § 4b. Architecture Decisions (★ amendment 2026-06-04 · scope ampliado durante el build, live-verified + firmado por Chris)

> El build cambió el paradigma de atención de **3 modos** a **2 modos** y destapó 2 bombas de wiring FE↔BE que nunca se habían ejercido (modo + pausa). Estas decisiones son **intencionales** y `adr_004_compliance` sigue `full`. El auditor NO debe revertirlas; la doc (01-spec/04-validators) ya está reconciliada. SSoT de evidencia: `checkpoint.md::ui_polish_dod_evidence_2026_06_04_pm7..pm9` + `HANDOFF-audit-ready-r6-r8.md`.

| # | Decisión | Por qué | Surface |
|---|---|---|---|
| AD-1 | **2-modos** (`Adrián decide`/`Adrián consulta`), "Yo escribo" eliminado | Manual ≡ pausar (un solo concepto operativo, menos confusión). `ModeToggle` = `role=radiogroup` 2 segmentos; activo verde; OCC via `expected_updated_at` en **body** (no header). | FE `ModeToggle` + `use-mode-toggle` (`SEGMENT_TO_API`); BE `PATCH …/mode` |
| AD-2 | **RBAC `_INBOX_OPERATOR_ROLES`** = `_PHI_ROLES ∪ {owner, receptionist}` para TODAS las mutaciones del inbox | El inbox es la herramienta del operador (dueño/recepción), no solo del clínico. `dr.demo`=owner debía poder actuar (antes 403). Mismo set que Chris ratificó para list/detail. marketing/sales/patient siguen 403. | BE `inbox/api/router.py::_assert_phi_access` |
| AD-3 | **`ConversationRepository.set_pause_until`** (crm) + **`_NoOpRedisClient.setex`** (dev sin Redis) | La pausa nunca se había ejercido live → 500 latente (repo sin método + NoOp sin `setex`). El `pause_until` persiste en DB (fuente de verdad); Redis es solo fast-path. | BE `crm/infrastructure/persistence/conversation_repository.py` + `inbox/api/router.py` |
| AD-4 | **Query-keys crm-shared** en mode/pause/send | El thread/lista leen `['crm','conversation',id]` / `['crm','conversations']`; las mutaciones invalidaban las legacy `['adrian','inbox',…]` que nadie renderiza → el 200 nunca reflejaba en UI. Migrados a las keys reales. | FE `use-set-mode` / `use-pause-adrian` / `use-send-message` |
| AD-5 | **`PiiMaskedSpan.masked`** (default `true`) + `ContactSidebar masked={false}` | Leads visibles por defecto (interim ratificado Chris) sin romper el resto de la app ni el gate FE-A6: el wrapper + `data-phi` se conservan; solo se rinde el valor crudo en la ficha de lead. PHI clínica sigue fuera de Adrián (firewall RN-7). | FE `components/shared/phi/PiiMaskedSpan.tsx` + `ContactSidebar` |
| AD-6 | **ThreadComposerDock** (composer siempre montado al pie) + Pausa 60/permanente sin reason | "No salía la caja" = `ComposerArea` existía pero `InboxThread` no la montaba. Ahora dock con barra de estado (dot verde intermitente) + `PauseAdrianButton`(rojo) + composer. Permanente = far-future (~100 años; flag indefinido real = follow-up BE). | FE `InboxThread` (dock) + `ComposerArea` + `PauseAdrianConfirmModal` (`pause-modal-60`/`pause-modal-permanent`) |
| AD-7 | **UI**: wallpaper crema **fijo** (no scrollea), 🛠 tools fuera del header (actividad → `ActivityStream` inferior), "Estado" duplicado eliminado (queda "Etapa de la venta"), "Servicio de interés" siempre visible | Feedback de Chris r6–r8; el wallpaper en wrapper no-scrolleable evita el blanco bajo los mensajes; tools-icon redundante con el glass-box inferior. | FE `InboxThread`/`ThreadHeader`/`ContactSidebar` + `globals.css` (`--vt-watermark-ink`) |

**No cambió:** `ADR-vitalia-004` (route group + FSD-Lite + Server-First + RQ + Zustand + `PhiRepositoryBase` dual filter + audit sync write + `vitalia_growth_studio_event` + tests 4 capas) sigue `full`. § 6 Integration design (CONN) sigue válida. § Cross-cutting (audit sync, sanitize, response_model) intacto. **Full-canvas/responsive (RN-11/12/AC-7/AC-12)** = spliteado a `vitalia-bugfix-shell-nav-scroll-errors` (`done`).

---

## § 5. Prior art audit (NO-NEW-LAYER rule)

### Source of evidence
- [ ] CONTEXT-BRIEF.md § 7 + § 8 (no generado)
- [x] Self-run greps + exploración de código real (Path B)
- [x] Re-validación del prior-art scan de checkpoint.md contra el código vivo

### Audit cross-module ejecutado

```bash
# Inbox BE module — ya existe completo
find vitalia/backend/src/modules/vitalia/inbox -type f          # 8 endpoints + 7 services + DTOs
grep -n "validate_outbound\|_NoOpComplianceService" inbox/api/router.py  # stub a un-stub
# Compliance engine — NO recrear
grep -rln "class ComplianceService" core/luana-core-compliance/  # check() + CheckResult (engine SSoT)
# Conversation list + dual filter — ya existe
grep -n "list_for_inbox\|CompoundScopeRepositoryBase" crm/.../conversation_repository.py
# FE inbox — dos sets coexisten (huérfano + parity)
find vitalia/frontend/src/features/{inbox,adrian/components/inbox} -type f
# ChannelBadge — NO existe (crear)
find vitalia/frontend/src -iname "*channelbadge*"               # vacío
# shell store valeriaState — ya existe (REUSE)
grep -n "setValeriaState\|ValeriaState" vitalia/frontend/src/stores/shell-store.ts
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Inbox BE (8 endpoints + services) | `vitalia/backend/src/modules/vitalia/inbox/` | active (slice-1, con stubs) | **EXTEND** — un-stub compliance + add nudge endpoint |
| ComplianceService | `core/luana-core-compliance/.../compliance_service.py` (`check()` + policies Protocol) | active engine | **CONSUME** — implementar `PhiChannelPolicy` que cumple el Protocol; NO recrear el service |
| ConversationRepository.list_for_inbox + OCC | `crm/.../conversation_repository.py` (`CompoundScopeRepositoryBase`) | active | **REUSE** — verificar filtros faltantes |
| `send_proactive_reengagement` tool | `vitalia/.../sales_agent/tools/send_proactive_reengagement.py` | active (brand, shipped) | **CONSUME** vía service resolver (nudge); NO import directo |
| `copilot_trace_event` + `sanitize_payload` | `core/luana-core-observability/` (vía `ActivityEventService`) | active | **CONSUME** — activity stream ya wired |
| FE inbox rico (huérfano) | `vitalia/frontend/src/features/inbox/` (~40 comps + hooks + store) | orphan (page borrado) | **MIGRATE** → `features/adrian/components/inbox/` |
| FE inbox parity | `vitalia/frontend/src/features/adrian/components/inbox/` (8 comps) | active | **MERGE** con la versión rica |
| `useShellStore` (valeriaState) | `vitalia/frontend/src/stores/shell-store.ts` | active | **REUSE** — modo conversación lo consume |
| `resizable.tsx` (ResizablePanel) | `vitalia/frontend/src/components/ui/resizable.tsx` | active | **REUSE** — 3-pane |
| Wrapper shell (ShellOrganismLayout, ValeriaSidebar, Ribbon, SubTabsBar, EmptyState) | `components/shared/shell-organism/` | active | **REUSE** — NO tocar |
| ChannelBadge | (no existe) | — | **NEW** — `components/shared/shell-organism/ChannelBadge.tsx` |

### Decisión por sistema

- **Inbox BE:** EXTEND. El módulo es DDD correcto; el trabajo es swap de stub→real (compliance) + 1 endpoint+service (nudge). NO se crea layer paralelo.
- **ComplianceService:** CONSUME engine. La `PhiChannelPolicy` brand-local implementa el `CompliancePolicy` Protocol del engine — extensión legítima, no mirror. Inventario anti-duplication confirma: compliance gates viven en `core/luana-core-compliance/`.
- **FE consolidación:** MIGRATE+MERGE+DELETE. Dos sets de inbox NO pueden convivir (anti-duplicación). Hogar canónico = `features/adrian/components/inbox/`. El huérfano `features/inbox/` se borra en el mismo PR de consolidación (T-4).
- **Cross-brand mirror check:** ejecutado mentalmente — el inbox es vitalia-específico (HIPAA-lite, 3-modos paradigma vitalia). NO hay mirror en nicolify/comunify/lupulo que justifique lift. `ChannelBadge` es candidate brand-local; NO se lifta ahora (regla: ≥2 brands).
- **Cero edición de `core/` o `sales_agent/` runtime.** Si la `PhiChannelPolicy` revelara necesidad de un primitive nuevo en el engine compliance → escalar `/pm-luana` (NO ticket).

**Veredicto NO-NEW-LAYER:** sin violaciones. Todo es EXTEND/CONSUME/REUSE/MIGRATE. La única creación nueva (`ChannelBadge`, `NudgeService`, `PhiChannelPolicy`, piezas FE) no duplica nada existente.

---

## § 6. Integration design (CONN — anti-orphan, ninguna isla)

| Contención | Cómo se cumple |
|---|---|
| **C**onsumed (≥1 consumidor real) | La ruta `adrian/inbox` la consume el shell (Ribbon Adrián → SubTabsBar Inbox). El nudge endpoint lo consume `NudgeButton`. La activity-stream la consume `ActivityStream`. El mode endpoint lo consume `ModeToggle`. |
| **O**n the map (vive en un cap con hogar) | cap `adrian.inbox` (NEW) en zona `agentes` → box `adrian`. `dev_preview` → `adrian/inbox/page.tsx`. |
| **N**avigable/reachable | Ruta estática `adrian/inbox/page.tsx` registrada en `SHIPPED_STATIC_SUBTABS` (`adrian.inbox`) → toma precedencia sobre el dispatcher `[agent]/[subtab]`. `agent-catalog.ts` ya tiene `adrian.defaultSubtab='inbox'` + entry en RIBBON_SUBTABS. Reachability path: login → `mateo/agenda` (default) → Ribbon click Adrián → SubTabsBar Inbox → `/{tenant}/adrian/inbox`. |
| **N**otarized/registered | (1) `app.include_router(inbox_router, prefix="/api/v1/vitalia/inbox")` ya en `main.py` (nudge entra al mismo router → notarizado). (2) `SHIPPED_STATIC_SUBTABS += "adrian.inbox"` (FE). (3) `features/adrian/index.ts` exporta `AdrianInboxView` + `getInitialInboxState` (barrel). (4) `InboxPlaceholder` se des-wirea del uso activo (queda solo como fallback del dispatcher genérico si aplica). |

**Reachability path concreto:** `/{tenantId}/adrian/inbox?conv={id}&filter=todos` → `adrian/inbox/page.tsx` (static, precede dispatcher) → `getInitialInboxState` SSR → `AdrianInboxView`. Sin la entry en `SHIPPED_STATIC_SUBTABS`, el dispatcher dinámico la captaría → `InboxPlaceholder` (isla). El registro es OBLIGATORIO en el mismo PR (T-3).

---

## § 7. ADR-vitalia-004 compliance: full

| § | Sección ADR-004 | Cumplimiento |
|---|---|---|
| 3.1 | Routing route group | `adrian/inbox/page.tsx` static segment (precede dispatcher); RSC; `getInitialInboxState` SSR; searchParams `{conv, filter}` whitelist (PHI nunca en URL); `params`/`searchParams` Promise. **N3-static NO aplica** (inbox = 1 panel coherente 3-pane, no 3 vistas discretas → § 3.1.1 tabla: "single panel"). |
| 3.2 | FSD-Lite | `features/adrian/components/inbox/` + `api/` + `hooks/` + `store/` + `types/`. Sin cross-feature imports. Sin shell components en features (ChannelBadge va a `shared/shell-organism/`). |
| 3.3 | Client root | `AdrianInboxView.tsx` (`"use client"` línea 1, `initialData` props, hidrata RQ). |
| 3.4 | Data layer | React Query (server data) + Zustand `inbox-store` (UI) + `useShellStore` (valeriaState) + `useSearchParams` (conv/filter). Split estricto. Keys `['adrian','inbox',action,...filters]`. |
| 3.5 | Forms | Composer no es form complejo; `inbox-schema.ts` (Zod) valida payloads de send/mode/nudge. Sin autosave (transacciones atómicas: send/mode/nudge submit-driven). Toasts `sonner`. |
| 3.6 | BE DDD + PhiRepositoryBase | `ConversationRepository` hereda `CompoundScopeRepositoryBase` (dual filter). `NudgeService` en `application/`, thin router. `response_model=` en todos. SA 2.0. Soft delete. |
| 3.7 | Migrations | **Sin migración** (modelo cubre 3-modos). Si surgiera columna (ej. `assigned_user_id` para "Asignadas a mí") → raw SQL idempotente `ADD COLUMN IF NOT EXISTS` (decidir en T-1; ver § 16). |
| 3.8 | Telemetría | `vitalia_growth_studio_event` (NO `copilot_trace_event`). Events spec § Telemetría (`adrian_inbox_viewed/conv_opened/mode_changed/takeover/nudge_sent/conversation_mode`). Sin PHI/montos en props. |
| 3.9 | Tests | Vitest unit + Playwright funcional (SC-1..SC-10) + visual golden ×12 + axe + BE pytest dual-tenant + arch fitness EXTEND. |

`adr_004_compliance: full`. Sin divergencias que requieran rationale.

---

## § 8. Agentic Surfaces

**N/A — esta story NO toca superficie agéntica de producción.** El inbox consume runtime existente (sales_agent + observability) read-only. No hay LangGraph state nuevo, ni topology, ni tools nuevos, ni prompt cache slots, ni eval goldens nuevos. El único "agentic touch" es CONSUME: (a) el endpoint nudge invoca el tool `send_proactive_reengagement` (shipped) vía service resolver, (b) el activity-stream lee `copilot_trace_event` sanitizado. **Cero tickets editan `core/luana-core-{sales-agent,copilot}/src/` ni `vitalia/.../sales_agent/` runtime.** `04-validators.yaml § agentic_eval` = skip con esta razón.

---

## § 9. Migration & consolidation plan (★ explícito — el corazón de la story)

> Hogar canónico final: `vitalia/frontend/src/features/adrian/components/inbox/`. El huérfano `features/inbox/` se elimina al final (T-4). Anti-duplicación: dos sets NO pueden convivir.

### 9.1 — MIGRATE (source → dest, lógica rica de `features/inbox/`)

| Source (`features/inbox/`) | Dest (`features/adrian/`) | Estrategia |
|---|---|---|
| `components/SegmentedControl3Modes.tsx` | `components/inbox/ModeToggle.tsx` | MIGRATE + renombrar al nombre del spec; + banner autonomía + "Tomar control"; map 3-modos→`{handler_mode,proposal_required}` |
| `components/AgentActivityStream.tsx` | `components/inbox/ActivityStream.tsx` | MIGRATE verbatim (glass-box, consume activity-stream sanitizado) |
| `components/ConversationList.tsx` + `ConversationItem.tsx` + `ConversationListPanel.tsx` | `components/inbox/InboxConvList.tsx` (+ `ConversationItem.tsx`) | **MIGRATE+MERGE** con la versión parity de `adrian/.../inbox/ConversationItem.tsx` (unificar en una) |
| `components/ConversationThread.tsx` | `components/inbox/InboxThread.tsx` | MIGRATE + integrar `ToolCallCard` inline |
| `components/MessageBubble.tsx` | `components/inbox/MessageBubble.tsx` | **MIGRATE+MERGE** con parity (bubble por tipo: paciente/bot/humano/delegate/tool) |
| `components/ThreadHeader.tsx` | `components/inbox/ThreadHeader.tsx` | **MIGRATE+MERGE** con parity + ModeToggle + `ConversationModeButton` (⛶full) |
| `components/ContactSidebar.tsx` (PHI version) | `components/inbox/ContactSidebar.tsx` | MIGRATE la PHI-aware (descartar la parity simple); tabs Datos/Actividad/Lead/Notas |
| `components/FilterChips.tsx` + `SearchInput.tsx` | `components/inbox/InboxFilters.tsx` | MIGRATE |
| `components/ComposerArea.tsx` + `MessageInput.tsx` + `ComposerAttachButton.tsx` + `ComposerVoiceButton.tsx` + `SendButton.tsx` | `components/inbox/Composer*.tsx` | MIGRATE; placeholder dinámico por modo |
| `components/PauseAdrianButton.tsx` + `PauseAdrianConfirmModal.tsx` | `components/inbox/PauseAdrian*.tsx` | MIGRATE |
| `components/ActionReceiptUndoChip.tsx` | `components/inbox/ActionReceiptUndoChip.tsx` | MIGRATE (undo 5min) |
| `components/{VoiceMessagePlayer,ImageAnalysisCard,AdrianToolsSheet,ProposalCardBanner}.tsx` | `components/inbox/` idem | MIGRATE |
| `api/*` hooks RQ (`use-set-mode`, `use-send-message`, `use-activity-stream`, `use-pause-adrian`, `use-proactive-outbound`, `use-retract-message`, `use-attach-media`, `use-transcribe-audio`, `use-tools-state`, `_keys.ts`) | `features/adrian/api/inbox.ts` (+ split por concern) | MIGRATE; re-apuntar imports a `features/adrian/api` |
| `hooks/{use-activity-stream-poll,use-mode-toggle,use-conversation-filters,use-action-receipt-timer}.ts` | `features/adrian/hooks/` | MIGRATE |
| `store/inbox-store.ts` | `features/adrian/store/inbox-store.ts` | MIGRATE + agregar `priorValeriaState` slot (modo conversación) |
| `types/{message,conversation-detail,activity-event,action-receipt,tools-state}.ts` | `features/adrian/types/inbox.types.ts` | MIGRATE+MERGE con `adrian/.../inbox/types.ts` |
| `url-state.ts` + `copy.ts` | `features/adrian/.../inbox/` | MIGRATE (copy → microcopy SSoT spec) |
| `__tests__/*` (Vitest) co-located | mover junto a su componente | MIGRATE (mantener verdes — regression_guard) |

### 9.2 — MERGE (dos versiones → una; `features/adrian/components/inbox/` parity)

`ConversationItem`, `ContactSidebar`, `ThreadHeader`, `MessageBubble`, `MessageInput`, `TakeoverBanner`, `CampaignTag`, `types.ts` (parity F1-S10) → fusionar con la versión rica migrada. Regla: **quedarse con la lógica más rica** (PHI-aware, 3-modos, voice/image), preservar la API pública que el shell ya consume. `TakeoverBanner` parity = REUSE (banner "tienes el control").

### 9.3 — DELETE (al consolidar, en el MISMO PR T-4)

| Path | Razón |
|---|---|
| `vitalia/frontend/src/features/inbox/` (TODO el directorio) | consolidado en `features/adrian/` |
| Uso activo de `features/adrian/components/placeholders/InboxPlaceholder.tsx` | reemplazado por ruta real; se des-wirea del `[subtab]` dispatcher para `adrian.inbox` (el archivo puede quedar como fallback genérico solo si el dispatcher lo necesita; sino borrar) |

### 9.4 — NEW (no existe equivalente)

| Pieza | Path |
|---|---|
| `adrian/inbox/page.tsx` (RSC) | `app/[tenantId]/(shell-organism)/adrian/inbox/` |
| `AdrianInboxView.tsx` (client root 3-pane) | `features/adrian/components/inbox/` |
| `ConversationModeButton` (⛶full, colapsa Valeria) | `features/adrian/components/inbox/` |
| `ToolCallCard` (colapsable inline) | `features/adrian/components/inbox/` |
| `NudgeButton` + confirm | `features/adrian/components/inbox/` |
| `ChannelBadge` | `components/shared/shell-organism/` |
| `useValeriaReaccion` (hook básico) | `features/adrian/hooks/` |
| `inbox-server.ts` (`getInitialInboxState` SSR) | `features/adrian/api/` |
| `inbox-schema.ts` (Zod) | `features/adrian/types/` |
| BE `NudgeService` + endpoint + `PhiChannelPolicy` | `vitalia/backend/src/modules/vitalia/inbox/application/` + `api/router.py` |

### 9.5 — Tests audit (default flip)

- [x] **No aplica** — esta story NO flipea defaults de feature flags side-effect. El un-stub de ComplianceService es swap de DI (NoOp→real), no un flag flip. El outbox (`adapter_bus`) ya está en su default ON (shipped). Sin `USE_*_PATTERN_*` tocado.

---

## § 10. File Structure

Ver § 9 (migration plan) para el detalle MIGRATE/MERGE/NEW/DELETE. Resumen de árboles destino:

```
BE (vitalia/backend/src/modules/vitalia/inbox/)
├── application/
│   ├── services/nudge_service.py                    NEW
│   ├── policies/phi_channel_policy.py               NEW (implementa CompliancePolicy Protocol del engine)
│   └── dto/nudge_dto.py                             NEW
├── api/router.py                                    MODIFY (un-stub compliance DI + nudge endpoint)
└── (resto shipped — REUSE)

FE
├── app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx   NEW
├── features/adrian/
│   ├── components/inbox/  (ver § 9 — MIGRATE+MERGE+NEW)
│   ├── api/{inbox.ts, inbox-server.ts}                     NEW (consolida hooks RQ)
│   ├── hooks/{useValeriaReaccion.ts, ...migrated}          NEW+MIGRATE
│   ├── store/inbox-store.ts                                MIGRATE+EXTEND
│   ├── types/{inbox.types.ts, inbox-schema.ts}            MIGRATE+NEW
│   └── index.ts                                            MODIFY (export AdrianInboxView + getInitialInboxState)
├── components/shared/shell-organism/ChannelBadge.tsx       NEW
├── lib/{shell-routes.ts, agent-catalog.ts}                MODIFY (SHIPPED_STATIC_SUBTABS += adrian.inbox)
└── features/inbox/                                          DELETE (todo)
```

---

## § 11. Cross-Cutting Concerns

(Ver § 4 — resumen): tenant+clinic dual filter siempre · audit sync write en mode/takeover/pause/nudge/compliance-block · PHI masked (PiiMaskedSpan/RequireRole) + sanitize_payload en traces + PHI nunca en URL · Spanish neutro en chrome, voz tenant en output Adrián · native-first :3002/:8002.

---

## § 12. Architecture Fitness Impact

- **BE gates que corren:** `test_phi_dual_filter.py` (NudgeService + repo), `test_audit_log_sync_write.py` (nudge + compliance-block), `test_response_model_required.py` (nudge endpoint), `test_growth_studio_event_no_phi.py`, suite `tests/modules/vitalia/inbox/` (regression_guard: las 11 suites shipped siguen verdes).
- **FE gates que corren:** `test_no_hardcoded_strings_inbox.test.ts`, `test_no_hardcoded_colors.test.ts`, `test_no_cross_feature_imports.test.ts`, `test_fsd_boundaries.test.ts`, `test-agent-catalog-ssot.test.ts` (registro adrian.inbox), `test-no-cross-brand-shell-mirror.test.ts`, `test_server_first.test.ts`, `test-ribbon-no-shadcn-tabs.test.ts` (ModeToggle = Shadcn Tabs OK dentro de body? → usar segmented control/RadioGroup, NO confundir con nav tabs; verificar), `test_phi_pii_components_used.test.ts`, `test_no_voseo_in_copy.test.ts`, whitelist searchParams (PHI in URL).
- **Allowlists:** la consolidación + DELETE de `features/inbox/` debería **shrink** cualquier allowlist que listara el huérfano. Ninguna allowlist crece. El gate `test_no_cross_feature_imports` valida que la consolidación no introduce import cross-feature.

---

## § 13. capability YAML + modules/{m}.md Updates Required (post-merge)

- `vitalia/docs/product/capabilities/inbox/adrian.inbox.yaml` — **NEW** (v3.2 blocks): `scenarios[]` mapeando SC-1..SC-10 con `@rule-ID` tags · `access` (roles PHI doctor/nurse/admin_clinic) · `business_rules` (RN-1..RN-14) · `dev_preview: adrian/inbox/page.tsx` · zona derivada de SYSTEM-MAP (`agentes`).
- `vitalia/docs/product/modules/inbox.md` — narrativa: inbox re-hogareado en shell, 3-modos, nudge 1:1, PHI firewall via ComplianceService real.
- Headers `# cap: inbox.adrian.inbox` (Python) / `// cap: inbox.adrian.inbox` (TS/TSX) en archivos NEW (líneas 1-3).

---

## § 14. Test Surfaces (TDD RED-first)

(Detalle completo en `04-validators.yaml § test_construction_plan`.)

- **BE (RED por capa):** `PhiChannelPolicy` unit (allow/block por canal) → `NudgeService` unit (nudge sobre conv viva, audit+activity, sin conv nueva) → `test_phi_voice_redirect.py` (SC-3: ComplianceService bloquea + redirect, ya stub a llenar) → router test nudge (PHI-gated, dual-tenant, response_model) → `test_activity_stream_sanitize.py` (RN-10) → regression_guard: suite inbox shipped verde.
- **FE (RED):** hooks RQ migrados (vitest) → `ModeToggle` (3-modos→mapping) → `AdrianInboxView` (3-pane render) → `ConversationModeButton` (colapso/restore valeriaState) → `ToolCallCard`/`ChannelBadge`/`NudgeButton` unit.
- **E2E (Playwright, importan `e2e/fixtures/base.ts`):** SC-1 (decide+tool-call+Valeria), SC-2 (consulta edita borrador), SC-3 (PHI block), SC-4 (takeover concurrente 409), SC-5 (modo conversación full), SC-6 (nudge), SC-7 (empty), SC-8 (network failure), SC-9 (a11y+axe), SC-10 (cross-tenant+i18n).
- **Visual golden ×12:** 3 modos × 2 themes × 2 (desktop split / full conversación) — ratchet shrink-only.

---

## § 15. Research Notes (date-aware)

- **TanStack Query — Advanced Server Rendering (Next.js App Router)** · https://tanstack.com/query/latest/docs/framework/react/guides/advanced-ssr · accessed 2026-06-03 · React Query v5. Takeaway: patrón canónico = `prefetchQuery` + `dehydrate`/`HydrationBoundary` en RSC; `initialData` prop es el "quickest, not recommended" pero **aceptable y ya es la convención del codebase** (mateo/agenda usa `initialData`). Decisión: seguir la convención del codebase (initialData prop) para consistencia + cero scope creep; el inbox tiene N queries (lista + detalle + activity) → si el equipo prefiere robustez, `HydrationBoundary` es opt-in (no obligatorio). Conocimiento post-cutoff verificado live (Opus 4.8 cutoff ene 2026).
- **Next.js 16 App Router data fetching** · https://nextjs.org/docs/app/api-reference/file-conventions/intercepting-routes · accessed 2026-06-03. Takeaway: el patrón intercepting-route (embudo) NO aplica al inbox porque el thread es panel central siempre-visible del 3-pane, no un overlay. Deep-link = `?conv={id}` searchParam (RN-14), no `@modal`/`(.)`.
- **Anchor interno (no web):** `mateo/agenda/page.tsx` (pattern mirror), `ADR-vitalia-004` (9 secciones), `conversation_repository.py::list_for_inbox` (dual filter shipped), `core/luana-core-compliance/.../compliance_service.py` (`check()` + Protocol — consume).

---

## § 16. Open Questions for PM

1. **Filtros "Asignadas a mí" / "Esperando humano":** `vitalia_conversations` no tiene `assigned_user_id` (verificado modelo). "Asignadas a mí" requiere esa columna O derivarla de audit/takeover. **Recomendación:** diferir "Asignadas a mí" a story futura (no está en los 10 SC); cubrir "Esperando humano" como `proposal_required=true` + sin reply humano (derivable en query, sin columna). Confirmar scope con /pm-vitalia.
2. **`[conv-id]/page.tsx` N3-dyn:** el spec lo lista como NEW pero la naturaleza 3-pane lo hace **redundante** con `?conv={id}` (el thread es siempre-visible). **Recomendación:** NO construirlo en esta story (searchParam cubre AC-3/RN-14); marcarlo diferido. Confirmar.
3. **`PhiChannelPolicy` ubicación:** ¿vive en `inbox/application/policies/` (brand-local) o se promueve a `vitalia/.../compliance/`? Si el patrón de detección PHI-por-canal se reusara en otros módulos vitalia → candidate a `compliance/`. MVP: `inbox/application/policies/`. Si requiere primitive nuevo en el engine `core/luana-core-compliance/` → escalar `/pm-luana` (NO ticket).
4. **Búsqueda en lista:** ¿el filtro de búsqueda (debounce 300ms) busca por nombre masked + snippet? El snippet (`last_message_preview`) existe; el nombre del paciente es PHI (búsqueda server-side con RBAC). Confirmar alcance MVP (búsqueda solo en snippet vs nombre con reveal).
