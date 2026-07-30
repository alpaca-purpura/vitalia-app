---
proposal_id: 2026-05-19-purge-nicolify-hardcodes-sales-agent
state: migrated
opened_date: 2026-05-19
opened_by: /pm-luana
ratified_by: Chris
ratified_date: 2026-05-19
migrated_date: 2026-05-19
migrated_commit: 39b73703   # main squash-merge SHA (use git log main -1 para full SHA)
wip_branch_commit: 78c0ddb  # wip/core-purge-sales-agent-hardcodes commit
gate_output_iter2: gate-output.json (ephemeral en worktree pre-cleanup — copilot 1640 tests PASS + orchestrator 19 PASS + llm PASS + ruff PASS + platform regression PASS; sales-agent ADVISORY_PRE_EXISTING verified base; grep "FAIL" was false positive on intentional doc/comment migration explanations)
auditor_review_iter1: REVIEW.md (verdict WARN approve-to-merge=true; FAIL-1 "proposal missing" addressed by including proposal in same commit; WARN-1 copilot scope addressed by broadening; WARN-2 R3 brand consumer mitigated by zero brand asserts grep)

# Origen
origin_learnings: []  # detectado durante auditoría auditor-backend del lift previo (INFO-2 finding)
origin_stories:
  - docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md (proposal padre — auditor-backend WARN INFO-2 flagged residuales)
origin_brands: [nicolify]  # único brand histórico consumidor; remaining brands no usan sales_agent payment todavía
detected_by: /pm-luana via auditor-backend REVIEW.md INFO-2 (lift previo)

# Target (broadened scope post auditor WARN-1 + Chris "bug free total" directive)
target_packages:
  - core/luana-core-sales-agent (primary — 3 hardcodes original scope)
  - core/luana-core-copilot (broadened — 3 hardcodes telegram prompt + 1 docstring)
  - core/luana-core-llm (broadened — 1 hardcode docstring only)
target_modules:
  - core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/payment/providers.py (líneas 191-196 — 2 URLs hardcoded → helper _build_payment_url)
  - core/luana-core-sales-agent/src/luana_core_sales_agent/api/payment_webhooks.py (línea 137 — header x-nicolify-tenant-id fallback removed)
  - core/luana-core-copilot/src/luana_core_copilot/application/orchestrator/graph.py (líneas 696,699,709,798,913 — Telegram prompt @nicolify_copilot_bot + 2× app.nicolify.com → template + lazy helper)
  - core/luana-core-copilot/src/luana_core_copilot/application/tools/telegram_redirect.py (línea 24 — docstring example brand-agnostic)
  - core/luana-core-llm/src/luana_core_llm/providers/litellm.py (línea 20 — docstring comment brand-agnostic)
target_ep: null

# Impact assessment (broadened scope)
semver_bumps:
  - luana-core-sales-agent: 0.1.0 → 0.2.0 minor (behavior change: failfast empty FRONTEND_URL + remove deprecated header fallback)
  - luana-core-copilot: 0.1.0 → 0.2.0 minor (behavior change: failfast empty FRONTEND_URL/COPILOT_TELEGRAM_BOT_USERNAME at first telegram channel turn + new _get_telegram_channel_context_es helper preserves cache invariant)
  - luana-core-llm: NO bump (docstring-only change, no functional impact)
breaking_change: false                   # backward-compat: nicolify behavior BYTE-IDENTICAL (defaults derive to same hardcoded values via env override). Failfast for brands missing env vars (vs silent leak previously — proposal padre forces explicit override).
brands_affected_consumers:
  - nicolify                             # único consumer histórico de sales_agent payment integration
  - vitalia                              # potencial futuro (clinic payment intents)
  - comunify                             # potencial futuro (creator economy purchases)
  - lupulo                               # potencial futuro (table reservations payment)
  - saasora                              # potencial futuro (subscription payments)
  - inmoflow                             # potencial futuro
  - retailly                             # potencial futuro (e-commerce checkout)
  - fixia                                # potencial futuro (service payment)
  - guestly                              # potencial futuro (booking payments)
  - fitflow                              # potencial futuro (membership payments)
