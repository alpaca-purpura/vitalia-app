# Storybook + Component Inventory — TO-BE (norte técnico)

> **★ DISUELTO 2026-06-25 → [ADR-016](ADR-016-design-system-inventory-governance.md) (accepted) + `design-system-canon.md`.** Este doc fue el DRAFT-norte que Chris pidió cerrar; su doctrina viva (ejes ortogonales · reuse/extend/create · toolkit de extensión · inventario-espina · contrato de fidelidad mockup===resultado) se **consolidó en ADR-016 + el canon** tras la auditoría de paridad (Fase 1). **No usar como fuente** — queda como génesis histórica. Plan de ejecución = `core-ds-foundation/checkpoint.md` (Fase C).
>
> ~~**Estado:** DRAFT to-be · pendiente de refinar + ratificar Chris en sesión dedicada.~~ (resuelto: ratificado vía ADR-016)
> **Owner:** `/pm-vitalia` (platform/core) + Chris como UI-senior decisor.
> **Origen:** sesión 2026-06-24/25 — Chris pidió fijar el norte del design system multimarca porque **es solo Chris + Claude, Claude es el único que programa**; sin disciplina técnica + norte explícito, el inventario degenera en componentes de 1-solo-uso inútiles + drift cross-brand.
> **Complementa (no reemplaza aún):** `design-system-canon.md` · `ADR-014-design-system-homologation.md` · `.claude/rules/frontend-visual-fidelity.md`. Este doc es el **target**; al ratificarse, su doctrina se cementa EN esos archivos + en los skills/agents.

---

## 0. Por qué este doc existe (el problema de fondo)

Operación solo-operador (Chris dirige, Claude programa). El riesgo no es escribir mal un componente — es **no tener un norte**: que cada sesión decida ad-hoc qué va al inventario, qué se duplica, qué se generaliza. Eso produce dos fallas opuestas, ambas caras:

1. **Inventario-basura:** storybook lleno de componentes de 1 uso que nadie reutiliza → ruido, mantenimiento sin retorno.
2. **Drift cross-brand:** cada marca forkea/reinventa lo que debería ser compartido → un fix no propaga, 4 copias divergen.

El to-be de abajo es la disciplina que mata ambas, basada en best-practice de design systems (EightShapes/Nathan Curtis, rule-of-three, shadcn ownership, composition-over-configuration) — ver § Fuentes.

---

## 1. El modelo (doctrina central)

### 1.1 — Dos capas, no una

| Capa | Qué es | Dónde vive | Storybook |
|---|---|---|---|
| **L1 · Design system compartido** | átomos + moléculas + patrones **brand-agnostic** (Button, Card, Select, EntityWorkspaceLayout, Ribbon, ChatPanel…). Mismo componente, tokens de marca distintos | `core/@luana/ui-kit` | **EL inventario** (`:6007`) |
| **L2 · Features de marca** | componentes con **vocabulario/lógica de UNA marca** (PHI mask, NPS-clínico, lead-scoring). Componen L1 pero el kit no los puede contener | `{brand}/frontend/src` | brand-local, **solo molecules de dominio** |

"Todas comparten atomic design con CSS distinto" = **verdad para L1**, no para L2. L2 no es "el mismo con otro color" — son componentes distintos porque encodean dominio que el kit (brand-agnostic by design, RN-2) no puede conocer.

### 1.2 — El mecanismo de adaptación: composición > configuración > copia

Para "adaptar un componente al uso específico de la marca" hay tres caminos. Orden de preferencia (best-practice 2025-26 "configuration collapse"):

1. **Composición ✅ (default)** — primitivas chicas + compound components (`<Card>`/`<Card.Header>`) que la marca **ARMA** por slots. Cero prop-explosion, cero fork. La adaptación = componer/envolver.
2. **Configuración (con cuidado)** — props/variants. Útil para variación acotada y conocida. Peligro: prop-explosion (4 booleans = 16 estados sin testear). Si un componente pasa de ~1 dimensión de variación → mover a composición.
3. **Copia + fork (shadcn, último recurso)** — copiás el componente y editás internals. Da ownership pero **drift garantizado** (fix del kit no llega a la copia). Válido SOLO como punto de partida desde el inventario, con piezas chicas, asumiendo el costo conscientemente.

