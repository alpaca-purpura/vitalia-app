# vitalia-ux-discovery — 00-research

> **Handoff de sesión 2026-05-17.** Para retomar UX iteration en nueva conversación sin empezar de cero. Producido por `/pm-vitalia` + Claude Opus directo.

## TL;DR (lectura obligada al retomar)

1. **El design-system base está cementado** en `vitalia/docs/architecture/design-system.md` (paleta + tipografía + tokens + agentes UI + PHI conventions + brand voice). NO re-litigar tokens en sesión UX siguiente.
2. **Backend vitalia tiene 24 endpoints reales pero 17 EPs son scaffolds** (sales agent tools, copilot extractors, workflows, KB packs — todos placeholders con `NotImplementedError`). Esto significa: **chat-first puro NO es viable hoy** porque Valeria sería teatro.
3. **3 patrones de layout explorados fueron descartados** por Chris por jerarquía visual ambigua. **NO copiar el mockup `/tmp/vitalia-mockups.html`** — era exploratorio.
4. **Empezar por flujo de navegación + personas + jobs-to-be-done por rol**, NO por layout. El layout es consecuencia.
5. **Reuso máximo del Copilot Nicolify** (65+ componentes, audio waveform + tool calls + voice overlay) sigue siendo el camino — solo cambia DÓNDE se ubica en la UI según el flow ratificado.

## Estado de la story

| | |
|---|---|
| state | idea |
| phase | RESEARCH |
| parent_outcome | vitalia-mvp-ui-foundation (pendiente crear) |
| ratified_by_chris | false |
| spawned_at | 2026-05-17 |
| next_action | Refining: personas + jobs + flow → DESPUÉS layout |

## Decisiones cementadas en esta sesión (NO re-litigar)

### 1. Separación obligatoria: web promo ≠ app interna

| | Promo (`vitalialat.com`) | App (`dev-app.vitalialat.com`) |
|---|---|---|
| Audiencia | Clínicas que aún no compraron | Equipo clínico ya cliente |
| Agentes IA (Valeria, Adrián, Lucas, Camila, Mateo) | Páginas dedicadas `/equipo/{nombre}`, headlines "Hola soy X", CTAs "Contratá al equipo" | Atribución funcional ("Adrián cerró tu turno"), avatar iniciales+gradient, sin páginas dedicadas |
| Gradient mariposa | Toda la artillería marketing | Solo loading/empty/onboarding splash (one-time) |
| Avatares con foto IA-generated | Sí (futuro) | NO — iniciales con gradient en MVP |
| Videos/animaciones agentes | Sí | NO (eye-candy sin valor operativo) |

Fundamento: jobs-to-be-done opuestos (convencer vs operar). Mezclar desenfoca al usuario operativo.

### 2. Roster de agentes IA (5 worker pattern, inspirado en Darwin AI)

| Agente | Rol | Estado backend MVP | Aparece en app MVP? |
|---|---|---|---|
| Valeria | Ejecutiva / Copilot conversacional (hub) | Backend scaffold — tools T-tools-1..4 pending | Sí — depende patrón ratificado |
| Adrián | Closer / Sales agent | Backend scaffold | Sí — atribución en inbox + activity feed |
| Lucas | Setter / Growth studio | Defer — depende port `nicolify/advertising` (~4-5h) | Probable no en MVP, sí Slice 2 |
| Camila | Diseñadora (flyers) | No existe | NO MVP — defer |
| Mateo | Developer (landings) | `luana-core-landing` scaffold | NO MVP — defer |

### 3. MVP fundamentos arquitectónicos

- Sign-in queda en Clerk default (NO rediseñar visual)
- Avatares con iniciales + gradient (NO IA-generated MVP)
- NO crear `/equipo/{nombre}` en app (esas viven en promo)
- Reuso máximo Nicolify (~70-85% según patrón final)
- Compliance HIPAA-lite framework defensivo (NO claim HIPAA US)
- Spanish neutro LATAM (tuteo, NO voseo en UI chrome)

