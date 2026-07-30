# 01 · Legacy pipeline (nicolify monolito) — reverse-engineering

> Fuente: worktree `~/Proyectos/luana-nicolify-legacy` (branch `legacy/nicolify-original`). Investigado por agente Explore (read-only). Objetivo: extraer la maquinaria del pipeline ORIGINAL agent-operated para adaptarla a vitalia salud.

## Hallazgo central: hay DOS boards, uno real y uno mock

- **`ConversationPipelineBoard`** (`nicolify/frontend/src/features/closer-studio/components/pipeline/`): el board **REAL operativo**. Stages basados en `funnel_stage` (estados de conversación conducidos por el agente IA). Tiempo real vía WebSocket. **Es la pieza que importa.**
- **`LeadPipelineBoard`** (`nicolify/frontend/src/features/sales/components/organisms/`): board **mock display-only** con `lead.status` (new/contacted/qualified/proposal/won/lost), data hardcodeada, sin drag-drop real, sin IA. Prototipo de diseño, no el sistema vivo.

> ⚠️ Dato clave: en el legacy el **drag-drop de mover etapa NO estaba implementado** (`ConversationPipelineBoard.tsx:55` tiene `// TODO: implement stage move mutation`). El board renderizaba pero el move no persistía. **El stage lo movía el AGENTE, no el humano arrastrando.** Esto confirma el paradigma conversation-first.

## Stages (conversación, agent-driven)

`rapport (Nuevo) → discovery (Calificando) → presentation (Negociando) → closing (Cerrando) → won (Ganado) / lost (Perdido)`

Separado del `lifecycle_stage` CRM (`SUBSCRIBER → LEAD → MQL → SQL → OPPORTUNITY → CUSTOMER`) que se muestra como barra de progreso en el detail.

## ★ Mecanismos AGÉNTICOS (lo más valioso)

| Mecanismo | Qué hace | Archivo legacy |
|---|---|---|
| **LangGraph multi-especialista** | `supervisor → qualifier \| product_expert \| closer \| escalation \| tool_executor → signal_accumulator` | `application/agents/sales/graph.py` |
| **Transiciones de etapa autónomas** | el agente auto-promueve etapa según count de qualification_answers + buying_signals + lead_score thresholds. Sin aprobación humana | `nodes.py:_determine_stage` |
| **Score computado por el agente** | `score = QUAL_WEIGHT*len(qual_data) + SIGNAL_WEIGHT*len(buying_signals)`, capped | `nodes.py:_compute_lead_score` |
| **Detección semántica de intención** | `SemanticRouter.detect_and_accumulate()` corre en cada mensaje, acumula buying signals | `conversation_pipeline.py` |
| **Bloques estructurados en el output** | el especialista embebe `[QUALIFICATION_DATA:{}]`, `[SIGNALS:{}]`, `[TOOL_REQUEST:{}]` en su respuesta; el accumulator los parsea + los borra del mensaje visible | `nodes.py` |
| **★ Takeover humano (STOP/Resume AI)** | operador toma control → `handler_mode="human"`, `paused_at`. Header ámbar "Tienes el control". Resume con `objective` opcional inyectado | `command_service.py:stop_ai/resume` |
| **★ Inyección de instrucción del operador (oculta al lead)** | operador susurra al agente `[INSTRUCCION DEL OPERADOR]` mientras la IA sigue activa; el lead NUNCA lo ve | `command_service.py mode=instruction` |
| **Nudge** | operador dispara mensaje proactivo de la IA con contexto | `nudge` endpoint |
| **★ Congeladas + AI Diagnose** | convs estancadas → `frozen_at`+`frozen_reason`, tab "Congeladas" con badge. AI genera `diagnosis.summary + recommendation` (reglas: score≥70+3signals→"listo para cerrar"; stuck rapport>5turns→"pregunta necesidad directa"; etc.) | `command_service.py:diagnose` |
| **LLM-as-judge** | evalúa cada turno IA en 5 rubricas (brand_voice, channel_format, commercial_effectiveness, pii_safety, tone_locale), umbral 3.5, fail-soft | `quality/judge.py` |
| **WS tiempo real** | `/ws/closer-studio?tenant_id=`; eventos new_message/handler_changed/conversation_updated; backoff reconnect | `use-closer-ws.ts` |
| **★ Atribución bot vs humano** | cada burbuja muestra ícono Bot (violeta, `sender_source=auto`) vs Humano (verde, `human_direct`) vs instrucción (pill violeta, `human_instruction`). Audit trail completo | `MessageBubble.tsx` |
| **Session summary auto** | al timeout de sesión, el agente auto-genera resumen (LLM) para continuidad | `conversation_pipeline.py:build_checkpoint_data` |
| **Outbound mode** | lead pre-warm (score≥40) salta qualifier → directo a closer | `nodes.py:node_sales_supervisor` |

