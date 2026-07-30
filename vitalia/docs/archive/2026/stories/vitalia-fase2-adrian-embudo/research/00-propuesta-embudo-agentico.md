# Propuesta — Embudo de Adrián (agent-operated) · vitalia salud

> Síntesis de las 3 investigaciones ([[01-legacy-pipeline]] · [[02-core-engine]] · [[03-agentic-best-practices]]) + recomendación de arquitectura. Para ratificación de Chris. Acompaña al mockup `mockups/embudo-agentico-concept.html`.

## 1 · El reframe (lo más importante)

El embudo NO es un Kanban CRM manual donde un humano arrastra tarjetas para vender. Es la **superficie de supervisión sobre Adrián**, el empleado-IA que vende. Adrián conversa por WhatsApp/IG, **califica, mueve de etapa y puntúa solo**; el humano (coordinadora de la clínica) **observa, toma el control cuando hace falta, le da instrucciones ocultas y resuelve los casos trabados.**

Esto se alinea con el paradigma Luana (trabajadores digitales sobre un sistema · supervisora). Y — hallazgo clave — **el runtime para esto YA EXISTE en `core/`** (closer-studio + checkpoint del agente + transitions audit + diagnose + KPIs + workers), byte-idéntico al legacy. Lo único B2B-específico son los **labels de etapa** y los **prompts de los especialistas**.

**Consecuencia para la UX:** el drag-drop manual pasa de protagonista a **override de excepción**. La acción principal es leer lo que hizo Adrián, confiar o corregir. (En el legacy el move manual ni siquiera estaba implementado — el agente movía todo.)

## 2 · Decisión de arquitectura (revisa la decisión B del batch 1)

| | Batch 1 (con lectura parcial) | **Propuesta revisada (con investigación completa)** |
|---|---|---|
| Stage machine | vitalia-local from scratch, engine = solo referencia | **Consumir el sustrato agéntico del engine** (closer-studio `AgentStateCheckpointModel.current_stage` + transitions audit + diagnose + KPIs + EventBus) **+ vocabulario dental + prompts vitalia vía Extension SDK** (patrón EP-15 ya probado con `vitalia:pending_consent`) |
| Por qué cambia | creía que el engine era 100% B2B | el runtime agent-operating es **vertical-agnóstico**; solo labels+prompts son B2B. Recrearlo brand-local = duplicar 155 archivos de maquinaria probada |
| Qué NO se consume | — | el `LifecycleStage` marketing (SUBSCRIBER→CUSTOMER) NO se co-opta como funnel dental; el funnel dental es brand-local sobre el checkpoint |

> **Lo que sigue igual de batch 1:** módulo home = `crm` (EXTEND) ✓ · Lead = non-PHI ✓ · side-effect `→reservado` stubbed ✓ · lead-detail core ✓. **Solo cambia B.** Necesito tu OK para revisar B.

**Boundary concreto:**
- **REUSE engine:** closer-studio command surface (stop/resume/nudge/diagnose), `AgentStateCheckpointModel` (current_stage, handler_mode, buying_signals, lead_score, frozen), `lifecycle_transitions` (patrón audit), EventBus (Appointment/Payment events), workers (follow_up, frozen_detection, reminders).
- **BUILD vitalia (Extension SDK):** las 6 etapas dentales + el board agregado por etapa (`GET /crm/board`), el agent-tool `mover_a_etapa(stage)`, los prompts de especialistas de salud (intake/asesor/confirmador), el PHI firewall, la FE del embudo.

## 3 · Las 6 etapas del funnel clínico (reemplazan S1-S6 B2B)

| # | Etapa | Significado | Quién la mueve |
|---|---|---|---|
| 1 | **Interesado** | Llegó un lead (WA/IG/web/referido). Adrián saludó | Adrián (auto al ingresar) |
| 2 | **Calificando** | Adrián pregunta: qué busca, urgencia, presupuesto, obra social | Adrián (al detectar intención) |
| 3 | **Consulta agendada** | Hay una cita/evaluación reservada (consume Agenda F2-S1) | Adrián / Valeria (stub aquí) |
| 4 | **Plan presentado** | Se presentó el tratamiento + precio; el paciente lo está considerando | Adrián |
| 5 | **Reservado** ⭐ | **Depósito recibido** (webhook pago). Es el WON real, no la palabra | sistema (stub aquí) |
| 6 | **Decidió que no** | El paciente no avanza (con razón) → dispara reactivación Camila | Adrián / humano |

> ⭐ **North-star:** la métrica de Adrián es **depósito / lead ingresado**, no "consulta agendada". El depósito (no la promesa verbal) cierra. Patrón de salud electiva (best-practices §3).

## 4 · Funcionalidades detalladas