### 4. Decisión Steve-Jobs aplicada: lo que NO va en MVP

- Sign-in rediseñado (Clerk default)
- Páginas `/equipo/*` en app
- Avatars IA-generated / videos agentes
- Pago online wizard (backend wired automáticamente vía webhook)
- Recordatorios programables UI (backend dispara automático)
- Campañas masivas / segmentación / reportes avanzados
- Consentimientos firmables UI (defer)
- Brand Studio conversacional vía Valeria desde Slice 1 (scope creep)

## Análisis competitivo (resumen — pointer a sesión previa)

**5 competidores investigados + Darwin AI como playbook:**

- `cero.ai` — landing minimalista pre-launch (sin info útil)
- `botclinico.cl` — clínicas estética/médico/dental/láser. Agentes IA voz + chat. "$0 evaluación" opaco
- `rendu.app` — **mejor competidor con pricing público** (CLP 40-250k/mes). Dental focused. Odontograma FDI, integración Dentalink. Sin nombre/personalidad agentes
- `dentalink contact center` — suite dental integrada, IA WhatsApp + llamadas, configurable nombre pero genérico
- `doctocliq` — LATAM 20+ países, sistema integral cerrado, "Asistente IA" genérico

**Ningún competidor LATAM health tiene:**
- Agentes IA con nombre + personalidad humana (todos genéricos o configurables)
- Booking prepaid 30% deposit nativo
- Chat-first interface

**Ventajas únicas Vitalia (a defender en flow):**
- 5 agentes con roles diferenciados (vertical health + beauty)
- Booking prepaid 30% deposit (reduce no-show estructuralmente, no por recordatorio)
- Compliance HIPAA-lite framework defensivo
- Multi-vertical configurable (KB packs dental/psicología/psiquiatría + futuro estética/fertilidad)
- Pricing público USD ($49/$199/$599)
- Backend operativo + tested (86 BE + 22 FE + 24 E2E)

**Inspiración patrón:** Darwin AI (`getdarwin.ai/es/worker/alba`) — workers con nombres en marketing. **Aplicable solo en promo, NO en app.**

## Audits realizados esta sesión (pointers)

### Backend Nicolify (5 módulos)

- **`advertising`** = JOYA reusable. 95% reusable, 9 endpoints, 10 tests pass. Meta + Google Ads + offer-campaign association + health-check + metrics-by-offer. **Port a vitalia: ~4-5h.** Lucas (Setter) sale de acá.
- `edges` (composition), `workers` (ARQ), `persistence` (model_registry) → extend via EP
- `admin` (Streamlit) → no_aplica vitalia
- **NO portar:** CRM B2B (proposals/contracts/billable_hours), Client Portal, Bowtie funnel B2B-specific

"Growth Studio" no es módulo — es composite (advertising nicolify + analytics-engine core + campaigns core + crm core). Vitalia ya consume los 3 cores.

### Frontend Nicolify (16 features, 1027 archivos)

Stack idéntico vitalia. 0 hardcoded brand colors en `components/shared/`. Top 10 reusables:

1. `AppSidebar` config-driven (directo)
2. `DashboardShell` + `Shell Mutex` (directo)
3. `Brand Studio` 4 secciones identity+contact+team+testimonials (directo — coincide vitalia `enabled_sections`)
4. `ConversationThread` + `MessageBubble` (directo)
5. `EventTypeForm` + `AvailabilityView` RHF+Zod (adapt)
6. `NotificationCenter` (directo)
7. `TenantSwitcher` + `TenantGuard` (directo — multi-clinic)
8. `OfferStudio` variant pattern (adapt — tratamientos con variants)
9. **Copilot panel ENTERO** (adapt — 65+ componentes, audio + tool calls + voice + streaming)
10. `Audit` feature (directo — compliance log viewer)

