<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: vitalia-shell-state-persistence (consolidated T-1..T-5)

**Date:** 2026-05-28
**PR / spec / arch:** `vitalia/docs/product/stories/vitalia-shell-state-persistence/{01-spec.md,03-arch.md,04-validators.yaml}` · ADR-vitalia-006
**Files Reviewed:** 25 (vitalia/frontend) · diff da0602ea~1..HEAD scoped to story commits
**Domains touched:** shell-organism (Valeria chrome), lib/store factory, features/valeria/store, stores/
**Skills consulted:** frontend-expert (FSD-Lite + runtime-quality), tessl__react-patterns (hydration/effects/a11y), tessl__zustand-via-frontend-expert, playwright-expert (E2E SC-1..SC-8)
**Live-verified:** N/A acceptable — change is invisible (persistence + SSR timing); SC-1..SC-8 E2E + axe wcag2aa cover observable contract; no new visual component (mockup gate exempt, ratified Chris). Chrome-devtools live check not required for this class.
**Verdict:** **APPROVED (PASS)**

## /test-frontend Gate Status (consumed from gate-output.json — fresh, head bf03639c, any_fail=false)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit | PASS | 0 errors strict |
| QUALITY | ESLint (60+ rules) | PASS | 0 errors |
| QUALITY | Arch fitness (148 tests) | PASS | FSD boundaries; no-store-in-skeleton; no cross-brand mirror |
| FUNCTIONAL | Vitest | PASS | 2310/2310 tests, 211 files |
| FUNCTIONAL | E2E (smoke) | PASS | 28/28, 19.4s (Clerk teardown warnings benign) |
| HEALTH | jscpd/knip/madge/audit | n/a in gate-output | not flagged; no new cycles introduced by lib/store |

scenario_coverage: SC-1..SC-8 + SC-5b all PASS.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 (lib/store no feature imports; named exports only; no new madge cycle) |
| 2 | Server/Client | PASS | 0 (skeleton store-free; "use client" only on leaf interactive nodes) |
| 3 | React Patterns | PASS | 0 (ref-guarded rehydrate; viewport guard cleanup; stable selectors) |
| 4 | Code Quality | PASS | 0 (2 justified `as any` casts for persist generic mismatch + eslint-disable w/ explanation) |
| 5 | Accessibility | PASS | 0 (SC-8 axe wcag2aa both states; focus return; aria-expanded/modal) |
| 6 | Forms (RHF+Zod) | n/a | no forms in scope |
| 7 | Multitenancy | PASS | 0 (no API; tenant-store signout cleanup intact) |
| 8 | Master Data / Spanish | PASS | 0 (aria-label "Abrir/Cerrar panel Valeria" neutro, no voseo; SC-8d asserts) |
| 9 | Security / Deps | PASS | 0 (no dangerouslySetInnerHTML/eval; HIPAA: UI prefs only, no PHI) |
| 10 | Tests / TDD | PASS | 0 (RED-first per impl logs; factory 19 assertions non-vacuous; SC-3 genuinely instruments setItem) |
| 11 | Domain Alignment | PASS | 0 (shell-organism contract honored; ADR-vitalia-004 N/A — no new sub-tab) |
| 12 | Architecture Fitness (148) | PASS | 0 — incl. self-corrected test_server_first (allowlist back to empty) |
| 13 | Mirror detection | PASS | 0 (factory vitalia-local; nicolify dismiss-store NOT mirrored — lift candidate only) |
| 14 | Decisions honored cite | PASS | T-* result md + commit bodies cite ADR-vitalia-006 D1-D6; D5 mobile slice cited verbatim |

## Audit-focus findings (all PASS — no blockers)

### PASS: Fix is REAL, not masked (focus #1)
`create-ssr-safe-persisted-store.ts:132-138` — `setItem` is a genuine NO-OP while `getHydrated()===false`, reading a stable `hydrationRef`. This cuts the spurious default write **at the source**, independent of timing/StrictMode — exactly the gap the 4 failed techniques (00-research.md) left open (they all left setItem active). NONE of the forbidden techniques is the actual mechanism: skipHydration:true is used but the no-op-storage is the load-bearing piece. SC-3 E2E (`valeria-state-survives-reload.spec.ts:140-183`) instruments `setItem` and asserts ZERO `valeriaState='full'` writes when 'rail' was seeded — genuine adversarial assertion, not stubbed. Factory unit test (19 `expect`, spies `Storage.prototype.setItem`) confirms no-op pre-hydration + writes post-rehydrate + `_hasHydrated` flip.

### PASS: Skeleton store-free (focus #2)
`ShellOrganismLayout.tsx:61` renders `<TopBarGlobal variant="skeleton" />` outside the `ssr:false` boundary; `TopBarGlobal.tsx:145-190` skeleton variant takes no store selector. Arch guard `no-store-in-ssr-skeleton.test.tsx:83-90` spies `useShellStore` and asserts NOT called in skeleton AND called in interactive (regression guard) — non-vacuous.