### 4.1 · Board Kanban (vista supervisión)
- 6 columnas dentales. Cada columna: ícono + label + **conteo** + **valor sumado** (S/ proyectado) + **conteo de estancados** (badge ámbar/rojo).
- **Toggle Kanban | Lista** (persistido en `?view=`).
- **Toggle "Modo Adrián" | "Todos"**: filtra los leads que Adrián opera vs todos (incluye los que tomó un humano).
- Header con KPIs tiny: Activos · 🤖 Adrián N · 🙋 Humano N · Hot/Warm/Cold · Score prom · **Tasa depósito** · Congeladas (badge).
- Drag-drop = **override manual** (el humano puede mover, pero con confirmación + razón obligatoria si salta etapas) → `PUT /pipeline/{id}/stage` (`triggered_by=manual_override`).

### 4.2 · LeadCard (la tarjeta — glass-box agéntico)
- Nombre (PII-masked) + canal origen badge.
- **Badge de operador:** 🤖 `Adrián activo` (cian) vs 🙋 `Coordinadora` (verde) — quién maneja AHORA.
- **Score 0-100** con barra de color (verde≥70 / amarillo≥40 / rojo<40).
- **Time-in-stage SLA:** dot + texto (`3d`); ámbar si >1.5× la mediana de la etapa, rojo si >2× (best-practices §9). El color comunica "este lead se está enfriando".
- **Chips de buying-signals** que Adrián detectó (`💬 preguntó precio`, `📅 pidió cita`, `⏰ urgencia`).
- **Micro-log de última acción del agente:** `🤖 Adrián movió a Calificando · hace 2h · ver conv` (atribución + reason + link al inbox).
- Valor proyectado (S/) + temperatura (border-left).

### 4.3 · Lead detail (drawer derecho, sin salir del board) — 3 tabs core
- **Banner de estado del agente** arriba: "Adrián activo · autonomía: puede mover etapa + agendar · NO puede cobrar sin tu OK" + botón **`Tomar control`**.
- **Datos:** contacto (masked) · canal · etiquetas · doctor asignado · servicio de interés.
- **Historial conversaciones:** timeline cronológico que **mezcla** mensajes WA + movimientos de etapa + acciones del agente (atribuidas bot/humano) + link al Inbox (F2-S3).
- **Score (glass-box):** breakdown explicable — `Score 78 = tratamiento mencionado (+25) · respondió en <5min (+15) · presupuesto confirmado (+20) · 3 días sin actividad (−12)…` (best-practices §5). Sin ML; reglas + recencia.
- *(diferidos: Propuestas — F2-S6 · Time-in-stage timeline dedicado · Tools-registry)*

### 4.4 · Supervisión humano-IA (lo que diferencia a Luana)
- **Tomar control / Devolver a Adrián** (handler_mode ai↔human) con header ámbar "Tienes el control". Al devolver, Adrián recibe un **resumen de handover** auto-generado (no leés todo el chat).
- **Instrucción oculta al paciente:** susurrarle a Adrián ("ofrecé el combo de blanqueamiento", "este paciente necesita financiación") sin que el paciente lo vea (`[INSTRUCCION DEL OPERADOR]`).
- **Nudge:** disparar un mensaje proactivo de Adrián con contexto.
- **Display de autonomía por tipo de acción:** la coordinadora ve qué puede hacer Adrián solo (mover etapa, agendar, mandar info) vs qué requiere su OK (cobrar, prometer descuento, dar info clínica). Empieza conservador, gana autonomía con track record (best-practices §4, §7).

### 4.5 · Triage "Congeladas" (leads trabados) + AI Diagnose
- Tab/sección "Congeladas": leads donde Adrián se trabó (`frozen_reason`).
- **AI Diagnose:** Adrián genera recomendación estructurada ("paciente trabado en el pago → mandá el link directo"; "ansiedad pre-tratamiento → ofrecé llamada de 10min"). La coordinadora **Reactiva** con un objetivo, o toma el control.

### 4.6 · Nuevo lead manual + filtros + reactivación
- **+ Nuevo lead** (modal): captura manual (nombre · canal · contacto · etapa inicial · servicio · notas).
- **Filtros:** origen · doctor · etiquetas · rango fecha · score · operador (Adrián/humano).
- **Reactivación 90 días** (Camila, soft-handoff): leads en "Decidió que no" o inactivos → cohorte de reactivación WhatsApp-first, tono suave (best-practices §4 — desbloquea `camila-reactivar`).

## 5 · Reglas de negocio (RN)

