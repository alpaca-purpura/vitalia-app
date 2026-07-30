<!-- voseo-allowed: internal architectural audit doc, Chris-targeted, not user-facing UI -->

> [HISTÓRICO — read-only. Auditoría previa al nicolify-reset (2026-05-29) y reorg multibrand. Estructuras/paths descritos pueden no existir hoy. Conservado por trazabilidad.]

# Luana Core — Purge Audit

> **Status:** Draft v0.1 — 2026-05-15 (F4 reorg multibrand)
> **Owner:** /pm-luana + Chris (alpacapurpura@)
> **Purpose:** Identificar y catalogar leakage brand-specific en los 26 paquetes `core/luana-core-*`. Output: tabla candidatos a purge/refactor con severity HIGH/MEDIUM/LOW.
> **Scope:** Solo `core/luana-core-*/src/`. Tests + scripts excluidos del scan inicial.

## Filosofía de purga

> *"El core nunca sabe de brand específica. Cero `if (brand === 'X')`. Diferencias se materializan via brand-config declarativa o extension points formales."*

Cualquier ref a `visionarias`, `nicolify`, o lógica brand-specific hardcoded en core es un **bug** que debe purgarse. Excepción: ADRs históricos/migration notes que mencionan el nombre como contexto.

## Severity classification

| Severity | Significado | Acción |
|---|---|---|
| **HIGH** | Refs explícitas a brand específica + bloqueo a otras brands | Purge inmediato, refactor a config/extension |
| **MEDIUM** | Refs sospechosas que requieren context check (legacy defaults, comments, doc strings) | Audit caso-por-caso, refactor si confirmado leakage |
| **LOW** | Refs a vocabulario sectorial (coaching, gym, etc.) que pueden ser legítimas en preset packs o ejemplos | Verify intent. Probablemente OK. |

## Resultados scan

### "visionarias" hits (14 total cross-packages)

| Package | Hits | Severity | Razón |
|---|---|---|---|
| `luana-core-sales-agent` | 5 | **MEDIUM** | Tests/configs sales agent — verify si son hardcoded en runtime o solo metadata legacy |
| `luana-core-analytics-engine` | 3 | **MEDIUM** | Probable refs a database name `visionarias_logs` (legacy SQL DROP) o configs ETL |
| `luana-core-platform` | 2 | **HIGH** | Config defaults: `SHOPIFY_APP_URL`, `QDRANT_COLLECTION`, `LITELLM_BASE_URL` apuntan a `visionarias.*` o container `visionarias_litellm` |
| `luana-core-tenant-domains` | 1 | **MEDIUM** | Verify context |
| `luana-core-llm` | 1 | **MEDIUM** | LiteLLM config probable apunta a container `visionarias_litellm` |
| `luana-core-iam` | 1 | **LOW** | Verify — probablemente comentario doc |
| `luana-core-copilot` | 1 | **MEDIUM** | Verify context |

### "nicolify" hits (60 total cross-packages)

| Package | Hits | Severity | Razón |
|---|---|---|---|
| `luana-core-copilot` | 33 | **HIGH** | Acoplamiento masivo — extractors + KB + workflows + prompts probablemente hardcoded a Nicolify domain |
| `luana-core-sales-agent` | 8 | **HIGH** | Payment webhooks + payment providers + tools probablemente Nicolify-specific (Stripe Connect for agencies?) |
| `luana-core-campaigns` | 4 | **MEDIUM** | Templates campaign probable Nicolify-specific |
| `luana-core-platform` | 3 | **HIGH** | Config defaults Nicolify-specific (URLs, env vars) |
| `luana-core-observability` | 3 | **MEDIUM** | Probable refs a tenant Nicolify en docs/comments |
| `luana-core-llm` | 2 | **MEDIUM** | LiteLLM config + provider keys probable refs Nicolify env vars |
| `luana-core-extension-sdk` | 2 | **LOW** | Probable docs/examples mencionando Nicolify como caso |
| `luana-core-tenant-domains` | 1 | **LOW** | Verify |
| `luana-core-offer-studio` | 1 | **MEDIUM** | Probable preset Nicolify "agency_services" |
| `luana-core-events` | 1 | **LOW** | Probable docstring |
| `luana-core-brand-studio` | 1 | **LOW** | Probable preset Nicolify "agency_b2b" |

### "Brand-coupling vocab" hits

| Package | Vocab | Hits | Severity | Razón |
|---|---|---|---|---|
| `luana-core-sales-agent` | `appointment` | 12 | **LOW** | Genérico scheduler — OK, aplica cross-brand (vitalia, fitflow, lupulo, etc.) |
| `luana-core-copilot` | `coaching` | 5 | **MEDIUM** | Preset Visionarias-style coaching mencionado en audit §6.1 item #7 — purgar a `coaching_offers` preset pack vertical-creator-economy |
| `luana-core-offer-studio` | `coaching` | 4 | **MEDIUM** | Idem — preset coaching debe vivir en `creator_economy_v1` preset pack |
| `luana-core-offer-studio` | `gym` | 3 | **LOW** | Preset gym genérico — OK aplica fitflow |
| `luana-core-channels` | `creator` | 3 | **LOW** | Probable doc/example o channel name |
| `luana-core-platform` | `appointment` | 4 | **LOW** | Genérico locale/timezone scheduler — OK |

## Candidatos prioritarios a purgar

### HIGH severity (purga inmediata recomendada)

#### 1. `luana-core-platform/src/luana_core_platform/core/config.py` — Visionarias defaults

