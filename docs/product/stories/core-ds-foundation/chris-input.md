# chris-input — core-ds-foundation

> Bitácora verbatim de decisiones con Chris. Cada entry: verdict (✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE).

## 💬 Conversación

### 2026-06-21 · arranque (origen D11 → inventory-first)

**Contexto:** /po-ux refinando el mockup de `vitalia-fase2-mateo-nueva-cita` (D11). El audit UI mostró que
el mockup mapea a componentes reales, pero que mantener "todo del shared / mínimo local" hoy NO es sostenible:
el inventario no tiene catálogo vivo y los mockups driftean por copia de `_shared.css`.

**Chris (decisión 1) · ✓ APLICADO** — "la idea es llegar a solo reutilizar y adaptar; lo local mínimo, todo del
shared … sin demasiados local que no nos dejen crecer / rompan la uniformidad. Inventario siempre al día."
→ Confirmado: la disciplina = reusar/consolidar + promover-al-2º-consumidor; el inventario necesita maquinaria.

**Chris (decisión 2 · sequencing) · ✓ APLICADO** — eligió **"Inventory-first (arreglar la maquinaria)"**:
catálogo generado + mockup-kit + drift-lint, antes de promover nada.

**Chris (decisión 3 · vehículo) · ✓ APLICADO** — eligió **"Scaffold full core-ds-foundation"**: la maquinaria
entra como Fase 0 del programa DS completo (no story dedicada ni harness-pass suelto). D11 parkea y resume después.

**/pm-luana · 💡 PROPONE (pendiente ratificación de Chris):**
- Scaffold escrito (este checkpoint). Scope = Fase 0 machinery → Fase 1 componentes (incl. deltas D11) → Fase 2 arch-test.
- Deltas D11 a promover: `SegmentedControl` (consolida `.toggle-pill`+`.segmented`), `EntityRow`/`EntityChip`,
  `PageHeader` back-slot · REUSAR Badge para avail/dur · `AvailabilityStrip` vitalia-shared (no core aún) · `ComputedField` flag.
- **Falta tu ✓:** ratificar el scope consolidado → habilita `/architect` (ready package, empezando por Fase 0).
- Handoffs que NO hago yo (anti-creep): /pm-vitalia parkea D11 + ownea AvailabilityStrip · /harness-issue captura el hallazgo de inventario.

### 2026-06-21 · ratificación de scope + visual-review gate

**Chris (decisión 4 · ratify scope) · ✓ APLICADO** — ratificó el scope consolidado **as-is** (Fase 0 machinery →
Fase 1 componentes incl. deltas D11 → Fase 2 arch-test) + el **per-component visual-review gate** (Batch 1→2→3).
→ checkpoint: `state refining→refined`, `phase=READY_FOR_ARCHITECT`, `per_component_visual_review_gate: true` +
§ Visual-review gate documentada (orden Batch 1 mockup-kit → Batch 2 layout-primitives review-only → Batch 3 deltas D11 uno-por-uno).

**Chris (decisión 5 · promote 558cd564) · ✓ APLICADO** — eligió **batchear** al cierre de sesión (no promote-now).
`558cd564` es pure platform/docs (cero `{brand}/**`) → se promueve con `make promote-to-main + sync-all` junto al
resto de commits platform/docs de esta sesión.

**/pm-luana · 💡 PROPONE (routing, anti-creep)** — el siguiente paso NO es `/po-ux` (esto es `type:
platform-engineering`, no UI story). Es **`/architect <brand>: platform`** → ready package empezando por **Fase 0**
(des-gated). /po-ux es el *estilo* de revisión (mockup-per-component), no el builder acá. Encadeno a `/architect`.

### 2026-06-22 · /architect (technical-story lane) — Fase 0 firmada + Batch 1 construido

**Chris (decisión 6 · approach Fase 0) · ✓ APLICADO** — firmó (single signature) el approach: mockup-kit = UN
`kit.css` brand-agnostic var()-based (base = nicolify 166-líneas) + `tokens.{brand}.css` GENERADO de globals.css
(R-FID, no copia). Catálogo = node script de index.ts. Drift-lint = eslint no-arbitrary + vitest arch-test.

**/architect · ✓ APLICADO (Batch 1 artifact)** — construido `docs/design-system/mockup-kit/` (`kit.css` +
`tokens.vitalia.css` + `preview.html` + `README.md`). 26/26 vars del kit resuelven.

**/architect · 💡 PROPONE (recon que achica el scope)** — Fase 1 está MÁS hecha de lo que decía el checkpoint:
Entity*/Picker/archetypes/layout/TogglePill/autosave YA exportan de `@luana/ui-kit/src/index.ts`; tokens-scale YA
existe (`@luana/design-tokens` 0.2.0). → Batch 2 = review-only confirmado. Fase 0 net-new real = catálogo +
mockup-kit + drift-lint (nada de "construir el lego").

**/architect · ⚠️ DUDA (flag del kit, para Chris)** — el kit hereda `.btn-primary{color:#fff}` de la base nicolify.
Con Mateo (amarillo) la acción primaria queda blanco-sobre-amarillo (bajo contraste). El canon §2.8 pide
texto-por-contraste (Mateo→oscuro). Fix = token `--agent-active-fg` en vez de `#fff` hardcodeado. Lo dejo anotado
para el ticket del kit (no lo resuelvo en el review del sustrato).

**AWAIT Chris:** revisar `preview.html` → aprobar el kit → produzco el reduced ready package (06-tickets + 04-validators) Fase 0.

### 2026-06-22 · Chris RECHAZA el mockup-kit CSS — pivote a componentes REALES

**Chris · ❌ REFUTADO (mockup-kit CSS)** — "no duplicar ni tener artefactos que son solo una foto del momento,
sino código real que sea reutilizado con clases y todo ya 'lista' para copiar y pegar por parte del agente y
ensamblar de forma coherente". Detectó que el `kit.css` re-crea (en CSS) el dropdown lista/detalle que ya existe
como componente real, y que NO renderiza los componentes que tenemos.

**/architect · ✓ APLICADO (auto-corrección)** — tiene razón. El `kit.css` es un espejo estático = duplicación =
"foto del momento" (lo que el canon §5/§6.8 quiere matar). Removí los 4 archivos. El error de mi parte: consolidé
el mirror en vez de eliminarlo. El objetivo real (que el canon ya fija) = **catalogar + renderizar los componentes
REALES de `@luana/ui-kit`**, no un look-alike CSS.

**/architect · 💡 PROPONE (Fase 0 correcta)** — dos piezas, ambas sobre lo REAL:
- **Catálogo generado del source REAL** (`@luana/ui-kit/src`): por componente → import real + props (de TS) +
  snippet de uso/composición "listo para copiar-pegar, con clases reales". Des-gated (lee source, emite md/json).
- **Showcase que renderiza los componentes REALES** (canon §5: route en app real / Storybook) — "lo que ves ES lo
  que es", cero drift. Mata los 9 `_shared.css` porque los mockups se componen de lo real (o el showcase ES el SSoT visual).
- **Falta tu decisión:** host del render vivo (route vs Storybook vs catálogo-solo-ahora · respeta el gate Fase 1).

**Chris (decisión 7 · render host) · ✓ APLICADO** — eligió **Storybook en `@luana/ui-kit`**. /architect cerró el
ready package Fase 0 reducido: `06-tickets.yaml` (T-1 catálogo · T-2 Storybook · T-3 drift-lint) + `04-validators.yaml`
(técnica). **Storybook = la superficie del per-component visual-review gate** (Batch 1→2→3 se revisan navegando
Storybook · cero CSS mirror). Catálogo = índice máquina (props viven en Storybook autodocs, no se duplican).
state=refined→ready. **AWAIT Chris:** ¿arranco /dev-team con T-2 (Storybook, lo que vas a VER) o querés revisar el
06-tickets primero?