**NO portar:** CRM Hub B2B, Campaigns-Lite mass-blast, Sales booking links, Shopify/MailerLite/Telegram connections.

### Backend Vitalia (estado real vs checkpoint declarado)

| | Checkpoint decía | Real |
|---|---|---|
| Endpoints REST | 15 | **24** (onboarding 4 + bookings 7 + treatments 5 + patients 3 + compliance 4 + offer presets 1) |
| EPs registrados | 35 | 35 — pero **17 son scaffolds** |
| Sales agent tools (EP-3) | 4 vivos | **4 placeholders** |
| Copilot extractors (EP-7) | 2 | **Ambos scaffold** |
| Copilot KB packs (EP-14) | 3 | **Los 3 scaffold** |
| Treatment followup workflow (EP-4) | LangGraph state machine | **Steps tuple vacío** |
| Guardrails (EP-13) | 4 médicos | **Los 4 retornan `blocked=False`** (permissive) |
| Payment adapters (EP-8) | 3 gateways | **Skeleton + webhooks OK, adapters scaffold** |

**Implicación crítica:** chat-first puro con Valeria configurando todo NO es viable hoy. Valeria tendría que decir "ok te ayudo" sin ejecutar nada real (las tools están vacías). MVP debe ser **funcional-first** con copilot evolutivo (Q&A stub → configurador real cuando T-tools-1..4 landed).

### Copilot Nicolify FE (65+ componentes — fork directo a vitalia)

- 11 tipos de bloques (Text, Image, Audio con waveform + scrubber + transcript collapsible, Video, Document, Table, Code, Citation, QuoteReply, Card, ToolResult)
- 5 cards interactivas (Alternatives, Checkpoint, Clarify, ExtractionSummary, InterviewComplete)
- 8 composer sub-components (ChatComposer, Toolbar, VoiceOverlay 40-bar waveform + timer + cancel/accept, AttachmentTray, etc.)
- 4 layout containers (CopilotSidebar = orquestador + CopilotChatPanel + CopilotHistoryPanel + CopilotRail)
- Tool calls inline con progress bar (running/done states)
- SSE streaming, tier chips (SMART/FAST/PRO)
- Shell Mutex coordina sidebar + copilot panel responsive
- 20 arch tests + 223 unit tests + 44 E2E specs

**Anchos:** collapsed=60px (solo rail) · rail=460px (chat+rail) · full=680px (history+chat+rail) · chat fijo=400px.

## Mockups producidos esta sesión

**Path:** `/tmp/vitalia-mockups.html` (autocontenido, abrir con `xdg-open /tmp/vitalia-mockups.html`)

3 patrones explorados con copilot real heredado de Nicolify:
- **B** — Sidebar + Main funcional + Copilot panel persistente derecho
- **D.1** — Copilot central protagonista + panel contextual derecho dinámico
- **D.4** — Bi-modal con toggle chat↔página

**Feedback Chris:**
- "Me gustó la versión de página" (modo página de D.4)
- "Pero la propuesta no me gustó por completo"
- **Problema raíz:** las 3 columnas (sidebar izq + chat centro + panel info der) **no son intuitivas en jerarquía visual** — el usuario no sabe qué viene antes o después
- "Necesitamos revisar el flujo de navegación"

## Lo que NO funcionó (a evitar próxima iteración)

| Anti-patrón | Por qué falla |
|---|---|
| 3 columnas simultáneas (sidebar + chat + info derecha) | Jerarquía visual ambigua. Viola atención focal. Usuario no sabe foco primario |
| Chat-first puro con copilot scaffold | Sería teatro hasta que T-tools-1..4 landen |
| Atajos marketing dentro del app (5 worker pages, "Contratá a X") | Viola separación promo/app. Confunde rol del usuario (cliente vs prospecto) |
| Diseñar layout antes de mapear flujo | Resultado parece prototipo Figma, no producto real. Chris explícitamente lo señaló |
| Mockup HTML sin antes definir personas + jobs-to-be-done | Sin baseline de quién usa cuándo, layout es decisión estética |

