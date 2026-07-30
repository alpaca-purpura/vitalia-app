---
story_id: vitalia-fase1-topbar-global
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.topbar-global
state: done
phase_state: MERGED_ARCHIVED
last_modified: 2026-05-23
merged_at: 2026-05-23T02:05:00-05:00
archive_path: vitalia/docs/archive/2026/stories/vitalia-fase1-topbar-global/
capability_promoted: vitalia/docs/product/capabilities/platform/topbar-global.yaml
reviewing_started_at: 2026-05-23T01:55:00-05:00
reviewing_owner: /auditor (direct examination)
audit_verdict: APPROVED
audit_verdict_at: 2026-05-23T02:00:00-05:00
audit_iterations: 1
self_fix_iter: 0
developing_started_at: 2026-05-23T01:05:00-05:00
developing_finished_at: 2026-05-23T01:55:00-05:00
developing_owner: /dev-team (autonomous Sonnet per R23 FE no-agentic)
chain_position: "F1-S2 tercero en chain F1-S0→S1→S2→S3 · F1-S0 done 69948873 · F1-S1 done 5c59e89b · F1-S3 ready awaiting"
last_artifact: T-8-result.md
commit_sha: b37b37b3
tickets_completed: [T-1, T-2, T-3, T-4, T-5, T-6, T-7, T-8]
validators_green: [fe_typecheck, fe_lint, fe_no_default_exports_grep, fe_no_any_typescript_grep, fe_vitest_existing_regression, fe_topbar_role_banner_grep, fe_skip_link_present_grep, fe_main_content_id_present_grep, fe_logo_mark_next_image_grep, fe_brand_assets_present]
vitest_summary: "106 test files / 824 tests PASS (F1-S0 + F1-S1 + F1-S2 combined)"
architecture_fitness: "11 test files / 43 tests PASS"
ratified_by_chris: true
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-22T20:00:00-05:00
ratified_visual_iter: 1
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/topbar-global.html
  - vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/logo-mark.html
po_ux_iterations: 1
po_ux_decisions_cemented_2026_05_22:
  D1: "LogoMark 6 combinations (3 sizes sm/md/lg × 2 variants full/mark) height-based 24/32/40px width auto"
  D2: "Mobile responsive @media <768px switch a variant='mark' (libélula sola)"
  D3: "TenantSwitcherSlot returns null gap puro · F1-S3 reemplaza drop-in sin layout shift"
  D4: "Mockups separados: topbar-global.html (4 states light/dark × desktop/mobile) + logo-mark.html (6 combinations grid + dark toggle)"
  D5: "PNG via Next.js Image ahora · SVG roadmap futuro (story dedicada vitalia-fase2-logo-svg-conversion)"
  D6: "RESUELTA ✓ — vitalia-logo-dark.png (wordmark white) entregado Chris 2026-05-22"
assets_brand_real_2026_05_22:
  - vitalia/frontend/public/brand/vitalia-ico.png       # libélula multicolor (~156KB)
  - vitalia/frontend/public/brand/vitalia-logo.png      # libélula + wordmark VITALIA navy (~107KB) — light mode
  - vitalia/frontend/public/brand/vitalia-logo-dark.png # libélula + wordmark VITALIA white (~93KB) — dark mode
parallel_safe: false
priority: critical
estimated_dev_days: 1
dependencies:
  hard: [vitalia-fase1-stack-stability, vitalia-fase1-design-tokens-theme]
  soft: []
blocks_hard: [vitalia-fase1-shell-layout-5050]
reuse_map_summary: "NEW LogoMark + TopBarGlobal composes ThemeToggle (F1-S1) + TenantSwitcher slot (F1-S3)"
spawned_at: 2026-05-22
next_action: "AUTO-HANDOFF /pm-vitalia merge → write 07-merge.md + capability YAML platform/topbar-global + archive story + state reviewing→done"

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: topbar-global   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S2 vitalia-fase1-topbar-global — checkpoint

## Goal

Crear `TopBarGlobal` (organismo) + `LogoMark` (átomo) — la barra superior thin de 48px que aparece en todas las rutas del shell-organism. Compone logo izquierda + slot acciones derecha (ThemeToggle + TenantSwitcher placeholder).

## Anti-objetivos

- NO incluir TenantSwitcher funcional (F1-S3) — solo placeholder `<TenantSwitcherSlot />` o `null`
- NO tocar shell layout 50/50 (F1-S4)
- NO incluir notificaciones bell icon (Fase 2 postponed)