### 2026-06-22 · T-2 batch-1 (lista/detalle) construido — Storybook UP para review

**Chris (decisión 8 · go) · ✓ APLICADO** — "go, arrancá con T-2 storybook" + 2 requisitos: (a) revisaré cada
componente hasta que esté bien (per-component review), (b) cada componente debe tener un "cuándo es mejor usarlo".
Ambos cableados en T-2 (review_protocol + sección "Cuándo usarlo" por story + validator sb_when_to_use).

**/dev-team (builder-frontend) · ✓ APLICADO** — Storybook 10 en `core/@luana/ui-kit` (framework `@storybook/nextjs`,
espejo del setup que ya funciona en vitalia) + 4 stories del grupo lista/detalle que **importan los componentes
REALES de `../src/`** (anti-mirror verificado) + autodocs (props reales) + "Cuándo usarlo"/"Cuándo NO" por story.
Commit `55fd599e` (13 files, platform-only → promote-candidate al cierre). Gates GREEN (build-storybook EXIT=0,
2 checks PASS, vitalia tsc regresión EXIT=0) — re-verificados por mí, no solo claim del builder.

**/dev-team · 💡 PROPONE** — Storybook UP en http://localhost:6007. **AWAIT Chris:** revisar los 4
(EntityWorkspaceLayout/EntitySubNavBar/EntityPicker/EntityInfoCard) uno por uno → flags/OK. Tras tu OK, el builder
sigue con el resto del set canónico (archetypes/layout-primitives/Select/Badge/Avatar/Group/autosave/TogglePill).

### 2026-06-22 · Chris: "docs vacío" — bug real, fixeado + verificado live por mí

**Chris · ❌ REFUTADO (docs vacío)** — "abrí el storybook y me sale docs vacío, entrá vos mismo y recorrelo y
verificá si es lo que me quieres mostrar realmente". Tenía razón: yo le pedí revisar sin haber MIRADO yo.

**/dev-team · ✓ APLICADO (entré con Chrome + diagnostiqué + fixeé)** — entré a Storybook con Chrome DevTools MCP:
el **canvas de cada story renderiza bien** el componente REAL, pero la **pestaña Docs (autodocs) salía en blanco**
para TODOS (props + "Cuándo usarlo" + código = invisibles). Causa: Storybook 10 ya NO bundlea el docs addon (era
parte de addon-essentials en SB8); el `main.ts` solo registraba `addon-a11y` → `autodocs: "tag"` rendea vacío
(uncaught promise). Fix: `pnpm add -D @storybook/addon-docs` + registrarlo en `addons`. **Re-verifiqué LIVE con
Chrome** (2 screenshots): Docs ahora rendea completo en EntityInfoCard (simple) y EntityWorkspaceLayout (router) —
"Cuándo usarlo"/"Cuándo NO" + componente real + tabla de props + Copy code + las stories. Commit `9f56820a`.

**/dev-team · 💡 PROPONE (gate gap — learning)** — el validator decía GREEN porque chequeaba `build-storybook
EXIT=0` + el string en el source, NUNCA que la página Docs RENDERIZARA. `build OK ≠ render OK` (mismo patrón que
"GET 200 ≠ verificado"). Para los próximos batches el gate debe verificar el render real (headless check del Docs).
Lo aplico cuando el builder continúe el set. **AWAIT Chris:** revisá los 4 en :6007 (ahora con Docs) → flags/OK.

### 2026-06-22 · Batch 2 (page/layout lego) + gate de render REAL + "seguí con todo"

**Chris (decisión 9) · ✓ APLICADO** — "seguí con el resto del set, absolutamente todo … OJO: cuando tengamos
todo hay que actualizar el harness para que po-ux y todo lo de diseño/UI sepa que hay Storybook; el Storybook (TSX)
debe poder tomarse como HTML para armar el mockup y partir de la misma base; el architect cita qué usar." →
Harness-update CAPTURADO (checkpoint § Harness update, DEFERIDO a cuando el set esté completo, va al CIL — regla
HLP no-mid-build). Cada componente lleva "Cuándo usarlo" (ya cableado).

**/dev-team (builder + yo verificando con Chrome) · ✓ APLICADO** — Batch 2 = 16 stories (layout-primitives +
4 archetypes + Group + autosave). **NO confié en el "GREEN" del builder — entré a Storybook con Chrome y cacé 2
bugs reales:** Docs en blanco (faltaba addon-docs, `9f56820a`) + ListPageScaffold "Con contenido" crasheaba
(`name=` en vez de `title=` → charAt undefined, `9127b111`). **Reescribí el render-gate**: el `_smoke` era
registration-check (index.json) + test-runner muere en SB10 → ahora `_smoke_storybook.mjs` carga cada story
headless en chromium (pageerror/React-error real). **69/69 rendean limpio.** Gate durable en 04-validators.

**/dev-team · 💡 PROPONE** — gate ya confiable → encadeno el próximo batch (átomos + overlays + nav, ~24
componentes) con el render-smoke OBLIGATORIO (el builder debe sacar 100% antes de cerrar). En paralelo podés
revisar los 20 ya hechos en Storybook :6007 (Docs ahora rendean). Quedan después: data/specialized/molecules/shell.

### 2026-06-22 · Batch 3 (átomos + overlays + nav, 24 stories) — verificado 136/136

**/dev-team (builder + yo) · ✓ APLICADO** — Batch 3: 13 átomos (button/input/textarea/label/select/checkbox/
switch/radio-group/badge/avatar/card/separator) + 8 overlays (dialog/popover/dropdown/tooltip/sheet/alert/
alert-dialog/command, todos con story ABIERTA para revisar) + 4 nav (tabs/accordion/collapsible/scroll-area).
Commit `b782905e`. **El render-gate OBLIGATORIO funcionó:** corrí yo mismo build+serve+smoke → **136/136 stories
render clean** (no solo el claim del builder) + Dialog-abierto verificado visual con Chrome. Cero bugs esta vez
(el gate confiable + el builder sabiéndolo de antemano). 44 componentes totales en Storybook (Batch 1+2+3).

**/dev-team · 💡 PROPONE** — **AWAIT Chris:** los 44 están en Storybook :6007 (Docs + Cuándo-usarlo). ¿Continúo
el batch FINAL (data/specialized/molecules: calendar/chart/table/slider/progress/sonner/currency-selector/
timezone-select/smart-datetime-picker/rich-select/form/CollapsibleSection/detail-panel/inline-editable/
loading-button/field-info/highlighted-text/brand-icons + el **shell organism** Ribbon/ShellLayout/etc. — más
complejo, quizá pase propia) o querés revisar los 44 primero?

### 2026-06-22 · Batch 4 (FINAL no-shell, 19 stories) — verificado 200/200 + chart fix + 1 src bug cazado

**/dev-team (builder sonnet + yo verificando con Chrome) · ✓ APLICADO** — escrito el batch FINAL no-shell (19
stories). **63 componentes totales en Storybook.** No confié en el GREEN del builder: corrí yo el render-smoke
(**200/200 render clean**) + spot-check con Chrome de los render-riesgosos (chart/table/calendar/sonner). El Chrome
cazó 2 cosas que el smoke NO ve (montar sin crashear ≠ rendear bien):
- **chart con barras NEGRAS** → `preview.css` no tenía `--chart-1..5` (la story está bien, usa `var(--chart-N)`
  como manda el canon). Lo arreglé en `.storybook/preview.css` (config, NO src). Re-verificado: barras cian+púrpura ✓.
- **calendar con días apretados** → **src bug Tailwind v4** (`h-[--cell-size]` sintaxis v3, rota en v4; afecta la
  app real). `forbidden_to_touch: src/**` → NO lo toqué, ticket aparte (checkpoint § Src bugs).

