# Frontend Visual Fidelity — operational detail (loaded on-demand, moved from .claude/rules/ 2026-05-30)


**Origen:** sesión 2026-05-28 — Chris pidió fijación en el **cumplimiento visual** del frontend: usar los átomos/moléculas ya definidos, FSD muy cuidado, y **pegarse lo más posible al mockup**, verificado por Playwright. Problema observado: hay mockups que luego se implementan y **no se parecen**. Matiz: los mockups a veces tienen MÁS de lo que la historia desarrolla → la regla NO es "construí todo el mockup" sino "cumplí visualmente lo que la historia SÍ scopea, sin exceder".

**Cement-date:** 2026-05-28. **Aplica a:** `/architect` (FE), `builder-frontend`, `auditor-frontend`. **Complementa:** `frontend-fsd.md` (boundaries) + `frontend-quality.md` (gates) + `spanish-text.md` + `anti-orphan-integration.md`.

## Regla cardinal

El FE construido debe **(1) reutilizar el design system existente, (2) parecerse al mockup en lo que la historia scopea, y (3) NO exceder la historia**. Tres disciplinas, una verificación (Playwright + auditor).

### D0 — Storybook = SSoT visual (partir de la story citada · cement 2026-06-22)

**Antes que nada**, el diseño/build **parte de Storybook** (`core/@luana/ui-kit` — el catálogo de los componentes REALES; SSoT visual, canon §5):
- `/po-ux` compone el mockup desde el **HTML renderizado** de las stories (`storybook-static/` o iframe `…/iframe.html?id=<story>&viewMode=story`) — misma base que el build, cero CSS inventado, cero `_shared.css` (mecanismo MUERTO).
- `/architect` **cita en `03-arch.md § FE` la story exacta** a usar (+ link). Una pieza net-new se marca `PROMOTE`.
- `builder-frontend` lee la story citada (controles + todos los estados) **antes** de escribir código y construye desde `@luana/ui-kit`.
- **Promover de vuelta:** si la historia introduce una primitiva shared genuinamente nueva, se **implementa en `core/@luana/ui-kit` + se agrega su story** (deliverable del ticket, antes del merge) y la feature la consume vía import. NUNCA una re-implementación local que driftea. "No limitarse a Storybook": proponer lo mejor → promoverlo → el catálogo crece para futuras historias.

### D1 — Design system first (átomos/moléculas, NO reinventar)

Tras partir de Storybook (D0), el builder MUST buscar y reutilizar, en orden:
1. **Átomos** — primitivas de `@luana/ui-kit` / Shadcn en `{brand}/frontend/src/components/ui/` (Button, Input, Card, Dialog, Select, Badge, …). NUNCA reinventar una primitiva que ya existe.
2. **Tokens** — `@luana/design-tokens` (colores, spacing, radios, tipografía) + Tailwind theme del brand. NUNCA hardcodear hex/px que ya son token.
3. **Moléculas compartidas** — `{brand}/frontend/src/components/shared/` (composiciones cross-feature ya definidas).
4. **Solo si nada sirve** → **proponer la pieza nueva + promoverla a `@luana/ui-kit` + story** (D0, reuso futuro); si es genuinamente single-use de la feature, crearla en `features/{m}/components/` CON átomos (no desde cero con `<div>` crudos) y marcarla como promotion-candidate al 2º consumidor.

```bash
# Gate pre-crear componente visual (builder + auditor):
WS=$(git rev-parse --show-toplevel); BRAND={brand}
ls ${WS}/${BRAND}/frontend/src/components/ui/           # átomos disponibles
ls ${WS}/${BRAND}/frontend/src/components/shared/        # moléculas disponibles
grep -rn "<NombrePropuesto" ${WS}/${BRAND}/frontend/src  # ¿ya existe algo parecido?
```

Reinventar un átomo existente → auditor-frontend FAIL (duplicación de design system, también cae bajo `anti-duplication.md`).

### D2 — Mockup adherence (pegarse al diseño)

El builder implementa para **parecerse al mockup** de `02-design-ui.md` (wireframes / `mockups/` / Figma link): jerarquía visual, layout, spacing relativo, estados (default/hover/loading/empty/error/success), y microcopy (Spanish neutro, `spanish-text.md`).

- El architect, en `02-design-ui.md` / `03-arch.md § FE`, declara los **elementos visuales clave** que deben estar presentes (no pixel-perfect: elementos + jerarquía + estados).
- Fidelidad = "un humano comparando mockup vs implementación reconoce que es la misma pantalla", no igualdad de pixeles.

### D3 — Scope discipline (NO exceder la historia)

El mockup puede mostrar MÁS de lo que la historia desarrolla (secciones futuras, features adyacentes, datos de relleno). El builder implementa **solo lo que scopean los scenarios de `01-spec.md` + los `deliverables` del ticket**. Lo demás del mockup: NO se construye en esta story.

