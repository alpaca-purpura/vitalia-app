---
story_id: vitalia-fase2-adrian-canal-inbound
doc: 00-research
author: /pm-vitalia
date: 2026-06-04
purpose: >
  Investigación pre-refinement pedida por Chris: (1) qué hay en core + si slice-1 dejó
  código huérfano recuperable, (2) review del sales_agent legacy "state of the art",
  (3) review del sales_agent + agentic de vitalia, (4) estado del LLM gateway (cimientos).
secrets: false   # valores reales viven en deploy/litellm/.env + vitalia/.env.dev (gitignored)
---

# 00-research — canal-inbound (Adrián) · estado real del terreno

> **Veredicto de naturaleza:** `extend` confirmado. El cerebro YA existe (engine). La extensión de
> marca YA existe in-tree y registrada. Lo que **falta es enchufar el runtime** (el loop nunca se
> cableó) + un **adapter Telegram nuevo**. NO se construye el agente.

## 1. Dónde vive el cerebro (CONSUMIR vía import — read-only, /pm-luana para tocarlo)

| Pieza | Path (engine) | Estado |
|---|---|---|
| Orchestrator inbound | `core/luana-core-sales-agent/.../application/orchestrator/chat.py` → `ChatOrchestrator.handle_telegram_webhook()` (L93-128) · `handle_whatsapp_webhook()` · `handle_incoming_webhook()` (L139-169) | ✅ existe en core |
| Smart debounce (ráfagas) | `.../orchestrator/smart_debounce_runner.py` (L46-157) — 0.5s + reset-check + chequeo semántico LLM + 4-6s + lock | ✅ §3 protected |
| Grafo + nodos | `.../orchestrator/graph.py` + `.../agents/sales/graph.py` (7 nodos: supervisor/qualifier/product_expert/closer/signal_accumulator/tool_executor/escalation) | ✅ |
| Pipeline de turno | `.../orchestrator/conversation_pipeline.py` (fetch config → load checkpoint → handle_human_mode → build state → invoke con typing → save → deliver) | ✅ |
| Contrato msg | `IncomingMessage(user_id, text, channel_type, metadata)` → grafo → `OutgoingMessage(...)` vía `BaseChannel.normalize_payload()` / `OutputManager.process_response()` | ✅ |
| Modo por-conversación | `handler_mode == "human"` ya hace bypass del AI en el pipeline (base para 🤖/🤝/👤) | ✅ parcial |
| Format + intent | `core/luana-core-channels/format_for_channel.py` + `intent_detector.py` (whatsapp/telegram/sms/email/instagram_dm/voice) | ✅ |
| Compliance PHI | `core/luana-core-compliance/` (firewall outbound) | ✅ |

**Receivers inbound NO viven en el engine** — cada marca cablea su webhook → orchestrator. (Por diseño.)

## 2. "slice-1 código huérfano recuperable" — RESPUESTA

**Sí, recuperable, y mejor que recuperable: está in-tree y registrado. Lo que falta es el wiring.**

- **Extensión de marca SHIPPED + viva** (`vitalia/backend/src/modules/vitalia/sales_agent/`, ~31 importers):
  tools (`screening_questions`, `payment_link`, `reschedule_appointment`, `retract_last_message`,
  `send_proactive_reengagement`) · `domain/state_overlay.py` (`VitaliaSalesAgentStateExtension`:
  clinic_id dual-filter, vertical, screening_outcome, phi_blocked_messages) · personas (5 warm-close
  por vertical) · prompts (adrián persona + medical safety rails) · observability (callback_handler +
  `sales_agent_llm_call` + `sales_agent_trace_event` + `lead_screening_event`).
  Registrada vía **EP-3** en `vitalia/backend/src/modules/vitalia/extensions.py::register_all`.
  ⚠️ Algunos handlers EP-3 son `_not_implemented_yet(...)` placeholders apuntando a T-tools-1..4
  (prepaid_payment_check, treatment_followup_check) — wiring de tool real pendiente.

- **El loop inbound NUNCA se cableó (son stubs):** `vitalia/backend/src/modules/vitalia/api/webhook_routes.py`
  L251 *"Real wiring in T-be-7 integration — stub here per T-be-8 scope"* · L473/525/621
  *"Dispatches to sales_agent (stub in T-be-8 scope)"*. **Ningún código vitalia importa el orchestrator
  del core** (grep `luana_core_sales_agent` orchestrator/chat/graph en vitalia = vacío).

- **Slice-1 archivado:** `vitalia/docs/archive/2026/stories/vitalia-slice-1-inbox/` (spec/arch/tickets
  completos — referencia de diseño). Caps `sales_agent/{inbox-handler-mode-occ, adrian-3-tools-mvp}.yaml`
  hoy deprecated/superseded.

→ **Decisión:** `extend` (re-home + cablea + mejora). NO hay que "rescatar" código borrado; hay que
**enchufar** lo que ya está + agregar lo que falta.

## 3. Legacy "state of the art" (`~/Proyectos/luana-nicolify-legacy`) — qué aporta