## Lo que SÍ funcionó (a mantener próxima iteración)

| Pattern | Por qué |
|---|---|
| **Copilot Nicolify completo** (audio, tool calls inline, voice overlay 40 bars, streaming, transcripts collapsible) | Diferenciador real, técnicamente probado |
| **Modo página simple con lista compacta** (badges PAID/DEPOSIT/PENDING) | Feedback positivo explícito Chris |
| **Activity feed con atribución agéntic** ("Adrián cerró 3 turnos") | Primer wow agéntic visible, bajo costo, backend data ya wired |
| **Paleta vitalia con identidad fuerte** (cian + púrpura + amarillo + azul marino + verde-lima) | Cementada en design-system.md |
| **Booking calendar con deposit badge** | Ventaja única vs competidores (prepaid 30%) |
| **Sidebar config-driven (Nicolify pattern)** | Reuso directo, solo cambia config de entries |

## Preguntas pendientes para próxima sesión UX

### 1. ¿Quién es el USUARIO primario del app vitalia?

Hipótesis: hay **al menos 3 personas distintas** dentro de una clínica cliente:

- **Doctor** (médico/dentista/psicólogo): usa la app esporádicamente, quiere zero-friction para preguntas rápidas ("¿quién viene a las 10?", "ver paciente X")
- **Recepción / Secretaria**: usa la app todo el día, necesita listas operativas, agenda visible, inbox unificado siempre presente
- **Admin clínica / Owner**: usa para configuración, reportes, plan & billing, equipo médico. Frecuencia media

¿Hay otras personas? ¿La pesona dominante depende del plan (solo_doctor vs clinic vs multi_site)?

### 2. ¿Cuáles son los TOP 5 jobs-to-be-done por persona?

Sin esto, layout es decisión estética. Para definir.

Hipótesis preliminar:

**Doctor:**
1. Ver mi agenda de hoy/mañana
2. Ver ficha rápida de paciente que entra ahora
3. Reagendar un turno
4. Iniciar/cerrar followup de tratamiento
5. Configurar nuevo tratamiento que ofrezco

**Recepción:**
1. Ver agenda general clínica
2. Responder mensaje paciente WhatsApp/IG/web
3. Confirmar/cancelar reserva paciente
4. Cobrar pago presencial
5. Cargar paciente nuevo

**Admin:**
1. Ver desempeño del mes (turnos, ARPU, no-show rate)
2. Configurar Brand Studio (identity + contact + team + testimonials)
3. Configurar tratamientos / planes
4. Agregar/quitar doctor del equipo
5. Cambiar plan / ver facturación

### 3. ¿Hay un patrón de "vista única dominante"?

Comparar paradigmas:
- **Single dominant view** (Linear: issues, Notion: page, Cursor: editor) — una cosa ocupa todo, todo lo demás es modal/overlay/sidebar pequeño
- **Multipane permanente** (Gmail: list+detail, Slack: channels+thread+rail) — el espacio se divide y mantiene
- **Híbrido contextual** (Cursor con tabs, Linear con peek) — cambia según acción

¿Qué encaja con clínicas LatAm? Posible: doctor prefiere SINGLE DOMINANT, recepción prefiere MULTIPANE.

### 4. ¿El copilot es siempre visible o invocable?

Opciones:
- Siempre visible (panel persistente) — ocupa pantalla, atribución constante
- Invocable (Cmd+K) — no estorba pero menos diferenciador
- Híbrido (FAB cuando no expandido, panel cuando expandido) — patrón Linear/Intercom

¿Decisión depende del rol? Doctor podría usar invocable; recepción persistente.

### 5. ¿Cómo conviven los 5 agentes en una sola UI?

- Valeria es la cara visible (chat = ella)
- Adrián/Lucas trabajan invisibles en background → aparecen en activity feed
- ¿Hay vista "Equipo trabajando" como Sentry dashboards o Linear cycles?
- ¿Notificaciones push agrupadas por agente?

