---
proposal_id: 2026-06-04-llm-gateway-chinese-first
state: proposed
opened_date: 2026-06-04
opened_by: /dev-team (nicolify-r1-abel-icp-buyer)
ratified_by: pending            # Chris gave direction (Chinese-first, model-independent); doc ratify pending
ratified_date: null
migrated_date: null

# Origen
origin_story: nicolify/docs/product/stories/nicolify-r1-abel-icp-buyer
origin_trigger: >
  Chris (2026-06-04): "el mejor camino para tener multiples providers LLM y poder
  usarlos en distintas partes del flujo dependiendo de la carga cognitiva ... un
  patron que permita que el manejo sea independiente del modelo para que cuando
  salgan mejores modelos simplemente hagamos el switch ... KimiK2 y Deepseek son
  la base, OpenAI solo excepcion."
origin_brands: [nicolify]       # surfaced here; applies to ALL brands

# Target
target_package: core/luana-core-llm + core/luana-core-platform/core/config.py + root docker-compose.dev.yml
target_module: deploy/litellm/ (shared gateway) + AI_PROVIDER_*/AI_MODEL_* defaults
target_ep: null                 # no new Extension Point; uses existing ModelRole abstraction

# Impact assessment
semver_bump: minor              # default-flip of AI_MODEL_*/AI_PROVIDER_* + shared infra service; backward-compatible (env-overridable)
breaking_change: false
brands_affected_consumers: [nicolify, vitalia, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
---

# Proposal — LLM Gateway: Chinese-first, model-independent (platform-wide)

## § 0 — TL;DR

El engine YA tiene la abstracción correcta para "usar el modelo según la carga
cognitiva, independiente del modelo": **`ModelRole`** (NANO/FAST/REASONING/AGENT/
VISION/EMBEDDING) + resolución `ModelRole → (provider, model)` vía
`AI_PROVIDER_<ROLE>` / `AI_MODEL_<ROLE>` (env) o binding per-tenant (DB), y el
transporte es **un gateway OpenAI-compatible** (`ChatOpenAI(base_url=LITELLM_BASE_URL)`).

La decisión cross-brand NO es "litellm sí/no" — es **qué gateway** + **qué defaults**.
**Recomendación (ratificada en dirección por Chris):** LiteLLM Proxy como gateway
COMPARTIDO de plataforma, política **Chinese-first** (DeepSeek V4 Flash + Kimi K2,
OpenAI = excepción), model-independence vía la capa `ModelRole` ya existente.

## § 1 — Findings verify-first

| Pieza | Estado | Evidencia |
|---|---|---|
| Capa "carga cognitiva" (`ModelRole`) | ✅ YA EXISTE en engine | `core/luana-core-platform/core/enums.py::ModelRole` + `config.py::get_provider_for_role` (override `AI_PROVIDER_<ROLE>`) |
| Transporte gateway OpenAI-compat | ✅ YA EXISTE | `core/luana-core-llm/providers/litellm.py::LiteLLMService` = `ChatOpenAI(base_url=LITELLM_BASE_URL, model="{provider}/{model}")` |
| Per-tenant model override | ✅ YA EXISTE | `core/luana-core-llm/infrastructure/role_binding_repository.py` |
| Defaults apuntan a OpenAI | ⚠️ default-flip needed | `config.py`: `AI_PROVIDER=openai`, `AI_MODEL_FAST="gpt-4o-mini"`, etc. |
| Pricing snapshots para modelos chinos | ❌ falta | cost_usd=null en `growth_studio_event` (token counts SÍ se registran) |

**Conclusión:** model-independence NO requiere código nuevo — requiere (a) un gateway
compartido con los providers chinos + (b) flip de defaults a Chinese-first + (c)
pricing snapshots de DeepSeek/Kimi. El "switch" a un modelo mejor = cambiar UN valor
(`AI_MODEL_<ROLE>` env / binding DB / `litellm_params.model` en el config del proxy).

## § 2 — Arquitectura recomendada

```
ALL brand backends ──OpenAI-compat──▶ LiteLLM Proxy :4000 ──▶ DeepSeek (V4 Flash)
  (LITELLM_BASE_URL)   1 container compartido, holds keys   ──▶ Moonshot (Kimi K2)
                       model_list + fallbacks                ──▶ OpenAI (excepción)
```

**Matriz cognitive-load → provider/model (default propuesto):**

| ModelRole | Uso | Provider | Modelo | Razón |
|---|---|---|---|---|
| NANO | clasificación, routing, intent | deepseek | deepseek-v4-flash (non-thinking) | $0.14/$0.28 · 1M ctx · barato |
| FAST | extracción estructurada (ej. abel ICP) | deepseek | deepseek-v4-flash (non-thinking) | barato, sin desperdicio de reasoning |
| REASONING | análisis complejo | deepseek | deepseek-reasoner (thinking) | thinking mode, sigue barato |
| AGENT | orquestación tool-use (los agentes) | kimi | kimi-k2.5 | mejor agentic/tool-use, 256K ctx |
| VISION | multimodal | kimi | kimi-k2.5 | multimodal |
| EMBEDDING | embeddings | openai | text-embedding-3-large | **excepción** — no hay embedding chino barato fuerte hoy |