- El architect declara en `04-validators.yaml § playwright_visual_scope`: `story_scope_routes` + `story_scope_components` (lo que SÍ es de esta historia) y `out_of_mockup_scope` (lo que el mockup muestra pero NO va ahora).
- Si el builder cree que algo del mockup es necesario pero está fuera de scope → lo documenta en `T-{n}-impl-log.md § Mockup scope notes`, NO lo construye (escalate `/pm-{brand}` para spec extension).
- Anti-exceso: construir secciones del mockup fuera de los scenarios = scope creep → auditor WARN/CHANGES_REQUESTED + posible isla (anti-orphan).

## Verificación Playwright (cumplimiento visual)

`04-validators.yaml § visual` declara assertions Playwright **scoped a los componentes de la historia** (no snapshot global frágil):
- Presencia + jerarquía de los elementos clave del mockup en `story_scope_components`.
- Estados: empty / loading / error / success renderizan como el mockup.
- Responsive: breakpoints declarados en el mockup (si aplica).
- Bounded assertions (rol/testid/texto visible), NUNCA `toHaveScreenshot()` de página completa fuera de scope (drift en zonas no tocadas rompería el test — ver `architect-autonomous-mode.md § playwright_visual_scope`).

```ts
// Patrón: assertion scoped al componente de la historia, no snapshot global
await expect(page.getByTestId('appointment-form')).toBeVisible();
await expect(page.getByRole('button', { name: 'Confirmar reserva' })).toBeEnabled();
// estado empty del mockup:
await expect(page.getByText('Aún no hay reservas')).toBeVisible();
```

`chrome-devtools-verify` (reinstaurado, Chrome DevTools MCP oficial) para verificación conversacional live del cumplimiento visual antes de cerrar.

## Auditor-frontend — categoría Visual fidelity

`auditor-frontend` verifica: (a) átomos/moléculas reutilizados **desde `@luana/ui-kit` (composición contra Storybook)**, cero primitiva reinventada · (b) tokens usados, cero hex/px hardcodeado fuera de token · (c) FSD boundaries (`frontend-fsd.md`) · (d) elementos clave del mockup presentes (vía Playwright visual + screenshot) · (e) scope: NO se construyó fuera de la historia · (f) Spanish neutro · (g) **promote check: una primitiva shared net-new se promovió a `@luana/ui-kit` + story** (no quedó local que driftea) → si no, CHANGES_REQUESTED. Carril A self-fix aplica a fidelidad cubierta por test existente (swap a átomo, token, estado faltante).

## Anti-patterns prohibidos

- ❌ Diseñar/maquetar UI sin **partir de Storybook** (inventar CSS o copiar `_shared.css`/mockup-kit — MUERTOS, canon §5)
- ❌ Primitiva shared net-new que queda **local en `features/{m}/`** sin promover a `@luana/ui-kit` + story (drift · futuras historias no la reusan)
- ❌ `/architect` que NO cita la story de Storybook (el builder improvisa sin saber qué lego usar)
- ❌ Reinventar un átomo Shadcn que ya existe en `components/ui/`
- ❌ Hardcodear color/spacing/radius que ya es token de `@luana/design-tokens`
- ❌ `<div className="...">` crudos componiendo algo que es un átomo/molécula existente
- ❌ Implementar TODO el mockup cuando la historia scopea solo una parte (scope creep)
- ❌ Ignorar estados del mockup (empty/error/loading) — son parte de la fidelidad
- ❌ `toHaveScreenshot()` de página completa fuera del scope de la historia (frágil)
- ❌ Cerrar ticket FE sin verificación visual (Playwright scoped o `chrome-devtools-verify`)
- ❌ Microcopy con voseo (salvo sales_agent) — ver `spanish-text.md`

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 0 | **Storybook = SSoT visual** (canon §5): po-ux parte de las stories · architect cita la story · builder construye desde ella · net-new se promueve al kit + story · auditor verifica composición + promote | ✅ cement 2026-06-22 (canon §5 + rule § Storybook + skills/agents) |
| 1 | `/architect` FE: cita la story de Storybook + `04-validators § playwright_visual_scope` (story_scope vs out_of_mockup_scope) | ✅ SKILL.md § canon binding + architect-orchestrator design_rule 24 |
| 2 | `builder-frontend` step: Storybook-first (D0) + design-system-first gate + mockup adherence + scope + promote net-new | ✅ technical_design step 1 |
| 3 | `auditor-frontend` categoría Visual fidelity (composición desde Storybook + promote check) | ✅ Cat 16 |
| 4 | Playwright visual assertions scoped (`04-validators § visual`) | ✅ schema existe (reforzar scoping) |
| 5 | `chrome-devtools-verify` live visual check pre-cierre FE | ✅ reinstaurado |

## Referencias

- `.claude/rules/frontend-fsd.md` — boundaries FSD-Lite + design system layers
- `.claude/rules/frontend-quality.md` — gates (tsc/eslint/vitest/jscpd)
- `.claude/rules/architect-autonomous-mode.md § playwright_visual_scope` — disciplina de scope visual
- `.claude/rules/spanish-text.md` — microcopy neutro
- `.claude/rules/anti-orphan-integration.md` — el componente debe estar enchufado (nav/route)
- `core/@luana/design-tokens` — tokens cross-brand