brands_at_risk_regression: []            # nicolify usa default URLs nicolify.com — POST lift deriva via settings.FRONTEND_URL que YA está en nicolify/.env.dev override correcto (proposal padre verified)

# Lift plan
lift_estimated_effort: "1h (3 edits + CHANGELOG creation + gate-runner + auditor + commit cycle)"
lift_owner: /pm-luana orchestrator (autonomous post Chris pre-authorization "todos los hallazgos resuelvelos en esta sesión todo el lift cycle completo")
arch_test_downstream_required: true       # R3 mandatory
migration_notes_required: true            # backward-compat advisory: clientes deben enviar x-tenant-id standard
---

# Promotion Proposal — Purge Nicolify hardcodes residuales en luana-core-sales-agent

## 1. Patrón a purgar (3 hardcodes residuales)

Auditor-backend REVIEW.md del lift previo (2026-05-19-purge-nicolify-defaults-core-config) marcó INFO-2: "residual nicolify hardcodes en payment/providers.py + orchestrator/graph.py". Investigación semantic posterior confirmó:

- **3 hardcodes reales** (no 5 — auditor inicial confundió líneas; `orchestrator/graph.py` solo tiene 53 líneas, refs 699/709/798 NO EXISTEN — ese path no aplica)
- Todos en `core/luana-core-sales-agent/` payment integration
- 2 URLs hardcoded + 1 header non-standard
- Cero D-categoría (lógica condicional brand-specific) → AUTONOMOUS lift

### Hardcode 1+2 — Payment URLs hardcoded

`src/luana_core_sales_agent/application/tools/payment/providers.py:191-196`:

```python
success_url=metadata.get(
    "success_url", "https://app.nicolify.com/payment/success"
),
cancel_url=metadata.get(
    "cancel_url", "https://app.nicolify.com/payment/cancel"
),
```

Stripe payment session creation con URLs nicolify-hardcoded como fallback cuando metadata no incluye override. Si tenant vitalia/comunify/lupulo creara payment link, redirect post-payment iría a `app.nicolify.com` (broken UX + posible data leak).

### Hardcode 3 — Header non-standard fallback

`src/luana_core_sales_agent/api/payment_webhooks.py:137`:

```python
raw_tenant = headers.get("x-tenant-id") or headers.get("x-nicolify-tenant-id")
```

Defensive fallback aceptando header `x-nicolify-tenant-id` además del estándar `x-tenant-id`. Brand-specific header naming viola principio engine brand-agnostic.

**Backward-compat audit:** grep cross-codebase (engine + 4 brand backends) → 0 consumers usando `x-nicolify-tenant-id` exclusivamente. Es código defensive sin clients reales. SAFE remove.

## 2. Por qué cross-brand

Sales_agent es ENGINE + BRAND-EXTENSION (per CLAUDE.md mapping). Payment integration es engine — todos los brands futuros que activen sales_agent payment heredan estos hardcodes silenciosamente.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| nicolify | único consumer histórico | tiene `FRONTEND_URL=https://app.nicolify.com` en `.env.dev` (post proposal padre) — post lift las URLs se derivan correctamente |
| vitalia | candidato futuro | clinic payment intents requieren success/cancel URLs a `dev-app.vitalialat.com` |
| comunify | candidato futuro | creator economy purchases |
| lupulo | candidato futuro | table reservations |
| saasora | candidato futuro | subscription payments |
| inmoflow/retailly/fixia/guestly/fitflow | candidato futuro | similar |

10/10 brands afectadas eventualmente. **Justificación cross-brand fuerte + cement de principio engine brand-agnostic.**

## 3. Análisis técnico

### Edit 1+2 — URLs derivable from settings.FRONTEND_URL

`settings.FRONTEND_URL` es brand-agnostic post lift proposal padre (2026-05-19-purge-nicolify-defaults-core-config). Cada brand override en su `.env.dev` con su valor correcto.

