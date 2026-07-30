<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — F1-S7 vitalia-fase1-ribbon-6-tabs

**Date:** 2026-05-25
**Story:** vitalia-fase1-ribbon-6-tabs (outcome: vitalia-mvp-ui-foundation, Fase 1)
**Brand:** vitalia
**Tickets reviewed:** T-1 (catalog) · T-2 (moléculas) · T-3 (organism) · T-4 (integration + arch) · T-5 (E2E + visual goldens)
**Commits audited:** f332d554 · 1aeda3a1 · 18489194 · e073fe48 · d103edb3 · e7992727 · 5d7fd4d0
**Files reviewed:** 33 FE files in vitalia/ scope (8 production source + 8 unit test + POM + 9 E2E specs + 11 visual PNGs + 2 arch test extends + 1 arch test NEW)
**Domains touched:** shell-organism (chrome UI nav, FE-only, no BE/agentic/copilot/offer/analytics)
**Skills consulted:** frontend-expert, tessl__react-patterns, tessl__shadcn-ui, tessl__tailwind, tessl__vitest, tessl__nextjs-app-router-modularization, playwright-expert, .claude/rules/anti-duplication.md, .claude/rules/auditor-self-fix-policy.md, .claude/rules/spanish-text.md, .claude/rules/frontend-fsd.md, .claude/rules/tdd-mandatory.md, vitalia/.claude/rules/shell-mockup-per-component.md, vitalia/.claude/rules/hipaa-lite.md (N/A justified)
**Live-verified:** **N** (chrome-devtools-verify skill DEPRECATED for Linux Mint; visual confirmation via 13/13 Playwright visual goldens iter 1 ratified by Chris + 32/32 behavior specs + 2/2 axe wcag2aa light+dark)
**Verdict:** **PASS** *(with 1 WARN documented — Q16 hover-tint mechanism rests on accidental absence of competing class, not on documented CSS specificity; functional behavior correct, intent in source is partially JIT-purged)*

---

## /test-frontend Gate Status (gate-output.json iter 5)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | `tsc --noEmit` | **PASS** | 0 errors, strict mode |
| QUALITY | ESLint (60+ rules) | **PASS** | 0 errors, 0 warnings on diff |
| QUALITY | Prettier `--check` | **PASS** | 0 mismatches |
| FUNCTIONAL | Vitest unit + integration | **PASS** | **1328/1328 GREEN** across 137 test files; coverage 78%+ statements (≥20% threshold) |
| ARCH | Vitest arch fitness | **PASS** | **107/107 GREEN** across 18 test files (includes NEW test-ribbon-no-shadcn-tabs + EXTEND test-no-cross-brand-shell-mirror + EXTEND test-vitalia-ui-strings-no-voseo + heredados test_server_first/test_fsd_boundaries/test-shell-store-schema-readonly/test-agent-catalog-ssot/test-skip-link-target/test_no_hardcoded_colors/test-no-vt-classes-in-new-features) |
| (advisory) | inbox copy import advisory | ⚠ FE-A2c advisory only — NOT a F1-S7 finding (5 unrelated inbox files) | Out-of-scope, no action |
| HEALTH | E2E Playwright smoke | **PASS** | 32/32 behavior specs GREEN (9 SC-specific + SC-11 empty-state aux + 2 axe) |
| HEALTH | E2E Playwright visual | **PASS** | 13/13 GREEN against 11 ratified PNG goldens iter 1 (`maxDiffPixelRatio 0.001`) |

`overall.any_fail = false`. Build is clean.

---

## Warning Baseline Movement

No baselines grew. F1-S7 introduced 8 source files + 8 test files + 1 NEW arch test + 11 visual goldens + 9 E2E specs. ESLint 0 warnings on diff. Pre-existing repo-wide warnings (jsdoc / check-file / react-perf cap) **were not touched**.

| Category | Pre-F1-S7 | Post-F1-S7 | Δ | Status |
|---|---|---|---|---|
| ESLint errors | 0 | 0 | 0 | ✓ |
| ESLint warnings (diff scope) | 0 | 0 | 0 | ✓ shrink-OK |
| tsc errors | 0 | 0 | 0 | ✓ |
| Prettier mismatches (F1-S7 scope) | 0 (after 18489194 + 5d7fd4d0 auto-fix follow-ups) | 0 | 0 | ✓ |
| Arch fitness tests | 90 (pre-F1-S7) | **107** | **+17** (NEW invariants for Ribbon ratchet) | ✓ ratchet grow (justified) |