## Card del pipeline (PipelineCard)

`display_name` · `lead_score` (0-100 + barra color: verde≥70/amarillo≥40/rojo<40) · `temperature` (hot/warm/cold → border-left rojo/naranja/azul) · `handler_mode` (ícono Bot violeta vs User verde) · `last_message_preview` · `last_message_at` (relativo).

**ConversationItem (inbox)** suma: `unread_count` badge · `funnel_stage` chip · `channel` (IG/TG/WA) · `is_frozen` triángulo naranja · `campaign_name` · temperatura en avatar.

**ContactSidebar (detail)** suma: `ScoreRing` SVG animado · emoji temperatura · barra lifecycle SUBSCRIBER→CUSTOMER · `lead_data` key-value · `qualification_answers` (QA extraídas por IA) · `buying_signals` (chips verdes).

## Drag-drop

`@dnd-kit/core` (DndContext, PointerSensor `distance:8`, useDraggable/useDroppable). Column highlight `ring-2 ring-primary/50` en isOver. **Move NO implementado** (TODO) — el endpoint referenciado era `PUT /crm/pipeline/{id}/stage`.

## Endpoints (closer-studio)

`GET /closer-studio/conversations?temperature=&handler_mode=&channel=&search=&limit=&offset=` · `GET .../conversations/{id}?message_limit=&before=` · `POST .../{id}/stop` · `POST .../{id}/resume` · `POST .../{id}/messages` (direct \| instruction) · `POST .../{id}/nudge` · `POST .../{id}/reactivate` · `POST .../{id}/diagnose` · `GET .../frozen` · `GET .../kpis` · WS `/ws/closer-studio`.

RQ keys: `["closer-studio","conversations",filters]`, `["closer-studio","detail",id]`, `["closer-studio","kpis"]`, `["closer-studio","frozen"]`. Polling 30s conversations+kpis, 60s frozen. Optimistic UI en stop/resume (snapshot + rollback onError).

## KPIs (header)

Total Activas · AI count (violeta) · Manual count (verde) · Hot/Warm/Cold counts · Score avg (mono) · Frozen badge · WS indicator (Wifi on/off) · Unread total.

## Reglas de negocio (legacy)

- Stage transition = agent-driven (no move manual en board — era TODO).
- `lifecycle_stage` (CRM marketing) separado de `funnel_stage` (conversación).
- `is_frozen` excluidas del pipeline → tab "Congeladas".
- `is_blacklisted` excluidos de todo.
- Human-mode ordena primero, luego `last_msg_at DESC`.
- Outbound + warm (≥40) bypassa qualifier.
- Max 3 turnos internos antes de forzar respond. Session timeout → resumen.

## 5 mejores ideas a conservar para vitalia

1. **Toggle handler_mode con header ámbar "Tienes el control"** — el mejor UX humano-IA del codebase. Perfecto para que la coordinadora tome una conversación de reserva sin perder el contexto IA.
2. **Inyección de instrucción oculta al paciente** — "ofrecé el jueves 3pm" / "este paciente necesita la suite VIP" sin que el paciente lo vea.
3. **Tab Congeladas + AI Diagnose** — convs estancadas con recomendación estructurada ("paciente trabado en el pago → mandá link directo"; "ansiedad → ofrecé consulta gratis").
4. **Buying signals → chips verdes** — mapea a intents de salud: `interes_procedimiento`, `pregunto_precio`, `menciono_obra_social`, `expreso_urgencia`. Confirmación visual de que la IA detectó intención.
5. **ScoreRing + barra lifecycle (dualidad)** — dos indicadores: `lead_score` (engagement IA) y `etapa` (journey). Vitalia necesita ambos: "qué tan enganchado" + "en qué punto de su atención".

## 3 cosas a DESCARTAR para salud/dental

1. **Labels de funnel B2B** (`discovery→Calificando`, `closing→Cerrando`). Un paciente no se "cierra". Reemplazar por etapas de salud: `primer_contacto → calificando → consulta_agendada → plan_presentado → reservado(depósito) → seguimiento`.
2. **Outbound skip-qualifier (score≥40 → closer)** — en salud todo paciente necesita intake propio; saltar calificación es riesgo clínico. Quitar o requerir override explícito.
3. **Especialistas `product_expert`/`closer` como constructos B2B** — renombrar/reprompt a `coordinador_intake → asesor_tratamiento → confirmador_reserva` con rúbricas de salud (la IA NUNCA da consejo clínico; deriva lo médico a un profesional).

`01-legacy-pipeline.md` (persistido por orquestador desde digest del Explore read-only)
