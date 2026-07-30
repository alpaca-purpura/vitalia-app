---
story_id: vitalia-ux-discovery
brand: vitalia
type: handoff-doc
purpose: "Reanudar v1 spec en nueva conversación con contexto limpio — Batches 4-7 + cierre"
created_at: 2026-05-17
created_by: /po-ux (Opus 4.7, sesión Batches 1-3)
phase_at_creation: SPEC_V1_BATCH_3_RATIFIED
next_session_starts_with: Batch 4 — /agenda
---

# Handoff doc — Batches 4-7 + cierre `vitalia-ux-discovery`

> **Propósito:** la sesión actual cerró Batches 1-3. Próxima conversación arranca con contexto limpio para Batches 4-7 + cierre. Este doc es el pointer-first para retomar sin re-discovery.

## Cómo retomar (próxima conversación)

```
/po-ux vitalia-ux-discovery batches 4-7

Producir Batches 4-7 + cierre v1 sobre la story `vitalia-ux-discovery` (state=refining, phase=SPEC_V1_BATCH_3_RATIFIED).

## Inputs cementados a leer ANTES de arrancar (NO re-litigar)

1. `vitalia/docs/product/stories/vitalia-ux-discovery/00-handoff-batch-4-7.md` — ESTE DOC, contiene todo lo cementado y patrones a respetar
2. `vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md` — Batches 1-3 ya cementados (§Layout shells · §Transición · §Back button · §§Ruta /inbox · §§Ruta /pipeline)
3. `vitalia/docs/product/stories/vitalia-ux-discovery/mockups/{inbox,pipeline}.html` — mockups de referencia (consistencia visual)
4. `vitalia/docs/architecture/design-system.md` — tokens vitalia
5. `vitalia/.claude/rules/hipaa-lite.md` — PHI compliance

## Protocolo

G6 batched clarification del skill `/po-ux` — por batch (no por sub-rondas dentro de batch como /inbox, que fue excepción). Cada batch propone Layout ASCII + 4 preguntas numeradas. Al ratificar → escribo §§Ruta /<batch> en spec v1 + mockup HTML + bitácora + checkpoint bump.

Arrancar Batch 4 — /agenda.
```

## Patrones globales cementados (NO re-litigar)

Estos patrones aplican a TODAS las rutas restantes (4-7). Cada nueva ruta los respeta sin re-proponer:

### Layout shell (Batch 1 ratificado)
- Fase 2 shell operación: Sidebar 240 + Main flex + ContactSidebar* 280 (toggleable) + Copilot rail Valeria 80
- Shell Mutex auto-colapsa sidebar 240→60 cuando copilot expande en viewport <1440px
- Mobile <768px: sidebar drawer + FAB redondo copilot
- TopBar 56px: logo + clinic switcher + ⌘K + 🔔 + user menu

### URL state nuqs (Batch 1)
- `replace` para sub-state intra-route (filters, modals, expand peek)
- `push` para navegación inter-ruta (sidebar click, "Abrir conversación")
- Event-based chat context refresh a Valeria backend en cada URL change

### Microcopy arquitectura (Batch 2)
- TS const tree-shakable en `vitalia/frontend/src/features/{ruta}/copy.ts`
- LatAm neutro estricto (sin voseo)
- Cero hardcoded strings en JSX — arch fitness test enforced
- Patrón: `RUTA_COPY.namespace.key` con variables `{placeholder}` resueltas con helper `formatCopy(template, vars)` en `vitalia/frontend/src/lib/copy.ts`

### Agentes con identidad humana (Batch 2 + 3)
- **Valeria** = copilot rail derecho (operador asistente) — gradient cian→púrpura
- **Adrián** = sales agent inbox + pipeline (closer paciente) — gradient púrpura→azul-marino
- **Lucas** = growth setter pipeline + marketing (calificador + screening clínico) — gradient verde-lima→cian
- Atribución per acción: avatar + nombre + verbo pasado simple ("Adrián propuso turno")
- NUNCA roles técnicos visibles ("sales_agent", "growth-studio")