- **RN-1 — Tenant isolation:** toda query filtra `tenant_id` (Lead non-PHI, filtro único). Cross-tenant → 404 genérico.
- **RN-2 — PHI firewall:** Adrián opera sobre **datos de interés** (procedimiento, presupuesto, agenda, canal), NUNCA sobre datos clínicos. El embudo no muestra diagnóstico/historia clínica. La IA deriva toda pregunta médica a un profesional (best-practices differentiator §2). Enmascarado de contacto en vistas compartidas.
- **RN-3 — Transición agent-driven por default:** Adrián mueve `current_stage` según señales (qualification_answers + buying_signals + score thresholds). Cada movimiento → `lead_stage_transition` row (`from`, `to`, `triggered_by=agent`, `reason`, `occurred_at`, `score_at_transition`). Sync.
- **RN-4 — Override manual con guardrail:** el humano puede mover una card; si **salta** etapas, modal de confirmación + razón obligatoria; `triggered_by=manual_override`.
- **RN-5 — `→Reservado` = depósito, no promesa:** la etapa Reservado se alcanza por **webhook de pago confirmado**, no por mover la card. (Esta story: STUB que simula el webhook + badge "💳 Esperando pago" / "✅ Depósito recibido").
- **RN-6 — `→Consulta agendada`** consume Agenda (F2-S1) — crear slot (stub aquí).
- **RN-7 — `→Decidió que no`** requiere `closure_reason` + dispara cohorte de reactivación (Camila).
- **RN-8 — Salud no saltea calificación:** NO existe el atajo outbound "score≥40 → directo a cierre" del legacy B2B. Todo paciente pasa por intake. (best-practices §, keep/drop §6.2).
- **RN-9 — Autonomía gated por tipo de acción:** acciones de bajo riesgo (mover etapa, info, agendar) = autónomas (HOTL); acciones de alto riesgo (cobrar, descuento, cualquier cosa clínica) = requieren OK humano (HITL). Configurable por tier.
- **RN-10 — Takeover preserva contexto:** tomar control pausa a Adrián sin perder el checkpoint; devolver genera handover summary.
- **RN-11 — Time-in-stage SLA:** cada etapa tiene mediana; >1.5× → ámbar, >2× → rojo; al rojo Adrián auto-dispara re-engagement (si autonomía lo permite) y el supervisor ve el conteo de estancados.
- **RN-12 — Atribución total:** todo mensaje/movimiento registra `sender_source` (auto / human_direct / human_instruction). Audit trail completo.
- **RN-13 — Frozen excluye del board activo:** `is_frozen` → tab Congeladas, no cuenta en columnas activas. `is_blacklisted` → excluido de todo.
- **RN-14 — Toggle persiste URL** (`?view=`). **RN-15 — i18n:** montos `formatMoney(tenant.currency)`, Spanish neutro.

## 6 · Qué se conserva del legacy / qué se descarta

**Conservar (5):** (1) toggle handler_mode + header ámbar · (2) instrucción oculta al paciente · (3) tab Congeladas + AI Diagnose · (4) buying-signals → chips · (5) ScoreRing + etapa (dualidad engagement/journey).

**Descartar para salud (3):** (1) labels funnel B2B (rapport/discovery/closing) → etapas clínicas · (2) outbound skip-qualifier (riesgo clínico) · (3) especialistas `product_expert/closer` → `intake/asesor/confirmador` con rúbricas de salud (sin consejo clínico).

## 7 · Diferenciadores agénticos (best-practices)

1. **Pipeline conversation-first** — la etapa se *deriva* de la conversación, no del drag manual. Card = recap de 2 líneas generado por IA.
2. **PHI firewall visible** — la separación interés/clínico es un concepto de UI de primera clase; genera confianza.
3. **Depósito = north star** — toda métrica de velocidad mide progreso hacia el depósito.
4. **Display de autonomía** — la coordinadora ve qué puede/no puede hacer Adrián; arranca conservador, gana autonomía.
5. **Reactivación LatAm-native** — WhatsApp-first, tono suave, sin presión agresiva de precio.

## 8 · Alcance propuesto para ESTA story (dado deps)

**Ship ahora:** board Kanban + Lista (6 etapas) leyendo el sustrato del agente · LeadCard glass-box (score+signals+atribución+SLA) · drawer detail 3 tabs core · **takeover + instrucción oculta + nudge** (consume closer-studio) · **Congeladas + Diagnose** (consume engine) · + Nuevo lead + filtros + KPIs + display de autonomía (read-only).

**Stub:** `→Reservado` (pago webhook simulado, MSW) · `→Consulta agendada` (Agenda real cuando F2-S1 se enlace).

**Diferir:** tabs Propuestas (F2-S6) · Tools-registry · editor de customización de etapas per-vertical · reactivación Camila (desbloqueada, story propia).

> Nota: esto crece el alcance vs el draft original (suma la capa de supervisión agéntica). Probable re-estimación: de 6-8 a **8-11 días**, o partir en 2 stories (S4a board+detail+supervisión · S4b congeladas+diagnose+reactivación). **Decisión de Chris.**

## 9 · Decisiones abiertas para Chris

1. **¿OK revisar la decisión B** → consumir sustrato agéntico del engine + vocabulario/prompts dentales (Extension SDK)? (Recomendado.)
2. **¿Embudo conversation-first** (etapa la mueve Adrián, drag = override) vs Kanban manual clásico? (Recomiendo conversation-first — es el alma del producto.)
3. **¿Alcance:** una story 8-11d (todo) vs partir S4a/S4b? 
4. **Score:** glass-box rule-based vitalia-local (recencia+señales+etapa) — ¿OK? (era la Q1 del batch 2, ahora resuelta por la investigación: rule-based explicable, sin ML, sin engine scoring B2B).