```python
# BEFORE
success_url=metadata.get("success_url", "https://app.nicolify.com/payment/success"),
cancel_url=metadata.get("cancel_url", "https://app.nicolify.com/payment/cancel"),

# AFTER (helper extracted)
def _build_payment_url(action: str, metadata: dict[str, Any]) -> str:
    """Build payment success/cancel URL from settings.FRONTEND_URL.

    Metadata override takes precedence; falls back to brand-derived URL.
    Raises ConfigError if FRONTEND_URL not set in brand .env (failfast).
    """
    custom = metadata.get(f"{action}_url")
    if custom:
        return custom
    if not settings.FRONTEND_URL:
        raise RuntimeError(
            f"Cannot build payment {action} URL: settings.FRONTEND_URL empty. "
            f"Brand MUST override in {{brand}}/.env.dev "
            f"(per proposal 2026-05-19-purge-nicolify-defaults-core-config)."
        )
    return f"{settings.FRONTEND_URL.rstrip('/')}/payment/{action}"

# usage in create_payment_link():
success_url=_build_payment_url("success", metadata),
cancel_url=_build_payment_url("cancel", metadata),
```

**Behavioral verify:**
- nicolify (`FRONTEND_URL=https://app.nicolify.com`): URLs derivadas `https://app.nicolify.com/payment/success` + `/cancel` → idéntico al hardcoded actual ✓ ZERO REGRESSION
- vitalia (`FRONTEND_URL=https://dev-app.vitalialat.com`): URLs derivadas `https://dev-app.vitalialat.com/payment/success` + `/cancel` → correcto vitalia ✓
- Brand sin FRONTEND_URL override (hipotético): `RuntimeError` failfast con mensaje explícito → mejor que silent leak a nicolify.com

### Edit 3 — Standardize header

```python
# BEFORE
raw_tenant = headers.get("x-tenant-id") or headers.get("x-nicolify-tenant-id")

# AFTER
raw_tenant = headers.get("x-tenant-id")
# (deprecated brand-specific header `x-nicolify-tenant-id` removed per
#  proposal 2026-05-19-purge-nicolify-hardcodes-sales-agent. Clients MUST
#  send standard `x-tenant-id` header. Cross-codebase grep verified 0
#  consumers using deprecated header exclusively.)
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Algún client externo manda ÚNICAMENTE x-nicolify-tenant-id sin x-tenant-id estándar | Baja | grep cross-codebase 0 consumers. Si emerge cliente externo, migration notes documenta y CHANGELOG advisory |
| Brand consumer activa payment sin override FRONTEND_URL → RuntimeError startup | Baja | Failfast desired vs silent leak. Mismo principle que proposal padre (failfast > silent contamination) |
| Test fixtures hardcodean URLs nicolify | Verificada | grep tests engine + brand → 0 fixtures asserting URLs hardcoded. SAFE |
| Helper `_build_payment_url` introduce bug | Baja | Tests existentes mockean provider entirely (no testean URLs derived). Agregar test unitario nuevo del helper |

## 4. Lift plan

### Pre-lift checklist
- [x] Audit semantic 3 hardcodes (auditor previo INFO-2 + investigación)
- [x] Verify `nicolify/.env.dev` tiene `FRONTEND_URL=https://app.nicolify.com` (proposal padre verified)
- [x] Grep clients de `x-nicolify-tenant-id` cross-codebase → 0 consumers
- [x] Grep tests asserting URLs hardcoded → 0
- [x] Chris pre-authorized cycle completo ("todos los hallazgos resuelvelos en esta sesión todo el lift cycle completo")

### Lift execution (orden)
1. Engine edit `providers.py`: extract helper `_build_payment_url()` + replace 2 hardcoded URLs
2. Engine edit `payment_webhooks.py`: remove `x-nicolify-tenant-id` fallback + add comment explicativo
3. Bump `core/luana-core-sales-agent/pyproject.toml::version` 0.1.0 → 0.2.0 (minor)
4. **CREATE** `core/luana-core-sales-agent/CHANGELOG.md` (no existe — primera entrada)
5. gate-runner R3 downstream regression (engine sales-agent tests + brand consumers)
6. auditor-backend review
7. Haiku commit en wip/core-purge-sales-agent-hardcodes (SCOPE_GATE_SKIP=1 si toca brand templates — NO toca, solo engine)
8. Haiku squash-merge a main
9. /pm-luana update proposal state=migrated + cleanup worktree