### PHI compliance (Batch 2 + 3)
- DNI/Teléfono/Email default masked + click 🔓 reveal con audit log row
- Diagnóstico/notas médicas NUNCA en listas/tooltips
- Wrappers obligatorios: `<PiiMaskedSpan>`, `<RequireRole>`, `<AuditedSection>`
- Dual filter tenant_id + clinic_id en TODO query backend
- PHI NUNCA en URL query params

### Estados visuales (Batch 2 cementado — 8 totales)
5 standard: `idle` · `loading` · `success` · `error` · `empty`
3 agentic: `agent-thinking` (typing/processing) · `agent-waiting-approval` (HITL suggest) · `agent-failed` (escalation banner)

### Venta consultiva ética (Batch 2 + 3)
- NO chips Hot/Warm/Cold visibles FE
- Stages decisión: Interesado · Considerando · Listo para reservar · Decidió no
- Chip "🟢 Estilo: consultivo · sin presión" siempre visible
- Screening clínico Lucas pre-cierre per vertical (contraindicaciones)
- Tono Spanish neutro LatAm cálido pero profesional

### REUSE pattern (Batch 2 + 3)
**Auditar PRIMERO** `nicolify/frontend/src/features/` para ver qué existe antes de proponer:
- `closer-studio/` → inbox + pipeline + frozen (REUSED Batches 2 + 3)
- `brand-studio/` → 4 secciones (REUSE Batch 7)
- `growth-studio/metrics-dashboard/` → posible base /marketing (Batch 6)
- `copilot/` → composer + messages primitives (reuse cross-batches)
- `crm-hub/` → ContactSidebar PHI base (reuse cross-batches)

Después de auditar:
- REUSE adapt = fork + adaptar tokens Vitalia + sumar PHI wrappers + sumar atribución agente
- NEW = solo componentes que NO existen (segmented control 3-modos, screening chip, action receipts, etc.)
- Fork físico vs shared package = DEFER `/architect` (flag, no resolver en spec)

### Action receipts agentic (Batch 2 + 3)
- Cuando agente actúa autónomo → chip undo countdown
- 5min window (matchea WA/IG retract API)
- Fallback "marcar como erróneo" si retract canal falla

### DnD + auto-progression (Batch 3)
- Drag manual + auto-progression event-driven entran cuando aplica
- Undo auto-move + animación suave = Slice 2 idea documented
- Conflict resolution = timestamp wins + re-fetch React Query

## Status v1 batches

