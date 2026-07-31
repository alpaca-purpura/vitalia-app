# Vitalia — Shell Mockup-per-Component Protocol

> **⚠️ SUPERSEDED 2026-06-22 (ratificado Chris) — por Storybook = SSoT visual** (`docs/architecture/luana-platform/design-system-canon.md § 5` + `.claude/rules/frontend-visual-fidelity.md § Storybook`). El mockup HTML por-componente (`.html` espejo) ya **NO** es el mecanismo: el diseño + la ratificación visual **parten de Storybook** (`core/@luana/ui-kit`, el componente REAL); lo net-new se **propone + promueve** al kit + su story. Este protocolo queda como referencia histórica — **NO aplicarlo en stories nuevas**.

**Overlay:** extiende `.claude/rules/` raíz Luana platform (refuerza `frontend-fsd.md` + paradigm v4 § Conv 1 DISCOVERY workflow).
**Brand:** vitalia (Salud + Bienestar — shell-organism agéntico)
**Scope:** stories Vitalia Fase 1+2 que construyen componentes UI shell-organism.
**Cement-date:** 2026-05-22.
**SSoT:** `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md`.

## Regla cardinal

Toda story Vitalia que construye componente UI nuevo bajo `vitalia/frontend/src/components/{ui,shared/shell-organism}/` o `vitalia/frontend/src/features/{agent}/components/` MUST producir mockup HTML por-componente en `vitalia/docs/product/stories/{story-id}/mockups/{component}.html` ratificado por Chris ANTES de transition `refining → refined`.

Sin esta ratificación visual: `/architect` REFUSE arrancar.

## Scope

### Aplica (gate bloqueante)

- F1-S1 `vitalia-fase1-design-tokens-theme` → mockup `theme-toggle.html`
- F1-S2 `vitalia-fase1-topbar-global` → mockups `topbar-global.html` · `logo-mark.html`
- F1-S3 `vitalia-fase1-tenant-switcher` → mockups `tenant-switcher-closed.html` · `tenant-switcher-open.html`
- F1-S4 `vitalia-fase1-shell-layout-5050` → mockup `shell-layout-agentic.html` + `shell-layout-web.html`
- F1-S5 `vitalia-fase1-valeria-rail-history` → mockups `valeria-rail.html` · `valeria-history.html` + estados collapsed/rail/full
- F1-S6 `vitalia-fase1-valeria-chat-skeleton` → mockup `valeria-chat-sample.html`
- F1-S7 `vitalia-fase1-ribbon-6-tabs` → mockup `ribbon-6-tabs.html` con 6 variants per active tab
- F1-S8 `vitalia-fase1-sub-tabs-line2` → mockup `sub-tabs.html` con 6 variants per agente
- F1-S9 `vitalia-fase1-routing-shell` → N/A (routing puro, sin componente visual nuevo — usar mockups F1-S2..S8 como referencia integral)
- F1-S10 `vitalia-fase1-empty-states` → mockup `empty-states-grid.html` con 22 sub-tab placeholders
- Toda story Fase 2 que construye componente UI sub-tab-specific (PipelineColumn, AgendaSlot, etc.) — aprox 20-22 stories según outcome master

### NO aplica (excepciones explícitas)

- F1-S0 `vitalia-fase1-stack-stability` — infra-only (Shadcn install + tokens + plan). NO crea componentes user-facing nuevos. Las 2 test pages auxiliares son fixtures Playwright (`primitives-showcase.tsx`, `agent-tokens-swatch.tsx`), no UI prod.
- Service-stories (`vitalia-payment-adapter-mvp`, `vitalia-fiscal-emission-pe`, etc.) — BE only.
- Agentic-stories conversacionales puras (usar `/ux-agentico` flow design en su lugar, no mockup HTML).
- Stories Fase 2 que solo agregan data a componentes ya ratificados Fase 1 (e.g., sub-tab que reusa Ribbon + SubTabsBar + adds solo placeholder content).

## Constraints

### Mockup HTML structure obligatoria

Todo mockup en `vitalia/docs/product/stories/{story-id}/mockups/{component}.html` debe:

- Usar **Tailwind CSS CDN** (`https://cdn.tailwindcss.com`) o Tailwind precompilado equivalente
- Cargar **tokens Vitalia via CSS vars** (mismo schema que Design Contract § 5.1: `:root { --background: ...; --agent-lisa: ...; ... }` y `.dark { ... }`)
- Renderizar **datos LatAm realistas** (no Lorem ipsum, no placeholders genéricos)
- **Spanish neutro LatAm** en todos los strings (validar contra `.claude/rules/spanish-text.md` glosario)
- Mostrar **todas las variantes** del componente (e.g., Button default/secondary/ghost/destructive/outline, ValeriaSidebar collapsed/rail/full)
- Incluir **dark mode** si el componente lo soporta (toggle button local en el mockup)
- **Sin frameworks externos** (NO Bootstrap, NO Material UI) — Shadcn-style copy-paste o markup Tailwind nativo

### ★ Shell wrapper fidelity (cementado 2026-05-27 — origen lisa-marca v2.1 refactor)

Cuando el mockup per-component aterriza dentro del shell-organism (sub-tab / sub-sub-tab / componente Fase 2 que ocupa el panel-content), el **wrapper visual de contexto** (TopBar global, Ribbon agentes, SubTabsBar, ValeriaSidebar/chat) MUST ser **portado verbatim** desde las fuentes canónicas archivadas. Reinventarlo simplificado genera 4 problemas observados:

1. Falsos "regression flags" de Chris al ver pestañas padre con apariencia distinta a producción
2. Colores grisáceos en vez de tokens marca (gradient mariposa, agent colors)
3. Layout estático (50/50 hardcoded) sin reflejar splitter resizable real
4. Chat de Valeria inventado simplificado en vez del componente shipped

**Fuentes canónicas obligatorias del wrapper** (Read-only, port verbatim):

| Layer del shell | Fuente canónica (archivada, immutable) |
|---|---|
| Shell integral (referencia macro) | `vitalia/docs/archive/2026/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` |
| TopBar global + logo gradient | idem § `.topbar`, `.topbar-logo`, `.tenant-switcher` (líneas ~109-200) |
| Splitter resizable 3 estados | idem § `.shell`, `.panel-valeria[data-state]` (líneas ~203-225) |
| Ribbon 5 especialistas + Plataforma con agent-color borders | idem § `.ribbon`, `.ribbon-tab[data-color]` (líneas ~485-538) · ★★ v1.2: Lisa · Mateo · Adrián · Lucas · Camila + PlataformaTab |
| SubTabsBar línea 2 con agent-soft active | idem § `.sub-tabs`, `.sub-tab[data-color]` (líneas ~540-568) |
| ValeriaChat con avatar + status + composer | `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html` (completo) |
| ValeriaRail (modo collapsed icons) | `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html` |

**Workflow correcto:**

1. Crear/editar `_shared.css` del story-folder con tokens HSL **idénticos** a `vitalia/frontend/src/app/globals.css` (NO inventar)
2. Definir clases del wrapper (`.shell-root`, `.shell-body[data-splitter-state]`, `.topbar`, `.chat-side`, `.chat-content`, `.chat-rail-only`, `.ribbon`, `.subtabs-bar`, `.subsubtabs-bar`, `.panel-side`) portando markup + nombres desde los canónicos
3. En cada `{component}.html` el wrapper es **idéntico cross-mockup** — solo cambia el `.panel-content` (la story owna eso)
4. Agregar `.splitter-control` en topbar (mockup-only widget) que cambia `data-splitter-state` ∈ `{chat-collapsed, chat-narrow, 50-50}` para que Chris verifique responsividad
5. `.panel-inner` **sin** `max-width` hard — usa `width: 100%` + `.cards-grid` con `repeat(auto-fit, minmax(...))` para fluidez real

**Cuándo NO aplica:** cuando el componente se ratifica aislado (`theme-toggle.html`, `logo-mark.html`, `tenant-switcher-open.html`) — esos NO necesitan shell, son atómicos. La regla aplica a mockups que muestran el componente **dentro del slot** (cualquier sub-tab Fase 2, cualquier integración intra-shell).

### Servidor local para revisión Chris

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/{story-id}/mockups
python3 -m http.server 8888
# Chris abre http://localhost:8888/{component}.html
# Chris itera con /po-ux hasta ratificación
```

### Ratificación tracking en `checkpoint.md`

Frontmatter de la story checkpoint MUST agregar al ratify:

```yaml
ratified_visual_by_chris: true                     # ★ NEW field mandatory para stories scope
ratified_visual_at: 2026-MM-DDTHH:MM:SSZ           # timestamp ratificación final
ratified_visual_iter: N                            # iteración final (1-N)
ratified_visual_mockups:                           # lista mockups ratificados con paths absolutos
  - vitalia/docs/product/stories/{story-id}/mockups/topbar-global.html
  - vitalia/docs/product/stories/{story-id}/mockups/logo-mark.html
