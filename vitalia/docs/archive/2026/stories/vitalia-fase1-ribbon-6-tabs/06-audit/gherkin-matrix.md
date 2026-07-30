<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Gherkin Coverage Matrix — F1-S7 vitalia-fase1-ribbon-6-tabs

**Story:** vitalia-fase1-ribbon-6-tabs  (Phase D of audit, paradigm v4)
**Auditor:** auditor-frontend (Opus)  ·  **Date:** 2026-05-25
**Source:** 01-spec.md § Gherkin (SC-1..SC-9)  ·  06-tickets.yaml § gherkin_coverage (43 entries)
**Goal:** verify every Gherkin scenario from spec has ≥1 PASS test (unit Vitest or E2E Playwright) traced.

## Matrix

| SC | Title | Spec § | Unit tests (Vitest) | E2E tests (Playwright) | Visual goldens | Tickets | Status |
|---|---|---|---|---|---|---|---|
| **SC-1** | happy · click tab agente → router.push default subtab | 01-spec.md L68-84 | `agent-catalog.test.ts` (tabLabel + defaultSubtab values, 5 agents) · `RibbonTab.test.tsx` (renders avatar/label/role, data-testid, role=tab) · `Ribbon.test.tsx` (click ribbon-tab-lucas → router.push('/tenant-x/lucas/lanzar')) | `ribbon-nav.spec.ts` (Lisa→Lucas navigation + active migration) | `ribbon-active-{lisa,lucas,adrian,valeria,camila}.png` × 5 | T-1, T-2, T-3, T-5 | **PASS** |
| **SC-2** | happy · URL deep link marca active state | 01-spec.md L86-102 | `Ribbon.test.tsx` (usePathname='/tenant-x/lisa/marca' → ribbon-tab-lisa data-active=true; other 4 false) · `agent-catalog.test.ts` (extractAgentFromPath valid agent) | `ribbon-deeplink.spec.ts` (3/3 GREEN) | `ribbon-active-camila.png` | T-1, T-3, T-5 | **PASS** |
| **SC-3** | happy · ConfigTab → /{tenantId}/config/cuenta | 01-spec.md L104-119 | `ConfigTab.test.tsx` (role=tab + aria-selected + size-10 + ml-auto + Settings icon + Tooltip 'Configurar') · `Ribbon.test.tsx` (click ribbon-config-tab → router.push('/tenant-x/config/cuenta')) · `agent-catalog.test.ts` (extractAgentFromPath('config')) | `ribbon-config-nav.spec.ts` (3/3 GREEN) | `ribbon-active-config.png` | T-1, T-2, T-3, T-5 | **PASS** |
| **SC-4** | negative · URL inválido → idle state | 01-spec.md L121-138 | `Ribbon.test.tsx` (usePathname='/tenant-x/foobar/baz' → all 6 tabs data-active=false; no console.error) · `agent-catalog.test.ts` (extractAgentFromPath invalid returns null × 7 cases) | `ribbon-invalid-agent.spec.ts` (3/3 GREEN) | `ribbon-idle.png` | T-1, T-3, T-5 | **PASS** |
| **SC-5** | edge · viewport mobile 375px → horizontal scroll | 01-spec.md L140-157 | (visual + responsive class covered in unit indirectly: `overflow-x-auto` in container className) | `ribbon-responsive.spec.ts` (3/3 GREEN at 375x667) | `ribbon-mobile-375.png` | T-3, T-5 | **PASS** |
| **SC-6** | adversarial · XSS payload → safe | 01-spec.md L159-175 | `agent-catalog.test.ts` (extractAgentFromPath('<script>alert(1)</script>') → null; javascript: → null) · `RibbonTab.test.tsx` (no dangerouslySetInnerHTML grep) | `ribbon-xss-guard.spec.ts` (3/3 GREEN; document.querySelector('script[data-injected]') == null) | n/a | T-1, T-3, T-5 | **PASS** |
| **SC-7** | a11y · keyboard WAI-ARIA tablist completo | 01-spec.md L177-196 | `Ribbon.test.tsx` § keyboard (15 tests: Arrow Right/Left circular wrap from Lisa↔ConfigTab + Home → idx 0 + End → idx 5 + Enter/Space → navigateTo + other keys no-op) · `RibbonTab.test.tsx` (tabIndex prop passthrough + focus-visible:ring-2) · `ConfigTab.test.tsx` (tabIndex + focus-visible) | `ribbon-keyboard.spec.ts` § SC-7-1..SC-7-6 (6 GREEN) + § SC-7-axe (2 GREEN: light + dark @axe wcag2aa 0 critical/serious) | `ribbon-keyboard-focus.png` | T-2, T-3, T-5 | **PASS** |
| **SC-8** | i18n · microcopy Spanish neutro verbatim | 01-spec.md L198-220 | `agent-catalog.test.ts` (5 tabLabels match glossary, Adrián tilde, Mi Clínica tilde) · arch `test-vitalia-ui-strings-no-voseo.test.ts` § F1-S7 EXTEND (Mi Clínica + Adrián tildes + voseo grep 0 matches on Ribbon/RibbonTab/ConfigTab/agent-catalog) | `ribbon-i18n.spec.ts` (3/3 GREEN, 11 verbatim strings) | (multiple visual goldens encode strings) | T-1, T-2, T-4, T-5 | **PASS** |
| **SC-9** | edge · Avatar PNG falla → fallback initial | 01-spec.md L222-237 | `RibbonTab.test.tsx` § Avatar fallback (AvatarFallback renders letter 'V'/'L'/etc + agentBgSoftClass on fallback for color identification) | `ribbon-avatar-fallback.spec.ts` (3/3 GREEN: page.route abort PNG → AvatarFallback initial + click navigates) | n/a | T-2, T-5 | **PASS** |

## Auxiliary scenario (out-of-spec, additional E2E coverage)

| SC | Title | E2E test | Tickets | Status |
|---|---|---|---|---|
| **SC-11** | empty-state (auxiliar) — equivalent to SC-4 idle | `ribbon-empty-state.spec.ts` (3/3 GREEN) | T-5 | **PASS** (redundant w/ SC-4 — bonus coverage, no harm) |

## NOT applicable sub-categories (justified)

Per 04-validators.yaml `sub_categories_coverage` + 01-spec.md L240-247:

- `race_condition` — N/A (no DB writes, no concurrent state mutation)
- `concurrent_users` — N/A (no shared cross-user state, URL is client-side derived)
- `network_failure` — N/A (no FE fetch; SC-9 cubre el único network dependency = PNG avatar)
- `large_dataset` — N/A (5 tabs fijos + ConfigTab, sin pagination)
- `empty_state` — N/A (lista estática; SC-4 cubre conceptual "active=null")

## Sub-categories mandatory v4.1 that apply

- ✅ `accessibility` — SC-7 + axe wcag2aa light + dark (2 specs, 0 critical/serious)
- ✅ `i18n` — SC-8 + arch voseo regex glossary scan

## Phase D Verdict

**Coverage:** 9 / 9 spec Gherkin scenarios fully mapped to ≥1 unit + ≥1 E2E test (where applicable per playwright_required). Total assertions per spec: ~32 unit assertions in agent-catalog + 23 unit in RibbonTab + 17 unit in ConfigTab + 39 unit in Ribbon + 11 unit in AppPanelSlot + 32 E2E behavior + 13 E2E visual + 2 E2E axe = **1328 unit + 32 E2E behavior + 13 visual + 2 a11y axe (light+dark) all GREEN per gate-output.json iter 5**.

**No scenario lacks coverage. Phase D PASS.**