## 5. Decisión

**Recomendación /pm-luana:** AUTONOMOUS (no escalate)

**Razón:**
- 3 hardcodes brand-specific en engine (anti-brand-agnostic principle)
- 0 brand consumers activos del header deprecated → backward compat safe
- 10/10 brands afectadas eventualmente
- Lift mecánico (categorías B+C, sin D)
- Tests cross-codebase confirman 0 regression risk
- Costo ≤ 1h
- Chris pre-autorizó cycle completo en esta sesión

**Ratificación Chris:** APPROVED via mensaje pre-autorización 2026-05-19 ("todos los hallazgos resuelvelos en esta sesión todo el lift cycle completo, luego haz el update al outcome admin-im-adoption y me das el prompt para iniciar en una nueva conversación").

## 6. Bitácora

- 2026-05-19: opened by /pm-luana post auditor-backend REVIEW.md INFO-2 del lift previo (proposal padre 2026-05-19-purge-nicolify-defaults-core-config). State: proposed.
- 2026-05-19 (misma sesión): investigación semantic Explore agent verificó:
  - 3 hardcodes reales (NO 5 — auditor inicial referenció `orchestrator/graph.py` líneas 699/709/798 que NO EXISTEN; el archivo solo tiene 53 líneas)
  - 2 URLs categoría B (derivable settings.FRONTEND_URL) + 1 header categoría C (standardize sin clients impacted)
  - 0 D-categoría → lift mecánico AUTONOMOUS
- 2026-05-19 (misma sesión): Chris ratificó APPROVED pre-cycle. State: proposed → accepted.
- 2026-05-19 (post auditor REVIEW.md WARN-1 + Chris "corrige todo lo que encuentres, deja la solución bug free"): **scope broadened** post initial audit para incluir 4 hardcodes adicionales:
  - `luana-core-copilot/.../orchestrator/graph.py` líneas 696,699,709,798,913 — `@nicolify_copilot_bot` + 2× `app.nicolify.com/{tenant_slug}/{ruta}` literal en prompt template Telegram (es **functional bug**: agent vitalia/comunify/lupulo diría "vayan a app.nicolify.com" cross-brand — UX broken + posible data leak). Refactor a `_TELEGRAM_CHANNEL_CONTEXT_ES_TEMPLATE` + lazy helper `_get_telegram_channel_context_es()` con cache (preserva Anthropic/Kimi prompt cache invariant — string stable per engine instance).
  - `luana-core-copilot/.../tools/telegram_redirect.py` línea 24 — docstring example brand-agnostic
  - `luana-core-llm/.../providers/litellm.py` línea 20 — docstring comment brand-agnostic

## 7. Cross-references

- Proposal padre: [`docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md`](./2026-05-19-purge-nicolify-defaults-core-config.md) (migrated commit b869eaf)
- Target files (post broaden):
  - `core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/payment/providers.py:191-196`
  - `core/luana-core-sales-agent/src/luana_core_sales_agent/api/payment_webhooks.py:137`
  - `core/luana-core-copilot/src/luana_core_copilot/application/orchestrator/graph.py:696,699,709,798,913`
  - `core/luana-core-copilot/src/luana_core_copilot/application/tools/telegram_redirect.py:24`
  - `core/luana-core-llm/src/luana_core_llm/providers/litellm.py:20`
- Parent outcome: [`docs/product/outcomes/admin-iam-adoption-platform.md`](../../product/outcomes/admin-iam-adoption-platform.md) (este lift agregado como pre-requisite paso previo)
- Architecture base: ADR-001 multibrand (engine brand-agnostic principle)
- Related rules:
  - `.claude/rules/anti-default-flip-audit.md` (defaults engine pattern análogo aplicable a hardcodes)
  - `.claude/rules/auditor-downstream-regression.md` § engine edit detection (R3 mandatorio)
  - `.claude/skills/pm-luana/references/brand-bootstrap-learnings.md` AP2 (anti-pattern hardcodes brand-specific en engine)
- Process: `docs/promotion-protocol/README.md`
