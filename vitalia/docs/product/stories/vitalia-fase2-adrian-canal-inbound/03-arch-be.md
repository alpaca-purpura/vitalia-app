---
story_id: vitalia-fase2-adrian-canal-inbound
brand: vitalia
doc: 03-arch-be
owner_builder: builder-backend (workhorse)
owner_auditor: auditor-backend (flagship)
consumes: 03-arch.md
lift_gated: false   # TODO el BE es brand-local, cero engine — buildable hoy
---

# 03-arch-be — superficie BE (canal Telegram + plomería scheduling)

> **Todo buildable hoy, cero engine.** El engine `handle_telegram_webhook` YA está wired (resuelve token
> per-tenant + adapter + debounce). El BE solo (1) expone la ruta + valida secret + dedup, (2) cierra la
> plomería de scheduling (marcar slot + hold-TTL + sweep). DDD Inside-Out + hipaa-lite (dual-filter + audit sync).

## 1 · Telegram inbound channel (`connections/telegram/` NEW)

### 1.1 Adapter (`connections/telegram/adapter.py`)
Implementa `BaseChannel` (engine `core/luana-core-platform/.../infrastructure/channels/base.py`):
`normalize_payload(payload) -> IncomingMessage | None`. Patrón = `connections/whatsapp/adapter.py` +
`instagram/adapter.py` (outbound vivos). Normaliza el Telegram update → `IncomingMessage(user_id=chat_id,
text, channel_type="telegram", metadata)`.

### 1.2 Webhook route (`connections/telegram/api/router.py`)
```
POST /api/v1/connections/telegram/webhook   response_model=TelegramWebhookAck
```
- **RN-9 secret:** valida header `X-Telegram-Bot-Api-Secret-Token` contra el secret del setWebhook per-tenant.
  Inválido → descarta sin dispatch (no crea conversación, sin leak). NO Bearer (Telegram no lo manda).
- **RN-8 tenant resolution:** resuelve el tenant dueño del bot (token en connections config per-tenant).
- **RN-9 idempotencia:** dedup por `update_id` (tabla `vitalia_telegram_update_dedup`, PK `(tenant_id, update_id)`).
  Repetido → 200 sin re-proceso.
- **Dispatch:** `await orchestrator.handle_telegram_webhook(payload, background_tasks, tenant_id, db)` (engine VIVO).
- `include_router` en `vitalia/backend/src/main.py`.

### 1.3 Reemplazar stubs (`api/webhook_routes.py` MODIFIED)
Los stubs T-be-8 (L251/473/525/621 "stub in T-be-8 scope") → dispatch real al orchestrator. WhatsApp/IG quedan
fuera de scope (telegram-first); sus stubs se mantienen documentados (no se borran, no se activan — Critical Rule #37).

## 2 · Honor-modo bridge (`HonorModeBridge`)
Lee del inbox shipped (cap `adrian-inbox`): `conversation.handler_mode` (`ai`/`human`) + `proposal_required`
(bool) + `pause_until` (datetime). Mapea:
- `handler_mode=ai` + `proposal_required=false` + no pausa = **decide** → corre grafo + ENVÍA outbound.
- `handler_mode=ai` + `proposal_required=true` = **consulta** → corre grafo + retiene outbound → banner propuesta inbox.
- `pause_until` futuro / `handler_mode=human` = **pausa/humano** → el engine `handle_human_mode` ya skip-AI; el
  inbound se persiste + alimenta el inbox, Adrián NO responde.

El engine pipeline natively solo honra `human` (skip). El bridge brand añade el caso **consulta** (corre el
grafo pero el outbound se intercepta antes del send). **Punto de intercepción:** entre el resultado del grafo y
`OutputManager.process_response` (no tocar OutputManager — §3 protected; interceptar en el delivery del brand).

## 3 · Scheduling plomería (`scheduling/` EXTEND)

### 3.1 `create_appointment_service.py` MODIFIED
Tras crear el turno (appointment + clinic_map + audit), **marcar el slot + hold** (cerrar RN-26 gap):
```python
await self._repo.mark_slot_confirmed(tenant_id=..., clinic_id=..., slot_id=..., confirmed=True)
# si origin == "proactivo_adrian" y sin pago: set hold
await self._hold.set_hold(tenant_id=..., clinic_id=..., appointment_id=...,
                          status="hold_pending_payment", expires_at=now_utc + ttl)
```
TTL = `tenant_config.adrian_hold_ttl_minutes` (default 30). Audit sync ya existe. Anti doble-booking:
unique constraint / advisory-lock sobre `(doctor_id, slot)` → 2º create = 409 (RN-22).
**Nota cross-story:** este fix corrige también el create manual de Mateo (no marcaba el slot) — coordinar con
`vitalia-scheduling-mateo-review`.

### 3.2 `scheduling_hold_service.py` NEW + `scheduling_hold_port.py` NEW
`mark_slot_confirmed`, `set_hold`, `list_expired_holds` (async, tenant+clinic scoped). Models § 03-arch.md §2.

### 3.3 `hold_expiry_sweep_service.py` NEW (worker)
Job periódico (ARQ): `list_expired_holds(now)` → por cada hold vencido: cancela turno + `mark_slot_confirmed(False)`
+ emite activity al inbox ("turno liberado por falta de pago"). **Idempotente.** Coordina con el engine
`verify_pending_bookings` (no duplica reconciliación; el sweep cubre el lado del lane vivo que el worker engine
no ve directamente).

## 4 · Set-instruction endpoint (`sales_agent/api/` — BE side del operator instruction)
```
POST /api/v1/adrian/conversations/{conversation_id}/instruction   Bearer + X-Tenant-ID
   response_model=SetOperatorInstructionResponse
```
Delega a `OperatorInstructionService` (agentic) → `override_context_wire`. Audit row + activity NON-PHI.
Valida que la conversación esté en `decide` (en `human`/pausa el composer es directo, no instrucción).

## 5 · Cross-cutting
- **Dual-filter:** toda query scheduling/conversación filtra `tenant_id + clinic_id`. `PhiRepositoryBase`
  para repos PHI (ADR-vitalia-004 §6). Arch test `test_phi_dual_filter.py`.
- **Audit sync pre-response** (hipaa-lite). **response_model=** en cada route. **PHI nunca en URL** (POST body).
- **Migrations idempotentes** raw SQL (§ 03-arch.md §9). **UTC store** + `DateTime(timezone=True)`.
- **structlog**, no print. SQLA 2.0 async. No `Any` en superficie pública.

## 6 · Tests (TDD RED-first)
- `test_telegram_webhook_security.py` (SC-5: secret inválido → 0 filas · update_id repetido → 1 fila).
- `test_telegram_tenant_isolation.py` (SC-6: bot A → solo data A, dual-filter).
- `test_hold_expiry_sweep.py` (SC-10: hold vence → liberado + slot reaparece).
- `test_create_appointment_marks_slot.py` (RN-26: create proactivo_adrian → slot has_confirmed_appointment=True).
- `test_honor_mode_bridge.py` (decide envía · consulta borrador · pausa skip).
- Arch fitness: `test_phi_dual_filter`, `test_audit_log_sync_write`, `test_response_model_required`.
