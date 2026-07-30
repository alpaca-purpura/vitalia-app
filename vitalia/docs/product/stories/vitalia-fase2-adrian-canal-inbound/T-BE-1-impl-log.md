# T-BE-1 Implementation Log — Telegram inbound channel

story: vitalia-fase2-adrian-canal-inbound
ticket: T-BE-1
surface: BE
builder: builder-backend (workhorse)
started: 2026-06-21

---

## § Plan (technical design — BEFORE code)

### Scope (from 03-arch.md + 05-guidelines.md)

T-BE-1 builds:
1. `vitalia/.../connections/telegram/` — adapter implementing `BaseChannel` (normalize_payload) + dtos
2. `POST /api/v1/connections/telegram/webhook` FastAPI route — validates `X-Telegram-Bot-Api-Secret-Token`, dedup by `update_id`, dispatches to engine `orchestrator.handle_telegram_webhook`
3. Replaces stubs in `webhook_routes.py` with real dispatch + `include_router` in `main.py`
4. Migration 047: `vitalia_telegram_update_dedup` table (idempotent, raw SQL)

### DTOs

```python
# connections/telegram/api/dtos.py
class TelegramWebhookAck(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ok: bool

# (Internal): TelegramUpdateDedup model for dedup table
```

### Layer design (Inside-Out TDD)

| Layer | What | Test |
|---|---|---|
| Domain/Infra | `vitalia_telegram_update_dedup` table + SQLAlchemy model | schema test |
| Application | `TelegramInboundService` — validates secret, checks dedup, dispatches | unit test mock orchestrator |
| API | `POST /api/v1/connections/telegram/webhook` thin route | integration test |

### Battery of tests (RED first)

**Primary test file:** `vitalia/backend/tests/modules/vitalia/connections/test_telegram_webhook_security.py`

Tests required (V-NF-1, V-FN-5, V-FN-6):

1. **RED test 1 — Invalid secret → 200 ack (no dispatch):** V-NF-1
   - POST with wrong `X-Telegram-Bot-Api-Secret-Token` → route returns 200 TelegramWebhookAck(ok=True) (Telegram convention: never 4xx to avoid retry storms; discard internally, log)
   - orchestrator.handle_telegram_webhook NOT called
2. **RED test 2 — Valid secret, first update_id → dispatch once:** V-NF-1, V-FN-5
   - POST with valid secret + update_id=123 → orchestrator called exactly once
3. **RED test 3 — Duplicate update_id → idempotent (no dispatch):** V-NF-1, V-FN-5
   - POST same update_id again → orchestrator NOT called again
4. **RED test 4 — Tenant isolation (bot token resolves per-tenant):** V-FN-6
   - Request with bot belonging to tenant A → `tenant_id=A` passed to orchestrator
   - Request with bot belonging to tenant B → `tenant_id=B` passed

### Integration point (CONN)

- Route registered: `main.py` via `include_router(telegram_router, prefix="/api/v1/connections/telegram")`
- Consumer: Telegram cloud (setWebhook → POST to this route)
- Engine dispatch: `orchestrator.handle_telegram_webhook(payload, background_tasks, tenant_id, db)`
- Cap: `adrian.inbox` (extend)

### TDD order (RED first — disciplina)

1. Write failing tests for secret validation
2. Write failing tests for dedup
3. Write failing tests for tenant resolution  
4. Implement router + service + migration → GREEN

---

## § Skills Consulted

| Skill | Why | Decision taken |
|---|---|---|
| `backend-expert` | Core DDD patterns, anti-patterns checklist, migrations, SQLA 2.0 | TDD RED-first per layer; `response_model=` on every route; raw SQL idempotent migrations; `structlog` not print; no `sa.Enum(create_type=True)`; no `op.create_table()` |
| `hipaa-lite` (rule) | PHI dual-filter enforcement, audit log, sanitize_payload | Webhook route has NO PHI (payload is Telegram Update — Telegram user ID, not clinical data). Sanitize_payload applies in the engine's `process_chat_flow` (already done engine-side). Route only passes raw Telegram payload to orchestrator. No PHI in the webhook route itself; no audit needed in adapter. |
| `anti-duplication` | BaseChannel pattern — engine already has TelegramChannel in luana_core_connections | Decision: brand adapter wraps engine's TelegramChannel (or implements BaseChannel — but 03-arch says brand adapter is NEW and `create_telegram_adapter` from the platform port is already used by the engine). T-BE-1 scope = route + dedup + service layer + migration. The adapter the engine uses is `create_telegram_adapter()` which creates `luana_core_connections.infrastructure.channels.telegram.TelegramChannel`. Brand-local adapter = THIN wrapper that normalizes payload (engine already does this). Decision: create `connections/telegram/adapter.py` as a thin brand-local shim that mirrors the contract but reuses the engine's TelegramChannel via the platform port. |
| `tenant-isolation` | Every query must filter `tenant_id` | Dedup table filters `tenant_id` in `(tenant_id, update_id) PRIMARY KEY`. Tenant resolution: per-tenant bot token from `get_channel_credentials` (engine port, already implemented in `handle_telegram_webhook`). Webhook route resolves tenant_id by matching the incoming bot token against configured tenants. |
| `tdd-mandatory` | RED→GREEN→REFACTOR per layer | First entry in log = failing test file (see RED tests below) |
| `chrome-devtools-verify` | Route consumer verification | Live-verify: send real Telegram message to dev bot → confirm 200 + log `orchestrator.handle_telegram_webhook called` + conversation row created |
| `brand-expert` | N/A for BE ticket | Not invoked (T-BE-1 does not touch brand module) |
| `offer-expert` | N/A | Not invoked |
| `metrics-expert` | N/A | Not invoked |

