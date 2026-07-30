# vitalia-ux-discovery — 00-research-chat-layout

> **Research independiente** (Claude Opus 4.7) sobre patrones de layout chat+workspace para apps agéntico-conversacionales 2025-2026. Producido 2026-05-17 para informar decisión `/po-ux` v1 Vitalia. NO sustituye ratificación Chris — provee evidencia.
> Scope: 4 ejes (3-columnas viability, chat-LEFT layouts, chat-driven nav híbrida, URL state mgmt). 13 productos analizados + 3 docs oficiales fetchados.

---

## § TL;DR

1. **El patrón "chat-LEFT + workspace-RIGHT" es la convención emergente dominante en herramientas agéntico-creativas 2025-2026** (Devin, Manus, OpenAI Operator, Claude Artifacts, ChatGPT Canvas, v0/Vercel, Lovable, Perplexity), mientras que **"chat-RIGHT como rail copilot"** es la convención de SaaS productivos donde el workspace primario NO es output del chat (Microsoft 365 Copilot, Notion Agents, GitHub Copilot, Cursor original).
2. **Vitalia cae en zona híbrida ambigua:** el chat (Valeria) NO genera el workspace (no es generativo), pero el chat SÍ puede instruir navegación + ejecutar acciones que afectan al workspace (booking, NPS, marketing). No es Devin ni es Notion AI — es operacional con copilot conductor.
3. **El patrón Nicolify (sidebar 240 + main + rail 60→460/680 con Shell Mutex auto-collapse) NO es una invención exótica — es una **variante refinada del patrón "Side-by-side Copilot Mode" de Microsoft 365** (inline default → expanded on demand), pero con la innovación de auto-collapsar la nav cuando el copilot se expande para mantener máximo 2 columnas dominantes simultáneas.
4. **Recomendación tentativa para Vitalia:** **NO** invertir a chat-LEFT-primary. Mantener el patrón Nicolify (Propuesta A) ratificado por uso real, con **dos mejoras de UX que sí valen la pena**: (a) **chat-driven navigation con URL como SSoT** (vía `nuqs` o equivalente), (b) **rail más visible en idle** (60px → 72-80px con identidad Valeria + hint de acción "pedile algo").
5. **Si Chris quiere disruptivo,** la única alternativa con evidencia productiva sólida es **Propuesta C: "Wizard-First Asymmetric"** — chat-LEFT solo durante onboarding/wizards de alto valor (Brand Studio, configuración inicial), luego transición permanente a layout Nicolify para operación diaria. Híbrido por fase de uso, no por preferencia visual.

---

## § Evidencia Eje 1 — ¿El patrón 3 columnas (nav + main + chat) realmente falla?

### Veredicto: NO falla universalmente. Depende del rol semántico de cada columna.

### Evidencia productiva (productos en uso real con 3 columnas)