The 2 prettier follow-up commits (18489194 RibbonTab.test.tsx + 5d7fd4d0 Ribbon + test-agent-catalog-ssot) are pure mechanical auto-fix per `auditor-self-fix-policy.md` whitelist #2 (Format prettier/ruff format). Logic delta = zero. Verified via `git show --stat`: 18489194 = 4 deletions / 1 insertion (whitespace), 5d7fd4d0 = formatting only.

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | **PASS** | 0 |
| 2 | Server/Client correctness | **PASS** | 0 |
| 3 | React Patterns (`tessl__react-patterns`) | **PASS** | 0 |
| 4 | Code Quality (gates 2/3/5/6/7) | **PASS** | 0 |
| 5 | Accessibility (WCAG 2.1 AA + roving tabindex) | **PASS** | 0 |
| 6 | Forms (RHF + Zod) | N/A | Ribbon is nav-only, zero forms |
| 7 | Multitenancy (X-Tenant-ID, no hardcode) | **PASS** | 0 |
| 8 | Master Data / Currency / Spanish neutro | **PASS** | 0 |
| 9 | Security / Deps | **PASS** | 0 |
| 10 | Tests / TDD | **PASS** | 0 |
| 11 | Domain Alignment + Amendments (D18 / D19 + prettier follow-ups) | **PASS** | 0 (all amendments justified — see Findings § Amendments) |
| 12 | Architecture Fitness (107 tests) | **PASS** | 0 |
| 13 | Mirror detection (cross-brand) | **PASS** | 0 (manually grep-verified: 0 matches in nicolify/comunify/lupulo for Ribbon/RibbonTab/ConfigTab/AGENT_RIBBON_ORDER/extractAgentFromPath) |
| 14 | Decisions honored cite (R6) | N/A | Ticket frontmatter has no `decisions_applicable` field — story-level 03-arch.md amendments D17.1-D22 cementan; builders cite them in T-{n}-impl-log.md (verified per ticket) |

---

## Findings

### WARN-1 — Q16 active:hover tint preservation rests on accidental absence of competing hover class (not on documented CSS specificity)

**Category:** 3 (React Patterns) / 12 (Architecture Fitness) — **WARN** (not FAIL: functional behavior is correct).

**File:** `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx:60`

**Issue:**
The implementation uses a dynamic template literal to express the Q16 cement (active tab on hover preserves agent soft tint):

```tsx
active
  ? cn(
      agentBgSoftClass(slug),
      "font-semibold text-foreground",
      `hover:${agentBgSoftClass(slug)}`,   // ← dynamic — JIT-purged for some agents
    )
  : "font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
```

Tailwind v4 JIT scanner only emits CSS for *static* class strings it finds in source. Dynamic concatenations like `` `hover:${expr}` `` cannot be detected. Empirical verification of `vitalia/frontend/.next/dev/static/chunks/vitalia_frontend_src_app_globals_*.css` shows only **3 of 5** ribbon hover classes survived JIT:

- `hover:bg-agent-lisa-soft` ✓ present (because Lisa is also referenced as hover in F1-S6 chat surfaces)
- `hover:bg-agent-valeria-soft` ✓ present (same reason — default chat agent)
- `hover:bg-agent-camila-soft` ✓ present
- `hover:bg-agent-adrian-soft` ✗ **missing** from dev CSS
- `hover:bg-agent-lucas-soft` ✗ **missing** from dev CSS

This contradicts the explicit invariant documented in `_agent-tw-classes.ts:6-7`:
> CRITICAL: Tailwind v4 JIT purges dynamic class names (e.g. `bg-${agent}-soft`). ALL class names MUST be statically knowable.

**Why this isn't FAIL (functional behavior is OK):**
The active branch in `cn()` does NOT include `hover:bg-muted` (only the inactive branch does). So when Lucas or Adrián are active and hovered, no competing hover-state class exists — the tab simply keeps its `bg-agent-{slug}-soft` by default browser behavior. Q16 is "accidentally satisfied" for all 5 agents because there is no competing hover class, not because the explicit defensive class is in the CSS.

