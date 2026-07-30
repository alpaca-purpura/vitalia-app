<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: Shell dual-mount + a11y fix (single-main + single-slot)

**Date:** 2026-06-01
**Story:** vitalia-shell-dual-mount-a11y-fix (bugfix arquitectónico, ADR-011)
**Tickets:** T-1 (production fix · `b65baae6`) + T-2 (live-verify spec · `bfb6d418`)
**Brand:** vitalia
**Files Reviewed:** 3 code (1 prod + 1 unit test + 1 live spec) + 4 docs
**Domains touched:** shell-organism (FE chrome, no agentic, no PHI, no BE)
**Skills consulted:** frontend-expert, vitalia-design-system (shell SSoT), tessl__react-patterns (hook-count stability), tessl__vitest, playwright-expert (live spec)
**Live-verified:** YES — `single-slot-live.spec.ts` autenticado contra stack real (FE:3002 + BE:8002), Clerk testing token, SIN backend mocks; 6 passed. Evidence en `checkpoint.dev_app_verified.evidence` (honesta: writes/navegación real ejercida + DOM `.count()` + console capture + axe, NO "GET 200").
**Verdict:** **APPROVED**

## /test-frontend Gate Status (consumed from gate-output.json — fresh, post bfb6d418)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit | PASS | exit 0, 0 errors strict |
| QUALITY | ESLint (changed files) | PASS | exit 0, 0 errors/warnings |
| QUALITY | Arch fitness (skip-link) | PASS | 2/2 (independently re-run) |
| FUNCTIONAL | Vitest shell-organism | PASS | **31 files / 501 tests** (independently re-run — confirmed) |
| FUNCTIONAL | Playwright live-verify | PASS | 6 passed (2 setup + 4 live), real stack no-mock |

`overall.any_fail = false`. Gate-output `generated_at` (11:55) is newer than both commits (10:22 / 10:51) → fresh, no re-spawn of gate-runner needed.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns (hook-count) | PASS | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | 0 — the a11y fix itself |
| 6 | Forms (RHF + Zod) | N/A | no forms touched |
| 7 | Multitenancy | PASS | 0 — chrome, no queries |
| 8 | Master Data / Spanish | PASS | 0 — no voseo |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 — strict RED→GREEN, not weakened |
| 11 | Domain Alignment / Agentic UI | PASS | 0 — shell SSoT honored |
| 12 | Architecture Fitness | PASS | skip-link 2/2; mirror failures PRE-EXISTING (not this diff) |
| 13 | Mirror detection | PASS | brand-local pattern applied, file NOT shared |
| 14 | Decisions honored cite (R6) | N/A | no `decisions_applicable` in 06-tickets |
| 15 | Connectivity (anti-isla) | PASS | mount pre-existing (layout.tsx), not disconnected |
| 16 | Visual fidelity | PASS | no primitives reinvented; live + axe verified |

## Critical-focus findings (per orchestrator brief)

**1. Root cause resolved WITHOUT reintroducing the hooks crash — CONFIRMED.**
`ShellOrganismLayoutClient.tsx`:99-170 — ALL hooks (`useStoreHydration`, 2× `useShellStore` selectors, `useViewportGuard`, `useRef`, 2× `useState`, 2× `useEffect`, `useGroupRef`, `useDefaultLayout`) are called unconditionally at the top, before any branch/early-return. The `shellMode` ternary (line 215) lives in JSX only — zero hooks inside the branches → hook-count identical across renders. `<Group>` is always mounted (line 228), never gated by `isDesktop`/`useMediaQuery` (D4 honored: `useMediaQuery` not imported). This is exactly the nicolify lesson applied. (tessl__react-patterns: Rules of Hooks invariant satisfied.)

**2. Single `<main>` + single `<AppPanelSlot>` guaranteed across all viewports/modes — CONFIRMED.**
- D1: one `<main id="main-content" tabIndex={-1} aria-label="Contenido principal">` (line 207) wraps all chrome; `containerRef` + `data-shell-ready` live there.
- D2: `<AppPanelSlot>` appears physically once per branch — agentic (line 280), web (line 300). Branches are XOR by `shellMode`; only one renders at runtime. NO separate mobile branch (the nicolify residue). Mobile responsiveness = CSS `hidden md:flex`/`hidden md:block` on the Valeria *containers* (lines 247, 256, 294, 298), never on the slot. Net: 1 slot in DOM, any viewport.
- Verified in REAL DOM by `single-slot-live.spec.ts` `.count() === 1` across agentic-desktop / web-desktop / mobile (not just jsdom).

