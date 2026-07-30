# T-11 Impl Log — Visual goldens suite · F1-S10 vitalia-fase1-empty-states

**Ticket:** T-11 (TESTS-ONLY)  
**Date:** 2026-05-26  
**Builder:** claude-sonnet-4-6 (builder-frontend)

---

## Skills Consulted

See T-11-result.md § Skills Consulted for full table.

Short form:
- `playwright-expert` — POM/fixture reuse, viewport per-describe, `toHaveScreenshot` API, tolerance values
- `frontend-expert` — TESTS-ONLY scope enforcement, runtime-quality-checklist confirmed (no production code)
- `tessl__react-patterns` — async test body correctness, no stale closures
- `e2e-testing.md` — port 3002, native Linux, preflight mandatory
- `shell-mockup-per-component.md` — 7 mockup baselines referenced; golden crop to content area only

---

## Implementation Notes

### Scope verification (T-11 TESTS-ONLY)

Pre-implementation grep confirmed no production code modifications:
- No files under `vitalia/frontend/src/` were touched
- Only `e2e/regression/vitalia-fase1-empty-states/visual-goldens.spec.ts` created
- Story artifacts updated (06-tickets.yaml, checkpoint.md, T-11-result.md, T-11-impl-log.md)

### Sub-tab inventory verification

22 sub-tabs sourced from RIBBON_SUBTABS SSoT (`vitalia/frontend/src/lib/agent-catalog.ts`):
- `lisa`: marca, doctores, servicios, compliance (4)
- `lucas`: lanzar, envuelo, recursos, resultados, mercado (5)
- `adrian`: inbox, embudo, outbound, propuestas (4)
- `valeria`: agenda, pacientes (2)
- `camila`: voz, reactivar, multiplicar, reputacion (4)
- `config`: cuenta, conexiones, avanzado (3)
- `mateo`: [] — excluded (transversal agent, empty array per SSoT)
- Total: 22

### POM reuse (T-10 shipped)

All 3 POMs confirmed present and reused:
- `e2e/pages/ShellOrganismPage.ts` — `goto(agent, subtab)` + `expectSubTabContentVisible()`
- `e2e/pages/AdrianInboxPage.ts` — `adrianModeChip`, `takeControlButton`, `returnControlButton`, `closeSidebarButton`, `takeControl()`, `closeSidebar()`
- `e2e/pages/ValeriaAgendaPage.ts` — `goto()`, `expectAgendaMounted()`

### Fixture reuse (T-10 shipped)

`e2e/fixtures/empty-states.fixture.ts` provides:
- `shellPage` — light theme, Clerk auth, localStorage seeded with `vitalia-theme: light`
- `darkShellPage` — dark theme, Clerk auth, localStorage seeded with `vitalia-theme: dark`
- `tenantId` — from base fixture

### Takeover UX (Section B)

State machine: local `useState<'bot'|'human'>('bot')` (F1 scope — NOT Zustand).
- State A default: `adrianModeChip` + `takeControlButton` visible
- State B after `takeControl()`: `returnControlButton` visible, `TakeoverBanner` displayed
- Sidebar closed: `data-sidebar="closed"` attribute present

### Crop strategy

All visual goldens crop to `[data-testid="subtab-content-{agent}-{subtab}"]` — NOT full-page screenshots.
This excludes:
- Ribbon (bottom navigation tabs)
- TopBar (global header)
- ValeriaSidebar (chat sidebar)

Per architect 03-arch.md spec: goldens must NOT include chrome navigation.

### Responsive section (Section C)

6 specials chosen per mockup protocol (each has dedicated HTML mockup):
1. `lisa-servicios` (mockups/lisa-servicios-placeholder.html)
2. `adrian-embudo` (mockups/adrian-embudo-placeholder.html)
3. `adrian-inbox` (mockups/adrian-inbox-placeholder.html)
4. `valeria-agenda` (mockups/valeria-agenda-placeholder.html)
5. `camila-voz` (mockups/camila-voz-placeholder.html)
6. `config-conexiones` (mockups/config-conexiones-placeholder.html)

Tolerance 0.005 for mobile/tablet (minor anti-aliasing differences cross-viewport).
Desktop 1280 uses 0.001 (same as main sections).

### TypeScript strict compliance

`npx tsc --noEmit` passed with 0 errors.
Key type decisions:
- `ALL_SUBTABS` declared `as const` with explicit `readonly { agent: string; subtab: string }[]` type
- `SPECIAL_PLACEHOLDERS` uses explicit `SpecialPlaceholder` interface
- All test callbacks properly typed by Playwright fixture inference

### ESLint compliance

`npx eslint src/` passed with 0 errors.
Note: spec file lives in `e2e/` not `src/` — covered by Playwright config, not main ESLint scope.

---

## Pending Items

1. **Live golden generation**: Stack must be live on port 3002. Run `--update-snapshots` to generate ~74 PNGs.
2. **Chris visual ratification**: Review generated PNGs against 7 HTML mockup baselines. Set `pending_chris_visual_ratify: false` after approval.
3. **Golden commit**: After live generation, commit the `e2e/__screenshots__/` directory contents.

---

## §11 Gaps (partial faithfulness flag context)

No gaps detected. CONTEXT-BRIEF.md had `Faithfulness flag: clean`. Validator pass: SKIPPED (magic ack not required as context was manually loaded).

---

## Anti-patterns avoided

- No production code touched (TESTS-ONLY strictly enforced)
- No `git add .` — stage by exact filename only
- No cross-brand paths referenced
- No `core/luana-core-*/` edits
- No `agent-catalog.ts` edits (22 sub-tabs sourced by reading, not modifying)
- No `make e2e*` — native `npx playwright` only
- No inline `style={{}}` (not a React component)
- No `chrome-devtools-verify` (deprecated for Linux Mint — escalated to Chris staging gate per rules)