**/dev-team · 💡 PROPONE** — **AWAIT Chris:** revisá los 63 en Storybook :6007 (per-component). Después arranco el
**SHELL organism** como pase propio (createShellStore + decorator de store/routing — el más complejo). 3 src bugs de
`@luana/ui-kit` flaggeados (calendar v4 · timezone-select tsc · jest-dom tsconfig) → `/pm-luana` triage, ticket aparte.
¿Y los ~8 commits platform-only sin promover: `make promote-to-main + sync-all` ahora o batcheo al cierre?

### 2026-06-22 · SHELL organism increment 1 (3 átomos de chat) — UP para review

**/dev-team · ✓ APLICADO** — arranqué el shell por lo más barato y de-riskeante: los 3 **átomos de chat sin store**
(`MessageBubble`/`DelegateMarker`/`TypingIndicator`, 9 stories). Probé que el color-por-agente RESUELVE en contexto
shell antes de meterme con `ShellLayout` (incremental, no big-bang). Necesité 2 fixes de **config** (NO src): `@source
"../stories"` en preview.css (las clases `bg-agent-*` literales del fixture viven en stories/ → sin esto, gris/negro
como el chart) + keyframe `typing-dot` (mirror de globals.css). Verifiqué yo: render-smoke 209/209 + **Chrome de los 3
estados color** (púrpura/verde/naranja OK). Fixture reusable `stories/_shell-fixtures.tsx` (catálogo demo + switch
literal de clases).

**/dev-team · 💡 PROPONE** — **AWAIT Chris:** revisá los 3 átomos en :6007 (grupo **Shell/Chat**). Tras tu OK sigo con
increment 2 = **ChatPanel** + sub-tree (`ChatHeader`/`ChatMessages`/`ChatComposer`) — éstos SÍ necesitan un decorator
con store mock (`createShellStore` real + chat store mock zustand), por eso pasan aparte. ¿Promuevo los ~9 commits
platform-only a main ahora o batcheo al cierre?

### 2026-06-22 · Chris: "resolvé los 3 src bugs primero, cero bugs en el ui-kit" — RESUELTOS

**Chris (decisión 10) · ✓ APLICADO** — "primero revisá los 3 src bugs, no podemos tener bugs y menos en el luana ui
kit, resolvámoslo aquí, luego continuá con el increment 2". Levantó el `forbidden_to_touch: src/**` para estos bugs.

**/dev-team · ✓ APLICADO (verify-first, no confié en el checkpoint)** — corrí tsc/grep ground-truth antes de tocar:
(1) **calendar v4** `[--cell-size]`→`(--cell-size)` — y el **grep exhaustivo cazó el MISMO bug-class en 4 archivos más**
(popover/select/dropdown/chart, breakage sutil que el render-smoke no ve) → los arreglé todos (cero bare `[--var]` en
src); (2) **timezone** tsc → tsconfig lib/target ES2022; (3) **jest-dom** tsc → setup `/vitest` + `vitest.setup.ts` en
`include`. **Verificado:** tsc **0** · vitest **289/289** · render-smoke **209/209** · Chrome (calendar grilla correcta +
select sin regresión). Son fixes de correctitud (no API) → promueven con los commits DS, sin promotion proposal aparte.

**/dev-team · 💡 PROPONE** — bugs cerrados. Arranco **increment 2** (ChatPanel + sub-tree con store decorator) como
pediste. ¿Promuevo lo platform-only a main ahora o al cierre?

### 2026-06-22 · SHELL increment 2 (chat sub-tree completo) — UP para review

**/dev-team · ✓ APLICADO** — chat sub-tree entero: ChatHeader (agente/web/especialista) · ChatMessages (4-roles /
vacío) · ChatComposer (interactivo) · **ChatPanel** (composite con-conversación / vacío). 8 stories. Resolví el
decorator de stores en el fixture: shell store = el `createShellStore` REAL del kit; chat store = `createSsrSafePersistedStore`
seedeado in-memory (sin hydration → seed estable, cero localStorage — ideal para catálogo). Verifiqué: render-smoke
**217/217** + **Chrome** ChatPanel con-conversación (los 4 roles + color por agente: Valeria púrpura, Sofía verde) +
vacío (empty state). Spanish neutro.

**/dev-team · 💡 PROPONE** — **AWAIT Chris:** revisá el chat sub-tree en :6007 (grupo **Shell/Chat**). Tras tu OK,
increment 3 = **Ribbon/RibbonTab/SubTabsBar/SubSubTabsBar + Supervisor (Sidebar/CollapsedStrip/History) + TopBarShell/
StatusDot/TogglePill** (nav + chrome · menos store, más routing). El más complejo (`ShellLayout` con store+routing
decorator integrado) lo dejo de último (increment 4). ¿Promuevo lo platform-only a main ahora o al cierre?

### 2026-06-22 · Chris: "seguí con inc-3 y luego reviso todo yo" — inc-3 DONE

**Chris (decisión 11) · ✓ APLICADO** — "seguí con el increment 3 y luego hago el review yo mismo de todo".

**/dev-team · ✓ APLICADO** — inc-3 = 9 stories (Ribbon · SubTabsBar · SubSubTabsBar · SupervisorCollapsedStrip ·
SupervisorHistory · TopBarShell · StatusDot · TogglePill · PlaceholderCard). SupervisorSidebar + AppPanelSlot van en
inc-4 (ensamblaje, se ejercen vía ShellLayout). **El render-smoke cazó un bug real:** `react-docgen-typescript` estampa
`displayName`/`__docgenInfo` enumerables en los objetos exportados del fixture → SubTabsBar (que hace Object.entries)
crasheaba. Lo diagnostiqué con un probe en Chrome + lo arreglé (Record limpio desde el array de slugs). Verifiqué con
Chrome los 4 de riesgo (Ribbon color+activo · SubTabsBar · SubSubTabsBar · SupervisorHistory). render-smoke 235/235.

**/dev-team · 💡 PROPONE** — **AWAIT Chris (tu review completo):** revisá TODO en :6007 — grupos **Shell/Chat** (inc-1+2)
+ **Shell/** (Ribbon/SubTabsBar/SubSubTabsBar/SupervisorCollapsedStrip/SupervisorHistory/TopBarShell/StatusDot/
TogglePill/PlaceholderCard, inc-3). Tras tu OK armo inc-4 = **ShellLayout** completo (el composite con todo integrado) +
SupervisorSidebar (3 estados) + AppPanelSlot. ¿Promuevo lo platform-only a main ahora o al cierre?

### 2026-06-22 · SHELL increment 4 (ShellLayout + SupervisorSidebar + AppPanelSlot) — SET COMPLETO, UP para review

**Chris (decisión 12 · go inc-4) · ✓ APLICADO** — "Arrancá inc-4 ya" (sin esperar su review de 1+2+3).

**/dev-team · ✓ APLICADO** — cerré el shell con el ensamblaje final (autoreado por mí, integración intrincada). 3 stories,
12 estados: `ShellLayout` (Valeria-chat default · Lisa color+N3 · Diego color · cerrado tira-avatar · chat+historial) ·
`SupervisorSidebar` (A-tira / B-chat / C-historial / drawer-móvil) · `AppPanelSlot` (Valeria sin-N3 / Lisa con-N3 /
skeleton). **El render-gate cazó un bug real** (8/247 rojas): exportar el clean-subtabs como objeto desde el fixture lo
hacía estampar por react-docgen (mismo trap de inc-3) → lo convertí a función `buildCleanSubtabs()` (resultado a const
local no-exportado). Cosmético: `splitGroupId` propio por story (el ancho del split bleedeaba entre stories). **No confié
en el smoke — Chrome screenshot de cada estado** confirmó contenido real (composite entero · color por agente · N3 ·
tira-avatar · estado-C 3-columnas · drawer móvil 414px · AppPanelSlot N1+N2+N3). render-smoke **247/247** · tsc **0**.

