# T-3 Result — adrián/inbox route + ChannelBadge + CONN registration

**Ticket:** T-3 vitalia-fase2-adrian-inbox  
**Commit SHA:** d544ecf4  
**Branch:** worktree-agent-aaaf562bd9b1c0fce  
**Files changed:** 9 (6 new, 3 modified)  
**Date:** 2026-06-03

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | Mandatory — FSD-Lite boundary matrix, RSC/client split, RQ patterns, runtime-quality-checklist | Server-first RSC page.tsx; `"use client"` only in AdrianInboxView skeleton; inbox-server follows agenda-server.ts pattern exactly |
| `vitalia-design-system` | ★ SSoT shell/tokens (mandatory per 06-tickets T-3) | ChannelBadge uses CSS tokens (`--agent-*`) not hardcoded hex; shell wrappers REUSE only (not touched); confirmed `SHIPPED_STATIC_SUBTABS` pattern |
| `brand-expert` | FSD-Lite + FE-canonical patterns (form-runtime not applicable; no new form in T-3) | No form in T-3 scope; autosave non-applicable |
| `chrome-devtools-verify` | Mandatory live-verify gate FE PR ≥ M | dev-app.vitalialat.com not exercised in T-3 (T-3 is skeleton only — no visible UI to verify beyond a loading placeholder). Live-verify gate applies to T-5/T-6 when 3-pane is real. Escalated: Chris staging gate deferred to T-6 DoD sign-off as specified in 06-tickets T-6 human_gate. |

---

## Diff summary

### NEW files

| File | Purpose |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx` | RSC route — mirror of mateo/agenda/page.tsx. Awaits params/searchParams (Next 16 async). UUID guard for `?conv=`. Filter whitelist. Calls `getInitialInboxState()`. No `"use client"`. |
| `vitalia/frontend/src/features/adrian/api/inbox-server.ts` | SSR fetch — `getInitialInboxState()`. Graceful degradation: returns `{conversations:[],detail:null,tenantId}` on any error (SC-7/SC-8). Never throws. `INTERNAL_API_URL` → `NEXT_PUBLIC_API_URL` → localhost fallback. |
| `vitalia/frontend/src/features/adrian/api/__tests__/inbox-server.test.ts` | Vitest RED-first: 5 tests covering SC-7 (empty_state on 503/no-token) + SC-8 (network failure, auth rejection). |
| `vitalia/frontend/src/features/adrian/components/inbox/AdrianInboxView.tsx` | SKELETON — minimal compiling component so page.tsx + barrel + tsc work. T-5 replaces body with 3-pane ResizablePanelGroup. `"use client"` on line 1. Props contract matches 03-arch-fe.md § 3. |
| `vitalia/frontend/src/components/shared/shell-organism/ChannelBadge.tsx` | Reusable channel badge molecule. Channels: whatsapp/instagram/email/web/telegram. Lucide icons. CSS-token-only colors (no hardcoded hex — `test_no_hardcoded_colors` passes). Cross-feature lift candidate. |
| `vitalia/frontend/src/features/adrian/components/inbox/__tests__/ChannelBadge.test.tsx` | 6 tests — one per channel + no-hardcoded-hex + AdrianInboxView skeleton render. |

### MODIFIED files

| File | Change |
|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` | `SHIPPED_STATIC_SUBTABS` += `"adrian.inbox"` — CONN anti-orphan: static route shadows dispatcher, prevents island. Comment traces to T-3 date. |
| `vitalia/frontend/src/features/adrian/index.ts` | Added exports: `AdrianInboxView`, `AdrianInboxViewProps`, `getInitialInboxState`, `GetInitialInboxStateOptions`, `InitialInboxState`, `InboxConversationSummary`. InboxPlaceholder kept for compat. |
| `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.tsx` | Removed `InboxPlaceholder` import + `"adrian.inbox"` from `PLACEHOLDER_MAP` (count 19→18). Added comment explaining exclusion. Updated count comment. Arch test `test_subtab_content_uses_ribbon_subtabs_ssot` validates the invariant PLACEHOLDER_MAP === RIBBON_SUBTABS − SHIPPED_STATIC_SUBTABS. |

