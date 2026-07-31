---
slug: ui-kit-app-panel-slot-flex-col
date: 2026-06-15
state: accepted                      # Chris ratificó (/pm-luana completo) — fix core cross-brand
kind: core-fix                       # no es un lift brand→core; es modificación de core existente
target_package: core/@luana/ui-kit
semver: patch (0.4.0 → 0.4.1)
origin_story: vitalia/docs/product/stories/vitalia-bugfix-horarios-toolbar-sticky
ratified_by: Chris
consumers: [vitalia, nicolify]      # únicos que importan @luana/ui-kit (vitalia 35 · nicolify 8); comunify/lupulo NO lo consumen (0 imports)
---

# Core fix — `@luana/ui-kit` AppPanelSlot content-area flex-col

## Qué cambia (1 línea)

`core/@luana/ui-kit/src/organism/shell/AppPanelSlot.tsx` — el host del content-area pasa de
`<div className="flex-1 min-h-0 overflow-y-auto">` a `<div className="flex flex-col flex-1 min-h-0 overflow-y-auto">`.

## Por qué (root cause)

El content-area de `AppPanelSlot` era un `block` con `overflow-y-auto` (correcto para páginas
normales: la hoja scrollea, el shell queda fijo). Pero `EntityWorkspaceLayout` (mismo paquete
core) se monta con `flex-1` esperando un **padre flex-column** para clampar a la altura del panel
y manejar su PROPIO scroll interno (N3 fijo + grilla scrolleable). Con el content-area en `block`,
el `flex-1` de EWL era inerte → EWL crecía a la altura de su contenido → el content-area
scrolleaba TODO, arrastrando los toolbars de la hoja (la barra N3 sobrevivía solo por su `sticky`).

Mismatch de contrato entre dos componentes CORE (`AppPanelSlot` block-scroll ↔ `EntityWorkspaceLayout`
flex-child). Afecta toda marca que monte EWL dentro del shell.

Diagnóstico completo + mediciones live: `vitalia/.../vitalia-bugfix-horarios-toolbar-sticky/T-1-LIVE-VERIFY.md`.

## Verificación

- **vitalia — VERIFICADO LIVE** (dev-app, Chrome DevTools MCP, viewport 1280×720, vista 24h):
  EWL clampa (574/574), grilla = único scroller interno (361/1197), toolbars FIJOS al scrollear
  (heading 209→209, nav 272→272), day-header sticky, página no scrollea, bloque scrolleó 836px.
  Screenshot: `…/live-verify-fixed-scrolled.png`.
- **Páginas normales (no-EWL):** una hoja = un bloque alto en flex-column con `overflow-y-auto`
  sigue scrolleando igual → no rompe el caso común.
- **Downstream MECÁNICO (ambas marcas, VERDE):** nicolify FE `tsc` + 198 tests, comunify FE
  `tsc` + 38 tests — el `+flex flex-col` en el content-area compartido no rompe ninguna brand
  (ver `…/T-2-guards-downstream.md`). ui-kit vitest 270/270.
- **nicolify — VERIFICADO LIVE** (2026-06-15, fix aplicado al core del worktree nicolify +
  FE restart, Chrome MCP, viewport 1280×720, autenticado `owner.demo@nicolify.com`): shell
  renderiza sano, content-area = `flex flex-col … overflow-y-auto` (fix compilado), frame
  fijo (`pageLevelScrollable: false`), y **contenido normal scrollea DENTRO del content-area**
  (probe 2000px → scrolleó 1960px, página no scrollea) → el fix preserva el scroll de páginas
  normales, cero regresión. (ICP empty-state sin seed → el caso EWL detalle queda probado por
  vitalia, EWL canónico.) Screenshot: `…/downstream-nicolify-shell.png`.
- **comunify + lupulo — NO son consumers** (verificado 2026-06-15): comunify FE no importa
  `@luana/ui-kit` (0 imports, no lo declara en `package.json`, sin shell-organism; usa shell
  propio/pre-lift) y lupulo es placeholder (0 imports). **El fix no puede alcanzarlos** → fuera
  de scope, no aplica live-verify. (El stack comunify se levantó y se intentó verificar, pero al
  confirmar que no consume `@luana/ui-kit` la verificación es N/A — nada que verificar.) Cuando
  comunify adopte el shell core a futuro, recibirá la versión ya fixeada vía sync.

> **Consumers reales = vitalia + nicolify, AMBOS live-verificados → downstream COMPLETO.**

> Las ediciones temporales del core en los worktrees `../luana-nicolify` y `../luana-comunify`
> (aplicadas solo para el live-verify) fueron **revertidas**: el fix canónico vive en el worktree
> vitalia y llega a las marcas por el sync normal `wip/vitalia → main → wip/{brand}`.

## Guards (anti-regresión)

- **Core (vitest ui-kit):** assert que el content-area de `AppPanelSlot` incluye `flex flex-col`
  (evita revertir el clamp silenciosamente).
- **Comportamiento (Playwright vitalia):** scroll real + assert que toolbars mantienen su `.top`.
- El guard estructural jsdom previo (`horarios-toolbar-sticky.test.tsx`) se reencuadra como
  "presencia de clases" — NO valida conducta (jsdom sin layout engine = dio verde-fantasma).

## Notas

- `auditor-downstream-regression.md`: edit a `@luana/ui-kit` (engine) con consumers cross-brand →
  esta proposal + downstream tests por brand. Live-verify per-brand cierra cuando los stacks
  nicolify/comunify estén arriba con creds.
- Aprendizaje tooling capturado: el fix recompiló server-side (Turbopack) pero el **cache HTTP de
  chunks del browser** servía el bundle viejo → hard-reload/ignoreCache necesario para live-verify
  de cambios en `core/@luana/*`. Ver `docs/learnings/tooling/`.