| # | Foco | Estado | Sección spec resultante |
|---|---|---|---|
| 1 | Layout shells (wizard + operación) + transición + back button | ✅ ratificado | §Layout shells · §Transición · §Back button + URL state |
| 2 | `/inbox` ruta más frecuente P1 | ✅ ratificado | §§Ruta /inbox (+ mockup `mockups/inbox.html`) |
| 3 | `/pipeline` lead→reserva depósito 30% (MUST #2) | ✅ ratificado | §§Ruta /pipeline (+ mockup `mockups/pipeline.html`) |
| **4** | `/agenda` calendar + cobranza | **next session arranca acá** | §§Ruta /agenda + `mockups/agenda.html` |
| 5 | `/fidelización` NPS post-tratamiento auto (MUST #4) | pending | §§Ruta /fidelización + `mockups/fidelizacion.html` |
| 6 | `/marketing` Lucas performance multi-canal | pending | §§Ruta /marketing + `mockups/marketing.html` |
| 7 | Wizard Brand Studio 5 preguntas stub (MUST #3) | pending | §§Wizard Brand Studio + `mockups/wizard-brand-studio.html` |
| Cierre | Slice 1 cut confirmation + components mapping consolidado + transition state refining→refined + handoff `/architect` | pending | §Slice 1 cut · §Components mapping consolidado + frontmatter `state: refined` |

## Decisiones cementadas pendientes de surface (no relitigar)

| Decisión | Cementada en | Aplica a |
|---|---|---|
| 6 stages venta consultiva | Batch 3 | /pipeline, /fidelización (re-engagement input), /marketing (funnel cross-ref) |
| Screening clínico Lucas | Batch 3 | /pipeline (origen), /inbox (Lucas chip en lista), Brand Studio wizard (configurar) |
| Atribución agente per stage | Batch 3 | Todas rutas que tocan agentes (todas excepto wizard) |
| Diferenciador MUST #2 (depósito 30%) | Batch 3 | /pipeline (origen), /agenda (badge color slot), /marketing (métrica clave) |
| Action receipts undo 5min | Batch 2 | /inbox (mensajes), /agenda (cobranza manual confirmaciones), Slice 2 /pipeline (auto-move) |
| Segmented 3-modos agente | Batch 2 | Solo /inbox por ahora — Slice 2 evaluar para /pipeline (Adrián decide cuál mover) |
| Multimedia (audio IN + imagen IN stub + imagen OUT asset) | Batch 2 | /inbox (origen) — futuro pipeline cards podrían embeber preview |

## Preview de los batches restantes (NO empezar — solo guía contextual)

### Batch 4 — `/agenda`

**JTBD #3 P1**: agenda del día + cobranza activa. Calendar con turnos color-coded por status pago + procesar pago presencial + chase pago pendiente.

**REUSE candidato:** verificar `nicolify/frontend/src/features/sales/` (event types + AvailabilityView + GenerateLinkModal) — puede tener calendar primitives.

**Highlights spec:**
- Vista calendar día/semana/mes (toggle)
- Color-coded slots ratificado v0: verde (pagado completo) · cian (depósito 30%) · warning (pendiente) · rojo (no-show riesgo)
- Procesar pago presencial (cuando paciente llega, completar 70% restante)
- Chase pago pendiente (envío automático recordatorio + manual override)
- Reagendar/cancelar (con politicas reembolso depósito)
- Cross-link `/pipeline` Stage 5 → `/agenda` slot auto-sync
- Atribución Adrián cuando agendó / sistema cuando paciente reservó self-serve
- PHI: nombre paciente full + diagnóstico/tratamiento NUNCA en hover slot (solo en detail audited)
- Microcopy en `vitalia/frontend/src/features/agenda/copy.ts`

**Preguntas batch (sugeridas):**
1. Vista default: día / semana / mes
2. Procesar pago presencial: modal in-place vs sheet lateral
3. Política reembolso depósito en cancelación (estándar 24h cancelación)
4. Reagendar — drag-and-drop slot (DnD-kit) o modal selector

### Batch 5 — `/fidelización`

**JTBD #4 P1**: fidelización post-tratamiento. **Slice 1 SCOPE LIMITADO**: SOLO NPS post-tratamiento automático (ratificado Chris previo).

**Deferred Slice 2** (NO entran v1):
- Pedido reseña Google (requiere Google Places API)
- Recordatorio birthday (cron mensual)
- Re-engagement inactivos (cron semanal + segmentación)

**Highlights spec:**
- Workflow trigger: turno cerrado (procesado pago presencial) → 24h después → envío NPS via WhatsApp + email
- Captura score 0-10 + comentario opcional
- Lista NPS recibidos (filtros: score range, vertical, agente atribuido)
- Métrica NPS score promedio + distribución (promotores/pasivos/detractores)
- Atribución sistema (auto-trigger) + Adrián si paciente responde con conv adicional
- Si detractor (score 0-6) → flag automático "🔴 Atención requerida" + sugiere acción (llamar paciente, ofrecer disculpas, etc.)
- Activity feed cross-ruta: "Sistema envió NPS post-tratamiento a M. Rodríguez" · "M. Rodríguez respondió 9/10"
- Microcopy `vitalia/frontend/src/features/fidelizacion/copy.ts`

**Preguntas batch (sugeridas):**
1. Layout: lista + detalle vs tabla con expand
2. Trigger timing post-turno (24h fijo vs configurable per offer)
3. NPS detractor: auto-derivar a Owner o solo flag visible operador
4. Cross-ruta surfacing: ¿NPS también surface en `/inbox` como tag conv?

### Batch 6 — `/marketing`

**JTBD #5 P1 + #1 P2**: performance publicidad multi-canal con Lucas. Meta Ads + Google Ads + IG orgánico unificado.

**REUSE candidato:** `nicolify/frontend/src/features/growth-studio/metrics-dashboard/` (channel widgets + sidebar) — puede tener charts base.

**Highlights spec:**
- Dashboard con KPIs principales: gasto YTD vs budget · costo per lead · conv lead→reserva · ROI per campaña
- Breakdown per canal (Meta, Google, IG, organic, referido) con sparklines
- Atribución Lucas: "Lucas calificó X leads esta semana" · "Lucas recomienda subir budget Meta $200→$400/mes genera +N leads/mes"
- Bandeja "Recomendaciones Lucas" inline en dashboard
- Filtros: período · canal · campaña · vertical
- Cross-link a `/inversion-publicitaria` Slice 2 (P2 only) para aprobaciones budget
- Charts: bar + line + funnel
- Microcopy `vitalia/frontend/src/features/marketing/copy.ts`

**Preguntas batch (sugeridas):**
1. Layout dashboard: stats top + charts grid abajo vs sidebar canal-detail
2. Recomendaciones Lucas: cards inline vs sheet lateral
3. Atribución por canal: ¿mostrar % conversión per canal en breakdown principal?
4. Data viz: chartlib (recharts vs visx vs custom Tailwind)

### Batch 7 — `/onboarding/brand-studio` (wizard)

**Diferenciador MUST #3**: Brand Studio con voz clonada. **Slice 1 = STUB MÍNIMO** 5 preguntas → Brand Studio scaffold backend Story 11 ya shipped.

**Aplicar Fase 1 layout cementado Batch 1**: chat-LEFT 50/50 con Valeria + form Brand Studio + live preview derecha + botón "Cerrar setup" único punto salida + back replace intra-wizard + transición morph 400ms al terminar.

**REUSE candidato:** `nicolify/frontend/src/features/brand-studio/` (4 secciones existing) — qué viene de allá adaptado a wizard.

**Highlights spec:**
- 5 preguntas básicas Valeria (cementadas en spec):
  1. ¿Cómo se llama tu clínica? → `tenant.name`
  2. ¿Cuál es tu vertical principal? (dental/estética/psicología/fertilidad/otro) → `tenant.vertical`
  3. ¿Dónde está ubicada? (ciudad + país) → `tenant.location`
  4. ¿Cómo describirías el estilo de tu clínica? (clásica · moderna · familiar · premium · alternativo) → `brand.tone_default`
  5. ¿Qué tratamiento querés ofrecer primero? (input freeform) → `offer[0]` scaffold
- Live preview lado derecho: cómo se ve voz Adrián en mensaje WhatsApp ejemplo
- Progress bar 5 pasos (●○○○○ → ●●○○○ → ●●●○○ → ●●●●○ → ●●●●●)
- Skip per paso con warning ("Tu progreso se guardará") — pasos pueden completarse después en `/brand-studio` full (Slice 2)
- Botón "Cerrar setup" warning modal + redirect a /inbox
- Al terminar → transición morph 400ms (Batch 1) + redirect /inbox + toast "¡Listo! Tu clínica está configurada."
- Microcopy `vitalia/frontend/src/features/onboarding/copy.ts`

**Preguntas batch (sugeridas):**
1. Las 5 preguntas — confirmar contenido o ajustar
2. Live preview: WhatsApp message ejemplo vs landing page snippet vs ambos
3. Skip per paso: permitir todos opcionales o algunos required (vertical + nombre obligatorios?)
4. Voz Adrián live update: real backend wire Slice 1 o stub hardcoded?

### Cierre v1 — Slice 1 cut + components mapping + handoff `/architect`

Cuando Batches 4-7 ratifiquen:

**1. §Slice 1 cut confirmation** (sección final spec)

| Componente | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| Rutas P1 | /inbox · /pipeline · /agenda · /fidelización (NPS only) · /marketing | + /dashboard · /inversion-publicitaria · /brand-studio (full) · /tratamientos · /configuracion | + multi-clinic switcher · audit log viewer · advanced analytics |
| Onboarding | /onboarding/brand-studio (5 preguntas stub) | + Offer Studio wizard + Buyer persona wizard | — |
| Multimedia | Audio IN real · Imagen IN stub · Imagen OUT asset library · Composer attach | Audio OUT (voz clonada Premium) · Imagen IN vision real · Audio tone detection | — |
| Agentes | Adrián + Lucas + Valeria (rail) | + Camila (diseñadora) + Mateo (developer) defer | — |
| Pipeline | Kanban + DnD manual + auto-progression + screening Lucas | + Undo auto-move + animación suave + Lista view + drop-off métricas + tiempo per stage + bulk actions + ROI per canal | + Pipeline templates per vertical |
| Mobile | Responsive web (FAB copilot + drawer sidebar + cards en mobile pipeline/agenda) | + PWA polish | + Native iOS/Android |

**2. §Components mapping consolidado** — tabla agregada cross-rutas mostrando REUSE adapt vs NEW components con paths exactos.

**3. Frontmatter transition** `state: refining → refined` + `v1_batches_status: all ratified` + `ratified_by_chris: true`.

**4. Bitácora cierre v1** entry final con resumen.

**5. Handoff `/architect`** — mensaje en checkpoint.md:
```
Spec ratificada v1 para brand vitalia. State: refined.

Próximo: /architect vitalia: lee 01-spec.md → spawn /architect-be + /architect-fe en paralelo →
produce ready package (03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml).

Open questions a /architect:
- Fork físico vs shared package para reuso Nicolify (closer-studio, brand-studio, copilot, crm-hub, growth-studio)
- Backend additions Slice 1: proposal_required col, screening_outcome col, retract endpoints, activity-stream endpoint, tools endpoint, Whisper STT integration, payment webhook handler, cron timeout 7d
- Promotion gate brand→core para componentes que aparezcan ≥2 brands (futuro)
- Side stories paralelas: vitalia-payment-adapter-mvp + vitalia-copilot-tools-impl deben estar shipped/developed antes /dev-team Slice 1 build
```

## Comandos útiles

```bash
WS=/home/chalreme/Proyectos/luana-platform

# Leer spec actual
cat ${WS}/vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md

# Servir mockups locales
cd ${WS}/vitalia/docs/product/stories/vitalia-ux-discovery/mockups
python3 -m http.server 8888
# Abrir http://localhost:8888/{inbox,pipeline}.html

# Auditar Nicolify para REUSE (cambiar feature según batch)
ls ${WS}/nicolify/frontend/src/features/sales/        # Batch 4 /agenda
ls ${WS}/nicolify/frontend/src/features/growth-studio/ # Batch 6 /marketing
ls ${WS}/nicolify/frontend/src/features/brand-studio/  # Batch 7 wizard

# Verificar status story
cat ${WS}/vitalia/docs/product/stories/vitalia-ux-discovery/checkpoint.md
```

## Métrica de progreso

- Batches completados: 3 / 7 (43%)
- Líneas spec actuales: ~1.500+ (de v0 396 LOC base + Batches 1-3)
- Mockups creados: 2 / 6 (inbox, pipeline)
- Tiempo estimado restante: 4 batches @ 1 sub-ronda c/u (~30-45 min cada uno con G6) + cierre ~30 min

## Token budget próxima sesión

Próxima conversación arranca con contexto limpio. Para asegurar capacidad:
- Sesión actual cerró con ~33% context Opus 1M (decisiones cementadas + 2 mockups HTML grandes)
- Próxima sesión: solo lee ESTE handoff + spec actual + 2 mockups referencia = ~70k tokens contexto inicial
- Margen para 4 batches + cierre + ratifications: ~600-700k tokens disponibles (cómodo)

## Notas finales

- Mantener el ritmo G6 batched clarification — NO dumps masivos
- Si Chris pide auditar Nicolify antes de proponer (como en Batch 2) → hacerlo SIEMPRE (es el patrón ratificado)
- Si encuentro algo NUEVO que no está en patrones globales arriba → flag explícito a Chris antes de spec-ear
- Mockups HTML siguen el patrón de `inbox.html` / `pipeline.html` (Tailwind CDN + tokens Vitalia + Lucide icons + state switcher arriba si aplica)
- Próxima conversación debe usar `/po-ux vitalia-ux-discovery batches 4-7` (no `/po-ux vitalia-ux-discovery v1` que arranca de cero)