```python
# Líneas confirmadas problemáticas:
SHOPIFY_APP_URL: str = ""  # comment: "https://api.visionarias.ai"
QDRANT_COLLECTION: str = "visionarias_knowledge"
QDRANT_COLLECTION_HYBRID: str = "visionarias_hybrid"
LITELLM_BASE_URL: str = "http://visionarias_litellm:4000/v1"
```

**Refactor propuesto:**
- `QDRANT_COLLECTION = "luana_knowledge"` (default genérico) o `f"{brand}_knowledge"` parametrizable
- `LITELLM_BASE_URL` default vacío → cada brand pin via `{brand}/config/.env`
- Container name `visionarias_litellm` → `luana_litellm` o `{brand}_litellm` (requiere coordinación infra: Docker compose + K8s manifests)

**Bloqueante:** infra (Docker compose, K8s manifests, env vars en deploy/cloudflared/). Ticket separate.

#### 2. `luana-core-copilot/src` — 33 hits "nicolify"

Probable acoplamiento masivo. Workflows + extractors + KB + prompts del módulo copilot tienen refs hardcoded a Nicolify domain (agencies, propuestas, CRM B2B).

**Refactor propuesto:** auditoría ticket-por-ticket. Cada ref:
- Si es ejemplo/comment → reemplazar por slug genérico o `{brand}` placeholder
- Si es lógica runtime → extraer a `nicolify/backend/src/modules/nicolify/copilot/` (brand extension)
- Si es prompt template → parametrizar via `BrandContext`

**Estimación:** 1-2 días auditoría + refactor incremental por ticket.

#### 3. `luana-core-sales-agent/src` — 8 hits "nicolify"

Payment webhooks (`api/payment_webhooks.py`) + payment providers (`application/tools/payment/providers.py`) probablemente Nicolify-specific (Stripe Connect agencies model).

**Refactor propuesto:**
- Mover Nicolify-specific webhook handlers → `nicolify/backend/src/modules/nicolify/sales_agent/payment/`
- Generalizar provider abstraction en core (Stripe genérico, MercadoPago genérico)
- EP-3 toolRegister covers brand-specific payment tools

### MEDIUM severity (audit caso-por-caso, refactor selectivo)

| Package | Owner | Acción próxima sesión |
|---|---|---|
| `luana-core-analytics-engine` | `/pm-luana` | Verify si "visionarias_logs" DB ref es legacy SQL drop o runtime |
| `luana-core-llm` | `/pm-luana` | Confirmar LiteLLM proxy config (container name) — coordinar con HIGH item #1 |
| `luana-core-campaigns` | `/pm-luana` | Verify si templates Nicolify están en core o ya en `nicolify/backend/` |
| `luana-core-observability` | `/pm-luana` | Audit refs a tenant nicolify (probablemente docstrings, no runtime) |
| `luana-core-offer-studio` | `/pm-luana` | Auditar preset `agency_b2b` o similar — debería vivir en `nicolify/config/brand.yaml::preset_pack` |
| `luana-core-brand-studio` | `/pm-luana` | Idem |

### LOW severity (probablemente OK, sweep cosmetic)

- `appointment` vocab en core — genérico aplica cross-brand
- `gym`, `creator` vocab — genérico aplica fitflow/comunify
- Docstrings/comments con refs a Nicolify como ejemplo — actualizar a "ej. {brand}" placeholder

## Recomendaciones de ejecución

### Plan próxima sesión (post-reorg multimarca cierre)

**Sprint 1 (HIGH severity — bloqueantes promotion):**
1. `luana-core-platform/core/config.py` defaults purge (1 día)
2. `luana-core-copilot/src` audit + refactor 33 nicolify hits (2 días)
3. `luana-core-sales-agent/src` audit + refactor 8 nicolify hits + 5 visionarias hits (1-2 días)

**Sprint 2 (MEDIUM severity):**
4. `luana-core-analytics-engine` + `luana-core-llm` cleanup (1 día)
5. `luana-core-{campaigns, observability, offer-studio, brand-studio}` audit (1 día)

**Sprint 3 (LOW + infra):**
6. Docstrings/comments sweep cosmético (medio día)
7. Container name rename `visionarias_litellm → luana_litellm` (coordinación infra: Docker compose, K8s manifests, env vars en `{brand}/deploy/`) (1 día)

## Bloqueantes

- HIGH item #1 + item LOW infra: requieren coordinación con `{brand}/deploy/k8s/` manifests + `docker-compose.dev.yml`. NO purgar core sin actualizar deployment paralelo.
- HIGH items #2 + #3: requieren `/dev-team` ticket-por-ticket. No es scope master /pm.

## Notas operativas

- **NO purgar refs en docs/archive/** — son frozen históricos (snapshot pre-multibrand).
- **NO purgar refs en docs/architecture/luana-platform/01-core-audit.md** — son referencias técnicas legítimas (preset cleanup pendiente, container name K8s, SQL histórico).
- **Tests excluidos del scan** — auditarlos en sprint propio (probable que tests usen fixtures Nicolify-specific que también necesitan generalización).

## Bitácora

- 2026-05-15: scan completo F4 reorg multimarca. Output: 14 hits visionarias + 60 hits nicolify + 30+ hits brand-coupling vocab cross-package.
- Próxima acción: sprint 1 HIGH severity tickets cuando Chris ratifique prioridad.

## Cross-references

- `docs/architecture/luana-platform/01-core-audit.md` — plan multibrand original (catálogo 10 brands + cleanup §6.1)
- `.claude/rules/anti-duplication.md` — prevención cross-brand mirror
- `.claude/rules/auditor-downstream-regression.md` — R3 obligatorio para cualquier purge
- `core/luana-core-extension-sdk/` — EP-1..EP-18 (donde brand extensions deben vivir)
- `docs/promotion-protocol/` — workflow inverso (brand→core lift)
