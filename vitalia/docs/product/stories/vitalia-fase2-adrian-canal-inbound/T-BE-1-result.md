# T-BE-1 Result — Telegram inbound channel

story: vitalia-fase2-adrian-canal-inbound
ticket: T-BE-1
surface: BE
state: tests-passing
builder: builder-backend (workhorse sonnet-4-6)
commits: e27f6cbd 22192d83
date: 2026-06-21

---

## Verdict

tests-passing (16/16 unit GREEN · 361/361 arch GREEN)
Awaiting: gate-runner → auditor-backend (independent downstream)

---

## Files shipped

| File | Type | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/connections/telegram/__init__.py` | new | package init, cap: adrian.inbox |
| `vitalia/backend/src/modules/vitalia/connections/telegram/adapter.py` | new | TelegramAdapter shim around luana_core_connections |
| `vitalia/backend/src/modules/vitalia/connections/telegram/api/__init__.py` | new | api sub-package |
| `vitalia/backend/src/modules/vitalia/connections/telegram/api/dtos.py` | new | TelegramWebhookAck (Pydantic v2) |
| `vitalia/backend/src/modules/vitalia/connections/telegram/api/router.py` | new | POST /webhook — secret + dedup + tenant + dispatch |
| `vitalia/backend/alembic/versions/047_vitalia_telegram_dedup.py` | new | migration 047: vitalia_telegram_update_dedup IF NOT EXISTS |
| `vitalia/backend/src/main.py` | modified | include_router telegram_router at /api/v1/connections/telegram |
| `vitalia/backend/tests/modules/vitalia/connections/test_telegram_webhook_security.py` | new | 16 tests covering V-NF-1, V-FN-5, V-FN-6 |
| `vitalia/docs/product/stories/.../T-BE-1-impl-log.md` | new | implementation log |

---

## Gate summary

| Gate | Result |
|---|---|
| ruff check (new files) | PASS — 0 errors |
| ruff format (new files) | PASS — 0 violations |
| Unit tests T-BE-1 (16 tests) | PASS — 16/16 |
| Architecture fitness (361 tests) | PASS — 361/361 |
| test_response_model_required | PASS — TelegramWebhookAck response_model on /webhook |
| Migrations idempotent | PASS — raw SQL IF NOT EXISTS |
| Arch: tenant_id scope | PASS — dedup table PK (tenant_id, update_id) |
| Arch: cross-brand isolation | PASS — NONE touched |
| Arch: engine read-only | PASS — 0 edits to core/ |

---

## Validators covered

| Validator | Test | Result |
|---|---|---|
| V-NF-1 webhook secret + dedup | test_invalid_secret_returns_ack_no_dispatch | GREEN |
| V-NF-1 webhook secret + dedup | test_duplicate_update_id_no_second_dispatch | GREEN |
| V-NF-4 response_model every route | TestTelegramWebhookResponseModel | GREEN |
| V-FN-5 SC-5 secret inválido + dedup | test_invalid_secret + test_duplicate | GREEN |
| V-FN-6 SC-6 tenant isolation | test_dispatch_receives_correct_tenant_id | GREEN |

---

## Key decisions

1. **Direct await vs background_tasks**: `_orchestrator_dispatch` is called via `await` (not `background_tasks.add_task`) so tests can assert `mock_dispatch.assert_called_once()`. Engine's `handle_telegram_webhook` manages its own debounce/background scheduling internally.

2. **Non-message filter in route**: The route filters `"message" not in payload` before dispatch (covers edited_message, channel_post, inline_query). Engine's `normalize_payload` would return None anyway — early exit keeps dispatch clean.

3. **Anti-retry-storm**: Never return 4xx. Invalid secret, duplicate update_id, missing tenant → all return `TelegramWebhookAck(ok=True)` with internal discard + structlog.

4. **Tenant resolution phase 1**: `VITALIA_TELEGRAM_DEFAULT_TENANT_ID` env fallback for dev. Multi-tenant: queries `channel_connections WHERE channel_type='telegram' AND is_active=TRUE LIMIT 1`. Full per-bot token matching deferred (single bot phase).

5. **Adapter shim**: `TelegramAdapter` delegates to `luana_core_connections.TelegramChannel` (lazy import) with graceful fallback for test env (stub mode). No reimplementation — anti-duplication.md compliant.

---

## Live-verify status

DoD #37 (dod_live_verified) = false pending.
Pre-conditions for live-verify:
- `VITALIA_TELEGRAM_WEBHOOK_SECRET` env set in vitalia/.env.dev
- `VITALIA_TELEGRAM_DEFAULT_TENANT_ID` env set
- Migration 047 applied: `alembic upgrade head` inside container
- Telegram bot configured with setWebhook pointing to dev tunnel

Signal to PM: live-verify requires Telegram bot credentials + dev tunnel. Cannot exercise live without those values configured. Ping Chris for env values + route to live-verify phase.

---

## Warnings (non-blocking)

- Bidirectional validator advisory: SOFT_DRIFT (drift=2, pre-existing unrelated caps — not introduced by T-BE-1)
- DeprecationWarning `luana_core_platform.core.config.settings` (pre-existing in TelegramChannel engine — not in scope)
- Pre-existing ruff errors in `scheduling_hold_repository.py` (T-BE-2 scope, not touched)