**/dev-team · 💡 PROPONE** — **AWAIT Chris (review COMPLETO):** el set Storybook está **100%** en :6007 (todos los Shell/* +
los 63 no-shell). **Precondición del harness-update cumplida.** Tras tu OK: (1) capturo el harness-update al CIL vía
`/harness-issue` (po-ux/ux-agentico/architect parten de Storybook) · (2) T-1 catálogo + T-3 drift-lint · (3) promuevo lo
platform-only a main. ¿Promuevo ahora o al cierre? ¿Arranco T-1/T-3 o esperás tu review primero?

### 2026-06-22 · Chris: "pon los avatares reales + nombres reales de los módulos, lo más real a lo que tenemos"

**Chris (decisión 13) · ✓ APLICADO** — recorrer el shell y dejar el catálogo demo **idéntico a producción**.

**/dev-team · ✓ APLICADO** — reemplacé el fixture genérico (alfa/beta/Sofía/Diego, hues inventadas) por el catálogo
REAL de vitalia (espejo de `agent-catalog.ts` + `shell-routes.ts` + `globals.css` + avatares `public/agents/`):
6 agentes reales (Valeria supervisora + Lisa/Mateo/Adrián/Lucas/Camila) · nombres/roles/tabLabels/sub-tabs/N3 reales ·
avatares PNG reales (copiados a `stories/assets`, servidos vía `staticDirs /sb-assets`) · colores reales (preview.css
espejo de los tokens `--agent-*`, light+dark, contraste mateo/lucas → `text-foreground`). El kit sigue brand-agnostic
(RN-2): esto es DATA de demo en `stories/`, no `src/`. **★ Bug cazado entrando con Chrome (no por el smoke):** el chat
del supervisor salía "Lisa" porque `agentCatalog` era el array de ribbon (5, sin Valeria) y el lookup caía al primero →
fix `DEMO_AGENTS_ALL` (6, supervisora incluida; ribbon sigue 5, = producción). render-smoke **247/247** + tsc **0** +
Chrome de cada estado (Valeria supervisora correcta · color por agente real · N3 real). Commit pathspec.

**/dev-team · 💡 PROPONE** — Storybook dev de nuevo arriba en **:6007** con los avatares + nombres reales. Recorrelo y
tirame los comentarios. (Mismas decisiones pendientes: promote ahora/cierre · T-1/T-3 ahora o tras tu review.)

### 2026-06-25 · /pm-luana — reencuadre estructural: programa de FIDELIDAD de pipeline (mockup===resultado)

**Contexto:** Chris pidió cerrar el norte del DS multimarca + storybook y cementarlo en los harnesses. PASO 0 (leí
canon + ADR-014 + to-be) + Fase A (4 subagentes mapearon el scatter de doctrina DS por docs/rules/skills/agents).

**Hallazgo (verificado, no del to-be):** ~60% del to-be YA está en canon (ratif 2026-06-08) + harness-update
(aplicado 2026-06-22). El scatter REAL = (1) 5-capas + contratos + loop duplicados 3-4× en docs-arquitectura sin
cross-pointers · (2) **fork de autoridad 5-capas(canon) vs 3-buckets(to-be DRAFT)** · (3) catálogos brand
hand-narrados que driftean · (4) genesis-docs sin archivar. La cadena de enforcement (po-ux→architect→dev→auditor)
está SANA (pointer-chain intacto). Vitalia tiene 44 stories brand-local con duplicados reales (`ChannelBreakdownRow`
×2, `AttributionMatrixWidget` ×2, `LucasStageRecommendationsCard` ×2). nicolify storybook = 0. Colisión puerto :6006
(vitalia+nicolify). Promotion FE = de-facto (12 proposals `ui-kit-*`) pero sin doctrina escrita.

**Chris (input clave · ✓ APLICADO) — la necesidad real:** "el mockup que apruebo en refinamiento = el resultado
final EXACTO, garantizado end-to-end; el inventario debe ser la espina; cada token/átomo con paridad 1:1; el
architect debe saber CÓMO extender en detalle; el dev-team con lineamientos claros; reglas mapeadas a nivel UX de
cuándo reusar/extender/crear. Todo lego, no ladrillo con cemento (reemplazar uno sin destruir la pared)." Principios
HARD recurrentes: alta cohesión · bajo acoplamiento · DRY · clean architecture · hexagonal.

**Chris (decisión 14 · ratifica blueprint estructural) · ✓ APLICADO** — eligió **"Ratifico — arrancá Fase 1
(auditoría paridad)"**. Blueprint = inventario-como-espina (core hexagonal; actores = adapters que dependen del
inventario, no entre sí) + **4 pilares**: P1 inventario-1:1 (catálogo generado + gate de paridad) · P2 reglas
reuse/extend/create mapeadas a UX (vocabulario único, **cero bucket-1/2/3**; toolkit de extensión nombrado:
compound/slots · asChild/polymorphic-as · variant-props · render-props · wrappers) · P3 contrato de fidelidad por
actor (handoffs = juntas de lego; architect cita entrada exacta + patrón de extensión + ruta) · P4 garantía
mockup===resultado (mockup de Storybook → architect cita stories → dev ensambla las mismas → auditor diffea + gates
mecánicos).

**Chris (decisión 15 · alcance Fase C) · ✓ APLICADO** — eligió **"Full: incluir catálogo-generado ahora"** (el
recableo de doctrina + el catálogo generado en la misma tanda).

**/pm-luana (decisión propia · Q3 delegada) · ✓ APLICADO** — **ADR-016 nuevo** (gobernanza de inventario +
composición/extensión) + **recortar ADR-014** a solo-enforcement (apunta al canon para contratos). Justificado por
el principio de cohesión de Chris (concerns distintos = ADRs distintos).

**Estructura limpia ratificada (1 SSoT por concern · resto apunta):** inventario-generado (espina) · canon
(contratos QUÉ) · ADR-016 (PORQUÉ: reglas+toolkit) · frontend-visual-fidelity (QUIÉN enforza + contrato por actor) ·
promotion-protocol §FE (CÓMO promueve) · brand-docs + shell-paradigm compartido (BRAND-LOCAL; skills=routers).

**/pm-luana · 💡 PROPONE (en curso)** — **Fase 1 lanzada**: 4 subagentes read-only auditan paridad (kit inventory +
extensión · 44 vitalia → destino+acción · file-upload Abel/nicolify lift-candidate + mirror cross-brand · token dual
+ gate-parity HB-106/107). **AWAIT:** sintetizo la evidencia de paridad y te la paso antes de diseñar el spine (P1)
+ reglas (P2). Track aparte (no doctrina): gate-parity vitalia-only · promote-check sin gate · dual-token vitalia
(`--radius` 0.5 vs 0.625) = Fase 2/3 de core-ds-foundation.

**/pm-luana · ✓ APLICADO (Fase 1 — evidencia de paridad, 4 subagentes read-only):** Kit sano (156 exports · 83
stories · 92-98% paridad · **0 tier-3** = cero fork forzado · 4 tier-2 con techo: EntityInfoCard/Chart/RichSelect/
SmartDatetimePicker). **4 fuentes de drift mockup≠resultado:** (1) `@luana/design-tokens` = SOLO nombres para
color/typo/shadow → marcas inventan valores (driver #1; nicolify es el patrón bueno: importa vía `@theme`, vitalia
es dual-system) · (2) mirrors locales (vitalia 20 shadcn + EmptyState/Placeholder + 4 dead-stubs `ChannelBreakdownRow`/
`AttributionMatrix`/`LucasStageRec`/`Bowtie`; cross-brand 7 shell + `button` ~95% copiado) · (3) gates sin paridad
(no-div-layout solo vitalia · **comunify eslint no-arbitrary APAGADO** · HB-106) · (4) sin promote-gate (HB-107).
**Taxonomía VALIDADA:** `UniversalIntake` (nicolify Abel = el file-upload de Chris) = **EXTEND** vivo (lift+slot
`supportedModes`/`fileAccept` → vitalia extiende no forkea) · 20 shadcn+EmptyState/Placeholder = **REUSE** (kit ya
los tiene) · 4 stubs = **DELETE** · NPS/PHI/Deposit = **KEEP** · los 7 shell = adopción incompleta no lift.
**Lean /pm-luana:** design-tokens = SSoT de todos los ejes (valores color/typo/shadow incluidos), marcas migran al
`@theme` de nicolify. **AWAIT Chris:** greenlight Fase 2 (diseño del spine P1 + reglas P2 → draft ADR-016 +
catalog-spec + toolkit + contrato por actor) o ajustar el modelo con esta evidencia primero.