```

Sin `ratified_visual_by_chris: true`: state NO transitions `refining → refined`.

## Tests requeridos (que la implementación debe cumplir)

Cuando `/dev-team` builde el componente, los tests obligatorios incluyen:

1. **Playwright visual golden side-by-side** del componente React real vs mockup HTML montado en viewport idéntico. `maxDiffPixelRatio: 0.001` (0.1% tolerance).
2. **Mapping trazable** en `01-spec.md § 7 Visual Goldens`: tabla `mockup HTML path → golden snapshot path → componente React path → Design Contract ref`.
3. **Ratchet shrink-only:** una vez generado y ratificado el golden, cualquier PR que lo modifique requiere re-ratificación explícita Chris (no se renueva silencioso).

## Anti-patterns prohibidos

- `/architect` arranca sin verificar `checkpoint.md::ratified_visual_by_chris == true` (gate bloqueante violado)
- `/po-ux` transitions `refining → refined` sin mockup HTML por componente nuevo (gate bloqueante violado)
- Mockup HTML con Lorem ipsum, placeholders genéricos, o data USA (use AR/MX/CO/PE/CL realistic)
- Mockup HTML con Bootstrap, Material UI, u otros frameworks (debe ser Tailwind + Shadcn-style para fidelidad post-implementación)
- Mockup HTML committed sin Chris ratificado explícito (estado tracking: draft → review → ratified en checkpoint)
- Reusar mockup integral `dual-mode-shell.html` (1439 líneas) como sustituto de mockups-per-component (eso es SSoT del shell completo, no de componentes individuales)
- Skipear protocolo argumentando "es un componente trivial" — la regla aplica TODOS los componentes user-facing del shell, sin excepción más allá de las listadas en § Scope NO aplica
- Mockup HTML que diverja del componente final SIN actualizar el mockup en el mismo PR (genera ratchet roto)
- ★ **Reinventar el wrapper del shell** (topbar/ribbon/sub-tabs/chat-side) en lugar de portarlo verbatim desde `dual-mode-shell.html` + `valeria-chat-sample.html` + `valeria-rail.html` (cementado 2026-05-27 — caso origen: `vitalia-fase2-lisa-marca` v2 → v2.1 refactor obligado por Chris)
- ★ **Mockup con layout 50/50 hardcoded** sin permitir simular los 3 splitter states (`chat-collapsed`, `chat-narrow`, `50-50`) — pierde fidelidad responsive del shell real
- ★ **Panel-content con `max-width` fijo** en píxeles (ej. `max-width: 680px`) — debe ser fluido (`width: 100%`) + cards-grid con `auto-fit/minmax` para aprovechar el ancho dictado por el splitter
- ★ **Tokens HSL inventados o divergentes** de `vitalia/frontend/src/app/globals.css` — el `_shared.css` del story-folder MUST ser espejo de los tokens reales (paleta primario cian #01B2F8, accent púrpura #7B2D91, agent-lisa #00D084, agent-valeria #7B2D91, agent-camila #180D95, **agent-mateo #FEE209** ★★ v1.2, gradient mariposa)
- ★ **ChatValeria simplificado** (textarea suelto sin avatar + dot status + mode pill + composer con adornos 📎🎙️⚡ + Cmd+K hint) — debe portar markup verbatim de `valeria-chat-sample.html`

## Referencias

- `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` — autoridad arquitectónica brand-local (SSoT del por qué)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — atomic design SSoT del shell (qué componentes existen + sus props)
- `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` — mockup integral SSoT visual del shell completo (referencia macro)
- `vitalia/docs/specs/templates/01-spec-shell-template.md` § 7 Visual Goldens — sección spec donde se cita el mockup
- `vitalia/docs/learnings/2026-05-22-shell-mockup-per-component-protocol.md` — promotable candidate cross-brand
- `.claude/skills/po-ux/SKILL.md` § Workflow Step 3 — donde se inserta gate visual obligatorio
- `.claude/skills/architect/SKILL.md` — gate REFUSE pre-arch (consume este protocolo via overlay rule load)
- `.claude/rules/frontend-fsd.md` — boundaries FSD-Lite que el componente final respeta
- `.claude/rules/spanish-text.md` — Spanish neutro LatAm glosario