El review confirma que los "gems" del legacy **ya están mayormente en el core actual** (el core se
extrajo de ese monolito). Piezas notables (verificar que sigan en core antes de asumir):
`smart_debounce_runner` (chequeo semántico DENTRO de la ventana) · **PR-8 inbound campaign
recognition** (liga el mensaje entrante a una campaña reciente → atribución) · `tool_call_dedup`
(anti-loop) · **stage-gated tool registry** (whitelist de tools por etapa: rapport=∅ … closing=~8) ·
prompt-cache de 8 slots (`compose.py`). **Acción:** durante `/architect`, confirmar cuáles de estos
ya están en `core/luana-core-sales-agent` vs son candidatos de lift (`/pm-luana`). No recrear en vitalia.

## 4. Vitalia tiene DOS superficies agénticas (review pedido por Chris)

| Módulo | Qué es | Relación con esta story |
|---|---|---|
| `vitalia/.../sales_agent/` | Extensión de **Adrián** (el bot inbound): tools + personas + state_overlay + observability + lead_screening | **CORE de esta story** — es lo que se re-hogar + cablea |
| `vitalia/.../agentic/` | Hogar agéntico más amplio: **Lucas** (LangGraph daily analysis cron — growth, NO inbound) + `screening/` + `guardrails/` (medical_safety_no_diagnosis/no_prescription/disclaimer/prompt_injection) + `tools/` (prepaid_payment_check, medical_consent_request, treatment_followup_check, appointment_reschedule) + `prompts/compose.py` (slot architecture) | **REUSE** guardrails + tools + compose; NO es el inbound loop |
| `vitalia/.../copilot/` | Copilot interno (extractors médicos, simulate_personality, KB) | tangencial |

⚠️ Hay **solapamiento aparente** entre `sales_agent/tools/` y `agentic/tools/` (ambos tienen
reschedule + payment + followup variantes). `/architect` debe resolver cuál es el canónico para el
loop inbound (evitar mirror intra-brand — `anti-duplication.md`).

## 5. LLM gateway (los "cimientos" — Chris) — estado + dónde viven las keys

**Arquitectura (ya correcta + model-independent):** engine habla a UN gateway OpenAI-compat vía
`ChatOpenAI(base_url=LITELLM_BASE_URL)`. Carga cognitiva = abstracción `ModelRole`
(NANO/FAST/REASONING/AGENT/VISION/EMBEDDING) resuelta por `AI_PROVIDER_<ROLE>`/`AI_MODEL_<ROLE>`.
**El "switch sin tocar código" que pidió Chris YA es posible** (cambiar 1 env / 1 línea del proxy).

- **Gateway:** LiteLLM Proxy, **UN container compartido** `luana_litellm_dev` (`luana_dev_net:4000`,
  alias `visionarias_litellm`). Up: `scripts/litellm-proxy-up.sh` (idempotente).
- **Config (tracked, sin secretos):** `deploy/litellm/config.dev.yaml` — Chinese-first: DeepSeek V4
  Flash (NANO/FAST/REASONING) + Kimi K2/Moonshot (AGENT/VISION) + OpenAI excepción (embeddings).
  Fallbacks cross-provider deepseek↔kimi (nunca cae silencioso a OpenAI para chat).
- **Keys (gitignored, per-worktree):** `deploy/litellm/.env` — DEEPSEEK/MOONSHOT/OPENAI/MASTER.
  **Creado en este worktree 2026-06-04** (faltaba — footgun: las keys vivían solo en el worktree
  nicolify). Ahora el proxy corre desde vitalia.
- **Defaults Chinese-first per-marca:** ahora en `vitalia/.env.dev` (`AI_PROVIDER_*`/`AI_MODEL_*` +
  `LITELLM_MASTER_KEY`) — antes faltaban en vitalia.
- **SSoT del diseño + lo que falta:** `docs/promotion-protocol/proposals/2026-06-04-llm-gateway-chinese-first.md`
  (verificado live 2026-06-04 con nicolify abel-extract → DeepSeek real).

**Mejorar el gateway "al máximo nivel" = trabajo de `/pm-luana` (NO de esta story vitalia):** toca
`core/luana-core-llm` + `core/luana-core-platform/config.py` + root `docker-compose.dev.yml` +
`core/luana-core-observability` (pricing snapshots chinos). Esta story **CONSUME** el gateway; no lo
posee. Pendientes del proposal: (1) fold proxy a root compose, (2) default-flip Chinese-first en core
config (auditado), (3) pricing snapshots DeepSeek/Kimi (hoy cost_usd=null), (4) secret store prod.

## 6. Lo que esta story REALMENTE construye (preview — refina /po + /ux-agentico)

1. **Adapter Telegram NUEVO** (inbound + outbound) en `vitalia/.../connections/telegram/` — no existe
   (solo whatsapp + instagram, y solo OUTBOUND).
2. **Cablear el loop:** webhook receiver → normalizar a `IncomingMessage` → persistir conversación
   (crm/inbox) → `ChatOrchestrator.handle_incoming_webhook()` con debounce → honrar **modo
   por-conversación** del inbox (🤖 decide/🤝 consulta/👤 humano) → outbound tras firewall PHI +
   format_for_channel → emitir activity event al inbox.
3. **Reemplazar los stubs** de `webhook_routes.py` (T-be-7/T-be-8) por dispatch real al orchestrator.
4. **Regression scope del inbox** (obligatorio Chris): los tests del inbox shipped pasan sin tocarse.

## 7. Open questions para Chris (antes de /po) — ver chris-input.md
