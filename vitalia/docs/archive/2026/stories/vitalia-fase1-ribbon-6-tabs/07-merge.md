---
story_id: vitalia-fase1-ribbon-6-tabs
brand: vitalia
phase: fase-1
type: ui-story
module: shell-organism
capability: shell.ribbon
state: done
merged_at: 2026-05-25T04:35:00Z
merged_by: /pm-vitalia
auditor_verdict: APPROVED
auditor_warns: 1
auditor_warns_inventory:
  - WARN-1 Q16 active:hover JIT purge mechanism (non-blocking · optional follow-up F1-S8 o standalone)
audit_iterations: 1
self_fix_iter: 0
gherkin_coverage_pct: 100  # 9/9 SC scenarios PASS
checkpoints_passed: "29/29 (C1 4/4 · C2 5/5 · C3 6/6 · C4 8/8 · C5 6/6)"
---

# 07-merge.md — F1-S7 vitalia-fase1-ribbon-6-tabs

> **5 secciones cementadas** post story-closure-gate 2026-05-18 (`.claude/rules/story-closure-gate.md` Layer 7).

## § 1 — Gherkin verification matrix

Source: `06-audit/gherkin-matrix.md` (Phase D, auditor-frontend). 9 scenarios SC-1..SC-9 todos PASS, 43 test entries trazadas.

| SC | Título | Tests | Status |
|---|---|---|---|
| SC-1 | happy · click tab agente → router.push default subtab | agent-catalog.test + RibbonTab.test + Ribbon.test + ribbon-nav.spec | **PASS** |
| SC-2 | happy · URL deep link marca active | Ribbon.test (usePathname) + ribbon-deeplink.spec | **PASS** |
| SC-3 | happy · ConfigTab → /{tenantId}/config/cuenta | ConfigTab.test + Ribbon.test + ribbon-config-nav.spec | **PASS** |
| SC-4 | negative · URL inválido → idle | Ribbon.test + agent-catalog.test (extractAgentFromPath null) + ribbon-invalid-agent.spec | **PASS** |
| SC-5 | edge · viewport mobile 375px → horizontal scroll | overflow-x-auto + ribbon-responsive.spec (375x667) | **PASS** |
| SC-6 | adversarial · XSS payload → safe | agent-catalog.test (script/javascript: → null) + ribbon-xss-guard.spec | **PASS** |
| SC-7 | a11y · keyboard WAI-ARIA tablist completo | Ribbon.test § keyboard 15 tests + ribbon-keyboard.spec + axe wcag2aa | **PASS** |
| SC-8 | i18n · microcopy Spanish neutro verbatim | agent-catalog.test (Adrián tilde, Mi Clínica tilde) + arch voseo grep + ribbon-i18n.spec | **PASS** |
| SC-9 | edge · Avatar PNG falla → fallback initial | RibbonTab.test § Avatar fallback + ribbon-avatar-fallback.spec | **PASS** |

**Coverage:** 9/9 scenarios = **100%** (sub-categorías mandatory aplicables todas cubiertas: a11y + i18n + edge + adversarial · 5 N/A justificadas: race / concurrent / network / empty / large — Ribbon es UI nav puro).

## § 2 — Playwright E2E run

Source: T-5-result.md + gate-output.json iter 5.

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-ribbon-6-tabs/ --project=smoke-linux
```

**Result:** 32/32 smoke specs PASS (9 SC behavior specs × ~3-6 cases each)

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-visual.spec.ts --project=visual
```

**Result:** 13/13 visual goldens PASS (iter 1 baseline, `--update-snapshots` autorizado post Chris ratify mockup ribbon-6-tabs.html iter 2, ratchet shrink-only desde merge)

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-a11y.spec.ts
```

**Result:** axe wcag2aa 0 critical/serious violations (D18 contrast amendment applied)

## § 3 — Capabilities updated/created

### NEW capability

**`vitalia/docs/product/capabilities/shell-organism/ribbon.yaml`**

- capability_id: `vitalia.shell-organism.ribbon`
- status: **live** (planned → live al merge)
- date_introduced: 2026-05-25
- story_introduced: vitalia-fase1-ribbon-6-tabs
- package_version: vitalia-frontend@0.1.0
- package_path: `vitalia/frontend/src/components/shared/shell-organism/`
- license: proprietary
- lift_candidate: cross-brand-when-2-brands-need-multi-agent-ribbon

Surfaces:
- backend: N/A (UI nav puro, sin BE)
- frontend: `vitalia/frontend/src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab,AppPanelSlot}.tsx` + `vitalia/frontend/src/lib/agent-catalog.ts` (EXTEND F1-S6)
- tests: `vitalia/frontend/src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab}.test.tsx` (1328/1328 unit) + `vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/` (32/32 smoke + 13/13 visual + 2/2 a11y)
- docs: `vitalia/docs/archive/2026/stories/vitalia-fase1-ribbon-6-tabs/` (post-archive)

Scenarios embedded verbatim del 01-spec.md (9 SC) → capability.scenarios[].

### Modules MD refreshed

**`vitalia/docs/product/modules/shell-organism.md`** — append entry `ribbon` post `valeria-chat` capability (auto-list section refresh manual since module narrative MD).

## § 4 — How to verify (commands reproducibles)

```bash
WS=$(git rev-parse --show-toplevel)
BRAND=vitalia

# (1) Unit tests scoped story
cd ${WS}/${BRAND}/frontend && npx vitest run src/lib/agent-catalog.test.ts src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab}.test.tsx