> Regla práctica: el "extender" de Chris (architect/dev agarran del inventario y adaptan) DEBE materializarse como **composición** (envolver/slottear primitivas del kit), no como fork de un componente grande. Si te encontrás copiando un organism entero para cambiarle 2 cosas → el organism estaba mal granulado (demasiado grande), partirlo.

---

## 2. La taxonomía de decisión (3 buckets) — el corazón operable

Todo componente cae en exactamente uno. El test es **"¿otra marca lo reusaría tal cual, solo cambiando tokens?"**

| Bucket | Definición | Acción | Storybook |
|---|---|---|---|
| **1 · Genérico** | ≥2-3 usos (reales o claramente inminentes) + sin vocabulario de marca | **Promover a `@luana/ui-kit`** vía promotion gate. Construir **composable** (slots), no mega-props | **KIT inventory** — story obligatoria |
| **2 · Composición de marca** | arma primitivas del kit + copy/data de marca, 1 uso, sin lógica propia interesante | **Queda como código de app.** No se cataloga | **SIN story** (Playwright lo cubre) |
| **3 · Molecule de dominio** | lógica/vocabulario propio que el kit no puede tener (PHI, NPS-clínico) | Queda brand-local | **Story brand-local SOLO** si tiene estados ricos que valga ver aislados; si es trivial, ni eso |

**Anti-reglas (lo que NO se hace):**
- ❌ Catalogar un bucket-2 como inventario (= el inventario-basura que Chris teme).
- ❌ Generalizar a bucket-1 antes de 2-3 usos reales (premature abstraction; "duplicar es más barato que la abstracción equivocada").
- ❌ Dejar un bucket-1 viviendo local en una marca (drift; el auditor lo caza como deuda).
- ❌ Un bucket-3 con una primitiva genérica adentro sin promover esa primitiva.

> **Single-use NO es pecado.** Un componente de 1 uso bucket-2 está BIEN — como código de app. El error es ponerlo en el inventario. No se borran los single-use; se los mantiene fuera del catálogo de reutilizables.

---

## 3. Topología de Storybook (to-be)

| Storybook | Rol | Contenido | Puerto |
|---|---|---|---|
| `core/@luana/ui-kit` | **EL inventario** (L1). Brand-agnostic + toggle de marca (tokens). Lo que po-ux compone + dev extiende | bucket-1 (genérico compartido) | `:6007` |
| `{brand}/frontend` | features de marca (L2) | **solo** bucket-3 (molecules de dominio). NUNCA espejos del kit, NUNCA bucket-2 | (asignar 1 por marca, sin colisión) |

**Vista unificada — Storybook Composition (`refs`):** el storybook del kit embebe los de cada marca como secciones (`Kit/…`, `Vitalia ▸`, `Nicolify ▸`) en UNA ventana. Cada marca conserva su config (resuelve su `@/`, sus deps, sus providers) — el kit no se acopla. Una sola superficie para mirar todo.

```ts
// core/@luana/ui-kit/.storybook/main.ts  (to-be)
refs: {
  vitalia:  { title: "Vitalia",  url: "http://localhost:6011" },
  nicolify: { title: "Nicolify", url: "http://localhost:6012" },
}
```

**NO hacer** (trampa descartada): un solo config con globs a `{brand}/frontend/src` — colisiona `@/` (vitalia ≠ nicolify), colisiona CSS (`:root` × marca), exige cargar el árbol de deps de todas las marcas, e invierte el boundary (core tooling importando código de marca). Frágil. Composition lo resuelve sin ese costo.

**Pendiente de topología:** asignar puertos distintos por marca (hoy vitalia + nicolify ambos `:6006` → colisión latente). Sugerido: alinear a la convención de allocation (ver `CLAUDE.md`).

---

## 4. El workflow (to-be) — cómo lo usan los 5 actores

El bucle que Chris quiere ("inventario → po-ux lo muestra → yo acepto → architect/dev lo agarran y extienden"):

