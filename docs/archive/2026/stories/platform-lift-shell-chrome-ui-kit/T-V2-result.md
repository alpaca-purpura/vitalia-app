# T-V2 Result — Vitalia: chrome local retirado + suite e2e completa contra el kit

**Story:** platform-lift-shell-chrome-ui-kit · **Ticket:** T-V2 · **Branch:** wip/vitalia · **Date:** 2026-06-11
**Commits:** `3c1597dd` (bloque 1 borrado+allowlists) · `cc45a060` (ConfigTab TooltipProvider) · `25b81395` (re-port verbatim + hydration) · `38449db6` (edge-redirects + harness shape/dark/waitFor) · `34b17521` (axe AA + harness final)

## Resultado final (evidencia literal)

```
npx playwright test e2e/regression/shell-core-hardening/ e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts
→ 84 passed · 1 skipped (test.fixme deuda inbox-dark) · 0 failed (2.5m)
resizer-matrix.spec.ts standalone → 7/7 (0 retries)
tsc 0 · eslint 0 · vitest 214 files (2485+) 0 fail · arch 30 files/187 PASS (allowlist mirror encogida) · kit 259/259
```

> Nota conteo: la suite actual = **85 tests** (la cifra "68" del hardening era el run de ese árbol; specs se estabilizaron post-merge). 84 verdes + 1 fixme rastreado.

## Borrado + allowlists (bloque 1, `3c1597dd`)

Chrome lifteado BORRADO de `components/shared/shell-organism/`: ShellOrganismLayout(Client), Valeria{Sidebar,CollapsedStrip,Chat,History}, Chat{Header,Composer,Messages}, MessageBubble, TypingIndicator, DelegateMarker, StatusDot, TogglePill, EmptyState(Inline), ChannelBadge, History{Group,Item}, PlaceholderCard, Ribbon(Tab), SubTab(sBar), SubSubTabsBar, ConfigTab, TopBarGlobal, AppPanelSlot, useViewportGuard (+tests). KEEP brand: LogoMark, ThemeToggle, Tenant*, AddClinicPlaceholderModal, _agent-tw-classes (Wire lo consume), types(Tenant), SubTabContent/EmptyState/PlaceholderCard variantes brand. `KNOWN_SANCTIONED_SHELL_MIRROR` ENCOGIDA en el mismo commit (RN-5). Store legacy retirado (key '-legacy' muerta); kit store v2 canónico.

## Fix-loop Bif-3 — bugs del PORT encontrados por la suite (todos en kit/wire, cero asserts de conducta tocados)

1. **Re-port verbatim ShellLayoutClient** (`25b81395`): el port T-K2 "limpió" la fuente violando D1-D5 — JSX bifurcado por isLg (Group desmontado en mobile + AppPanelSlot duplicado → hook-count inestable), `shellReady` perdido (data-shell-ready fijo en div equivocado), reconciliación sin isCollapsed-retry/expand-first/snap-up, push `DEFAULT+hist` en vez de ±actual con floor min+hist, containerRef fuera del main. Re-portado effect-por-effect desde `3c1597dd~1`.
2. **useStoreHydration** (`25b81395`): la fuente era el ÚNICO `rehydrate()` del árbol (ADR-vitalia-006: setItem NO-OP hasta hidratar) — sin él el store kit JAMÁS leía/escribía localStorage. Kit hidrata el shell store inyectado; Wire hidrata tenant store.
3. **ConfigTab TooltipProvider** (`cc45a060`): kit no asume provider del consumidor.
4. **userBubbleBgClass drift** (`34b17521`): default `bg-primary` (cyan, white=2.49 AA fail) — original usaba accent del supervisor (bg-agent-valeria, AA ✓). Kit ahora deriva `getAgentClasses(supervisorSlug).accentBg`.
5. **RibbonTab sub-label /60→/75** (`34b17521`): 4.25 sobre mateo-soft DARK.

## Edge-redirects N3 (`38449db6`)

Censo refutó el supuesto del hardening ("solo el landing tiene redirect in-render"): 4 más (lisa/marca→identidad, [agent] bare→defaultSubtab, staff/{id}→perfil, embudo/{id}→resumen). Con el kit, el "Rendered more hooks" (learning next16-softnav) pasó de flaky ~40% a DETERMINISTA → todos al edge 307 (`shellInRenderRedirectTarget` en shell-routes + proxy). Pages quedan fallback.

## ★ HALLAZGO MAYOR (auditor + CIL) — el verde del hardening era parcialmente FANTASMA

El edge-redirect destapó que varios runs "verdes" del hardening escaneaban un **shell colgado** (DOM "Cargando" casi vacío por el flake Rendered-more-hooks): axe reportaba 0-violations sobre nada, y 2 asserts eran IMPOSIBLES contra la app real:
- dark via `classList.contains("dark")` — la app usa `attribute="data-theme"` desde F1-S1 (la clase nunca existe).
- Ribbon `<a href>` — el Ribbon original es `button+router.push` desde F1-S7.
La gherkin-matrix del hardening los marca PASS = sobre-reporte del builder T-7. **Upstream deficiency** → harness-backlog + este flag.

## Harness adjustments (contrato real, semántica intacta — justificación c/u)

| Ajuste | Justificación |
|---|---|
| seeds/lecturas localStorage → `supervisorOpen` v2 | shape persistido del kit; seeds legacy de tests de MIGRACIÓN intactos |
| `getComputedBg` + checks dark → `data-theme` | contrato real next-themes (clase .dark jamás existe) — assert-fantasma corregido |
| soft-nav :96 → tabs por testid + sin reload | Ribbon real = button+router.push (el `<a>` era assert-fantasma) |
| `isVisible({timeout})` → `waitFor` | isVisible retorna inmediato (race vs RQ fetch) |
| n3 click → link interno "Ver perfil" | la card es `<article>` no-clickeable; el nav real del usuario es el link |
| allowlist console compone text+URL + SC-12 all-zeros UUID | "Failed to load resource" no trae URL en msg.text(); 404 del recurso fake ES el escenario del test |
| testids n3 reales (staff-card-*/kanban-board) | los del spec (entity-info-card-*/embudo-board) no existían en esas páginas |
| soft-nav timeout 180s | loop ×15 × 2 navs en dev = tiempo real |

## Deuda destapada (NO causada por el lift) → CIL L3

- **inbox dark**: ~10 contrastes AA rotos en `features/adrian/inbox` (BUG#2 hardening; la Decisión C "verde" nunca escaneó la página real). `test.fixme` rastreado en dark-per-subtab adrian/inbox. Fix = story de feature.
- Fixes WCAG quirúrgicos aplicados (≤5 líneas c/u, documentados inline): mateo D20 text-foreground · tenant-palette cyan→text-cyan-950 · FilterChips listbox→toolbar · WeekCalendar role=group + contraste abbr/badge. Unit characterization tests actualizados con razón.
- tsc kit-wide: 116 errores PRE-EXISTENTES (jest-dom types + timezone-select) en files no tocados; organism/ = 0.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| frontend-expert + vitalia-design-system + playwright-expert | ✅ (builders ×3 + orchestrator) | port/e2e/fix-loop |
| checkpoint § Aprendizajes (v4 props-capture · symlink-war · learning next16-softnav) | ✅ | re-port + edge-redirects |
| .claude/rules/definition-of-done-live-verify § anti-masking | ✅ | detección verde-fantasma |