**3. Rewritten unit tests assert single-main + single-slot for real — NOT weakened. CONFIRMED.**
The OLD test (`735a1fa8`) used `toBeGreaterThanOrEqual(1)` for mains/slots/children (lines 264/284/385/398) — those WOULD pass with the buggy 2× dual-mount (masked the bug). The NEW test uses strict `.toBe(1)` for `#main-content`, `app-panel-slot`, and `unique-child` in BOTH agentic and web modes (test lines 177/189/202/215/227). This is a genuine tightening producing a correct RED against the old component → GREEN against the fix. Assertions are honest.

**4. Scope discipline — CONFIRMED.** `git diff 735a1fa8..bfb6d418` code surface = only `ShellOrganismLayoutClient.tsx` + its test + the live spec. `AppPanelSlot.tsx`/`.test.tsx` untouched; `useMediaQuery.ts`, `useViewportGuard.ts`, `ValeriaSidebar.tsx`, `Ribbon.tsx`, `ShellOrganismLayout.tsx` wrapper, `components/ui/`, `features/*` all untouched. No core/, no cross-brand. All paths under `vitalia/`.

**5. Visual fidelity / FSD / Spanish — PASS.** No primitive reinvented; tokens/aria preserved. Spanish strings neutral (`Contenido principal`, `Redimensionar paneles`, `Panel Valeria`, `Panel aplicación`) — voseo grep clean.

**6. a11y axe scope correct — PASS.** Live spec scopes axe to the fix's rule families (`duplicate-id`, `duplicate-id-aria`, `landmark-unique`, `landmark-no-duplicate-banner`) = 0 violations — exactly the symptom (3× `id="main-content"` + dup landmarks). Out-of-scope pre-existing shell violations correctly not gated.

## Downstream regression scope (.claude/rules/auditor-downstream-regression.md)

| Surface | downstream_test_targets | Status |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` (rendered for ALL 5 agents + Valeria — transversal blast radius) | full shell-organism vitest suite + live spec | PASS — 31 files/501 tests + 6 live (independently re-run) |

The component header declares `downstream-regression-na: brand-local shell component; no cross-brand consumers` — correct: it is FE brand-local, consumed only within vitalia via `(shell-organism)/layout.tsx`. No core engine edit, no cross-brand import. Transversal coverage (5 agents × 3 modes) is the right downstream set and is GREEN.

## Architecture fitness — cross-brand mirror failures (NOT a blocker)

`test-no-cross-brand-shell-mirror.test.ts` reports 23 failures (`SubTabMeta`, `Ribbon`, `extractSubtabFromPath` matched in nicolify). Verified PRE-EXISTING: the story diff touches NONE of those symbols (`git diff` grep empty); they originate from the nicolify R0 shell rebuild already in origin/main. Per orchestrator brief + `.claude/rules/auditor-downstream-regression.md`, this is a `/pm-luana` finding (cross-brand lift review), NOT introduced by this fix → NOT blocked here. The skip-link arch test (the gate this fix could break) passes 2/2.

## Native-First Audit
- No `docker exec ... tsc|eslint|vitest|playwright` — gates ran via npx native. PASS.
- No `make e2e` / `make e2e-smoke` — live spec ran via `npx playwright` (auth.fixture). PASS.
- Commits staged by pathspec (2 files / 5 files) — no `git add .`. PASS.

## Live Verification Audit
- User-facing surface (shell of all agents) → live-verify evidence present + honest (real stack, no mocks, real backend hit, DOM count + console + axe). PASS — exceeds the bar (ADR-vitalia-008 / Critical Rule #37).

## Verdict Math
- Categories 1/2/3/7/11/12 all PASS; Cat 14 N/A; no allowlist/baseline growth; all gate blockers PASS; skip-link arch PASS; downstream transversal PASS; live-verify honest. Mirror failures pre-existing (out of scope, /pm-luana). → **overall APPROVED**.

## Self-fix log
None — gates green, no mechanical fix required (Carril A not invoked).

## Suggested learning capture (advisory, ≥2 stories pattern)
The "weak assertion masks the bug" anti-pattern (old test used `toBeGreaterThanOrEqual(1)` where the bug produced 2) is a recurring shell-test smell (also seen in lisa-marca mocked-backend false-verde). Candidate for `vitalia/docs/learnings/` if it recurs once more.