# (2) Arch fitness
cd ${WS}/${BRAND}/frontend && npx vitest run src/__tests__/architecture/

# (3) tsc strict + ESLint + Prettier
cd ${WS}/${BRAND}/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx prettier --check src/lib/agent-catalog.ts src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab,AppPanelSlot}.tsx

# (4) Playwright E2E (requires dev stack vitalia 3002 running — `make dev-vitalia`)
cd ${WS} && bash scripts/e2e-preflight.sh
cd ${WS}/${BRAND}/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-ribbon-6-tabs/ --project=smoke-linux

# (5) Visual goldens (ratchet shrink-only — no --update-snapshots sin Chris ratify)
cd ${WS}/${BRAND}/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-visual.spec.ts --project=visual

# (6) Cross-brand mirror scan (post-merge invariant — debe ser 0)
for brand in nicolify comunify lupulo; do
  find ${WS}/${brand}/frontend/src -name "Ribbon*" -o -name "ConfigTab*" -o -name "extractAgentFromPath*" 2>/dev/null
done
# Expected: vacío en los 3 brands
```

## § 5 — Decisiones cardinales (learnings candidates)

### 5.1 — Mockup ratificado + Playwright real-browser audit cycle (PROCESS PATTERN)

**Pattern:** después de `/po-ux` ratificar mockup HTML + antes de `/architect` cerrar 03-arch.md, ejecutar Playwright real-browser inspect del mockup. Detectó 4 bugs visuales/a11y (Q13/Q14/Q15/Q16) que de otra manera habrían surgido recién en audit post-build.

**Learning:** `vitalia/docs/learnings/2026-05-25-mockup-playwright-audit-cycle.md` (promotable: yes — proceso aplicable cross-brand a TODA story UI).

### 5.2 — Tailwind JIT template literal purge gotcha (TECH PATTERN)

**Mechanism observado:** template literals `` `hover:${agentBgSoftClass(slug)}` `` son JIT-purged por Tailwind (no static class → no incluido en CSS bundle). En F1-S7 Q16 active:hover funciona accidentalmente porque active branch no tiene `hover:bg-muted` compitiendo — el tint simplemente no se degrada (no porque CSS specificity gana, sino porque no hay nada para degradarlo).

**Learning:** `vitalia/docs/learnings/2026-05-25-q16-tailwind-jit-template-purge.md` (promotable: candidate — Tailwind v4 cross-brand pattern).

**Follow-up sugerido:** F1-S8 o standalone "vitalia-shell-organism-q16-jit-static-classes" — agregar `agentHoverBgSoftClass` helper estático en `_agent-tw-classes.ts` + unit test asserting hover class present + visual golden `ribbon-hover-active.png`. Severity: LOW (functional behavior correct, hardening defensive intent).

### 5.3 — Anti-duplication HARD respected (ARCH INVARIANT)

EXTEND `vitalia/frontend/src/lib/agent-catalog.ts` in-place (F1-S6 SSoT). NO creación de `lib/agents/catalog.ts` paths duplicados. Arch fitness `test-agent-catalog-ssot.test.ts` enforce. 0 cross-brand mirrors detectados post-merge (grep en nicolify/comunify/lupulo).

### 5.4 — Auditor self-fix policy validation (PROCESS PATTERN)

2 prettier follow-up commits (18489194 RibbonTab.test post-T2 + 5d7fd4d0 Ribbon.tsx/Ribbon.test/test-agent-catalog-ssot post-T5) aplicados por orchestrator self-fix whitelist #2 (Format). Cero rounds CHANGES_REQUESTED → dev-team. Auditor self-fix policy v4.1 cement validado.

---

## Squash-merge commit (pending)

```
feat(vitalia/f1-s7): merge complete — ribbon 6 tabs shell-organism · WAI-ARIA tablist · 9/9 SC · CHECKPOINTS 29/29

- Ribbon organism: 5 RibbonTabs (Lisa·Lucas·Adrián·Valeria·Camila) + 1 ConfigTab IconButton + WAI-ARIA tablist + roving tabindex (Arrow/Home/End/Enter/Space)
- Active state URL-derived (extractAgentFromPath de usePathname) — single source of truth
- bg-agent-{slug}-soft tint + font-semibold + whitespace-nowrap (h-14 uniforme)
- Avatar fallback Shadcn <AvatarFallback> con initial sobre bg-agent-{slug}-soft
- Tabs orgánicos (no min-w) · overflow-x-auto natural · TooltipProvider para Configurar
- Catalog SSoT EXTEND in-place (anti-duplication HARD respect)
- 5 tickets DAG sequential T-1..T-5 · ~14h actual · ZERO Opus (all FE production_code+test)
- Tests: 1328/1328 Vitest + 107/107 arch fitness + 32/32 Playwright smoke + 13/13 visual goldens + 2/2 axe wcag2aa
- Capability NEW: vitalia.shell-organism.ribbon (status: live)
- 9/9 Gherkin SC scenarios PASS (43 test entries Phase D) · CHECKPOINTS C1-C5 29/29 ✅ · 1 WARN non-blocking
- D18 a11y contrast amendment (sub-label text-foreground/60 → axe wcag2aa serious fix)
- D19 AvatarFallback testid integration scope (T-5 enablement, similar T-3 onKeyDown extension pattern)
- 2 learnings: mockup-playwright-audit-cycle (promotable: yes) + q16-jit-template-purge (promotable: candidate)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```