### 2026-06-25 · Fase 2 — draft ADR-016 + verificación adversarial + endurecimiento

**Chris (decisión 16 · evidencia) · ✓ APLICADO** — "revisá las evidencias y decidí si hay algo que actualizar; si
no, proseguí con Fase 2". Revisé: **el modelo aguanta, cero cambio estructural**; la evidencia enriquece 4 puntos
(spine + token-values · toolkit a los 4 tier-2 · adopción≠lift · 3 huecos de gate). Prosigo.

**/pm-luana · ✓ APLICADO (draft ADR-016)** — autoreado (diseño = síntesis, no descubrimiento paralelo):
`docs/architecture/luana-platform/ADR-016-design-system-inventory-governance.md` (status: proposed). Decide: ejes
ortogonales (5-capas ⊥ 3-destinos) · vocabulario único `DESTINO{kit/app-code/brand-local}` + `ACCIÓN{REUSE/EXTEND/
CREATE/ADAPT/KEEP/DELETE}` (retira bucket-1/2/3) · árbol reuse/extend/create · composición>config (fork-de-internal
= error, EXTEND vía slot = válido) · toolkit nombrado (compound/slots/asChild/variant/render-prop/wrapper) aplicado a
los 4 tier-2 · inventario-espina 1:1 generado con lifecycle · design-tokens = SSoT de todos los ejes · contrato de
fidelidad por actor · backstops mecánicos. ADR-016 apunta al canon (contratos) y recorta ADR-014 — cero body duplicado.

**/pm-luana · ✓ APLICADO (verificación adversarial + endurecimiento)** — spawné un revisor adversarial. Veredicto:
**"core idea SÓLIDA"** + 3 BLOCKER + 5 MAJOR + 4 MINOR de **operacionalización** (no de modelo). Trié (el auditor
sobreestima) + apliqué 8 fixes al draft: def. de `ADAPT` (vs KEEP) · mecanismo del 2º-consumidor (auditor cuenta
imports, promote-gate enforça) · copia≠EXTEND afilado · owner de promote (architect marca · builder ejecuta · auditor
verifica) · auditor = gate-verifier · extension-contract gate (tier-2 sin story-consumidora → CR) · honestidad de
timing (catálogo/gates = Fase C, interino canon+manual) + **§Caveat** · comunify-eslint = pre-req no quick-win.
Refuté 1 (MINOR /showcase: el cement 2026-06-22 ya fijó Storybook-only; el canon tiene ref stale → de-dup Fase C).

**/pm-luana · 💡 PROPONE** — **AWAIT Chris (ratificación):** ADR-016 endurecido listo. Es el draft que firmás antes de
que Fase C toque código/harness. **Caveat clave:** ratificar = ratificar el endpoint + el orden de Fase C; la garantía
mockup===resultado se completa recién al cerrar Fase C (los gates mecánicos son la última milla; el día que aceptás la
ADR el pipeline NO cambia, cambia a medida que Fase C aterriza cada gate).

### 2026-06-25 · Fase C · Tramo C1 — homes de doctrina (DONE)

**Chris (decisión 17 · ratifica ADR-016 + arranque) · ✓ APLICADO** — ratificó ADR-016 (→ status accepted) + eligió
arrancar Fase C por **C1** (homes de doctrina · docs-only · bajo riesgo).

**/pm-luana · ✓ APLICADO (C1)** — home-map cableado: ADR-016 referenciado por canon (×3, con "Mapa de homes") +
ADR-014 (complemento ortogonal: 014=enforcement, 016=gobernanza, contratos→canon) + frontend-visual-fidelity (×2,
SSoT-map + el contrato §5 que la rule enforça). 3 genesis-docs **archivados** con banner→ADR-016 (`to-be` DISUELTO ·
HANDOFF + inventory ARCHIVADOS · refs históricas redirigen sin romper). `bucket-1/2/3` = **0 vivo**. `/showcase` stale
dropeado del canon. **Verificado:** `machinery-check` **72/0/0 · sin drift**. Commits platform-only → batch al cierre.

**/pm-luana · 💡 PROPONE** — **AWAIT Chris (checkpoint entre tramos):** C1 cerrado. Próximo: **C2 spine** (`/architect`
actualiza el ready package de core-ds-foundation con scope ADR-016: catálogo generado + lifecycle + token-lift
color/typo/shadow + migración vitalia off-dual → `/dev-team`) **o** tu **review del set Storybook** (`:6007`, deuda
AWAIT_CHRIS_VERIFY) primero. C2 toca código → entra por la lane SDD (architect→dev), no por subagentes sueltos.

### 2026-06-25 · Fase C · Tramo C2 (spine) — approach firmado + ready package en producción

**Chris (decisión 18 · arranque C2) · ✓ APLICADO** — eligió **C2 spine**. /pm-luana encadenó a `/architect`
(technical-story lane · core-ds-foundation es platform-engineering).

**/architect · ✓ APLICADO (recon + approach)** — el spine es thin sobre lo existente: el kit ya corre
react-docgen-typescript + Storybook genera index.json → el catálogo se extrae de ESE pipeline (cero tooling nuevo);
design-tokens ya es modular (falta shadow.ts + valores en color/typo); nicolify ya consume vía @theme.

**Chris (decisión 19 · firma del approach C2) · ✓ APLICADO** — firmó con **B1 (full)**: el unwind del dual-system
de vitalia entra EN C2 (no incremental aparte). Scope C2 = (T1) catálogo generado + gate de paridad 1:1 · (T2)
design-tokens = SSoT de valores (shadow.ts + color/typo) · (T3) **migración vitalia off-dual** (riesgo visual →
funcional + live-verify) · (T4) superficies de extensión de los 4 tier-2 + story-consumidora c/u.

**/architect · 💡 PROPONE (en curso)** — spawné architect-orchestrator → ready package C2 sufijado `-C2` (no clobbea
Fase 0). DAG: T2→T3 · T1/T4 paralelos. T2 toca engine (design-tokens) — autorizado por ADR-016 (technical-story
core-targeting, no lift WT6). **AWAIT:** valido el package (CONN + verification + boundaries) → transiciono el
checkpoint → handoff `/dev-team`. NO incluí C3/C4/C5/C6 (tramos aparte).

**/architect · ✓ APLICADO (ready package C2 validado)** — architect-orchestrator escribió 03-arch-C2 + 04-validators-C2
+ 06-tickets-C2 + dispatch-plan-C2 (sufijo -C2, no clobbea Fase 0). Validé: CONN completo (las 4 contenciones por
ticket) · contract-spec por pieza · DAG coherente (T2→T3 duro · T1/T4 paralelos) · assignment por ticket
(builder-frontend/workhorse · no agentic) · engine-boundary T2/T4 autorizado por ADR-016. **★ Cazó la decisión
cardinal:** NO shippear CSS desde design-tokens (canon §6.8 lo descartó) — el package es TS-only SSoT de VALORES, las
marcas wirean vía @theme guardado por arch-test no-drift; **RN-5 (colores de agente per-brand) preservado** vía split
shared-value ⊥ brand-identity. T-3 (unwind vitalia · 105 defs/121 consumers) flaggeado funcional/ambas con
live-verify + el footgun @source JIT.