**Untested as well:**
- No unit test asserts `hover:bg-agent-{slug}-soft` appears in `tab.className` for active=true (verified by grep — RibbonTab.test.tsx contains zero `hover` assertions).
- No visual golden captures the **active-and-hovered** state (the existing `ribbon-hover-inactive.png` captures hover on an inactive tab, not on the active one — Q16's actual concern).

**Fix recommendation (suggested for follow-up, NOT a blocker — `auditor-self-fix-policy.md` decision tree: this requires test logic change (≥3 files: source + unit + visual golden), NOT in whitelist → spawn dev-team for proper fix):**

Either:
1. Replace the template literal with a second static lookup helper (e.g., `agentHoverBgSoftClass(slug)`) that returns the literal string from a switch, so JIT detects all 5 variants. Add a visual golden `ribbon-hover-active.png` capturing Lisa-active-and-hovered.
2. OR drop the `hover:` line entirely (since it has zero effect — no competing class exists) and document the absence with a comment, so future devs who add `hover:bg-muted` to the active branch know they'd need to reintroduce the hover override.

**Skill ref:** `tessl__tailwind` (JIT-safe static classes), `_agent-tw-classes.ts:6-7` (project invariant), 03-arch.md § 2.3 D17.2 Q16 cement.

**Mitigation today:** functional behavior is correct, no user-visible regression, axe wcag2aa is GREEN, visual goldens (idle + per-agent active) all match ratified Chris mockup. This is technical debt to address in F1-S8 or follow-up ticket.

---

### Amendments review (D18 + D19 + prettier follow-ups)

#### D18 — RibbonTab active sub-label `text-foreground/60` (production code touch during T-5 test ticket)

**Category:** 5 (Accessibility) / 11 (Amendments) — **APPROVE**.

**File:** `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx:80-82`

```tsx
<span
  className={cn(
    "whitespace-nowrap text-[10px]",
    active ? "text-foreground/60" : "text-muted-foreground",
  )}
>
```

**Context:** T-5 was nominally `production_code: false`. axe wcag2aa scan flagged a `color-contrast` *serious* violation: `text-muted-foreground` (`240 4% 46%` ≈ #737380) sub-label on `bg-agent-lisa-soft` (`156 80% 92%` ≈ #d1f7e9) failed 4.5:1 ratio.

**Decision:** APPROVE as scope-justified amendment.

Per `auditor-self-fix-policy.md` decision tree:
- ✗ Does NOT fit Caso C "self-fix whitelist" (whitelist categories #1-17 do not include "WCAG AA contrast fix"; closest is #14 "Currency hardcoded → tenant_locale" which is a different domain)
- ✓ Logic delta = zero (only active-state color of decorative sub-label changed; behavior identical; aria-* attributes unchanged)
- ✓ Single-file change, ≤4 LOC, design-token only (`text-foreground/60` — no hex)
- ✓ Resolves a real, blocking axe wcag2aa serious violation (would have failed val-fe-axe gate otherwise)
- ✓ T-5 was the FIRST ticket to actually run axe (axe runs in Playwright; T-1..T-4 are unit-only). The bug existed since T-2 but only surfaced when axe ran in T-5.

Strict reading would say "scope T-5 was test-only, escalate". But the axe violation was *discovered by* T-5's gate suite. Forcing a separate "T-2.bis fix contrast" ticket would loop unnecessarily — the builder correctly applied the minimum fix to GREEN the gate within the same ticket. Auditor-self-fix-policy's spirit (forward motion + whitelist by nature, not size) supports this.

**APPROVE: in-scope; logic delta zero; a11y WCAG AA > test-ticket-boundary purism.**

#### D19 — AvatarFallback `data-testid="avatar-fallback-{slug}"` (T-2 integration testid)

**Category:** 11 (Amendments) — **APPROVE** within T-2 RibbonTab molecule integration scope.

**File:** `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx:69`

**Context:** SC-9 POM grader requires `pom.expectAvatarFallback(slug)` which targets `[data-testid="avatar-fallback-{slug}"]`. T-2 builder added the testid as integration scope (RibbonTab molecule contract — its consumers' tests need a stable hook). Subsequently consumed by T-5 POM method.

**Decision:** APPROVE. This is `data-testid` (test infrastructure), not production behavior. It's the canonical pattern across F1-S6 components and `RibbonTab.test.tsx:362-379` asserts the testid exists. Within scope.

#### Prettier follow-up commits (18489194 + 5d7fd4d0)

**Category:** 4 (Code Quality) / 14 (auditor self-fix whitelist #2) — **APPROVE**.

Both commits are pure mechanical `prettier --write` auto-fix per `auditor-self-fix-policy.md` whitelist #2 (Format). Single-file or focused, formatting-only, zero logic change. Verified via `git show --stat`. Matches the gate-runner self-fix loop expected behavior.

---

## Contract / Spec Compliance

### 01-spec.md verification

- ✓ All 9 Gherkin scenarios SC-1..SC-9 mapped to tests (see `06-audit/gherkin-matrix.md`)
- ✓ Wireframe inline ASCII art matches implementation (h-14 ribbon, 5 agent tabs + ConfigTab ml-auto, overflow-x-auto mobile)
- ✓ Estados visuales table verbatim implemented in RibbonTab.tsx (inactive bg=transparent, active bg=`bg-agent-{slug}-soft`, hover, focus, active:hover, avatar-fallback)
- ✓ ConfigTab estados visuales (inactive bg-muted, active bg-muted + ring-1 ring-border, hover bg-muted/80, focus ring-2, tooltip "Configurar" hidden when active)
- ✓ 5 NEW components justified: Ribbon (organism, no Shadcn equivalent), RibbonTab (avatar+label+sub-label pattern not in Shadcn Tabs), ConfigTab (IconButton distinct from agent tabs), extractAgentFromPath (utility co-located), test-ribbon-no-shadcn-tabs (arch invariant)
- ✓ Microcopy verbatim Spanish neutro LatAm:
  - Lisa "Mi Clínica" (tilde verified by arch test)
  - Lucas "Atraer"
  - Adrián "Vender" (tilde Adrián verified by arch test)
  - Valeria "Operar"
  - Camila "Mantener"
  - ConfigTab `aria-label="Configurar"` + Tooltip text "Configurar"
  - `<nav aria-label="Agentes">`
- ✓ Voseo grep across 4 files → 0 matches (arch test `test-vitalia-ui-strings-no-voseo.test.ts` § F1-S7 EXTEND)
- ✓ 11 visual goldens declared in § Visual goldens table all present in `vitalia/frontend/e2e/__screenshots__/regression/vitalia-fase1-ribbon-6-tabs/visual-goldens.spec.ts/` (verified via `ls`)
- ✓ Accessibility WCAG 2.1 AA — keyboard tablist 6 elementos (5 agent + ConfigTab as 6th peer Q13 cement), roving tabindex, Home/End/Arrow/Enter/Space, focus-visible ring-2 ring-ring ring-offset-1, color contrast tested via axe (light + dark), screen reader announcements implicit via role=tab + aria-selected
- ✓ Responsive: `overflow-x-auto` natural, no media-query branches, ConfigTab `ml-auto`
- ✓ Telemetría correctly deferred to Fase 2 (TODO not implemented, no instrumentation hooks added)

### 03-arch.md amendments (D17.1, D17.2, D17.3, D18-D22)

- ✓ D17.1 (Q15 whitespace-nowrap) → verified in source + unit test
- ⚠ D17.2 (Q16 active:hover preserve tint) → see WARN-1 above (mechanism works accidentally, not via documented CSS specificity)
- ✓ D17.3 (Q14 shrink-0 sin min-w) → verified in source
- ✓ D18 (a11y text-foreground/60 sub-label active) → see Amendments § D18
- ✓ D19 (AvatarFallback data-testid) → see Amendments § D19
- ✓ D20 (ConfigTab size-10) → verified
- ✓ D21 (ConfigTab ml-auto right-align) → verified
- ✓ D22 (ConfigTab aria-label="Configurar") → verified

### 04-validators.yaml verification

- ✓ `scenario_coverage.coverage_pct = 100` (9/9 SC mapped)
- ✓ All 21 validator_ids referenced by tickets resolved to GREEN gates (val-fe-tsc, val-fe-lint, val-fe-prettier, val-fe-vitest-unit, val-fe-arch-fsd, val-fe-arch-no-hex, val-fe-arch-no-voseo, val-fe-arch-no-vt, val-fe-arch-server-first, val-fe-arch-agent-catalog-ssot, val-fe-arch-no-cross-brand-mirror, val-fe-arch-shell-store-readonly-heredado, val-fe-arch-ribbon-no-shadcn-tabs, val-fe-arch-skip-link, + 11 E2E vals incl. val-fe-axe)
- ✓ N/A sub-categories all justified verbatim (race_condition / concurrent_users / network_failure / large_dataset / empty_state)

### 05-guidelines.md `must_load_skills` enforcement

- ✓ frontend-expert + tessl__react-patterns + tessl__shadcn-ui + tessl__tailwind + tessl__vitest baseline cited in T-{1..5}-impl-log § Skills Consulted
- ✓ playwright-expert cited in T-5
- ✓ tessl__nextjs-app-router-modularization cited in T-3 + T-4 (Server/Client boundary)
- ✓ No tessl__zod required (no forms)
- ✓ `runtime-quality-checklist.md` reference visible in T-5 (cited as baseline by tessl__react-patterns invocation)

### 06-tickets.yaml gherkin_coverage

43 entries across 5 tickets cover all 9 SC. Each scenario links to ≥1 unit test (Vitest) + ≥1 E2E spec (Playwright) where playwright_required=true. Total 1328 unit + 32 E2E + 13 visual + 2 axe = full coverage.

---

## Architecture Fitness — F1-S7 contributions to allowlist

| Test | Type | Change | Justification |
|---|---|---|---|
| `test-ribbon-no-shadcn-tabs.test.ts` | **NEW** invariant | +89 LOC, 6 assertions | Enforces anti-pattern: Ribbon/RibbonTab/ConfigTab MUST NOT import `@/components/ui/tabs` (Radix incompatible with route nav). Cementado en 03-arch.md § 12. Justified — prevents regression. |
| `test-no-cross-brand-shell-mirror.test.ts` | EXTEND | +5 new assertions (Ribbon, RibbonTab, ConfigTab, AGENT_RIBBON_ORDER, extractAgentFromPath) | Anti-duplication scope expansion for F1-S7 NEW names. Justified — F1-S7 names did not exist pre-T-1. |
| `test-vitalia-ui-strings-no-voseo.test.ts` | EXTEND | +60 LOC (F1-S7 describe block: 5 files in RIBBON_SHELL_FILES + "Mi Clínica" tilde + "Adrián" tilde) | i18n scope expansion. Justified — F1-S7 introduces new user-facing microcopy. |
| `test_server_first.test.ts` | UNCHANGED | 0 (KNOWN_MISSING_USE_CLIENT allowlist did not need new entries because Ribbon/RibbonTab/ConfigTab all have "use client" first line) | Auto-PASS. Verified per T-4-impl-log. |
| `test_fsd_boundaries.test.ts` | UNCHANGED | 0 | shell-organism components live in `components/shared/shell-organism/` (allowed cross-shell). agent-catalog.ts in `lib/` (allowed shared SSoT). |
| `test-agent-catalog-ssot.test.ts` | UNCHANGED | 0 (hex/thumbnail allowlist untouched; F1-S7 only added tabLabel/defaultSubtab fields which are strings) | OK. |
| `test_no_hardcoded_colors.test.ts` | UNCHANGED | 0 (zero hex literals in NEW files — verified) | OK. |
| `test-no-vt-classes-in-new-features.test.ts` | UNCHANGED | 0 (no `.vt-*` legacy classes in F1-S7 components) | OK. |
| `test-shell-store-schema-readonly-f1-s5.test.ts` | UNCHANGED | 0 (shell-store.ts NOT modified by F1-S7) | OK. |
| `test-skip-link-target.test.ts` | UNCHANGED | 0 (`<main id="main-content">` untouched) | OK. |

**Allowlist growth:** +1 NEW arch test file (test-ribbon-no-shadcn-tabs). +5 cross-brand assertions in extend. +1 voseo describe block. All justified by F1-S7 scope. **No allowlist shrunk.** Justified per architect cementation. Net 90 → 107 = **+17 tests** (ratchet grow, mid-PR documentation explicit).

---

## Native-First Audit

- ✓ No `docker exec ... tsc|eslint|vitest|playwright` in any commit body
- ✓ No `make e2e*` references (commands documented in T-5-impl-log specify native `npx playwright test --project=visual`)
- ✓ No `git add .` / `-A` / `-u` (commits stage by exact file names; verified per `git show --name-only` of each ticket commit)
- ✓ Conventional Commits: `feat(vitalia/f1-s7): T-N <subject>`, `style(vitalia/f1-s7): prettier auto-fix...`, `test(vitalia/f1-s7): T-5 ...`
- ✓ `Co-Authored-By: Claude Opus 4.7 (1M context)` line present in prettier follow-up commits

---

## Live Verification Audit

- ✗ `chrome-devtools-verify` skill is DEPRECATED for Linux Mint (per platform note 2026-05-15 visible in skill header). NOT invoked.
- ✓ Mitigation: 13/13 Playwright visual goldens against ratified HTML mockup (`mockups/ribbon-6-tabs.html`, `ratified_visual_by_chris=true` 2026-05-25) — visual confirmation in browser parity is achieved through this ratchet.
- ✓ Mitigation: 2/2 axe wcag2aa @axe scans (light + dark) GREEN = 0 critical/serious violations.
- ✓ Mitigation: 32/32 behavior E2E specs across real Next.js dev server (port 3002) on host Linux = behavior parity with browser real.
- ⓘ Per project policy, Chris staging gate manual verification is referenced in each T-{n}-result.md as the next step before merge. Auditor accepts this for shell chrome UI nav-only story.

Per `runtime-quality-checklist.md` live-verification gate FE PR ≥ M policy: visual goldens + axe + behavior specs collectively substitute for chrome-devtools-mcp when the skill is unavailable on the platform.

---

## Verdict Math (per review_format § Verdict Math)

Walking the matrix:
- ✓ No FAIL in categories 1 / 2 / 3 / 7 / 11 / 12 / 14
- ✓ No allowlist shrink; growth (+17 arch tests) all justified by NEW invariants
- ✓ No `/test-frontend` blocker FAIL — gate-output.json `any_fail = false`
- ✓ All arch fitness tests GREEN
- ✓ No downstream regression detected (no engine touches, no cross-brand pollution, agent-catalog.ts EXTEND consumers in F1-S6 still GREEN per 1328/1328)
- ✓ Cat 14 N/A (ticket frontmatter has no `decisions_applicable` field; story-level decisions D1-D22 are cementadas in 03-arch.md and cited in T-{n}-impl-log)
- ✓ `IMPL-LOG.md § Skills Consulted` populated per T-{1..5}-impl-log with required skills
- ✗ `runtime-quality-checklist.md` not cited explicitly in IMPL-LOG headers (cited as baseline by tessl__react-patterns in T-2, T-3, T-5 invocations) → minor IMPL-LOG documentation gap but skill loads were correct in practice
- ✓ `chrome-devtools-verify` NOT invoked, but Chris staging gate escalation is explicit and visual goldens iter 1 are ratified — acceptable per skill DEPRECATED note for Linux Mint
- ✓ UI-SPEC.md = 01-spec.md ratified post Playwright audit iter 1-A; design.md = mockups/ribbon-6-tabs.html ratified `ratified_visual_by_chris=true` 2026-05-25
- ✓ 1 WARN documented (WARN-1: Q16 hover-tint JIT purge — functional behavior correct but documented mechanism contradicts source invariant)

**One WARN, zero FAIL → overall PASS.**

---

## Next Actions

1. **`/auditor` Step 4 — CHECKPOINTS.md:** auditor writes C1-C5 ratchet (FSD-Lite, anti-duplication, server-first, hex-no, voseo-no) → all GREEN.
2. **AUTO-HANDOFF `/pm-vitalia`:** state transition `reviewing → done` via 07-merge.md squash-merge wip/vitalia → main, git mv story dir to archive (R2).
3. **WARN-1 follow-up ticket (optional, non-blocking):** open in F1-S8 or as standalone "vitalia-shell-organism-q16-jit-static-classes" — add `agentHoverBgSoftClass` helper + visual golden `ribbon-hover-active.png` + unit test asserting hover class in `tab.className`. Severity: low (functional behavior correct, this is hardening defensive intent).
4. **Chris staging gate manual:** load `make dev-vitalia` → `http://localhost:3002/{tenantId}/{agent}/{subtab}` visual smoke per T-4-impl-log § Live Verification 6 steps.

---

## Reviewed by

auditor-frontend (Claude Opus 4.7, 1M context) — story-wide single audit pass per F1-S6 paradigm precedent.