| Producto | Sidebar L | Main | Rail/Panel R | Cómo lo resuelven | Fuente |
|---|---|---|---|---|---|
| **Microsoft 365 Copilot** | App nav (Outlook/Teams/etc.) | Documento activo | Copilot inline + side-by-side expand mode | Inline default (40-50% rail), side-by-side opt-in cuando user lo invoca explícitamente. NO los 3 dominantes simultáneos. | [Microsoft Learn MCP guidelines](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-ui-widgets-guidelines) |
| **Notion AI Agents** | Workspace nav | Página activa | Custom Agent chat (sidebar mode) o Floating (window) | Usuario elige modo. Floating cuando quiere multitasking, Sidebar cuando quiere docked. Notion 3.1 (Nov 2025) introdujo tabbed sidebar para reducir densidad. | [Notion Custom Agents docs](https://www.notion.com/help/custom-agents), [Notion 3.1 release](https://www.notion.com/releases/2025-11-17) |
| **GitHub Copilot (VS Code)** | File tree | Editor | Copilot Chat (Secondary Side Bar) | Resolvable: rail-by-default + "Open Chat in Editor" (full pane) + "Open in New Window" (separate window). Tres modos según contexto. | [GitHub issue #245639](https://github.com/microsoft/vscode/issues/245639), [GitHub for Beginners Copilot](https://github.blog/ai-and-ml/github-copilot/github-for-beginners-essential-features-of-github-copilot/) |
| **Cursor 1.x** | File tree | Editor | Chat panel (left/right configurable) | Pane mode = chat sidebar + editor. Default es sidebar mode. | [Cursor docs Composer](https://docs.cursor.com/composer/overview), [Cursor chat overview](https://docs.cursor.com/chat/overview) |
| **Cursor 2.0 (Nov 2025)** | Agents/Plans/Runs first-class | Conversation + diffs | — | **Refactorizó a 2 columnas dominantes**: agentes como first-class objects + conversation/diffs centro. Eliminó el patrón "file-based 3 col" porque "el agente, no el archivo, es la unidad de trabajo". | [The Decoder Cursor 3 launch](https://the-decoder.com/new-cursor-3-ditches-the-classic-ide-layout-for-an-agent-first-interface-built-around-parallel-ai-fleets/), [Cursor 2.0 changelog](https://cursor.com/changelog/2-0) |
| **Manus AI** | History/sessions (L narrow) | Prompt input + chat (centro) | "Manus's Computer" (R panel ample) | **3 columnas claramente jerarquizadas**: L=meta-history (delgada), Centro=conversación primaria, R=execution viewer (la "vidriera de transparencia"). El centro NO es workspace persistente, es el chat. | [Manus AI architecture](https://ai-stack.ai/en/manusai), [WorkOS Manus intro](https://workos.com/blog/introducing-manus-the-general-ai-agent) |
| **Linear (post 2025 redesign)** | Workspace nav (compacto) | Issues/Projects | NO chat panel persistente | Refactorización 2025 explícitamente **redujo "visual noise"** y enfatizó "clarity, emphasize hierarchy". Linear AI vive embedded inline (no rail persistente). | [SaaS UI Design Trends 2026](https://www.saasui.design/blog/7-saas-ui-design-trends-2026), [Eleken UX nav patterns](https://www.eleken.co/blog-posts/ux-navigation-design) |

### Heurísticas formales encontradas

- **Nielsen Norman Group** (artículo "10 Guidelines for Designing Your Site's AI Chatbots"): la única crítica directa a chatbot-in-sidebar es de **context awareness** ("the chatbot doesn't know what I'm looking at"), NO de jerarquía visual de columnas. NN/G **no publica heurística sobre "máximo de columnas dominantes simultáneas"**. Esa restricción es folklore de practitioners, no canon. [Fuente: NN/G chatbot guidelines](https://www.nngroup.com/articles/ai-chatbots-design-guidelines/)
- **F1Studioz (2026 SaaS dashboard guide)**: "Avoid dashboards exceeding three columns" — pero esto aplica a **dashboards de datos** (gráficos en columnas), no a **layout de app shell**. Confusión común. [Fuente: F1Studioz SaaS dashboard guide](https://f1studioz.com/blog/smart-saas-dashboard-design/)
- **Luke Wroblewski (2025, ref. canónica AI chat layouts)**: critica chats en panels narrow ("by the time a task is complete, the initial user message is long off screen") pero su propuesta es **dual-column con collapse de left a summary**, no eliminar columnas. [Fuente: LukeW alternative chat UI](https://www.lukew.com/ff/entry.asp?2135)

### Shell Mutex (auto-collapse al expandir) ¿es invención Nicolify?

**No es invención propia ni convención cementada.** Es un patrón **implícito y caso-a-caso** en herramientas productivas:
- **Devin AI** (Feb 2025 update): permite drag-to-resize chat ↔ workspace ratio. **No auto-collapsa nav** porque no tiene nav lateral fija — su sidebar es minimal (history). [Fuente: Cognition Feb '25 update](https://cognition.ai/blog/devin-february-25-product-update)
- **GitHub Copilot Chat**: no auto-collapsa file tree cuando se expande. Usuario debe colapsar manual. (Issue abierto pidiendo mejora.)
- **Cursor 2.0**: directamente **eliminó** la columna file-tree para dar máximo espacio al agente. Solución más radical que auto-collapse.
- **Microsoft 365 Copilot side-by-side mode**: pide explícitamente que el panel side-by-side **NO incluya global navigation, multi-tab systems, settings panels** — es decir, su solución es "el copilot expandido es scope reducido", no "auto-collapsa otras cosas". [Fuente: Microsoft MCP guidelines](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-ui-widgets-guidelines)

**Conclusión Eje 1:** El patrón 3-columnas funciona si **una de las tres es claramente subordinada** (rail delgado, panel de transparencia, sidebar compacto). Falla cuando **las tres compiten visualmente**. Shell Mutex de Nicolify es **innovación sensata** pero **no estándar** — está bien que sea diferencial, no es deuda. Auto-collapse es preferible a "Cursor 2.0 elimina la columna" porque preserva navegación discoverable.

---

## § Evidencia Eje 2 — Chat-LEFT layouts en producción

### Veredicto: CONVENCIÓN EMERGENTE clara para herramientas **generativo-creativas**, NO universal para SaaS operacionales.

### Productos chat-LEFT (canvas/output a la derecha)

| Producto | Layout chat-LEFT | Workspace-RIGHT | ¿Tiene nav sidebar adicional? | Comportamiento mobile |
|---|---|---|---|---|
| **Devin AI** (Cognition) | Chat panel L, drag-resize | Workspace R con 4 tabs: Shell/Browser/Editor/Plan | Sí — file tree dentro del workspace R (sub-columna). Devin 2.0 (April 2025) introdujo IDE full. | Drag feature documented for desktop. Mobile no explícito. [Fuente: Cognition Feb '25](https://cognition.ai/blog/devin-february-25-product-update) |
| **Manus AI** | "L sidebar = history" + "Centro = chat" + "R = Manus's Computer" | El R panel ES el workspace observable (browser/terminal/VS Code) | L narrow (history), no es nav del workspace | No documentado mobile-first |
| **Claude Artifacts** | Chat L (50%) | Artifact R (50%) preview | NO — el chat IS el shell. Sidebar es history de conversations | Mobile responsive. Sidebar collapsible. [Fuente: IntuitionLabs comparison](https://intuitionlabs.ai/articles/conversational-ai-ui-comparison-2025) |
| **ChatGPT Canvas** | Chat L (25-30%) | Doc/Code editor R (70-75%) | NO — chat IS el shell. Sidebar history opcional | Mobile responsive — sidebar hideable [Fuente: AlgoCademy comparison](https://algocademy.com/blog/chatgpt-canvas-vs-claude-artifacts-for-programming-a-comprehensive-comparison/) |
| **OpenAI Operator** | Chat L | Live browser controlled by agent R | NO | — |
| **v0 by Vercel** (post rebrand to v0.app) | Conversation L | Live preview pane R | NO — chat IS el shell. Sidebar = history projects | Responsive con toggle [Fuente: nxcode v0 guide](https://www.nxcode.io/resources/news/v0-by-vercel-complete-guide-2026) |
| **Lovable.dev** | Conversation + live preview (chat-emphasized) | Code accessible pero not front-and-center | NO — design pensado para no-devs, código deprioritized | Mobile prototyping prominent [Fuente: aimonks ranking](https://medium.com/aimonks/i-ranked-every-ai-app-builder-lovable-vs-c7be562f24f0) |
| **Bolt.new** | File tree + chat | Editor + terminal + preview (multi-pane) | Sí — file tree L narrow. Más "dev tool" que "chat-first" | — |
| **Perplexity** | Conversation L | Source/Answer R | History sidebar L narrow opcional | Responsive |
| **MagicPath** | Infinite canvas con chat embedded | — | Canvas IS the workspace (spatial) | Desktop-first |
| **Replit Agent** | "Every time I open a repl, an AI-related chat window opens on the right" — chat-RIGHT! | Workspace L (editor) | Sí | [Fuente: Skywork Replit Agent](https://skywork.ai/blog/replit-agent-definition-2/) |
| **Cursor original** | Editor L | Chat R | File tree L narrow | — |

### Patrón "Split-Screen" (Anastasia Walia 2025 — Medium)

Su catálogo de 5 patrones AI chat UI es la mejor síntesis encontrada:

1. **Classic Chat** (WhatsApp/Slack) — full vertical scroll, sin workspace
2. **Chat + Workbench (Split-Screen) chat-LEFT** — Perplexity, Claude Artifacts. *"chat on left aligns with F-shaped scan pattern to emphasise co-creation"* [Fuente: Anastasia Walia](https://medium.com/@anastasiawalia/ai-chat-layout-patterns-when-to-use-them-real-examples-d03f04a19194)
3. **Embedded Assistant** — CRM summarization, Figma suggestions, Canva side panel. *"Multiple AI interfaces within one app can create decision fatigue"*
4. **Floating Assistant (Sidebar Copilot)** — SAP's Joule (dockable), siempre accesible
5. **Full-Screen AI** — agente autónomo con UI tradicional mínima

### Insight clave: Vitalia NO encaja en el pattern chat-LEFT generativo

El patrón chat-LEFT es **predominantemente para herramientas donde el chat GENERA el output que ves a la derecha**. En Vitalia:
- Cuando user navega a `/agenda`, el calendario YA existe (data persistente, no generada por chat).
- Cuando Valeria conduce el wizard de Brand Studio, el output (config guardada) NO es lo que mira a la derecha — lo que mira es un form pre-existente.
- El chat es **conductor/asistente**, no generador.

**Esto coincide con el patrón Microsoft 365 Copilot, no con Devin/v0.** M365 Copilot es chat-RIGHT explícitamente porque "Outlook es la app primaria, Copilot la asiste". Vitalia tiene la misma semántica: "Agenda es la app primaria, Valeria asiste".

### Convención emergente vs SaaS productivos

| Categoría producto | Convención dominante 2025-2026 | Ejemplo canon |
|---|---|---|
| **Generative tooling** (output = chat artifact) | **Chat-LEFT 50/50 split** | Devin, Claude Artifacts, ChatGPT Canvas, v0, Lovable, Manus |
| **SaaS operacionales** (workspace persistente, copilot asistente) | **Chat-RIGHT rail/sidebar** | Microsoft 365 Copilot, Notion Agents, GitHub Copilot, Salesforce Einstein, Cursor 1.x |
| **IDEs agéntico-first 2026** (agentes = unidad de trabajo) | **2 col: agents L + conversation R**, sin file tree | Cursor 2.0/3.0 |
| **Healthcare/Clinical assistants** | Embedded en widgets contextuales + lateral chat opcional | Microsoft Healthcare Agent Orchestrator, Innovaccer Cured |

**Conclusión Eje 2:** Chat-LEFT primary **no es disruptivo en 2026** — es **convención emergente para el subgrupo equivocado** de productos (generativos). Para Vitalia (operacional + copilot asistente) la convención emergente es chat-RIGHT rail, que es **exactamente lo que Nicolify implementó**. Chris no debería invertir basándose en "los mejores sistemas lo hacen al revés" porque los mejores sistemas SaaS operacionales NO lo hacen al revés.

---

## § Evidencia Eje 3 — Chat-driven navigation híbrido (chat navega + user navega)

### Patrones técnicos encontrados

#### Patrón 1: URL como SSoT, chat dispatch via router.push()

- **LangChain Deep Agents UI** (open-source, Next.js 16 + React 19): URL state managed via `nuqs` para `threadId`, `sidebar` state, `assistantId`. Cuando agent cambia estado → updates URL → componentes re-render. User puede navegar manual = mismo update path. [Fuente: DeepWiki deep-agents-ui](https://deepwiki.com/langchain-ai/deep-agents-ui)
- **assistant-ui** + **LangGraph**: stateful conversations con shareable URLs. Cada thread tiene URL propia. [Fuente: LangChain assistant-ui blog](https://blog.langchain.com/assistant-ui)
- **AG-UI Protocol** (Agent User Interaction): event-driven contract donde tools/messages/UI state son first-class. Permite el chat invocar acciones que cambian la app sin reload. [Fuente: LogRocket AG-UI](https://blog.logrocket.com/build-real-ai-with-ag-ui/)

#### Patrón 2: Generative UI con component grammars

- **CopilotKit Generative UI** (2026): tres sub-patrones:
  1. **Static Generative UI** (high control): agente selecciona qué componente predefinido mostrar + lo llena con data
  2. **Declarative Generative UI** (shared control): agente devuelve UI spec estructurada (A2UI / Open-JSON-UI)
  3. **Open-ended Generative UI** (low control): MCP Apps — agente devuelve UI completa
- Para Vitalia, **Static Generative UI** sería el patrón apto: Valeria selecciona "abrir vista agenda con filtro X" entre rutas/vistas predefinidas. NO inventa pantallas. [Fuente: CopilotKit Generative UI Guide 2026](https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026)

#### Patrón 3: Next.js App Router parallel/intercepting routes

- **Vercel docs**: Parallel Routes permite renderizar simultánea o condicionalmente múltiples páginas en mismo layout. Intercepting Routes permite cargar ruta dentro del layout actual sin navegación full. Combinados = URL-driven modals con back-button correcto. [Fuente: Next.js App Router docs](https://app-router.vercel.app/parallel-routes), [LogRocket Next.js routing](https://blog.logrocket.com/exploring-advanced-next-js-routing-conventions/)
- **Aplicabilidad Vitalia**: chat puede pedir "abrime el turno X" → intercepting route renderiza detail dentro del shell sin perder el chat thread visible.

#### Patrón 4: nuqs como URL state SSoT

- **nuqs.dev** (~6kb gzipped, usado por Sentry/Supabase/Vercel/Clerk): `useState`-like API que sincroniza estado con search params. Type-safe parsers (`parseAsInteger`, etc.). Soporta App Router + Pages Router + Remix + TanStack Router. [Fuente: nuqs.dev](https://nuqs.dev/), [InfoQ React Advanced 2025](https://www.infoq.com/news/2025/12/nuqs-react-advanced/)
- Patrón clave para Vitalia: cada vez que Valeria cambia algo (ej. filtra agenda por especialidad) → update URL search params → componentes re-render → estado bookmarkable + back-button funciona naturalmente.

### Ejemplos concretos chat ↔ workspace ↔ URL

| Producto | Chat puede navegar | User puede navegar manual | URL refleja ambos updates | Back button funciona |
|---|---|---|---|---|
| Deep Agents UI (open-source) | Sí (threadId update) | Sí (ThreadList component click) | Sí (nuqs) | Sí |
| Cursor 2.0 | Sí (agente abre files, runs) | Sí | Parcial (project-scoped state) | Sí |
| v0 | Sí (nuevo project, nuevo branch) | Sí (history sidebar) | Sí (project URL distinct) | Sí |
| Claude Artifacts | Limitado — chat dispatcha artifact en mismo thread | Sí (thread sidebar) | Sí (thread URL) | Sí |
| Notion AI Agents (Floating mode) | El agent puede crear/abrir páginas | Sí | Sí — Notion URLs page-scoped | Sí |
| ChatGPT Canvas | Sí (open canvas from chat msg) | Sí | Sí | Sí |

**Pattern dominante:** **URL = SSoT**. Chat history es secundario (caché de mensajes), pero la "verdad" del estado app vive en URL. Esto permite:
- Compartir links a "ese turno que Valeria me abrió"
- Refresh sin perder contexto
- Back button intuitivo
- Multi-tab funciona (cada tab tiene su URL)

**Conclusión Eje 3:** La combinación **nuqs + Next.js App Router parallel routes + chat tool-calling con `router.push()` dispatch** es el stack productivo bien documentado para chat-driven nav híbrido. Vitalia tiene Next.js 16 ya en stack — esto es brownfield-compatible.

---

## § Evidencia Eje 4 — URL state management para apps agéntic

### Preguntas y respuestas con evidencia

#### Q: ¿Qué se persiste en URL? ¿Solo ruta o también contexto conversacional?

**Pattern A (más adoptado): URL = ruta + contexto operacional, NO contexto conversacional**
- Ejemplo Vitalia: `/agenda?date=2026-05-18&specialty=odonto&doctorId=42&convId=abc-123`
- `convId` opcional como **hint** al chat para resumir conversación, pero la "verdad" de qué turno se muestra es `date + specialty + doctorId`.
- Beneficio: bookmarkeable, shareable, back-button correcto sin reproducir conversación.

**Pattern B (menos común): URL incluye chat turn id**
- Ejemplo: `/chat/abc-123/turn/42/view/agenda`
- Usado en Deep Agents UI (`threadId` + sidebar state). Implica que cada turn puede tener URL propia → cualquier persona con link reproduce el estado.
- Tradeoff: URLs largas, share complejo, back-button salta entre turns y rutas mezclados.

**Recomendación research:** Pattern A para Vitalia. El operador (recepción) NO quiere "compartir conversaciones" — quiere "abrir el turno tal" o "ver agenda de tal día". El contexto conversacional es para Valeria (state interno LangGraph), no para el operador.

#### Q: ¿Cómo se maneja back button cuando agente hizo 5 navegaciones consecutivas?

Tres approaches documentados:
1. **History stack normal** (default Next.js / nuqs): cada nav del agente es una entry en history. Back button retrocede una por una. **Confuso si agent navegó por su cuenta** — user puede sentirse "no entiendo a dónde voy". (Anti-pattern documented en Deep Agents.)
2. **Replace mode** (`router.replace()` en lugar de `push`): nav del agente NO crea entries. User solo retrocede por sus propios clicks. **Más predecible** pero pierde la traza de "qué hizo el agente".
3. **Hybrid** (nuqs `history: 'replace'` para search params, `push` para route changes): el cambio "abrí turno X dentro de agenda" usa replace, el cambio "fui de /inbox a /agenda" usa push. **Mejor UX** según docs nuqs. [Fuente: nuqs docs history controls](https://nuqs.dev/docs/options)

**Recomendación research:** Pattern hybrid. Aplica en Vitalia: navegación entre rutas P1 (Inbox/Pipeline/Agenda/Fidelización/Marketing) = push. Sub-state (filter, selected ID, modal open) = replace.

#### Q: ¿Conversación tiene URL propia?

- Manus AI: sí, replay sessions tienen URL shareable. Cada session = URL distinta.
- Claude.ai: sí, cada conversation en sidebar = URL propia (rename-able).
- ChatGPT: sí, chat history = URL propia.
- **Para Vitalia**: probablemente NO en MVP. El operador no quiere "compartir conversación con Valeria con la persona del turno siguiente" — quiere ver el turno. Conversación es persistent pero secundaria.

#### Q: ¿Sincronización chat ↔ workspace cuando user navega manual?

Tres approaches:
1. **Pasivo**: chat ignora navegación manual del user (mensajes previos quedan stale). Anti-pattern.
2. **Notificación al agent**: cuando user navega manual → app emite event al chat → chat puede contextualizar siguiente mensaje. ("Veo que abriste el turno de las 14h, ¿querés que te ayude con algo?")
3. **Chat context refresh**: chat backend recibe "current route" en cada turn como context. Más caro tokens-wise pero más coherente.

**Recomendación research:** Pattern 2 (event-based) es el balance correcto. nuqs facilita esto porque cada URL change es observable.

### Tradeoffs SSoT options

| SSoT | Pro | Con |
|---|---|---|
| **URL search params** (nuqs) | Bookmarkeable, shareable, back-button natural, type-safe | Limitado a strings serializables, URLs pueden crecer largas |
| **Zustand + manual URL sync** | Más flexibilidad para state complejo | Boilerplate alto, riesgo desync |
| **React Query cache** | Server state cacheado, refetch automático | NO es SSoT del UI state — falla bookmark/share |
| **TanStack Router search params** | Type-safety + nested routes | Vitalia usa Next.js, fuera de stack |
| **Chat history como SSoT** | "Replay completo" gratis | Refresh pierde estado, back-button no funciona, share imposible |

**Conclusión Eje 4:** URL search params (nuqs) + Next.js App Router parallel routes + event-based sync chat → ruta es el stack más sólido. Es lo que adoptaron Deep Agents UI, v0, Claude.ai y los stacks LangChain modernos. **No es disruptivo, es la convención emergente.**

---

## § 3 propuestas concretas para Vitalia

### Propuesta A — "Nicolify Refinado" (CONSERVADORA, baseline)

Layout actual Nicolify + 2 mejoras puntuales.

```
┌──────────────────────────────────────────────────────────────────┐
│ TopBar (clinic switcher + user menu + global search ⌘K)          │
├────────┬───────────────────────────────────────────┬─────────────┤
│        │                                           │             │
│ Sidebar│         Main Content                      │  Copilot    │
│  240px │         (la ruta activa)                  │  Rail       │
│        │         /inbox /pipeline /agenda          │  72px       │
│  Inbox │         /fidelizacion /marketing          │  (Valeria   │
│  Pipe  │                                           │  identity   │
│  Agen  │         [resizable handle entre main      │  visible)   │
│  Fide  │          y rail si user expande]          │             │
│  Mark  │                                           │  click →    │
│  ───   │                                           │  expand 460 │
│  Dash  │                                           │             │
│        │                                           │             │
└────────┴───────────────────────────────────────────┴─────────────┘

Estado expandido (Valeria active):

┌──────────────────────────────────────────────────────────────────┐
│ TopBar                                                            │
├────────┬───────────────────────────────────────────┬─────────────┤
│ Rail   │                                           │             │
│  60px  │         Main Content                      │  Copilot    │
│ collapse│        (la ruta activa)                  │  460px      │
│ (Shell │        [resizable handle]                 │  chat       │
│ Mutex) │                                           │             │
└────────┴───────────────────────────────────────────┴─────────────┘
```

**Pros:**
- Reuso máximo Nicolify (~85%): 65+ componentes copilot, paths exactos `nicolify/frontend/src/features/copilot/`
- 0 deuda de migración patrón — vitalia hereda lo cementado
- Cumple convención emergente "chat-RIGHT rail para SaaS operacional" (Microsoft 365 Copilot, Notion Agents pattern)
- Shell Mutex evita 3 columnas dominantes simultáneas (resuelve la objeción inicial Chris)

**Cons:**
- "Conservador" — no es disruptivo, no genera diferenciación de marca por layout
- Rail 60px puede ser "no descubrible" en idle (mejora con 72px + identidad Valeria visible)

**Mejoras propuestas vs Nicolify actual:**
1. **Rail idle 72-80px en lugar de 60px**: cabe avatar Valeria + nombre + hint "pedile algo". Refuerza diferenciador #1 (agentes identidad humana visible).
2. **chat-driven nav con URL como SSoT**: Valeria invoca `router.push('/agenda?date=...')` via tool. nuqs sincroniza search params. Back-button funciona.
3. **Event-based chat context**: cada nav del user emite event a Valeria backend para contextualizar siguiente turn.

**Productos que validan:**
- Microsoft 365 Copilot (inline + side-by-side toggle)
- Notion AI Agents (sidebar mode default)
- GitHub Copilot (Secondary Side Bar)
- Nicolify (uso real Q4 2025-Q1 2026)

**Riesgos:** mínimos. Patrón validado por uso productivo.

---

### Propuesta B — "Chat-LEFT Primary" (DISRUPTIVA, la idea inicial Chris)

Chat conversación es columna izq primaria persistente. Workspace queda a la derecha + sidebar nav arriba o como overlay.

```
┌──────────────────────────────────────────────────────────────────┐
│ TopBar (route breadcrumb actual + ⌘K + user)                     │
├──────────────────────────┬───────────────────────────────────────┤
│                          │ ┌─ Nav tabs horizontales ───────────┐ │
│  Valeria Chat            │ │ Inbox · Pipeline · Agenda · ...  │ │
│  (always visible)        │ └─────────────────────────────────────┘
│  ~40-50% viewport        │                                       │
│                          │  Main Content (ruta activa)           │
│  Conversation history    │                                       │
│  [resizable handle]      │  [chat puede instruir nav, user       │
│                          │   también puede tab/⌘K]               │
│  Input box               │                                       │
│                          │                                       │
└──────────────────────────┴───────────────────────────────────────┘

Mobile responsive: stack vertical. Chat top, content bottom (o tabs).
```

**Pros:**
- Diferenciación visual fuerte vs todos los competidores LATAM health (ninguno tiene chat-LEFT primary)
- Refuerza diferenciador #1 (agentes con identidad humana) al hacer al agente literalmente la columna primaria
- Disruptivo, memorable
- Wizard onboarding fluye natural (Valeria conduce desde la izquierda)

**Cons (severos):**
- **Romper convención del subgrupo SaaS operacional**: Microsoft 365 Copilot, Notion, Linear, todos optaron chat-RIGHT explícitamente. Vitalia disruptaría hacia el patrón "generative tooling" (Devin/v0/Lovable) que **no aplica** a salud operacional.
- **Reuso Nicolify cae a ~40-50%**: el copilot rail no es directamente reusable como columna primaria. Refactor sustancial features/copilot/ + features/{ruta}/ shells.
- **Recepción/Owner roles operativos**: su job-to-be-done es operar el día (agenda + inbox). Conversación con Valeria es **medio**, no **fin**. Hacer conversación la columna primaria es contradictorio con el JTBD.
- **Risk evaluación negativa Chris/usuarios**: layout "raro" en categoría salud LATAM — clínica usaria sistemas tradicionales (Doctocliq, Dentalink) y comparará. "¿Por qué este sistema me hace mirar a la izquierda?" es la pregunta-killer.
- **Healthcare workflow optimization** investiga que clínicas privilegian "data prominence" (agenda como hero) sobre "AI prominence". [Fuente: Microsoft Healthcare Agent Orchestrator pattern](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/agentic-ai-in-healthcare/4447082)

**Productos que validan:**
- Devin AI (chat L drag-resize)
- Manus AI (chat centro + Computer R)
- Claude Artifacts (50/50)
- ChatGPT Canvas (25/75)
- v0/Lovable (chat L)
- Perplexity (split-screen)

**Productos que NO validan (y deberían):**
- Cero SaaS healthcare encontrado con chat-LEFT primary
- Cero SaaS operacional (CRM, agenda, inbox) con chat-LEFT primary

**Riesgos:**
- ROI negativo: la disrupción visual no necesariamente se traduce en valor para clínica (cliente final)
- Bonito en demo, dudoso en uso diario 8h
- Cae fuera de convención emergente del **subgrupo correcto** (operacional, no generativo)

**Cuándo SÍ tendría sentido B:** si Vitalia fuera un producto donde Valeria genera todo el output (ej. generador de campañas marketing chat-driven exclusivamente). NO es el caso del MVP Slice 1 (5 rutas operacionales).

---

### Propuesta C — "Wizard-First Asymmetric" (HÍBRIDA, disruptivo por FASE)

Chat-LEFT **solo durante wizards/onboarding** de alto valor. Transición a layout Nicolify para operación diaria post-wizard.

```
FASE 1 — PRIMER LOGIN OWNER (wizard Brand Studio con Valeria):

┌──────────────────────────────────────────────────────────────────┐
│ Logo Vitalia + progress 1/5                                       │
├──────────────────────────────┬───────────────────────────────────┤
│                              │                                   │
│  Valeria                     │  Form Brand Studio scaffold       │
│  "Hola, soy Valeria. Vamos   │  (auto-fill desde respuestas      │
│   a configurar tu clínica.   │   chat, user puede editar)        │
│   Empecemos con el nombre."  │                                   │
│                              │  [Live preview de cómo se verá    │
│  [chat full conversation]    │   en sales_agent / landing]       │
│                              │                                   │
│  Input box                   │                                   │
│                              │                                   │
└──────────────────────────────┴───────────────────────────────────┘

POST-WIZARD (operación diaria):

(Vuelve a layout Propuesta A — Nicolify Refinado, chat-RIGHT rail)
```

**Pros:**
- **Disruptivo donde importa**: el primer login (momento "wow") es chat-LEFT primary. Refuerza diferenciador #1 (agentes identidad) en el momento de mayor atención del Owner.
- **Convencional donde importa**: operación diaria sigue convención operacional → reuso Nicolify ~85%, productividad alta.
- **Justificable productivamente**: wizards complejos (Brand Studio 5 secciones + Offer Studio + buyer personas) son **exactamente el tipo de tarea donde chat-LEFT funciona** — conversación genera el output.
- **Convención emergente correctamente aplicada**: chat-LEFT para tareas generativas (wizard), chat-RIGHT para tareas operacionales (agenda/inbox).
- **Refuerza diferenciador #3** (wizard Valeria scope mínimo Slice 1) — el wizard ya está en scope.

**Cons:**
- **Dos layouts en mismo producto**: introduce complexity. Riesgo de inconsistencia visual.
- **Transición wizard → app diaria** necesita micro-interaction cuidado (Valeria "se mueve" de columna primaria a rail).
- **No es chat-LEFT permanent** — Chris quería "disruptivo permanente". Esta es disrupción por fase.

**Productos que validan:**
- Onboardings de productos B2B SaaS modernos (Linear, Notion, Lovable) usan wizards conversacionales chat-prominente
- Lovable.dev: el primer prompt es chat-emphasized, después transition a editor split
- Cursor 2.0 plan flow: chat-prominente cuando planeas, sub-rail cuando ejecutás

**Riesgos:**
- Mediano: necesita design system con DOS layouts coherentes
- Implementación: probablemente 2-3 días extra vs Propuesta A

**Cuándo C sería ideal:** Vitalia tiene 1 wizard (Brand Studio onboarding) + 5 rutas operacionales. C aprovecha exactamente eso. Slice 2 podría agregar Offer Studio + buyer personas wizards con mismo patrón.

---

## § Open questions para Chris (decisiones humanas)

1. **¿Qué define "disruptivo" para vos?** ¿Layout visualmente único (B) o experiencia onboarding memorable + operación cómoda (C)? Ambos son disruptivos, pero por dimensiones distintas.
2. **¿Cuál es el peso relativo de "diferenciación visual vs competidores LATAM" vs "productividad operativa 8h/día"?** Si recepción usa la app 6-8h, ¿la disrupción visual permanente le suma o le resta?
3. **¿Aceptarías que Vitalia se parezca más a Microsoft 365 Copilot (chat-RIGHT rail) que a Devin AI (chat-LEFT)?** Esto es lo que la evidencia 2025-2026 indica para apps operacionales.
4. **¿El wizard Brand Studio escapa el scope Slice 1?** Si está cementado (checkpoint confirma scope mínimo wizard), la Propuesta C cae perfecto. Si lo querés escapar más al Slice 2, Propuesta C pierde su mejor caso de uso.
5. **¿URL como SSoT (nuqs + parallel routes) es OK con `/architect`?** Esto debe ser ratificado técnicamente — pero pide brownfield-compatible con Next.js 16 ya en stack.
6. **¿Mobile como first-class citizen?** Recepción podría usar tablet/mobile en ciertos contextos. Propuesta A responsive es la más simple (rail collapsa, main full-width). Propuesta B mobile = stack vertical complejo. Propuesta C mobile = wizard fácil, app diaria = A responsive.
7. **¿Aceptás el Shell Mutex de Nicolify como solución cementada al problema "3 columnas dominantes"?** La evidencia confirma que el patrón NO es estándar pero ES una innovación sensata. Si lo aceptás, gran parte de la pregunta inicial se disuelve.

---

## § Fuentes

### Evidencia productiva (productos analizados)

- **Devin AI / Cognition** — [Cognition Feb '25 Product Update](https://cognition.ai/blog/devin-february-25-product-update) · [ppaolo Substack Devin product analysis](https://ppaolo.substack.com/p/in-depth-product-analysis-devin-cognition-labs) · [Devin docs releases 2025](https://docs.devin.ai/release-notes/2025)
- **Manus AI** — [AI-Stack Manus analysis](https://ai-stack.ai/en/manusai) · [WorkOS Introducing Manus](https://workos.com/blog/introducing-manus-the-general-ai-agent) · [MIT Technology Review Manus test](https://www.technologyreview.com/2025/03/11/1113133/manus-ai-review/)
- **Claude Artifacts** — [IntuitionLabs Conversational AI UI comparison 2025](https://intuitionlabs.ai/articles/conversational-ai-ui-comparison-2025) · [AlgoCademy ChatGPT Canvas vs Claude Artifacts](https://algocademy.com/blog/chatgpt-canvas-vs-claude-artifacts-for-programming-a-comprehensive-comparison/)
- **ChatGPT Canvas** — [VentureBeat OpenAI Canvas launch](https://venturebeat.com/ai/openai-launches-chatgpt-canvas-challenging-claude-artifacts) · [XsOne Consultants Canvas vs Artifacts](https://xsoneconsultants.com/blog/chatgpt-canvas-vs-claude-artifacts/)
- **Cursor 1.x / 2.0 / 3.0** — [Cursor Composer docs](https://docs.cursor.com/composer/overview) · [Cursor 2.0 changelog](https://cursor.com/changelog/2-0) · [The Decoder Cursor 3 agent-first layout](https://the-decoder.com/new-cursor-3-ditches-the-classic-ide-layout-for-an-agent-first-interface-built-around-parallel-ai-fleets/)
- **v0 by Vercel** — [nxcode v0 complete guide 2026](https://www.nxcode.io/resources/news/v0-by-vercel-complete-guide-2026) · [aiagentskit v0 tutorial 2026](https://aiagentskit.com/blog/v0-vercel-tutorial/)
- **Lovable.dev** — [aimonks AI app builder ranking 2025](https://medium.com/aimonks/i-ranked-every-ai-app-builder-lovable-vs-c7be562f24f0) · [MindStudio Bolt vs Lovable](https://www.mindstudio.ai/blog/bolt-vs-lovable) · [nxcode Bolt.new vs Lovable 2026](https://www.nxcode.io/resources/news/bolt-new-vs-lovable-2026)
- **Bolt.new** — [techpoint Lovable vs Bolt 2025](https://techpoint.africa/guide/lovable-vs-bolt/)
- **Replit Agent** — [Skywork Replit Agent definition](https://skywork.ai/blog/replit-agent-definition-2/) · [MindStudio Replit Agent 4](https://www.mindstudio.ai/blog/what-is-replit-agent-4) · [Replit 2025 review blog](https://blog.replit.com/2025-replit-in-review)
- **GitHub Copilot / VS Code** — [GitHub Copilot panel left align issue #245639](https://github.com/microsoft/vscode/issues/245639) · [GitHub Copilot features docs](https://docs.github.com/en/copilot/get-started/features)
- **Microsoft 365 Copilot** — [MCP apps UI guidelines](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-ui-widgets-guidelines) · [Microsoft Healthcare Agent Orchestrator](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/agentic-ai-in-healthcare/4447082)
- **Notion AI Agents** — [Notion Custom Agents docs](https://www.notion.com/help/custom-agents) · [Notion 3.1 release notes](https://www.notion.com/releases/2025-11-17) · [Notion sidebar navigation guide](https://www.notion.com/help/navigate-with-the-sidebar)
- **MagicPath / Same.new** — [Banani MagicPath review](https://www.banani.co/blog/magicpath-ai-review) · [DesignToolMark MagicPath](https://www.designtoolmark.com/resources/detail/magic-path)
- **Linear** — [SaaSUI 7 Design Trends 2026](https://www.saasui.design/blog/7-saas-ui-design-trends-2026) · [Eleken UX navigation patterns](https://www.eleken.co/blog-posts/ux-navigation-design)

### Heurísticas + research papers + frameworks

- **Nielsen Norman Group** — [10 Guidelines for AI Chatbots](https://www.nngroup.com/articles/ai-chatbots-design-guidelines/)
- **Luke Wroblewski (LukeW)** — [Alternative Chat UI Layout 2025](https://www.lukew.com/ff/entry.asp?2135) — referencia canon
- **Anastasia Walia (UX Collective)** — [AI Chat Layout Patterns Real Examples](https://medium.com/@anastasiawalia/ai-chat-layout-patterns-when-to-use-them-real-examples-d03f04a19194) — síntesis 5 patrones
- **Emerge Haus** — [The New Dominant UI Design for AI Agents](https://www.emerge.haus/blog/the-new-dominant-ui-design-for-ai-agents) — chat-LEFT split-screen analysis
- **Fuse Lab Creative** — [Agent UX UI Design 2026](https://fuselabcreative.com/ui-design-for-ai-agents/)
- **Smashing Magazine** — [Designing for Agentic AI](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/) — control/consent/accountability patterns
- **UX Raspberry (Medium)** — [The agentic interface principles and patterns](https://medium.com/@uxraspberry/the-agentic-interface-principles-and-patterns-for-autonomous-user-experiences-b0c1ecb8544f)
- **CopilotKit** — [Developer's Guide to Generative UI 2026](https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026)
- **UX for AI** — [UX Best Practices for Copilot Design](https://www.uxforai.com/p/ux-best-practices-copilot-design)
- **Spiralscout** — [Practical AI UX Playbook For Websites: Chatbots And Recs](https://spiralscout.com/blog/ai-ux-playbook-for-websites)
- **LogRocket** — [Build real AI with AG-UI](https://blog.logrocket.com/build-real-ai-with-ag-ui/) · [Managing search parameters in Next.js with nuqs](https://blog.logrocket.com/managing-search-parameters-next-js-nuqs/)
- **F1Studioz** — [Smart SaaS Dashboard Design Guide 2026](https://f1studioz.com/blog/smart-saas-dashboard-design/)
- **Lollypop Design** — [SaaS Navigation Menu Design 2025](https://lollypop.design/blog/2025/december/saas-navigation-menu-design/)

### Stack técnico (URL state + routing)

- **nuqs** — [nuqs.dev official docs](https://nuqs.dev/) · [InfoQ React Advanced 2025 nuqs](https://www.infoq.com/news/2025/12/nuqs-react-advanced/) · [GitHub 47ng/nuqs](https://github.com/47ng/nuqs)
- **Next.js App Router** — [Vercel Parallel Routes playground](https://app-router.vercel.app/parallel-routes) · [LogRocket Next.js advanced routing](https://blog.logrocket.com/exploring-advanced-next-js-routing-conventions/)
- **shadcn/ui Resizable** — [shadcn/ui Resizable docs](https://www.shadcn.io/ui/resizable) · [react-resizable-panels GitHub](https://github.com/bvaughn/react-resizable-panels)
- **LangChain Deep Agents UI** — [DeepWiki deep-agents-ui](https://deepwiki.com/langchain-ai/deep-agents-ui) · [LangChain assistant-ui blog](https://blog.langchain.com/assistant-ui) · [Agent Chat UI docs](https://docs.langchain.com/oss/python/langchain/ui)
- **CopilotKit Generative UI** — [CopilotKit homepage](https://www.copilotkit.ai/) · [CopilotKit GitHub generative-ui](https://github.com/CopilotKit/generative-ui)
- **Anthropic Claude Design** — [Anthropic Claude Design launch](https://www.anthropic.com/news/claude-design-anthropic-labs) · [VentureBeat Claude Design](https://venturebeat.com/technology/anthropic-just-launched-claude-design-an-ai-tool-that-turns-prompts-into-prototypes-and-challenges-figma)
