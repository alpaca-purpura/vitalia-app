---
story_id: vitalia-fase2-adrian-inbox
surface: backend
builder: builder-backend
auditor: auditor-backend
architecture_pattern: ADR-vitalia-004
---

# 03-arch-be — vitalia-fase2-adrian-inbox (backend)

> **Naturaleza BE: un-stub + 1 endpoint.** El módulo inbox YA está shipped (8 endpoints, 7 services, modelo `vitalia_conversations` con OCC). NO hay migración nueva. El trabajo: (A) un-stub `ComplianceService` real (SC-3/AC-9/RN-7), (B) `NudgeService` + endpoint (RN-13), (C) verificar/cerrar filtros de lista para AC-2, (D) tests RED-first.
> **Owner:** `builder-backend` (Sonnet). **Auditor:** `auditor-backend` (Opus). **Cero edición de `core/` o `sales_agent/` runtime.**

## 1. Domain (sin entidades nuevas)

`vitalia_conversations` (model `ConversationModel`) ya tiene todo lo necesario — **NO crear entidades nuevas, NO migración**:

```
ConversationModel (vitalia_conversations) — SHIPPED
  id: UUID (PK)
  tenant_id: UUID (NOT NULL, index)            ← tenant isolation
  clinic_id: UUID (NOT NULL)                    ← HIPAA-lite dual filter
  lead_id: UUID | None · patient_id: UUID | None
  channel: str(50)                              ← whatsapp/instagram/email/web
  status: str(50) default 'open'
  handler_mode: str(50) default 'ai'            ← {ai, human} (3-modos mapea acá + proposal_required)
  proposal_required: bool default False         ← consulta = ai + proposal_required=true
  pause_until: datetime(tz) | None              ← pausa Adrián
  help_needed: bool · help_needed_reason: str | None  ← escala (RN-3)
  unread_media_count: int
  last_message_at · last_message_preview · messages_count
  stage_decision · linked_offer_id
  created_at · updated_at(tz)                    ← OCC token
  deleted_at(tz) | None                          ← soft delete
```

**3-modos → modelo (★ mapping cementado):**

| UI mode | `handler_mode` | `proposal_required` |
|---|---|---|
| 🤖 Decide solo | `ai` | `false` |
| 🤝 Consulta | `ai` | `true` |
| 👤 Manual / Yo escribo | `human` | `false` |

## 2. SQLAlchemy models — REUSE (sin cambios)

`ConversationModel`, `MessageModel`, `ActionReceiptModel`, `ActivityEventModel` — todos shipped en `crm/.../persistence/models/`. Repos en `crm/.../persistence/`. **Sin nuevos models.**

> **Decisión Open Q #1 (PM):** "Asignadas a mí" requeriría `assigned_user_id` (no existe). **NO agregar columna en esta story** (diferir filtro). Si /pm-vitalia ratifica incluirlo → migración raw SQL idempotente `ALTER TABLE vitalia_conversations ADD COLUMN IF NOT EXISTS assigned_user_id UUID` + index. Default: diferido.

## 3. Pydantic DTOs

Existentes (REUSE): `ConversationListResponse/Item/Filters`, `SetModeRequest`/`ConversationResponse`, `ActivityStreamResponse/Item`, `MessageResponse`, `ProactiveOutboundRequest/Response`.

NEW:

```python
# inbox/application/dto/nudge_dto.py
class NudgeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reason: str | None = None
    idempotency_key: str | None = None       # dedup doble-empujón

class NudgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    conversation_id: UUID
    message_id: UUID
    nudge_sent: bool
    activity_event_id: UUID | None = None
    sent_at: datetime
```

## 4. API Routes

| Method | Path (prefix `/api/v1/vitalia/inbox`) | Auth | Request | response_model | Estado |
|---|---|---|---|---|---|
| GET | `/api/v1/vitalia/crm/conversations` (list) | Bearer + X-Tenant-ID + X-Clinic-ID | query filters | `ConversationListResponse` | SHIPPED (REUSE) |
| GET | `/api/v1/vitalia/crm/conversations/{id}` | idem | — | `ConversationListItem` | SHIPPED |
| POST | `/conversations/{id}/messages` | idem | `SendMessageRequest` | `MessageResponse` | SHIPPED — **MODIFY** (wire ComplianceService real) |
| POST | `/conversations/{id}/messages/{msg_id}/revert` | idem | `RetractMessageRequest` | `RetractMessageResponse` | SHIPPED |
| PATCH | `/conversations/{id}/mode` (OCC) | idem | `SetModeRequest` | `ConversationResponse` | SHIPPED |
| POST | `/conversations/{id}/pause` | idem | `_PauseRequest` | `ConversationResponse` | SHIPPED |
| GET | `/conversations/{id}/tools` | idem | — | `ToolsStateResponse` | SHIPPED |
| GET | `/conversations/{id}/activity-stream` | idem | query | `ActivityStreamResponse` | SHIPPED |
| POST | `/proactive-outbound` | idem | `ProactiveOutboundRequest` | `ProactiveOutboundResponse` | SHIPPED |
| **POST** | **`/conversations/{id}/nudge`** | idem | `NudgeRequest` | `NudgeResponse` | **NEW** |
| POST | `/transcribe` | idem | `_TranscribeRequest` | `_TranscribeResponse` | SHIPPED |

