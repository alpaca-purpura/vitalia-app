# ADR-016 — Gobernanza de inventario del design system (fidelidad mockup===resultado por inventario-espina)

**Status:** accepted (ratificado por Chris 2026-06-25) · **Date:** 2026-06-25 · **Decider:** Chris · **Scope:** platform-wide (cross-brand · design system) · **Owner:** `/pm-vitalia`

> **Ratificado por Chris (2026-06-25)** tras verificación adversarial (8 fixes de operacionalización aplicados). Producido en Fase 2 del programa DS sobre la evidencia dura de la auditoría de paridad (Fase 1). Dispara **Fase C** (plan de tramos en `core-ds-foundation/checkpoint.md` · ver § Programa + § Caveat para el orden y la última-milla de gates).

> **Relación con lo que YA existe (no duplica — completa):**
> - **ADR-014** = *enforcement de homologación* (las 5 capas + por qué el enforcement es mecánico, no por criterio). ADR-016 NO re-tabla las 5 capas ni los contratos.
> - **design-system-canon.md** = los *contratos concretos* de cada componente (QUÉ hace cada pieza). ADR-016 apunta al canon para el QUÉ, **nunca lo re-escribe**.
> - **storybook-component-inventory-to-be.md** (DRAFT) = el origen de esta doctrina. Al ratificarse ADR-016, el to-be **se disuelve** (su contenido vivo queda acá + en el canon; el archivo se archiva).
> - Hermana de **ADR-012** (autosave primitive) y **ADR-014**: mismo principio — un patrón de UI se eleva a contrato compartido **con enforcement mecánico**, no a guía opcional.

## Contexto

**La necesidad (Chris, 2026-06-25):** *"el mockup que apruebo en refinamiento = el resultado final que veo, EXACTO, garantizado end-to-end. El inventario debe ser la espina. Cada token/átomo con paridad 1:1. El architect debe saber CÓMO extender en detalle. El dev-team con lineamientos claros. Reglas mapeadas a nivel UX de cuándo reusar/extender/crear. Todo lego, no ladrillo con cemento."* Principios HARD recurrentes: **alta cohesión · bajo acoplamiento · DRY · clean architecture · arquitectura hexagonal**.

ADR-014 resolvió que el drift se mata con enforcement mecánico. Esta ADR resuelve una pregunta distinta: **cómo se gobierna el inventario para que el mockto que el cliente aprueba sea, por construcción, el resultado que se construye** — y cómo se decide, en cada handoff, si una pieza se reúsa / extiende / crea, sin reinventar ni forkear.

**Diagnóstico (grounded — auditoría de paridad Fase 1, 4 subagentes read-only):**

| Señal | Evidencia | Concern |
|---|---|---|
| **Kit sano + composable** | 156 exports · 83 stories · 92-98% paridad story↔export · **0 componentes tier-3** (cero fork forzado) · 4 tier-2 con techo de extensión (`EntityInfoCard`/`Chart`/`RichSelect`/`SmartDatetimePicker`) | la espina existe y es buena base |
| **Tokens names-only = driver #1 de drift** | `@luana/design-tokens` congela SPACING + Z-index, pero **color/typo/shadow son SOLO nombres, sin valores** → cada marca define los valores en su `globals.css` → mismo componente, look distinto. **nicolify ya importa vía `@theme` (patrón correcto); vitalia es dual-system** (`--radius` 0.5 legacy vs 0.625 shadcn) | tokens deben ser SSoT de TODOS los ejes |
| **Mirrors locales** | vitalia: 20 copias locales de shadcn en `components/ui/` + `EmptyState`/`PlaceholderCard` (el kit YA los tiene) + **4 dead-stubs duplicados** (`ChannelBreakdownRow`/`AttributionMatrixWidget`/`LucasStageRecommendationsCard`/`MarketingBowtieSVG`: stub en `shared/` + prod en `features/`). Cross-brand: **7 componentes shell** (`ThemeToggle`/`LogoMark`/`TenantSwitcher`/`SubTabContent`/`TenantBadge`/`TenantOption`) + `button.tsx` ~95% copiados | el fix del kit no llega a la copia |
| **Gates sin paridad cross-brand** | `no-arbitrary` eslint: vitalia ✓ · nicolify ✓ · **comunify APAGADO** · lupulo n/a. `test-no-div-layout`/`no-native-select`: **solo vitalia**. arch-tests: vitalia 33 · nicolify 9 · comunify 3 · lupulo 0 | el drift no se detecta donde el gate no existe |
| **Sin promote-gate** | cero detección mecánica de "componente shared quedó local sin promover" — solo prosa (HB-107) | mirrors nuevos se forman libres |