---

## Validator output

### nf-fe-tsc (PASS)
```
node_modules/.bin/tsc --noEmit
→ 0 errors (strict mode)
```

### av-fe-arch-fitness (PASS)
```
vitest run src/__tests__/architecture/
→ 25 test files, 171 tests — all PASS
Key tests:
  ✓ test_subtab_content_uses_ribbon_subtabs_ssot (7 tests) — PLACEHOLDER_MAP === RIBBON_SUBTABS − SHIPPED_STATIC_SUBTABS
  ✓ agent-catalog-ribbon-taxonomy (14 tests) — SHIPPED_STATIC_SUBTABS contains mateo.agenda, lisa.marca, lisa.staff, adrian.inbox
  ✓ test_no_hardcoded_colors (2 tests) — ChannelBadge uses no hex literals
  ✓ test_no_cross_feature_imports (2 tests) — FSD boundaries intact
```

### av-no-orphan-inbox (PASS — by design)
`"adrian.inbox"` added to `SHIPPED_STATIC_SUBTABS` → route registered with shell dispatcher. Static Next.js route file exists at `app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx`. Condition satisfied: ruta no es isla.

### vis-runtime-error-gate
T-3 installs the skeleton for future live-verify. T-6 e2e specs import `e2e/fixtures/base.ts` (anti-burbuja) per 06-tickets T-6 guardrails. Live-verify deferred to T-5/T-6 where the real UI exists (Chris demo sign-off gate per 06-tickets `human_gate`).

### Full suite
```
vitest run --coverage
→ 224 test files, 2479 tests — all PASS
Coverage: Statements 82.95% / Branches 91.96% / Functions 69.45% / Lines 82.95%
(threshold ≥20% — well exceeded)
```

### ESLint
```
eslint src/ --cache
→ 0 errors, 0 new warnings
```

---

## CONN verification (anti-orphan)

| Check | Status |
|---|---|
| **C**onsumed — ≥1 real consumer | `page.tsx` renders `AdrianInboxView`; `index.ts` exports both |
| **O**n the map — cap YAML with home | `cap: adrian.inbox` header lines 1–3 on all new files |
| **N**avigable — explicit access path | `SHIPPED_STATIC_SUBTABS.has("adrian.inbox")` = true; shell SubTabsBar navigates to `/[tenantId]/adrian/inbox` |
| **N**otarized — runtime discovery | `SubTabContent.tsx` no longer intercepts `adrian.inbox` (it was a placeholder). Static route wins. `RIBBON_SUBTABS.adrian[0].id === "inbox"` and `adrián.defaultSubtab === "inbox"` → Ribbon click navigates here. |

---

## Notes for T-4/T-5

1. `AdrianInboxView.tsx` is a stub. T-5 replaces the body with the real 3-pane `ResizablePanelGroup` + all the pieces (ModeToggle, ConversationModeButton, ToolCallCard, NudgeButton, useValeriaReaccion).
2. `inbox-server.ts` SSR fetch is wired correctly. T-4 consolidates RQ hooks (`useInboxConversations`, etc.) in `features/adrian/api/inbox.ts` which will hydrate from `initialData`.
3. `features/inbox/` is NOT yet deleted — T-4 does that (DELETE + MIGRATE as a unit per 06-tickets T-4).
4. ChannelBadge is available for T-4/T-5 via `@/components/shared/shell-organism/ChannelBadge`.

---

<!-- @pm: build phase done (state: tests-passing). Commit: d544ecf4. Files: 9. Native ticket tests: 11/11 PASS (5 inbox-server + 6 ChannelBadge). Arch fitness: 171/171 PASS. Full suite: 2479/2479 PASS. Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). -->