Todas PHI-gated (doctor/nurse/admin_clinic), Bearer + X-Tenant-ID + X-Clinic-ID, `response_model=`. `redirect_slashes=False` ya en `main.py`.

## 5. Repository Interfaces — REUSE

`ConversationRepository(CompoundScopeRepositoryBase[ConversationModel, UUID])` (dual filter) ya tiene `list_for_inbox(tenant_id, clinic_id, handler_mode=...)`, `get_by_id(id, tenant_id, scope_id)`, `update_handler_mode(... OCC)`. `MessageRepository`, `ActivityEventRepository`, `LeadRepository`, `ActionReceiptRepository` shipped.

**Gap a verificar (AC-2):** `list_for_inbox` filtros. Existen `status/channel/handler_mode/help_needed/unread_media`. Cubrir si faltan:
- "Sin leer" → `unread_media_count > 0` o `unread_count` (verificar campo).
- "Esperando humano" → `proposal_required == True` (derivable; NO requiere columna).
- Búsqueda → por `last_message_preview` ILIKE (snippet); nombre paciente = PHI, server-side con RBAC (ver Open Q #4 — MVP solo snippet).

## 6. Application Services

### 6.1 — ComplianceService un-stub (★ trabajo central — SC-3/AC-9/RN-7)

**Consume engine, NO recrea** (`core/luana-core-compliance/.../compliance_service.py`):

```python
# El engine expone:
class ComplianceService:
    def __init__(self, policies: list[CompliancePolicy]) -> None: ...
    async def check(self, ...) -> CheckResult:   # short-circuit; first allowed=False gana
        # → CheckResult(allowed: bool, failed_policy: str | None)

class CompliancePolicy(Protocol):
    async def evaluate(self, ...) -> CheckResult: ...
```

**NEW brand-local — `inbox/application/policies/phi_channel_policy.py`:**

```python
# cap: inbox.adrian.inbox
class PhiChannelPolicy:   # implements CompliancePolicy Protocol
    """Bloquea outbound con intención de resultados clínicos por canal no-encriptado.

    RN-7: WhatsApp free / SMS → no PHI clínica. Deriva a portal seguro.
    PHI keywords de detección: 'diagnóstico', 'resultado', 'estudio', etc.
    (heurística — el sistema fuerte es la voz del agente + esta red de seguridad).
    """
    _UNENCRYPTED_CHANNELS = frozenset({"whatsapp", "sms"})   # tier free
    async def evaluate(self, *, message, channel, ...) -> CheckResult:
        if channel in self._UNENCRYPTED_CHANNELS and _looks_like_phi_results(message):
            return CheckResult(allowed=False, failed_policy="phi_unencrypted_channel")
        return CheckResult(allowed=True)
```

**Wiring DI (`api/router.py` MODIFY):** `_get_send_service` / `_get_proactive_service` inyectan `ComplianceService(policies=[PhiChannelPolicy(), <WABA24h/OptIn/Blacklist/CountryBlock si aplican>])` en vez de `_NoOpComplianceService`. El send path:
1. Antes de enviar outbound del agente → `result = await compliance_service.check(message=..., channel=...)`.
2. Si `not result.allowed` → reemplaza outbound por el redirect a portal (microcopy SSoT: "Por seguridad, tus resultados están en tu portal: {link}") + escribe activity event `compliance_block_outbound_phi` (description_es legible) + audit row `compliance_block_outbound_phi`.

> **Decisión:** la `PhiChannelPolicy` implementa el Protocol del engine = extensión legítima, NO mirror. Si requiere un primitive nuevo en `core/luana-core-compliance/` → escalar `/pm-luana` (NO ticket). El `_NoOpComplianceService` queda borrado del path de producción (puede quedar en tests como fake explícito).

### 6.2 — NudgeService (NEW — RN-13)

```python
# inbox/application/services/nudge_service.py
# cap: inbox.adrian.inbox
class NudgeService:
    """Empujón 1:1 a UNA conversación viva estancada.

    RN-13: aplica a conv activa estancada; NO crea conv nueva; NO reactiva lead frío
    (eso es Camila). Consume send_proactive_reengagement (brand tool, shipped) vía
    service resolver — NUNCA import directo de sales_agent/.
    Voz: respeta personality_profiles.system_instruction (voz tenant).
    """
    async def nudge(self, *, tenant_id, clinic_id, conversation_id, sent_by_user_id,
                    reason=None, idempotency_key=None) -> NudgeResult:
        # 1. get_by_id dual filter → 404 si no existe
        # 2. validar conv viva (status open) + estancada (last_message_at > umbral, ej. 24h)
        # 3. idempotency dedup: (tenant, conv, 'nudge', day) natural key
        # 4. invocar re-enganche (resolver → send_proactive_reengagement) → mensaje outbound
        # 5. activity event 'nudge_sent' (description_es) + audit row sync pre-response
        # 6. emit event vía adapter_bus (outbox)
```

DI: `_get_nudge_service` (NEW) con `ConversationRepository`, `MessageRepository`, `AsyncAuditWriter`, `ActivityEventRepository`, `_adapter_bus`, resolver del tool (mismo patrón que `send_proactive_reengagement.resolver`).

### 6.3 — REUSE (sin cambios)

`SetModeService` (OCC, ModeChanged event), `PauseAdrianService`, `ActivityEventService` (sanitize), `RetractMessageService`, `SendMessageService` (solo wiring compliance). `ProactiveOutboundService` (REUSE + wiring compliance real).

## 7. Idempotency on writes

- `send_message` ya recibe `idempotency_key` (REUSE).
- `nudge` NEW: `idempotency_key` opcional + dedup natural key `(tenant, conv, 'nudge', day)` → evita doble empujón. Si repetido en el día → 200 con `nudge_sent=false` (no error).
- `PATCH /mode` usa OCC (`expected_updated_at`) → 409 en stale (SC-4).

## 8. Migration Notes

**NINGUNA migración nueva** (modelo cubre 3-modos). Si /pm-vitalia ratifica `assigned_user_id` (Open Q #1) → raw SQL idempotente:
```sql
ALTER TABLE vitalia_conversations ADD COLUMN IF NOT EXISTS assigned_user_id UUID;
CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_assigned ON vitalia_conversations (tenant_id, clinic_id, assigned_user_id);
```
Prod-clone test: `make verify-vitalia-migration-idempotency` (si aplica). Default: sin migración.

## 9. Tests (RED-first)

1. **`test_phi_channel_policy.py`** (NEW) — RED: `evaluate(channel='whatsapp', msg=PHI-results)` → `allowed=False`; `channel='web'` → `allowed=True`; mensaje no-PHI por whatsapp → `allowed=True`.
2. **`test_phi_voice_redirect.py`** (EXISTE stub — llenar) — SC-3: send path con ComplianceService real → bloquea + redirect microcopy + activity event `compliance_block_outbound_phi` + audit row.
3. **`test_nudge_service.py`** (NEW) — RED: nudge sobre conv viva → outbound + activity `nudge_sent` + audit + sin conv nueva; conv inexistente → 404; idempotency repetido → no doble envío; lead frío fuera de scope (no toca).
4. **`test_router_nudge.py`** (NEW) — PHI-gated (403 role no autorizado), dual-tenant (404 cross-tenant), `response_model=` presente, 201/200.
5. **`test_activity_stream_sanitize.py`** (NEW/EXISTE) — RN-10: activity events servidos vía `sanitize_payload` (sin PHI cruda).
6. **`test_cross_tenant_denied.py`** (EXISTE) — SC-10: conv_id tenant B con tenant A → 404 sin leak (REUSE, regression_guard).
7. **regression_guard:** TODA la suite `tests/modules/vitalia/inbox/` shipped sigue verde sin modificarse (excepto el path de compliance que cambia: actualizar mocks de NoOp→real explícitamente, no mecánico).

**Comandos (native, host):**
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/modules/vitalia/inbox/ tests/modules/vitalia/inbox/
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/inbox/ -v
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q
```

## 10. Anti-patterns (NO hacer)

- ❌ Crear un layer de compliance nuevo en inbox — CONSUME el engine `ComplianceService` (Protocol).
- ❌ `from src.modules.vitalia.sales_agent...` en `inbox/` — usar resolver del tool (DI), no import directo.
- ❌ Tocar `SetModeService`/`PauseAdrianService`/OCC (shipped, §3-equivalente — solo wiring compliance + nudge nuevo).
- ❌ Flipear defaults de feature flags (no aplica — § 9.5).
- ❌ Endpoint nudge sin `response_model=` / sin dual filter / sin audit sync.
- ❌ Migración con `op.create_table()` (no idempotente) — solo raw SQL `IF NOT EXISTS` si surge columna.
