# 05-guidelines — canal-inbound (Adrián)

> Guía enforceable para los builders. **Frontera dura:** los tickets agentic `book`/`match`/`share` están
> BLOQUEADOS hasta el lift `/pm-vitalia` (ESC-1/2/3, ver 03-arch.md § Engine-boundary escalations). Lo demás es
> buildable hoy.

## Patterns REQUIRED

### Todos los surfaces
- **Tenant + clinic dual-filter** en TODA query (hipaa-lite). `PhiRepositoryBase` para repos PHI.
- **Audit log sync write pre-response** en booking + set-instruction + PHI block.
- **`sanitize_payload(compliance_level="hipaa_lite")`** en cada write a trace/activity/llm_call.
- **UTC store** + `DateTime(timezone=True)`; display tenant locale.
- **structlog** (no print/logging). **SQLA 2.0 async** (`select().where()`). **Pydantic v2** `ConfigDict`.
- **`response_model=`** en cada route. **No `Any`** en superficie pública.
- **TDD RED-first** por capa (domain→infra→app→api / hook→component→store).
- **Native-first:** `${WS}/.venv/bin/{ruff,pytest}` + `npx tsc/vitest/playwright`. NUNCA docker exec.
- **Commit por pathspec** (hub compartido). Spanish neutro en UI/schemas; voz del agente respeta tenant.

### BE (builder-backend)
- Telegram adapter implementa `BaseChannel` del engine (patrón whatsapp/instagram). Webhook **NO** Bearer
  (valida `X-Telegram-Bot-Api-Secret-Token` + resuelve tenant por bot). Idempotencia por `update_id`.
- Dispatch al engine `orchestrator.handle_telegram_webhook` (YA wired — consumir, no reimplementar).
- `create_appointment_service` MARCA `availability_slot.has_confirmed_appointment=True` + set hold (cierra RN-26).
- Hold-TTL desde `tenant_config.adrian_hold_ttl_minutes` (default 30) — NUNCA hardcoded.
- Sweep idempotente; coordina con engine `verify_pending_bookings` (no duplica reconciliación).
- Anti doble-booking: unique constraint / advisory-lock sobre `(doctor_id, slot)` → 409 (RN-22).

### Agentic (builder-agentic — buildable: overlay + persona tuning + operator-instruction + goldens)
- EXTEND `state_overlay` (keys booking) — NO extender `MeetingEntry` del engine (frozen → engine).
- Operator instruction REUSE `override_context_wire` (key `metadata_info`); persistente; SLOT volátil.
- Prompt slots cacheables → **declarar `"ttl": "1h"` explícito** (SOTA: default bajó a 5min mar-2026).
- Eval goldens con `pass^k` (3 trials / 0.66 / 0.5). Voz = tenant. Guardrails éticos = REUSE (no rebuild).
- **Selección de slot = razonamiento del agente** sobre `candidate_slots` (bar no-`if`s) — NUNCA regex/parser.

### FE (builder-frontend)
- EXTEND composer del inbox (effectiveMode: `human`→direct · decide→instruction). Reusa `MessageInput` legacy.
- Label "🤖 Instrucción a Adrián · el paciente no la verá" + chip instrucción activa. Spanish neutro.
- `tenant_id` via `useTenantId()` (NUNCA Clerk org). React Query server data + Zustand UI state.

## Patterns FORBIDDEN
- ❌ Editar `core/luana-core-*/src/` (cualquier paquete engine). → `/pm-vitalia` promotion gate.
- ❌ Usar `BookingService`/`vitalia_bookings` (deprecated) — turno solo en lane vivo `scheduling`.
- ❌ Reimplementar orchestrator/debounce/graph/OutputManager/follow_up_engine (§3 protected sales-agent-expert).
- ❌ Selección de slot con regex/parser/if-chain (bar no-`if`s).
- ❌ Dos rutas de reschedule vivas (dedup al cablear book).
- ❌ Mirror cross-brand (Telegram/scheduler provider = brand-local).
- ❌ PHI por Telegram / en URL / en localStorage / en traces sin sanitize.
- ❌ Stubs WhatsApp/IG no-verificables (Critical Rule #37 — telegram-first).
- ❌ `sa.Enum(create_type=True)` / `op.create_table()` (migrations no idempotentes).
- ❌ Voz neutro forzada en output de Adrián (respeta voz del tenant).

## Files in scope (NEW vs MODIFIED) — ver 03-arch.md § 10
- BE buildable: `connections/telegram/*` (NEW) · `scheduling/*` (EXTEND) · `api/webhook_routes.py` (MODIFIED) · `main.py` (MODIFIED).
- Agentic buildable: `sales_agent/domain/state_overlay.py` · `prompts/` · `personas/` · `goldens/` · `application/services/operator_instruction_service.py`.
- Agentic lift-gated: `sales_agent/tools/{book_appointment,match_service_and_specialist,share_doctor_profile}.py` · `infrastructure/scheduler/vitalia_scheduler_provider.py` · `extensions.py` (register).
- FE buildable: `features/adrian/components/inbox/composer/*` · `api/` · `hooks/` · `types/`.

## Files NEVER touch
- `core/luana-core-*/src/` (engine — `/pm-vitalia`).
- `vitalia/.../application/services/booking_service.py` + `vitalia_bookings` (deprecated).
- Otros brands (`nicolify/`, `comunify/`, `lupulo/`). Otras sub-tabs del inbox.

## must_load_skills (enforceable — por surface)
- **BE:** `backend-expert` · `hipaa-lite` (rule) · `anti-duplication` · `tenant-isolation` · `tdd-mandatory` · `chrome-devtools-verify` (route con consumer).
- **Agentic:** `sales-agent-expert` · `copilot-expert` (si toca observability shared) · `hipaa-lite` · `anti-duplication` · `tenant-isolation` · `tdd-mandatory` · LangGraph canonical docs · `chrome-devtools-verify`.
- **FE:** `frontend-expert` · `vitalia-design-system` · `playwright-expert` · `chrome-devtools-verify` · `tenant-isolation`.
- **PM (lift):** `pm-vitalia` (ESC-1/2/3 promotion proposal).