## Scope verbatim

### § 1 — `LogoMark` átomo

`vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx`:

Props:
- `size?: 'sm' | 'md' | 'lg'` (default 'md')
- `variant?: 'full' | 'mark'` (default 'full' = mark + "Vitalia" text · 'mark' = solo cuadrado V gradiente)

Visual contract (Design Contract § 3.1):
- Cuadrado 28x28 (md) con gradient 135° `from-agent-adrian to-agent-valeria` (#01b2f8 → #7b2d91)
- Letra "V" white center
- Si `variant="full"`: + texto "Vitalia" font-weight 700 size 16px al lado

```tsx
// Ejemplo (Spanish neutro)
export function LogoMark({ size = 'md', variant = 'full' }: LogoMarkProps) {
  return (
    <a href="/" className="flex items-center gap-2" aria-label="Vitalia inicio">
      <div className={cn('rounded-lg bg-gradient-to-br from-agent-adrian to-agent-valeria flex items-center justify-center text-white font-bold', sizeClass[size])}>
        V
      </div>
      {variant === 'full' && <span className="font-bold text-foreground">Vitalia</span>}
    </a>
  )
}
```

### § 2 — `TopBarGlobal` organismo

`vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx`:

```tsx
<header
  role="banner"
  className="h-12 border-b border-border bg-background flex items-center justify-between px-5 relative z-50"
  data-testid="topbar-global"
>
  <LogoMark />
  <div className="flex items-center gap-2">
    <ThemeToggle />
    <TenantSwitcherSlot />  {/* placeholder en F1-S2, real component en F1-S3 */}
  </div>
</header>
```

### § 3 — `TenantSwitcherSlot` placeholder

`vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx`:

Por ahora retorna `null` con TODO comment apuntando a F1-S3. Cuando F1-S3 merge, esta linea se reemplaza con `<TenantSwitcher />` real.

### § 4 — Skip link a11y

En `app/layout.tsx` o `(shell-organism)/layout.tsx` agregar antes del shell:

```tsx
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-[200] focus:p-2 focus:bg-primary focus:text-primary-foreground">
  Saltar al contenido
</a>
```

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | TopBar renderiza altura exacta 48px (h-12) |
| AC-2 | LogoMark visible izquierda con gradient correcto |
| AC-3 | ThemeToggle visible derecha (funcional desde F1-S1) |
| AC-4 | TenantSwitcherSlot retorna placeholder/null (real en F1-S3) |
| AC-5 | Skip link aparece al press Tab desde body root |
| AC-6 | TopBar tiene `role="banner"` |
| AC-7 | LogoMark `<a>` tiene `aria-label="Vitalia inicio"` |
| AC-8 | Visual golden snapshot match mockup |
| AC-9 | Light + Dark mode ambos renderizan correctamente |
| AC-10 | Mobile responsive (≥375px) sin overflow |

## Gherkin scenarios

### Scenario 1 — happy render

**Given:** Usuario navega a `/{tenant}/(shell-organism)/lisa/marca`

**When:** Página carga

**Then:**
- TopBar visible top con altura 48px exacta
- LogoMark izquierda con "V" + "Vitalia"
- ThemeToggle visible derecha
- NO TenantSwitcher real (placeholder)

### Scenario 2 — skip link a11y

**Given:** Usuario en cualquier shell route

**When:** Press `Tab` desde page root

**Then:**
- Skip link "Saltar al contenido" visible top-left con focus ring
- Press Enter → focus salta a `#main-content`

### Scenario 3 — mobile responsive

**Given:** Viewport 375x667

**When:** Página carga

**Then:**
- TopBar mantiene 48px altura
- Logo "Vitalia" texto puede ocultarse si necesita (only `variant="mark"` en mobile)
- ThemeToggle visible

### Scenario 4 — theme switch persists across TopBar

**Given:** TopBar visible, theme light

**When:** Click ThemeToggle

**Then:**
- TopBar bg cambia a dark mode
- Border color switch
- LogoMark gradient mantiene (es brand, no theme-dependent)

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/LogoMark.stories.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/LogoMark.test.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.stories.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.test.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx` | NEW (placeholder) |
| `vitalia/frontend/e2e/shell-organism/topbar.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/shell/topbar-{light,dark}.png` | NEW |

## Próximo paso post-done

F1-S3 `vitalia-fase1-tenant-switcher` arranca refining. Reemplaza `TenantSwitcherSlot` con componente real.