**La verdad incómoda:** el catálogo del inventario está **hand-narrado** (el skill `vitalia-design-system` afirma "19 átomos / Z_INDEX only"; el real es 23 primitivas / 5 ejes de token) → driftea respecto al código. Sin un inventario **generado del source, con paridad 1:1**, ni el architect ni el dev pueden planear/construir con certeza de fidelidad. **El inventario tiene que dejar de ser un documento y volverse la espina ejecutable.**

## Decisión

Gobernar el design system como un **inventario-espina con paridad 1:1 + reglas de reuso/extensión/creación mapeadas a UX + un contrato de fidelidad por actor**, todo bajo arquitectura hexagonal: **el inventario es el core; los actores (po-ux/architect/dev/auditor) son adapters que dependen del inventario, no entre sí.** El objetivo medible: **el mockup ratificado === el resultado construido.**

### 1 · Dos ejes ortogonales (disuelve el fork 5-capas vs 3-buckets)

Las 5 capas (ADR-014) y los "buckets" del to-be NO compiten — son **perpendiculares**:

- **Eje ESTRUCTURAL (5 capas):** *de qué está hecha* una UI — tokens → átomos → layout-primitives → page-archetypes → shell. (SSoT: ADR-014 + canon §0.)
- **Eje de GOBERNANZA (3 destinos):** *dónde vive* cada pieza — `kit` (compartido) / `app-code` (arreglo de un uso) / `brand-local` (dominio de marca). (SSoT: esta ADR.)

Un átomo (capa 2) puede ser destino `kit` o, si encoda dominio, `brand-local`. Un layout (capa 3) casi siempre `kit`. Un form de 5 campos no es ninguna capa nombrada → `app-code`.

**Se retira la jerga `bucket-1/2/3`** (era un 4º vocabulario que aumentaba el scatter). Vocabulario único y final:

- **DESTINO** (dónde vive): `kit` · `app-code` · `brand-local`
- **ACCIÓN** (qué se hace con una pieza):
  - `REUSE` — consumir el componente del kit tal cual (si hay copia local → `DELETE` la copia + importar).
  - `EXTEND` — componer/envolver una primitiva del kit con un patrón nombrado (§3) + un agregado acotado. **Importa la primitiva, no la copia.** Nunca forkea.
  - `CREATE` — construir una pieza genérica **nueva** en el kit (+ story).
  - `ADAPT` — pieza con UN solo consumidor hoy, genérica-por-naturaleza: queda brand-local **marcada como promotion-candidate**, y se promueve (→`CREATE` en el kit) al aparecer el 2º consumidor. **≠ `KEEP`:** `KEEP` nunca sube; `ADAPT` está en cola de lift.
  - `KEEP` — dominio de marca (PHI/NPS/clínica): vive brand-local permanente, no es candidato a kit.
  - `DELETE` — mirror / dead-stub: se borra (el kit o la versión prod ya lo cubre).

> **Alcance del vocabulario:** el canon conserva la cadena de 5 capas (§0) — esta gobernanza es la capa **ortogonal** aplicada a cada capa. `DESTINO`/`ACCIÓN` reemplaza `bucket-1/2/3` en TODA doc/skill/rule **nueva**; una doc vieja que aún diga "bucket" es deuda que apunta acá, no una inconsistencia de modelo.

### 2 · El árbol de decisión reuse/extend/create (mapeado a UX · aplicado por actor)

Dada una necesidad de UI:

```
¿El inventario ya la satisface tal cual?
├─ SÍ → REUSE (consumir del kit; si hay copia local = DELETE la copia + import)
└─ NO → ¿La satisface CASI, con un agregado acotado?
        ├─ SÍ → EXTEND (componer con un patrón nombrado — §3; NUNCA forkear)
        └─ NO → ¿Es genérica (otra marca la reusaría) o un arreglo de un solo uso?
                ├─ genérica → CREATE en el kit (+ story) · si nace en 1 marca con 2º
                │             consumidor nombrado → lift; si no, brand-local hasta el 2º (ADAPT)
                └─ arreglo de 1 uso → app-code (NO es un componente; ej. form de 5 campos)
        Si encoda dominio de marca (PHI/NPS/clínica) → KEEP brand-local.
```

