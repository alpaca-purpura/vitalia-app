# Lucas — Analysis Constraints (defensive guardrails)

<!-- voseo-allowed: this file documents the voseo glossary verbatim for human reviewers; Lucas prompts/personas separately verified by pre-commit hook -->

> Per vitalia/.claude/rules/hipaa-lite.md + .claude/rules/spanish-text.md +
> 03-arch-agentic.md § 5.3 (cache slot architecture invariance).
>
> Hard constraints every Lucas stage analysis must respect. Enforced at the
> service layer + tool layer via input validation, output validation and
> PII sanitization. This MD documents the contract.

## 1. Tenant isolation

- Every Lucas service call MUST carry `tenant_id` + `clinic_id`.
- Every repository query filters on BOTH (HIPAA-lite dual filter).
- Tools defensively re-check `input.tenant_id == ctx_tenant_id` at entry;
  raises `PermissionError` on mismatch.

## 2. Timezone awareness

- Cron schedule per-tenant at 06:00 LOCAL tenant TZ
  (`TenantLocationContract.timezone` engine SSoT).
- `period` parameter is `YYYY-MM` — month-granularity, TZ-neutral at storage.
- Any datetime uses `utc_now()` for `created_at` / `expires_at` (UTC storage),
  translated to tenant TZ only at presentation layer.
- NEVER `datetime.utcnow()` (deprecated).

## 3. Currency handling

- Lucas DTOs include `currency: str | None` ISO-4217.
- Currency comes from `TenantLocale.currency` — NEVER hardcoded.
- Pydantic models do NOT default `currency = "USD"`.

## 4. PII / PHI sanitization (HIPAA-lite)

- Every observability write passes payload through `sanitize_payload`
  (engine SSoT — `luana_core_observability.recording.sanitization`).
- Lucas works with analytics aggregates ONLY. PHI fields (patient.name,
  dni, diagnosis, etc.) MUST NEVER appear in:
  - LLM input prompts (slot 3 tenant data is aggregated, not row-level)
  - Tool output DTOs
  - Trace event payloads
- `top_referrers` rows use `referrer_id` (UUID) — NEVER patient names.

## 5. Spanish neutro tuteo

- Lucas is UI chrome (cards in /marketing + /pipeline), NOT sales_agent voice.
- Tuteo only: `tú/puedes/tienes/configura`.
- NO voseo: forbidden `vos/sos/tenés/podés/sabés/mirá/dejá/poné/usá/elegí/...`
- Tenant voice override does NOT apply to Lucas (that is exclusively a
  sales_agent prerogative).

## 6. Cost discipline

- BudgetGuard pre-flight check before every LLM call
  (`agent_kind="copilot"` — Others pool, NOT sales_agent reserved).
- Daily cap per tenant: $0.25 USD (5 stages times $0.02-0.05 each).
- BudgetGuard exceeded → service returns `status='skipped_budget'` (no LLM call).
- 1h cache TTL on slots 1+2 — break-even at 3 reads.
- Cache prefix invariance: NO timestamps, NO `{tenant_name}` interpolated.
  Only `{stage}` is allowed per-stage caching.

## 7. Output discipline

- `RecommendationDTO.confidence` MANDATORY (per design forbidden).
- `RecommendationDTO.status` MUST be one of:
  `active | skipped_timeout | skipped_budget | applied | rejected`.
- LLM output parser is strict (TÍTULO/DETALLE/JUSTIFICACIÓN); non-matching
  output falls back to raw text in body field (logged warning).

## 8. Error recovery

- LLM timeout (30s per stage) → log + persist row `status='skipped_timeout'`
- BudgetGuard exceeded → persist row `status='skipped_budget'`
- LLM hallucinates impossible recommendation → reject, retry 1× stricter, skip
- DB query timeout (10s) → log + skip, prev snapshot remains available

## 9. Engine boundary (anti-duplication cardinal)

- Lucas tools + services consume engine packages via `from luana_core_* import`.
- Engine packages READ-ONLY for this story. Modify need → escalate /pm-luana.
- NO `_GROUP_MAP` mirror, NO `STAGE_CHANNEL_MAP` mirror — engine ChannelRegistry SSoT.