**Fallback nativo del proxy:** deepseek↔kimi (nunca cae silencioso a OpenAI para chat).

**Por qué LiteLLM Proxy (vs SDK in-process / hosted):** (a) el engine ya está escrito
para gateway OpenAI-compat — cero cambio de código; (b) **un container sirve a todas
las marcas** → keys en UN lugar (no duplicadas por brand); (c) fallback/retry/budget/
spend-log/rate-limit nativos (alinean token-economy + observability rules nicolify);
(d) swap de provider sin redeploy.

## § 3 — Lo que YA quedó hecho + verificado live (dev enablement, nicolify)

Para desbloquear `nicolify-r1-abel-icp-buyer` (extract→borrador necesitaba LLM real),
se levantó el gateway en dev — reversible, sin tocar core:

- `deploy/litellm/config.dev.yaml` (tracked, sin secretos) — model_list provider-prefixed (`deepseek/deepseek-v4-flash`, `kimi/kimi-k2`, …) + fallbacks + master_key.
- `deploy/litellm/.env` (gitignored) — keys DEV DeepSeek + Moonshot + OpenAI.
- `scripts/litellm-proxy-up.sh` (idempotente) — proxy `luana_litellm_dev` en `luana_dev_net:4000` (alias `visionarias_litellm` back-compat).
- `nicolify/.env.dev` (gitignored) — `AI_PROVIDER_*` + `AI_MODEL_*` Chinese-first + `LITELLM_BASE_URL`.
- **Verificado live (2026-06-04):** `POST /api/v1/abel/icp/extract` → DeepSeek V4 Flash → borrador real de alta calidad (vertical/geo/dolor/ángulo/3 signals/2 buyers, Spanish neutro), `status=borrador origin=draft` (RN-3), `growth_studio_event` emitido + persistido **sin PII** (icp_id hasheado), cost attribution `model=deepseek/deepseek-v4-flash` tokens 1171/1443. 0 traceback.

## § 4 — Lo que falta (platform integration — ESTE proposal lo decide)

1. **Fold el proxy a `docker-compose.dev.yml` raíz** como servicio first-class compartido (hoy script standalone). Cada `{brand}/.env.dev` apunta `LITELLM_BASE_URL` al mismo proxy.
2. **Flip de defaults Chinese-first en `core/luana-core-platform/core/config.py`** (`AI_PROVIDER`/`AI_MODEL_*`) — para que TODAS las marcas hereden Chinese-first sin override per-brand. ⚠️ default-flip → seguir `.claude/rules/anti-default-flip-audit.md` (grep consumidores + correr suites con ambos valores). NO es flag side-effect, pero cambia el provider real → auditar.
3. **Pricing snapshots DeepSeek + Kimi** en `core/luana-core-observability` (hoy cost_usd=null para modelos chinos). Sin esto el token-economy de nicolify no calcula margen.
4. **Secret management prod** — las keys hoy viven en `.env` gitignored (dev OK, ratificado). Prod necesita un secret store (no env file).
5. **Producción del gateway** — el proxy en prod (HA, auth, budget per-tenant) cuando se provisione infra (hoy deferred per `github-actions-deferred.md`).

## § 5 — Riesgo + rollback

- **Riesgo bajo en dev:** todo override por env; borrar el proxy (`docker rm -f luana_litellm_dev`) + revertir `.env.dev` vuelve al estado previo.
- **Riesgo del default-flip (§4.2):** suites que asumen OpenAI model strings podrían romper → auditar antes de mergear el flip a core.
- **Dependencia externa:** DeepSeek/Moonshot APIs. Mitigado por fallback cross-provider en el proxy.

## § 6 — Acceptance criteria

- [ ] Chris ratifica la arquitectura (Chinese-first + LiteLLM proxy compartido + matriz §2).
- [ ] `/pm-luana` agenda: (a) proxy en root compose, (b) default-flip auditado en core config, (c) pricing snapshots chinos.
- [x] Dev gateway funcionando + extract live verificado (nicolify) — hecho 2026-06-04.

## § 7 — Notas de modelos (research 2026-06-04, live)

- **DeepSeek:** `deepseek-chat`/`deepseek-reasoner` deprecan 2026/07/24 → mapean a modos non-thinking/thinking de `deepseek-v4-flash` (1M ctx, 384K output, cache 98% off). Revisar el config del proxy antes de esa fecha (usar param thinking-disabled sobre `deepseek-v4-flash`).
- **Kimi/Moonshot:** `kimi-k2.5` (256K ctx) verificado; `kimi-k2.6` / `kimi-k2-thinking` disponibles. litellm provider = `moonshot/`, key `MOONSHOT_API_KEY`, base `https://api.moonshot.ai/v1`.
- **Qwen** (futuro, mencionado por Chris): agregar como nuevo model_list entry + `AI_PROVIDER_<ROLE>=qwen` cuando se sume — cero cambio de código.

Sources: api-docs.deepseek.com/quick_start/pricing · docs.litellm.ai/docs/providers/moonshot · openrouter.ai/moonshotai/kimi-k2.6