**Umbral = por NATURALEZA primero, conteo de desempate.** Genérico-por-naturaleza → kit (construido extensible desde el 1er uso). Incierto → brand-local (`ADAPT`) hasta el **2º consumidor nombrado**. No hay número mágico.

**Detección del 2º consumidor (quién/cuándo/cómo):** el **`/auditor`** en cada PR cuenta los consumers reales de una pieza `ADAPT` (`git grep` de su import a través de rutas/marcas); **≥2 rutas/marcas distintas → flag de promoción** → debe lift al kit en ESE PR o el siguiente (lo enforça el **promote-gate §6**). "Nombrado" = el 2º consumidor existe **en código o en una story refined/ready**, no una intención vaga.

**Adopción ≠ lift** (distinción que la evidencia exige): *adopción* = REUSE un componente que el kit YA tiene + borrar el mirror local (el grueso del trabajo cross-brand: 20 shadcn de vitalia, 7 shell, etc. → las stories `{brand}-ds-adoption`). *lift* = CREATE/promover algo genérico nuevo al kit (ej. `UniversalIntake`).

### 3 · Composición sobre configuración — y el toolkit de extensión NOMBRADO

Orden de preferencia (best-practice "configuration collapse"):

1. **Composición ✅ (default).** Primitivas chicas + compound components que la marca ARMA por slots.
2. **Configuración (con cuidado).** Props/variants para variación acotada y conocida. >1 dimensión de variación → mover a composición.
3. **Fork del INTERNO = ERROR.** El kit es **paquete compartido por import** (ADR-014 rechazó per-brand). Duplicar los internals de un componente para tocarle 2 cosas garantiza drift. **Distinción clave:** `EXTEND` (importar la primitiva del kit + envolverla/slottearla) **NO es copia** — es composición, y es la acción válida. Lo prohibido es copiar el `.tsx` del componente y editar adentro. Construir una primitiva chica **nueva desde cero** (no copiando otra) = `CREATE`, válido, se registra en el inventario + intenta lift al 2º consumidor.

**Toolkit de extensión (el contrato que hace "extender no duplicar" enforceable):**

| Patrón | Cuándo | Ejemplo |
|---|---|---|
| **Compound components** (`<X.Sub>`) | la marca recompone sub-partes | `<Card><Card.Header/></Card>` |
| **Slots / `children`** | inyectar contenido de marca | `UniversalIntake` expone slot → vitalia agrega su modo |
| **`asChild` / polymorphic `as`** | cambiar el elemento renderizado sin forkear | Radix pattern |
| **Variant props (cva)** | variación acotada y conocida | `<Button variant=…>` |
| **Render-props / children-as-function** | inyectar lógica/render de marca | el techo de los tier-2 |
| **Wrapper de composición** | la marca envuelve la primitiva agregando su bit | brand wrappea, no forkea |

**Aplicación inmediata a los 4 tier-2** (los únicos que hoy forzarían un fork): `EntityInfoCard` (grid fijo), `Chart` (wrapper recharts), `RichSelect` (no windowed), `SmartDatetimePicker` (UI hardcodeada) → declarar su **superficie de extensión** (slot/render-prop) en su entrada de catálogo + story.

> El toolkit son **patrones preferidos**, no un linter por línea. Lo que SÍ es mecánico: el **extension-contract gate** (§6) — todo tier-2 declara su superficie de extensión + trae **≥1 story-consumidora** que la ejerce (ej. `EntityInfoCard` + una story con badge custom vía slot). Tier-2 sin story-consumidora → CHANGES_REQUESTED. (Esto le da dientes a "extender no duplicar".)

### 4 · El inventario como espina (1:1 · generado · con lifecycle)

- **Catálogo generado del source REAL** (`@luana/ui-kit/src` + índice brand-local), 1 entrada por token/átomo/molécula/organism/layout/archetype. Cada entrada: `id · qué es · props + superficie de extensión declarada · story de Storybook (verdad visual) · cuándo-usar/cuándo-no · estado de lifecycle (vigente | deprecado | retirando)`. El skill hand-narrado deja de narrar → **lee** el catálogo.
- **Gate de paridad 1:1** (shrink-only): nada en código sin entrada · ninguna entrada `vigente` sin código y sin story. **El estado `deprecado`/`retirando` exime del gate de story** (ej. `AutosaveBadge` no tiene story porque se está retirando — NO es un gap).
- **`@luana/design-tokens` = SSoT de TODOS los ejes**, incluidos **valores** de color/typo/shadow (hoy names-only). Todas las marcas los consumen vía `@theme` (patrón nicolify); **vitalia migra off su dual-system**. Lo único per-brand son los valores que el package expone con nombre estable.