**/pm-luana · ✓ APLICADO (3 Open Questions confirmadas)** — (1) NO hornear hexes de agente cross-brand (RN-5; la
paleta semántica success/warning/danger SÍ puede ser shared-by-value) · (2) `@config` de vitalia = migración OPCIONAL
(canon §2.10 equivalente aceptado, gate=efecto) · (3) T-3 cierra con live-verify + demo Chris (G), no solo arch-test
verde. checkpoint actualizado (`c2_open_questions_confirmed`).

**/pm-luana · 💡 PROPONE** — **AWAIT Chris (checkpoint architect→dev):** C2 package listo + validado. Próximo:
arrancar `/dev-team` build (T1 catálogo + T4 tier-2 en paralelo · T2 design-tokens → T3 unwind vitalia secuencial ·
autonomous_mode:false → T-3 pausa en G para tu demo). O review del set Storybook primero. O pausa + batch commit.

### 2026-06-25 · C2-T1 — catálogo generado + gate paridad 1:1 (DONE)

**/dev-team (builder-frontend) · ✓ APLICADO (C2-T1)** — catálogo generado del source real en 4 piezas:
(1) `scripts/generate_ui_catalog.mjs` — cruza index.ts + storybook-static/index.json + react-docgen-typescript ref;
emite `catalog.json` (GITIGNORED, 54 módulos) + `catalog.md` (humano, 7 capas con links Storybook). RETIRING_NO_STORY
= `["AutosaveBadge"]` (exento per canon §2.6).
(2) `scripts/_check_catalog_parity.mjs` — gate de paridad CLI (`--mode=coverage` + default parity); exit 0/1.
(3) `scripts/_assert_parity_gate.mjs` — probe TDD (`--plant=export-without-story` + `--plant=retiring-no-story`).
(4) `core/@luana/ui-kit/tests/catalog-parity.test.ts` — vitest arch-test (RED→GREEN, 6 tests).
(5) `make ui-catalog` — Makefile target. `.gitignore` + `.gitignore` entries para catalog.json + catalog.md.
**4 validators PASS · 319/319 vitest GREEN · tsc 0 errores.**
Resultado: `docs/product/stories/core-ds-foundation/T-C2-T1-result.md`.

### 2026-06-25 · C2-T2 — SSoT de valores (shadow+color/typo/radius) @theme guardado (DONE)

**/dev-team (builder-frontend) · ✓ APLICADO (C2-T2)** — `@luana/design-tokens` 0.2.0 pasa de names-only a VALUES
en los 4 ejes pendientes:
(1) `shadow.ts` NEW — `SHADOW` elevation scale (none/sm/md/lg/xl) como valores CSS box-shadow cross-brand.
(2) `typography.ts` — ADD `TYPOGRAPHY_SCALE` (size/lineHeight/weight por tier display/heading/body/caption).
(3) `radius.ts` — ADD `RADIUS_SCALE` (sm/md/lg calc-based + control=md−2px per RN-7).
(4) `color-values.ts` NEW — `SEMANTIC_COLOR_DEFAULTS` (HSL channels success/warning/danger/info + foregrounds)
    + `AGENT_ACCENT_CONTRAST` (familias de contraste yellow-warm/dark-neutral per canon §2.8).
(5) `index.ts` + `package.json` — barrel exports shadow + color-values (exports map actualizado).
(6) `nicolify/frontend/src/app/globals.css` — @theme +shadow scale + semantic status color vars + :root HSL channels.
(7) Arch-test nicolify (`test-ds-single-token-source.test.ts`) — C2-T2 SHADOW equality (no-drift) +
    TYPOGRAPHY_SCALE/RADIUS_SCALE completeness + semantic colors (69/69 PASS, must_pass: true).
(8) Arch-test vitalia (`test-ds-tokens-lock.test.ts`) — C2-T2 SC-5 TS export structure checks (22/22 PASS;
    globals.css projection es T-3, no T-2).
(9) Guard scripts: `scripts/_assert_no_css_in_tokens_pkg.mjs` (canon §6.8 NO-CSS) +
    `scripts/_assert_token_value_renders.mjs` (renderable value check per token path).

Cardinal: NO CSS shippeado desde el package (canon §6.8); RN-5 preservado (hex agente per-brand, solo semántica shared).
**5 validators PASS · 31/31 scale tests + 69/69 nicolify + 22/22 vitalia GREEN · tsc 0 errores.**
Commit: `9ebbe8a7`. Resultado: `docs/product/stories/core-ds-foundation/T-C2-T2-result.md`.

### 2026-06-25 · C2-T4 — superficies de extensión 4 tier-2 + consumer stories (DONE)

**/dev-team (builder-frontend) · ✓ APLICADO (C2-T4)** — superficies de extensión NOMBRADAS y ADITIVAS para los 4 tier-2 (ADR-016 §3 toolkit composición>fork):

- `EntityInfoCard`: slot `footer?: React.ReactNode` — debajo del status chip; testid `entity-info-card-footer-{testId}`
- `ChartContainer`: slot `footer?: React.ReactNode` — debajo de `<ResponsiveContainer>`, atributo `data-chart-footer`; `useChart` ya estaba exportado (sin cambio)
- `RichSelect`: render-prop `renderItem?: (option: RichSelectOption) => React.ReactNode` — override del layout label+descripción por item; **+ fix**: eliminado `<FormControl>` interno que crasheaba fuera de un Form (patrón Shadcn correcto: el consumer wrappea; workaround ya documentado en ResumenView.tsx `ponytail:` comment)
- `SmartDateTimePicker`: slot `trigger?: React.ReactNode` — `PopoverTrigger asChild` + `React.isValidElement` check; cuando se omite, el `<Button>` default aparece

4 consumer stories ejerciendo cada slot (nuevos named exports en los `.stories.tsx` existentes):
  `ConSlotFooter` · `ConFooterCustom` · `ConRenderItem` · `ConTriggerCustom`

TDD: 6 tests RED→GREEN (`tier2-slots.test.tsx`). Gates:
- `tsc --noEmit`: **0 errores**
- `vitest run`: **313/313 PASS** (sin regresiones)
- `render-smoke` (build-storybook → serve → _smoke_storybook.mjs): **274/274 stories render clean**

Commit: `158c14d8`. Resultado: `docs/product/stories/core-ds-foundation/T-C2-T4-result.md`.

### 2026-06-25 · C2-T3 — unwind vitalia dual-system → @theme design-tokens (DONE, tests passing)

**/dev-team (builder-frontend) · ✓ APLICADO (C2-T3)** — migración `@theme` + alias-then-migrate en
`vitalia/frontend/src/app/globals.css`. Ponytail mode: shortest diff que pasa los arch-tests:

- `@theme` block agregado (después de `@source`): proyecta SHADOW scale (5 tokens) + TYPOGRAPHY_SCALE tiers
  (4 tokens) + semantic status colors vía `hsl(var(--status))` (para que el dark `:root` override propague)
- `--danger` e `--info` canónicos declarados en `:root` (brand vitalia clínica: `0 73% 50%` / `199 89% 48%`)
  + dark overrides en `.dark, [data-theme="dark"]`
- Aliases RN-5: `--vitalia-success/warning/danger/info` → `var(--canonical)` (no HSL crudo duplicado)
- `--radius-lg` derivado: `0.875rem` literal → `calc(var(--radius) + 4px)` (RADIUS_SCALE.lg; mismo valor numérico)

**Decisiones de ponytail (qué NO se hizo y por qué):**
- `@config` NO migrado (dark wiring ya funciona vía tailwind.config.ts · migración OPCIONAL per arch §9.Q2)
- RADIUS_SCALE NO en `@theme` (evita conflicto con `tailwind.config.ts::borderRadius` que cambiaría `rounded-lg`)
- Hexes de agente NO en `@theme` (RN-5: identidad per-brand, solo semántica shared se proyecta)