| Actor | Qué hace con el inventario |
|---|---|
| **`/po-ux`** | Compone el mockup **partiendo del inventario del kit** (consume el HTML renderizado de las stories). Si falta una pieza genérica → la **PROPONE** para promover (bucket-1). Una composición de marca (bucket-2) la arma con legos del kit, no inventa CSS. Nunca propone catalogar un single-use |
| **Chris** | Acepta el mockup. Es el decisor UI-senior: ratifica qué entra al inventario (bucket-1) vs qué es app-code (bucket-2) vs domain-molecule (bucket-3) |
| **`/architect`** | `03-arch.md § FE` **cita la(s) story(s) del kit a usar** + marca lo net-new genérico como `PROMOTE` (deliverable: crear en `@luana/ui-kit` + story antes del merge). Declara los gates mecánicos (no-arbitrary, no-div-layout) |
| **`/dev-team` (builder-frontend)** | Construye **componiendo** desde la story citada. Bucket-1 net-new → lo promueve al kit + story. Bucket-2 → lo arma como app-code sin story. **Extender = componer/envolver, NUNCA forkear un organism grande** |
| **`/auditor` (auditor-frontend)** | Verifica composición contra el kit (no estilo a mano) + que lo genérico se promovió (no quedó local) + que no se catalogó basura single-use. Bucket mal asignado → CHANGES_REQUESTED |

---

## 5. Qué YA quedó hecho (sesión 2026-06-24/25)

El storybook multimarca del kit (`:6007`) estaba roto; se arregló + verificó live:

1. **Docs en blanco (ambas marcas)** → era version-skew `@storybook/*` (10.3.6 + 10.4.0 + 10.4.6 conviviendo). Fix: `pnpm.overrides` → todo a `10.4.6`. ✅ live.
2. **Toggle de marca solo cambiaba CSS** (nombres/colores/avatares quedaban vitalia). Fix: capa de datos brand-aware (`BRAND_FIXTURES` registry + `getBrandFixtures(globals.brand)` en 13+ stories + bloque `[data-brand=nicolify]` de `--agent-*` + avatares/logos nicolify copiados). ✅ live ambas marcas.
3. **Chat demo + supervisor leak** ("Valeria"/turnos/paciente bajo nicolify). Fix: seed de conversación brand-keyed + `getBrandChatStore` + 2 stories wireadas. ✅ live.
4. **Downstream regression**: la refactor del fixture rompió un arch-test de vitalia (drift-guard que parsea el archivo del kit). Fixeado (regex → `VITALIA_RIBBON_ORDER`). ✅ 5/5.
5. **#5 topología (falso positivo corregido):** vitalia NO está vacío — tiene **44 stories** brand-local (features de clínica). Solo nicolify está vacío. NO se purgó nada.

Detalle técnico de la sesión: ver el commit asociado + `git log`.

---

## 6. El gap (qué falta para llegar al to-be)

| # | Tarea | Tipo | Notas |
|---|---|---|---|
| G1 | **Auditar los 44 stories de vitalia → 3 buckets** | análisis | bucket-1 → promover al kit (composable) · bucket-2 → des-storyficar (app-code) · bucket-3 → dejar. Resultado: el storybook de vitalia queda chico (solo dominio) |
| G2 | **Storybook Composition (`refs`)** + puertos distintos por marca | tooling | nicolify = cross-brand (su worktree). Mata la colisión `:6006` |
| G3 | **Refactor composición** de los bucket-1 promovidos (slots, no mega-props) | dev | aplica composition-over-config a lo que sube al kit |
| G4 | **Cementar la doctrina en harnesses** (§7) | harness | el paso que hace que esto sea NORMA, no decisión por sesión |
| G5 | **Definir el promotion-flow FE** (cómo un componente sube de marca→kit en la práctica: gate, semver del kit, story obligatoria) | proceso | hoy existe para BE (promotion-protocol); falta el equivalente FE explícito |

---

## 7. Cementación en harnesses (el verdadero objetivo de Chris)

Para que esto sea norma y no se re-decida cada sesión, la doctrina se escribe en:

| Artefacto | Qué agregar/cambiar |
|---|---|
| `docs/architecture/luana-platform/design-system-canon.md` | § nueva: **taxonomía de 3 buckets** + **composition-over-configuration** como contrato. Este doc to-be se funde acá al ratificarse |
| `docs/architecture/luana-platform/ADR-{nuevo}` | ADR que registra la decisión: 2 capas · 3 buckets · composition-first · storybook composition. (¿extiende ADR-014 o ADR nuevo?) |
| `.claude/rules/frontend-visual-fidelity.md` | agregar el **test de bucket** + "extender = componer, no forkear" + "single-use ≠ inventario" a los anti-patterns + binding por actor |
| `.claude/skills/po-ux/SKILL.md` | Step de composición: clasificar cada pieza del mockup en bucket; proponer promoción de bucket-1; no catalogar bucket-2 |
| `.claude/skills/architect/SKILL.md` | citar story del kit + marcar `PROMOTE` los bucket-1 net-new + declarar el gate |
| `.claude/agents/builder-frontend.md` | "extender = componer/slottear, no fork"; promover bucket-1 al kit con story |
| `.claude/agents/auditor-frontend.md` | categoría: bucket mal asignado · single-use catalogado · genérico-no-promovido · fork de organism grande |
| `docs/promotion-protocol/` | extender (o espejar) el gate brand→core para **componentes FE** (G5) |

> **Regla de oro del harness:** NUNCA editar el harness mid-feature. La cementación (§7) es su propia fase, después de ratificar el to-be (§1-4) e idealmente después de validar con G1 (la auditoría de los 44 da evidencia real de si la taxonomía aguanta).

---

## 8. Decisiones abiertas para la próxima sesión

1. **¿Composition (`refs`) ahora o más tarde?** Da la "una ventana" que Chris pidió. Bajo costo. Recomendado sí, pero toca nicolify (cross-brand).
2. **¿ADR nuevo o extender ADR-014?** ADR-014 es "homologación"; esto es "inventario + granularidad". Probablemente ADR nuevo que ADR-014 referencia.
3. **Granularidad del kit:** ¿cuán chico parten los organisms para que "extender = componer"? (ej. ¿ChatPanel se parte en slots para que una marca cambie el composer sin forkear?)
4. **Promotion-flow FE (G5):** ¿gate idéntico al BE (proposal + ratify + semver kit) o más liviano?
5. **¿Los 44 de vitalia se auditan antes o después de cementar?** (recomendado antes — evidencia real).
6. **Threshold del "rule of three":** ¿promovemos a bucket-1 con 2 usos o esperamos 3? (con 4 marcas activas, quizá 2 alcanza).

---

## 9. Fuentes (best-practice que fundamenta el to-be)

- Nathan Curtis / EightShapes — [Design System Contribution Criteria](https://medium.com/eightshapes-llc/i-made-this-does-it-go-in-the-system-3b67b9894531) ("casi todo NO va al sistema; si sirve a ~5 productos, va")
- Nathan Curtis — [Configuration Collapse](https://nathanacurtis.substack.com/p/configuration-collapse) (props frágiles → composición)
- [Configuration vs Composition — Design Reusable Components](https://dev.to/anuradha9712/configuration-vs-composition-design-reusable-components-5h1f)
- [shadcn/ui — The Component Library That Isn't a Library](https://dev.to/mechcloud_academy/shadcnui-the-component-library-that-isnt-a-library-5b94) (ownership / copy-and-own)
- [Building a Design System That Doesn't Collapse Under Its Own Weight](https://dev.to/tawe/building-a-design-system-that-doesnt-collapse-under-its-own-weight-4ll9)
- rule-of-three / "wrong abstraction" (Sandi Metz): duplicar < abstracción equivocada

---

## 10. Cómo retomar (próxima sesión)

1. Leer este doc + `design-system-canon.md § 5` (Storybook = SSoT visual) + `ADR-014`.
2. Refinar/ratificar §1-4 (el modelo) con Chris como UI-senior.
3. Resolver §8 (decisiones abiertas).
4. Ejecutar §6 (gap) en orden: G1 (auditar 44) → G2/G3 (composition + refactor) → G5 (promotion-flow FE).
5. Cementar §7 (harnesses) — fase propia, post-ratificación.