### 6. ¿El flujo de navegación tiene "shortcuts críticos"?

¿Qué se hace 80% del tiempo? Eso define el atajo principal (botón hero, keyboard shortcut, primer entry sidebar). Hipótesis: para doctor = "ver mi día"; para recepción = "inbox conversaciones".

## Próximos pasos sesión UX (orden propuesto)

1. **Empezar por el USUARIO, no el layout**
   - Definir 3 personas (Doctor / Recepción / Admin) con detalle
   - Mapear top 5 jobs por persona
   - Frecuencia de uso por job (daily / hourly / weekly)

2. **Mapear flujo de navegación principal** (sin layout aún)
   - Diagrama de flow con entradas + salidas
   - Detectar atajos críticos (80% del tiempo)
   - Posible: flujos DISTINTOS por rol

3. **Recién después decidir layout**
   - Basado en flow, no en preferencia estética
   - Considerar: layout dinámico por rol (doctor ve A, recepción ve B)

4. **Prototipar 2-3 flows completos** (no pantallas sueltas)
   - Click-through HTML mostrando: entrada app → tarea específica → resolución
   - Validar con Chris antes de implementar

5. **Si flow ratifica patrón, ratificar design-system.md** (corrección de tokens si hace falta)

6. **Después: redactar Slice 1 MVP con tickets atómicos** (T-fe-1..N)

## Cómo retomar en nueva conversación

```bash
# Bootstrap nueva conversación UX (terminal Claude Code)
/po-ux
```

Decirle a Claude:

> "Continuamos UX iteration vitalia. Lee en orden:
> 1. `vitalia/docs/product/stories/vitalia-ux-discovery/00-research.md` (este handoff — entrada obligatoria)
> 2. `vitalia/docs/architecture/design-system.md` (tokens base cementados — NO re-litigar)
> 3. `/tmp/vitalia-mockups.html` (mockup previo exploratorio — NO copiar, era ejercicio descartado)
>
> Empezamos por personas + jobs-to-be-done + flujo de navegación. NO arrancar por layout. Confirmá hipótesis de 3 personas (doctor/recepción/admin) o proponé otras."

## Referencias producidas/leídas esta sesión

| Path | Estado |
|---|---|
| `vitalia/docs/architecture/design-system.md` | **Creado esta sesión** (cementa tokens base) |
| `vitalia/docs/product/stories/vitalia-ux-discovery/checkpoint.md` | **Creado esta sesión** |
| `vitalia/docs/product/stories/vitalia-ux-discovery/00-research.md` | **Este doc** |
| `vitalia/docs/product/checkpoint.md` | **Actualizado** (agregada story `vitalia-ux-discovery` a active_stories) |
| `/tmp/vitalia-mockups.html` | Mockup HTML exploratorio (NO ratificado) |
| `nicolify/frontend/src/features/copilot/` | Audited (65+ componentes — fork target) |
| `nicolify/backend/src/modules/nicolify/advertising/` | Audited (joya reusable para Lucas) |
| `vitalia/backend/src/modules/vitalia/` | Audited (24 endpoints, 17 EPs scaffold) |
| `vitalia/backend/src/modules/vitalia/extensions.py` | Audited (EP-1..EP-18 registry) |
| `comunify/docs/architecture/design-system.md` | Leído (formato sibling — template estructural) |
| `vitalia/config/brand.yaml` | Leído (features + plan tiers + currencies) |
| `vitalia/.claude/rules/hipaa-lite.md` | Leído (PHI surface rules) |
| `docs/product/outcomes/dev-stack-cross-brand-fixes.md` | Leído (issues cross-brand deferidos) |
| `vitalia/docs/product/stories/vitalia-dev-stack-functional/checkpoint.md` | Leído (story paralela, issues 7+8 abiertos) |