**TDD RED→GREEN:** 16 tests nuevos en `test-ds-tokens-lock.test.ts` — gate de @theme (presencia · @source
footgun · dark wiring · shadow no-drift × 5 · typography tiers × 4) + aliases vitalia (×4) + canonical
--danger/--info (×2). Total **41/41 PASS** (25 T-2 + 16 T-3). Validators:
`c2_vitalia_tokens_lock` 43/43 · `c2_vitalia_legacy_unwound` 6/6 · `c2_vitalia_tsc_green` PASS.

**Pendiente:** `c2_vitalia_visual_parity` = `type: live-verify` — Chris lo corre en G phase (Chrome MCP,
`demo-script.md`). NO marcado `dod_live_verified: true` por builder.

Resultado: `docs/product/stories/core-ds-foundation/T-C2-T3-result.md` · `demo-script.md`.

### 2026-06-25 · Review Storybook · comentario #1 — gap selección de hora/rango horario

**Chris (review #1) · ✓ APLICADO** — "tengo calendar pero ningún componente para selección de hora y/o
rango horario". Verifiqué el inventario: **hora sola YA existía** (`SmartDateTimePicker` + `Input type=time`),
**rango de fechas YA existía** (`Calendar mode=range`), **slots/disponibilidad YA existía brand-local** en
vitalia (`DayAvailabilityStrip`/`AvailabilityChip`, D11 · `ADAPT`/vitalia-shared, owner /pm-vitalia, sin 2º
consumer refined/ready → no se promueve aún). El gap REAL = **rango horario inicio–fin**, no existía.

**Chris (decisión) · ✓ APLICADO** — eligió **TimeRangePicker (inicio–fin)** como `CREATE` genérico de kit
(vs TimePicker dedicado / promover slots / solo-visibilidad).

**/pm-luana (build directo · loop de review) · ✓ APLICADO** — `core/@luana/ui-kit/src/TimeRangePicker.tsx`:
compone **dos `Input type=time`** (mismo átomo que SmartDateTimePicker, NO reinventa dropdown de slots) +
separador "a" + validación inicio<fin (`aria-invalid` + mensaje `role=alert` en `text-destructive`). Props
`{value, onChange, stepMinutes, startLabel, endLabel, separator, disabled, errorMessage}`. Story
`Molecules/TimeRangePicker` (4 estados: default/con-valores/inválido/deshabilitado) + "Cuándo usarlo/NO".
**Gates:** tsc 0 · render-smoke 4/4 clean · **Chrome verify** (con-valores `09:00→18:00` ✓ · inválido con
error rojo ✓). Compone primitivas per ADR-016 §3 (composición>fork). Commit `303ed411` (3 files, platform-only
→ promote-candidate al cierre) · push wip/vitalia.

**/pm-luana · 💡 PROPONE** — gap cerrado. `:6007 → Molecules/TimeRangePicker`. Tirame el próximo comentario.
(Pendientes del cierre sin tocar: promote-to-main de los commits platform-only · tu firma G de C2-T3.)

### 2026-06-25 · Review #1 (cont.) — "no me gustó del todo, buscá en shadcn / cómo lo hacen mejor"

**Chris · ⚠️ DUDA (el nativo no convence)** — pidió buscar en shadcn si hay un componente mejor (que sirva
para una hora Y rango, o si sí o sí dos componentes), sin reemplazar a lo loco si no hay algo mejor, y revisar
cómo lo hacen más intuitivo/usable otros en internet.

**/pm-luana · ✓ APLICADO (investigación)** — WebSearch/WebFetch: **shadcn core NO tiene time picker oficial**
(los docs usan `<input type=time>` nativo = exactamente lo que teníamos → no hay "mejor" listo para adoptar
tal cual). El punto débil del nuestro = el **chrome del browser** del nativo (inconsistente). Lo mejor del
ecosistema = **input segmentado** (OpenStatus TimePicker MIT · huybuidac DateTimeInput): campo `HH:MM`
tokenizado, ↑↓ por segmento, cero widget del browser. UX (Eleken): rango = híbrido (2 campos + validación +
**presets** + defaults). **Una o dos componentes:** dos, por composición (lego ADR-016) — átomo single + range
compone dos. Fuentes: time.openstatus.dev · github huybuidac/shadcn-datetime-picker · eleken.co/blog-posts/time-picker-ux.

**Chris (decisión) · ✓ APLICADO** — eligió **"subir lo nuestro a segmentado + presets"** (vs adoptar lib
externa / dejar el nativo).

**/pm-luana · ✓ APLICADO (build)** — **átomo `TimePicker`** segmentado tokenizado (HH:mm 24h, ↑↓/←→/auto-avance/
blur-pad, buffer de display por segmento) + **`TimeRangePicker` reescrito** componiendo dos `TimePicker` +
**presets** (Mañana 09–13 / Tarde 14–18 / Todo el día, overridables vía `presets`, `[]` los oculta) + validación.
**★ 3 bugs reales cazados por la verificación LIVE en Chrome (no por el render-smoke ni tsc — verification-real≠render):**
(1) buffer parcial: emitir "" en estado a-medio-escribir wipeaba la hora en el parent controlado → estado interno
de segmentos + sync solo de valores completos; (2) padding-en-vivo bloqueaba el 2º dígito (`"3"→"03"`, maxLength
trababa el "0") → mostrar crudo mientras se escribe, padear on-blur; (3) el auto-avance dispara blur síncrono con
closure stale (`"0"` pre-`"9"`) → padeaba `"00"` pisando `"09"` → blur lee `e.target.value` del DOM, no el closure.
3 tests de regresión + verificación live de cada uno (typing `0930`→`09:30` · ↑ step 5 · preset puebla + chip activo).
**Gates:** tsc 0 · vitest 5/5 (TimePicker) + 6/6 (catalog-parity, catálogo regen 54→56) · render-smoke 8/8 · Chrome.
Commit pathspec platform-only → promote-candidate. Stories `Molecules/TimePicker` (3) + `Molecules/TimeRangePicker` (5).

**/pm-luana · 💡 PROPONE** — `:6007 → Molecules/TimePicker` + `Molecules/TimeRangePicker`. Próximo comentario.

### 2026-06-25 · Storybook — target `make storybook`

**Chris · ✓ APLICADO** — pidió levantar el Storybook + un comando `make` para hacerlo él. Agregué target
**`make storybook`** al Makefile raíz → `corepack pnpm --filter @luana/ui-kit storybook` (`:6007`). Usa
`corepack pnpm` (no el shim de PATH) porque el subshell de `make` puede no tener `pnpm` en PATH (cazado: el
target con `pnpm` pelado falló `Error 127` en spawn no-interactivo; corepack ships con node, resuelve el pin
9.15.9 siempre). Storybook levantado y verificado UP (200). Commit platform-only.

### 2026-06-25 · Review #1 (cont.) — TimePicker híbrido: dropdown click + teclado

**Chris · ✓ APLICADO** — pidió que el `TimePicker` despliegue un **dropdown** al click (columna Hora + columna
Min con 0/10/20/30/40/50) para que la secretaria no suelte el mouse al pasar de fecha a hora, **sin perder el
teclado** (igual puede tipear, ej. un minuto fuera de lista como 31).

**/pm-luana · ✓ APLICADO** — `TimePicker` ahora es **híbrido**: chevron `▾` (PopoverTrigger) → Popover con dos
`TimeColumn` scrollables — Hora (00–23, scroll-to-active) + Min (`minuteOptions`, default `[0,10,20,30,40,50]`,
overridable). Click setea el segmento + resalta el activo (cian). Los **segmentos siguen tipeables** (auto-avance,
↑↓, y cualquier minuto como 31). Compone `Popover` + `ScrollArea` del kit (no reinventa · ADR-016). `min-w-14`
(no arbitrary). `TimeRangePicker` hereda el dropdown en sus dos `TimePicker` sin cambios. **Verificado LIVE Chrome:**
abrir dropdown (14:30 → Hora 14 + Min 30 activos, scrolled) · pick Hora 16 + Min 00 → `16:00` · tipear `31` en
minuto → `16:31` (fuera de lista, por teclado). **Gates:** tsc 0 · vitest 5/5 · render-smoke 8/8. Commit platform-only.

### 2026-06-25 · Review #1 (cont.) — Calendar/fechas en español (Perú)

**Chris · ✓ APLICADO** — "el calendar y todo en sí debe estar en español, estamos en Perú". El `Calendar`
(react-day-picker) caía a **inglés** sin `locale` (meses/días) — bug ya flageado en bitácora.

**/pm-luana · ✓ APLICADO** — `Calendar` del kit ahora **default `locale={es}`** (`date-fns/locale`),
override-able por consumer. Decisión: español es default de **plataforma** (las 10 marcas son LatAm Sp), no
brand-specific → vive en el kit (RN-2 no se viola; una marca no-española overridearía el prop). También el
`formatMonthDropdown` respeta el `locale?.code` (antes hardcodeaba `"default"`). `SmartDateTimePicker` ya pasaba
`es` (redundante ahora, inofensivo). **Verificado LIVE Chrome:** Calendar → "junio 2026" + `lu ma mi ju vi sá do`
(lunes primero, correcto Perú) · SmartDateTimePicker popover → idem español + formato `22/06/2026`. **Gates:**
tsc 0 · render-smoke 16/16 (calendar + smart-datetime + time pickers). Commit platform-only.

> Nota: el `<input type=time>` interno de `SmartDateTimePicker` sigue siendo nativo (chrome del browser, "a.m./p.m.")
> — fuera de scope de este comentario (Chris cuestionó el nativo solo en el `TimePicker` standalone, ya resuelto).

### 2026-06-25 · Review #1 (cont.) — SmartDateTimePicker usa el TimePicker segmentado (mata el último nativo)

**Chris · ✓ APLICADO** — "sí, hazlo" (que el `SmartDateTimePicker` use el `TimePicker` nuevo adentro en vez del
`<input type=time>` nativo).

**/pm-luana · ✓ APLICADO** — reemplacé el `<Input type="time">` + `Clock` del popover por `<TimePicker>`
(segmentado + dropdown). `handleTimeChange` ahora recibe el string `"HH:mm"` directo (antes el event) + guarda
`if (date && newTime)` (TimePicker emite `""` en parcial). Imports `Input`/`Clock` removidos. **★ Footgun
verificado LIVE (Popover anidado):** el dropdown del `TimePicker` es un Popover dentro del Popover del
`SmartDateTimePicker` — Radix maneja layers anidadas: al abrir el dropdown interno el outer **NO se cierra**
(ambos `dialog` coexisten), y pick Hora 15 → trigger `22/06/2026 15:00` + ISO UTC `18:00Z` (conversión tz
correcta). Cero `<input type=time>` nativo en el kit. **Gates:** tsc 0 · vitest 11/11 (tier2-slots SmartDateTimePicker
+ TimePicker) · render-smoke 12/12. Commit platform-only.

> Gap menor pendiente (SR-only, NO visible): los aria-labels de nav del calendar siguen en inglés
> ("Go to the Next Month", "Today") — react-day-picker no los traduce con `locale`, necesitan el prop `labels`.
> El texto VISIBLE del calendar está 100% en español. Follow-up opcional si importa el screen-reader en español.

### 2026-06-25 · Review #1 (cont.) — FloatingAutosaveIndicator pertenece a la HOJA (no a la página)

**Chris · ✓ APLICADO** (confirmó entendimiento antes de construir) — el indicador debe estar **siempre pegado
al borde inferior de la HOJA**, jamás a toda la página/viewport — le pertenece a la hoja. **Tag/escape hatch**
para el caso excepcional no-mapeado → página.

**/pm-luana · ✓ APLICADO** — prop **`anchor: "sheet" | "page"`** (default `"sheet"`):
- `"sheet"` (principal) → `absolute inset-x-0 bottom-4` al marco `relative` de la HOJA (`AppPanelSlot` ya es
  `relative`), centrado en el ancho de la hoja, **siempre pegado abajo** (contenido corto o largo). Reemplaza el
  `sticky bottom-4` viejo (que con contenido corto flotaba a media hoja, no pegado al fondo).
- `"page"` (escape hatch) → `fixed inset-x-0 bottom-4` al viewport, SOLO para el caso excepcional sin hoja.

Contrato de placement: hermano del scroll, dentro del marco `relative` de la hoja (NO dentro del `overflow-y-auto`).
Wording corregido **página→HOJA** en: doc del componente + displayName + canon §2.6 + `frontend-visual-fidelity.md`.
**★ Verificado LIVE Chrome (3 casos):** hoja largo → pegado al fondo del marco, centrado en la hoja (no la página) ·
hoja corto → **igual pegado al fondo** (el caso que el sticky fallaba) · `anchor=page` → fixed al viewport, ignora el
marco. **Gates:** tsc 0 · vitest 16/16 (+2 tests anchor sheet/page) · render-smoke 7/7. Stories: 5 estados + contenido-corto
+ anchor-page, cada uno en un marco-hoja `relative` (sin meta-decorator: render propio, evita el doble-wrap de decorators).
Commit platform-only (kit + canon + rule).

### 2026-06-26 · Promotion gate — `UniversalIntake` (nicolify) → `DataIntake` en `@luana/ui-kit`

**Chris · 💡 PROPONE** — promover el componente de ingesta (URL/archivo/texto/conectar, hoy en el ICP de Abel)
al kit como **el mecanismo de ingesta de datos de la plataforma**, igual en todas las marcas. Ubicación +
análisis genérico-vs-acoplado + API `DataIntake`/`IntakeSeed` provistos. Pedido: ratificar la API → escribir
el proposal formal → lift.

**/pm-luana · ✓ APLICADO** — leí los 4 archivos de ubicación (`UniversalIntake` + `IcpIntakeOverlay` +
`use-icp-extract` + `extract.ts`) + ADR-016. La API **cierra**. Escribí el proposal formal
`docs/promotion-protocol/proposals/2026-06-26-ui-kit-data-intake.md` (state `proposed`, recomendación **APPROVED**).
Acción ADR-016 = `CREATE`/`kit` (lift de código genérico, ≥3 consumidores hoy + mitad-BE ya en
`core/luana-core-extraction`). **3 ajustes a la API (operacionalización, no objeciones):**
(1) `maxSizeMB` es **net-new behavior** — el origin muestra "10 MB" como copy pero no valida nada → el lift agrega
el chequeo real + error state + test; (2) `accentSlug` **no puede** ser `bg-agent-${slug}` (Tailwind JIT lo purga ·
G3) → resuelve a CSS var `--intake-accent` = `var(--agent-${slug})`, default `--primary`; (3) `IntakeSeed.file`
rico (`{name,base64,size,mimeType}`) — mejor que el `fileContent/fileName` flat del origin, habilita el size-check.

> Reconcile: ui-kit committed = **0.9.0** (el datepicker `showTime` ya está `migrated`; el "0.7→0.8 in-flight" del
> mandato quedó stale). Target bump del lift = `0.9.0 → 0.10.0` (reconcile contra current al ejecutar).

**Próximo paso:** Chris ratifica la API + el proposal (APPROVED → state `accepted`) → recién ahí el lift
(`/dev-team` o inline): build `DataIntake` + story + verify LIVE Chrome + refactor nicolify a wrapper fino.
NO encadeno a `/dev-team` ahora — el lift necesita tu APPROVED primero.