> **Estado (honestidad de timing):** el catálogo generado + el gate de paridad + el lift de tokens son **deliverables de Fase C — no existen aún.** La fuente visual es **Storybook** (`:6007` / `storybook-static`, cement 2026-06-22); la `/showcase` route que el canon §5 todavía menciona es referencia **stale** (se de-dup en Fase C). Ver **Caveat**.

### 5 · Contrato de fidelidad por actor (los handoffs = juntas de lego)

Cada actor depende del inventario (puerto), no del actor anterior. Cada junta lleva las referencias del inventario hacia adelante; nada se re-inventa downstream:

| Actor | Obligación (HARD) que garantiza mockup===resultado |
|---|---|
| **`/po-ux`** | Compone el mockup de **componentes REALES** (Storybook). Cada pieza **cita su entrada de inventario**. Pieza que falta → corre el árbol (§2) y flagea EXTEND/CREATE con el patrón (§3) + justificación. |
| **`/architect`** | `03-arch § FE` cita **por componente** la entrada exacta + **el patrón de extensión a usar + la ruta a replicar**. Net-new → lo **marca `PROMOTE`** con su diseño (el plan; NO ejecuta la promoción). (El architect SABE cómo extender, en detalle.) |
| **`/dev-team`** | Construye **de las entradas citadas** con los patrones declarados (único lego = el kit). **Ejecuta la promoción** del net-new al kit + story **antes del commit** (o lo marca brand-local explícito). Prohibido maquetar a mano / `<select>` nativo / arbitrary. |
| **`/auditor`** | **Gate-verifier** (no re-deriva a mano): verifica (a) **gates verdes** (no-arbitrary + no-div + arch-test FE + promote-gate + extension-contract), (b) **spot-check visual** mockup↔Storybook de 3-5 piezas complejas, (c) net-new **promovido** con story + lifecycle correcto, (d) **conteo de consumers** de piezas `ADAPT` (§2). Cualquier gate rojo, mockup≠resultado o mirror sin promover → CHANGES_REQUESTED. |

> **Pre-Fase C (bootstrap):** po-ux/architect citan la **story** de Storybook (la entrada de catálogo aún no existe); el auditor corre lint + arch-test + revisión visual **manual**. El contrato completo (entrada de catálogo + gates de paridad/promote/extension) es **estado-objetivo**, vivo al cerrar Fase C (ver **Caveat**).

### 6 · Backstops mecánicos (sin esto, la garantía se cae)

| Gate | Qué hace | Estado → target |
|---|---|---|
| **Paridad 1:1** | catálogo↔código↔story (con lifecycle) | construir (Fase C) |
| **`no-arbitrary-value`** | spacing/radius/font/color SOLO de la escala | vitalia+nicolify ✓ · **comunify = pre-req de Fase C (NO opcional — hoy driftea invisible)** · lupulo al bootstrap |
| **`no-div-layout` / `no-native-select`** | prohíbe `<div>` de layout donde hay primitiva | **solo vitalia → replicar a todas las marcas** |
| **Extension-contract** | todo tier-2 declara su superficie de extensión + trae ≥1 story-consumidora que la ejerce | construir (Fase C) |
| **Promote-gate** | detecta componente shared que quedó local sin promover (FE counterpart de anti-duplication) | construir (HB-107) |
| **Dark-wiring** (canon §2.10) | `dark:` → `[data-theme]`/`.dark` | vitalia+nicolify ✓ · replicar |

## Consecuencias

**Positivas:** el mockup ratificado === el resultado, por construcción (no por suerte) · el inventario deja de driftear (generado + gate de paridad) · "extender no duplicar" se vuelve enforceable (toolkit nombrado + promote-gate) · tokens con una sola fuente (incluido color) → cero look-divergente cross-brand · nuevas marcas heredan el sistema + las reglas gratis · piezas-lego reemplazables (bajo acoplamiento: cambiar una entrada del catálogo propaga a todos los consumers).

**Costos / riesgos:** (a) construir el generador de catálogo + el gate de paridad (esfuerzo real, Fase C) · (b) lift de valores color/typo/shadow a `design-tokens` + migración de vitalia off-dual (incremental, no big-bang) · (c) replicar los gates mecánicos a nicolify/comunify (paridad cross-brand) · (d) la adopción (borrar mirrors + consumir kit) es trabajo per-marca (`{brand}-ds-adoption`).