### PASS: Mobile slice independence (focus #3)
`mobileDrawerOpen` is an independent persisted field (shell-store.ts:65,100). Burger sets `setMobileDrawerOpen(true)` (TopBarGlobal.tsx:78), NOT setValeriaState. Drawer renders on `isMobile && mobileDrawerOpen` (ValeriaSidebar.tsx:170), NOT derived from valeriaState/isExpanded. useViewportGuard no-ops at <768 (does NOT touch valeriaState). Regression-lock SC-4 "desktop full does NOT auto-open mobile drawer" (mobile-collapsed-default.spec.ts:92-122) is genuine.

### PASS: Transversal correctness (focus #4)
tenant/agenda/agenda-filters migrated to factory with IDENTICAL partialize (activeTenant / drawerWidth / lastView). tenant-store keeps version:1 + signout cleanup (useSignOutCleanup + clearStore + removeItem) intact.

### PASS: FSD-Lite / no cross-brand / engine (focus #5,#6)
lib/store: no feature/component imports; named exports only. Diff scoped to vitalia/ + story md. Non-vitalia files in raw range (pre-commit hook, cockpit Tooltip, pm-* SKILL, comunify chris-input) belong to SEPARATE commit eaffd53d (R4 process-improvement), NOT story T-commits — confirmed via per-file git log. core/ untouched.

### PASS: Ratchet integrity (focus #7)
Commit 58a4ce5b SHRANK test_server_first allowlist back to empty (`KNOWN_MISSING_USE_CLIENT = new Set([])`) and fixed detection honestly: comment-stripped source + `startsWith('"use client"')` replaces the brittle `slice(0,500)` window. Verified ChannelConnectionWizard.tsx (real path: features/marketing/components/) genuinely has `"use client"` on line 15 after `// cap:` + JSDoc header. No allowlist growth anywhere; no warning-baseline growth (vitalia uses arch-fitness ratchet, not the nicolify jsdoc/check-file baselines).

### PASS: Spanish neutro (focus #8) + a11y (focus #9) + TDD (focus #10)
aria-labels neutro (SC-8d asserts no voseo regex). SC-8 axe wcag2aa both states (one justified `disableRules(['scrollable-region-focusable'])` — documented axe/Chromium false-positive for overflow-hidden flex; keyboard a11y separately verified SC-8a/b). RED-first per impl logs.

## Downstream regression scope

Surface `lib/store/create-ssr-safe-persisted-store.ts` is a shared util consumed by 4 stores (shell/tenant/agenda/agenda-filters). gate-output.json `command=test-frontend` ran FULL vitest (2310/2310) + full E2E suite → covers all 4 downstream consumers. agenda-stores-hydration.test.ts + tenant-store-hydration.test.ts + shell-store-hydration.test.ts present. Status: COVERED, no scoped re-run needed.

| Surface | Downstream consumers | Gate coverage |
|---|---|---|
| lib/store factory | shell/tenant/agenda/agenda-filters stores | full vitest+e2e PASS |
| useViewportGuard | ShellOrganismLayoutClient | resize-and-state.spec un-skipped PASS |

## Native-First / Live Verification / Verdict Math

- No `docker exec` lint/test, no `make e2e`, no `git add .`/-A/-u in commits.
- Live verification: invisible change → E2E+axe acceptable substitute; no missing evidence.
- Verdict math: 0 FAIL in cats 1/2/3/7/11/12/14; no allowlist/baseline growth (one SHRANK); 0 gate blockers; 148/148 arch; downstream covered; Cat 14 cite present; mockup gate exempt (ratified). → **PASS / APPROVED**.

## Notes for /pm-vitalia merge (non-blocking)

1. **ADR number correction (self-fix trivial — NOT applied, flag for merge):** 01-spec.md frontmatter says `new_adr_candidate: ADR-vitalia-005-...` but the actual ADR shipped as ADR-vitalia-006 (005 occupied by capability-model). Code + ADR file consistently cite 006. Correct 01-spec.md frontmatter `005→006` at merge. (Doc-only frontmatter; outside auditor self-fix whitelist for spec edits — leave to PM.)
2. **Capability update:** valeria.shell (cap_change_type: extend) — append change_log entry; mobileDrawerOpen slice = atomic added.
3. **Learning promotable /pm-luana:** factory `createSsrSafePersistedStore` is a lift candidate to core/@luana/hooks (Next 16 + Zustand 5 persist applies to all brand frontends). nicolify dismiss-store has same latent hazard — promotion would fix it cross-brand. Already flagged `promotion candidate` in factory header.
4. Parallel-build mislabel: commit 54ffb8e4 labeled "docs T-3" contains T-2 impl (content correct, pushed — cannot amend). Cosmetic; no code impact.
