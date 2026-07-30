---
brand: vitalia
date: 2026-05-25
slug: mockup-playwright-audit-cycle
promotable: yes
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: docs/process/po-ux-protocol.md (process pattern, no core code change)
origin_story: vitalia-fase1-ribbon-6-tabs (F1-S7)
---

# Mockup HTML ratificado + Playwright real-browser audit cycle

**Qué aprendimos:** después de `/po-ux` producir mockup HTML ratificado por Chris + ANTES de `/architect` cerrar 03-arch.md, ejecutar Playwright real-browser inspect del mockup (no del código real — el código no existe aún). Este ciclo descubre bugs visuales y a11y que de otra manera surgen recién en audit post-build, costando rondas CHANGES_REQUESTED → dev-team.

**Origen:** story `vitalia-fase1-ribbon-6-tabs` (F1-S7) 2026-05-25. Chris pidió "revisa el html con playwright para que tu mismo entiendas qué cosas están mal" después de servir mockup `ribbon.html` (luego renombrado `ribbon-6-tabs.html` per overlay rule `shell-mockup-per-component.md`). Resultado: 4 bugs detectados antes del build:

| # | Bug detectado | Severity | Cement | Hubiera detectado en audit? |
|---|---|---|---|---|
| Q13 | ConfigTab `<button>` con `role=null` dentro de `<nav role=tablist>` → inválido a11y | HIGH | Mockup + spec § Accessibility | Sí — pero hubiera bloqueado en CHANGES_REQUESTED |
| Q14 | Tabs widths org vs uniformes — open question | MEDIUM | Mockup + spec § Q-table | Sí — pero hubiera generado round-trip de spec ambiguity |
| Q15 | "Mi Clínica" wrappea a 2 líneas en widths estrechos (modo agentic 50/50, panel ~640px) — ribbon `h-14` se rompe | CRITICAL | Mockup + spec § Estados visuales | Sí — pero hubiera bloqueado en CHANGES_REQUESTED post-build |
| Q16 | Active:hover degrada tint del agente — CSS specificity bug latente | MEDIUM | Mockup + spec § Estados visuales | Probable miss en audit unitario, detectable solo con manual hover |

**Why:** el mockup HTML ratificado **no es el código real pero captura intent visual + interaction patterns**. Ejecutar Playwright contra el mockup (incluso con CDN Tailwind, sin Next.js, sin TypeScript) detecta:
- Bugs a11y semánticos (role/aria/tabindex) — Q13 Q7 tipo
- Bugs visuales de wrap/overflow/responsive — Q15 tipo
- Bugs de specificity/cascading CSS — Q16 tipo
- Bugs de layout/spacing — Q14 tipo

Estos bugs viven en el INTENT visual, no en la implementación. Detectarlos pre-build evita:
1. Round-trip CHANGES_REQUESTED post-build (cada round ~$5-15 USD Sonnet + tokens audit)
2. Mockup-vs-código drift (si el bug aparece post-build, el mockup queda "incorrecto" como referencia)
3. Refactor cascading en componentes related (T-2 RibbonTab al hot-fix por testid scope T-5)

**How to apply:**

1. `/po-ux` produce mockup HTML local servido `python3 -m http.server`
2. `/po-ux` ratifica visualmente con Chris (Q1-Q12 batches, decisiones cementadas en `01-spec.md` § Q-table)
3. ★ **`/po-ux` ejecuta `playwright inspect` del mockup post-ratify** — capture screenshots desktop+mobile+light+dark, audit DOM (role attrs, computed styles, focus management, contrast). Reporta findings a Chris.
4. Chris ratifica fixes adicionales (Q13-Q16+) o pide refresh mockup
5. ITER hasta cero findings críticos
6. `01-spec.md` bumps `po_ux_version` por cada amendment cycle
7. ENTONCES transition `refining → refined` + handoff `/architect`

**Implementación operativa:**

- Tooling: `node` + `playwright-core` desde `node_modules/.pnpm/playwright@1.60.0/...` (path canónico Linux Mint host)
- Script template: `/tmp/inspect-{story-id}-mockup.mjs` con `chromium.launch()` + `page.goto(mockup-url)` + capture + DOM audit
- Capture screenshots en `/tmp/{story-id}-inspect/` para Chris visual review
- Audit checklist:
  - Each tab/button: `role` + `aria-selected/checked` + `tabindex` + `aria-label`
  - Computed styles: `getComputedStyle()` post-click/hover para verify CSS specificity
  - Visual: wrap, overflow, alignment, contrast ratio
  - Keyboard: `page.keyboard.press()` verify focus movement
  - Network: PNG/asset 404 fallback rendering

**Limitaciones (caveats):**

- Mockup HTML CDN-Tailwind ≠ producción Next.js+Tailwind-CLI: algunos JIT purge issues (como Q16 mecanismo real) solo se ven en código real, no en mockup. Auditor debe re-validar post-build.
- Mockup no testea interaction handlers (keyboard nav handlers son stubs en mockup HTML estático). Solo testea look & feel + a11y semantic.
- Mockup no testea routing (no Next.js usePathname/useRouter). Spec deep-link scenarios verify post-build.

**Cross-brand applicability:**

Pattern aplicable a TODA story UI standard cross-brand. Cada brand puede mantener su mockup overlay rule (`vitalia/.claude/rules/shell-mockup-per-component.md`, futuras `{brand}/.claude/rules/...`). El proceso PO-UX + Playwright real-browser audit es brand-agnostic.

**Promotion candidate:**

`/pm-luana` debería evaluar liftar este pattern a `docs/process/po-ux-protocol.md` Step 4.5 (post-ratify inspect mandatory para UI stories). Promotable: yes — beneficia toda brand activa + futuras.