## Alternativas consideradas

- **Dejar el inventario como doc hand-narrado + disciplina** — RECHAZADO: ya driftea (skill dice 19/Z-only, real 23/5-ejes). El criterio no sostiene la paridad (mismo hallazgo que ADR-014).
- **Mantener `bucket-1/2/3` como vocabulario** — RECHAZADO: 4º naming sobre EXISTS/REUSE/Picks-canónicos = más scatter, justo lo que esta ADR consolida.
- **Color/typo per-brand en `globals.css`** (status quo) — RECHAZADO: es el driver #1 de drift de tokens; nicolify ya probó que el import `@theme` funciona.
- **Extender ADR-014 en vez de ADR nueva** — RECHAZADO: enforcement (014) y gobernanza de inventario (016) son concerns distintos → ADRs distintos (alta cohesión, principio de Chris).

## Programa (los tramos cuelgan de aquí · Fase C)

1. **Esta ADR** (doctrina + reglas) + **canon** (apunta acá para el PORQUÉ; sigue siendo SSoT del QUÉ) + **frontend-visual-fidelity** (apunta acá para las reglas; sigue siendo SSoT del QUIÉN-enforza, ahora con el contrato §5).
2. **Spine:** catálogo generado + gate de paridad + lift de valores a `design-tokens` + migración vitalia.
3. **Reglas en el harness:** el árbol §2 + toolkit §3 + contrato §5 cableados en po-ux/architect/dev-team/auditor (pointers, cero body duplicado) + brand-skills→routers que leen el catálogo.
4. **Gates:** paridad + promote-gate + replicación cross-brand (comunify-eslint quick-win primero).
5. **De-dup + archivo:** recortar ADR-014 (apunta al canon para contratos) · archivar genesis-docs (HANDOFF, inventory-best-of-best, to-be) · de-dup 5-capas/contratos/loop a un solo home.
6. **Adopción:** `{brand}-ds-adoption` (borrar mirrors + consumir kit) — per marca, `/pm-{brand}`.
7. **Verificación end-to-end:** un ciclo de prueba (necesidad → mockup del inventario → arch → dev → diff) que **demuestre** mockup===resultado.

> Caveat conocido (heredado de ADR-014): un programa platform multi-story no tiene contenedor limpio arriba de la story. Ancla = este par **ADR-016 + el checkpoint `core-ds-foundation`**; las stories son los tramos.

## Caveat — estado-objetivo vs bootstrap

Esta ADR diseña el **endpoint** (inventario-espina + gates de paridad/promote/extension + el contrato §5 completo). Hasta cerrar **Fase C**, varias piezas son estado-objetivo, no realidad: el **catálogo generado**, el **gate de paridad 1:1**, el **promote-gate** y el **extension-contract gate** se construyen en Fase C; el **lift de tokens** + la **migración de vitalia** son incrementales. Interino: la fidelidad se sostiene con `design-system-canon.md` (estático) + lint + arch-test + revisión visual **manual** del auditor.

**Ratificar esta ADR = ratificar el endpoint + el orden de Fase C**, sabiendo que la garantía **mockup===resultado es completa recién al cerrar Fase C** (los gates mecánicos son su última milla). El comportamiento del pipeline NO cambia el día que se acepta la ADR; cambia a medida que Fase C aterriza cada gate.

## Referencias

- `design-system-canon.md` — contratos (QUÉ) · **se actualiza**: §governance apunta acá; retira la jerga bucket
- `ADR-014-design-system-homologation.md` — enforcement de homologación (las 5 capas) · **se recorta**: apunta al canon para contratos
- `storybook-component-inventory-to-be.md` — DRAFT origen · **se archiva** al ratificarse esta ADR
- `.claude/rules/frontend-visual-fidelity.md` — QUIÉN enforza + el contrato §5 (apunta acá para las reglas)
- `docs/promotion-protocol/` — § FE a formalizar (los 12 proposals `ui-kit-*` de-facto)
- `core/@luana/{design-tokens, ui-kit}` — homes · `core-ds-foundation/checkpoint.md` — el programa de build
- Evidencia Fase 1 (auditoría de paridad): `core-ds-foundation/chris-input.md § 2026-06-25`
- ADR-012 (autosave) — patrón hermano · `.claude/rules/anti-duplication.md` — un solo engine/componente