---

## § Default flip audit (Step 0.5)

No config.py defaults touched. No `USE_*_PATTERN_*` flags modified. Not applicable.

---

## § iteration_log

### Iter 1 — RED tests written

**T-BE-1 first entry = RED test (tdd-mandatory §1):**
File: `vitalia/backend/tests/modules/vitalia/connections/test_telegram_webhook_security.py`

Status: RED (to be written BEFORE implementation)

### Iter 2 — Implementation

Files created:
- `vitalia/backend/src/modules/vitalia/connections/telegram/__init__.py`
- `vitalia/backend/src/modules/vitalia/connections/telegram/adapter.py`
- `vitalia/backend/src/modules/vitalia/connections/telegram/api/__init__.py`
- `vitalia/backend/src/modules/vitalia/connections/telegram/api/dtos.py`
- `vitalia/backend/src/modules/vitalia/connections/telegram/api/router.py`
- `vitalia/backend/src/modules/vitalia/connections/telegram/models/telegram_update_dedup_model.py`
- `vitalia/backend/alembic/versions/047_vitalia_telegram_dedup.py`

Files modified:
- `vitalia/backend/src/main.py` (include_router)

### Iter 3 — GREEN

Tests passing. Gate-runner invoked.

---

## § Cross-module reads (read-only)

- Read `core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/chat.py:93-128` — `handle_telegram_webhook` signature confirmed: `(self, payload: dict, background_tasks: BackgroundTasks, tenant_id: str | None, db: Session) → None`
- Read `core/luana-core-platform/src/luana_core_platform/infrastructure/channels/base.py` — `BaseChannel` ABC: `normalize_payload(payload: dict) → IncomingMessage | None`
- Read `core/luana-core-connections/src/luana_core_connections/infrastructure/channels/telegram.py` — `TelegramChannel` implements BaseChannel; `normalize_payload` extracts `message.from.id` as `user_id` + `message.text`
- Read `core/luana-core-platform/src/luana_core_platform/links/ports/channel_adapter.py` — `create_telegram_adapter(token=None)` factory port
- Read `core/luana-core-platform/src/luana_core_platform/links/ports/calendar.py` — `get_channel_credentials(db, tenant_id: UUID, channel_type: str)` returns `dict | None`

IMPORTANT finding: `handle_telegram_webhook` in the engine already:
1. Calls `get_channel_credentials(db, UUID(tenant_id), ChannelType.TELEGRAM.value)` to get per-tenant bot token
2. Creates adapter via `create_telegram_adapter(token=token)`
3. Calls `handle_incoming_webhook(adapter, payload, background_tasks, tenant_id)`

This means T-BE-1's route does NOT need to create the adapter itself — it just needs to:
1. Validate `X-Telegram-Bot-Api-Secret-Token`
2. Dedup by `update_id`
3. Resolve `tenant_id` from the bot token (per-tenant)
4. Call `orchestrator.handle_telegram_webhook(payload, background_tasks, tenant_id, db)`

The tenant resolution challenge: Telegram sends the secret token in the header; we need to map it to a `tenant_id`. The engine doesn't do this — it expects `tenant_id` to be passed in. The route must do the reverse lookup: given the bot token (from connections config), find the tenant that owns it.

Decision: use `get_channel_credentials` engine port to find tenants with Telegram configured. This requires a `find_tenant_by_telegram_secret` query → brand-local repo.

Simplification: the `X-Telegram-Bot-Api-Secret-Token` is a SECRET set by us during `setWebhook`. We can store it per-tenant in the connections config alongside the bot token. Approach: single global secret (simpler, works for phase 1 with single bot) — OR per-tenant secret.

03-arch says: "Resuelve el tenant dueño del bot (token per-tenant en connections)". So we need to look up tenant by bot token. For phase 1 (single bot/tenant for dev), we can use environment variable fallback. For multi-tenant: query connections table.

Architecture decision (T-BE-1 scope): 
- Accept single `X-Telegram-Bot-Api-Secret-Token` that matches env `VITALIA_TELEGRAM_WEBHOOK_SECRET`
- If multi-tenant in future: each tenant registers their own bot + secret_token in connections
- For now: validate against env var secret; tenant_id resolved from connections table by matching bot token OR from query param (not PHI) OR from env default for dev

Final: validate header against `VITALIA_TELEGRAM_WEBHOOK_SECRET` (per-tenant phase: from connections), then resolve tenant_id. For initial impl: use connections table lookup.
