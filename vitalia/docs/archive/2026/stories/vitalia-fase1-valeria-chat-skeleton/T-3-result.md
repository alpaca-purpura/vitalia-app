# T-3 Result — MessageBubble + ChatHeader + TypingIndicator + DelegateMarker

**Story:** vitalia-fase1-valeria-chat-skeleton (F1-S6)
**Ticket:** T-3
**Builder:** claude-sonnet-4-6 (frontend-expert)
**Date:** 2026-05-24
**State:** pushed

---

## Files Created

| File | LOC | Notes |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` | ~50 | DRY Tailwind class helper — switch/map, no template literals |
| `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.tsx` | ~87 | Bot/user chat bubble atom, XSS-safe JSX text children |
| `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.test.tsx` | ~168 | 13 tests: SC-1 happy + SC-3 edge + SC-4 adversarial + data-testid |
| `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.tsx` | ~117 | Chat header molecule, imgError fallback via useState |
| `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.test.tsx` | ~110 | 12 tests: SC-1 happy + custom agent + SC-4 avatar onError |
| `vitalia/frontend/src/components/shared/shell-organism/TypingIndicator.tsx` | ~99 | Rich typing bubble, name + action text + 3 animated dots |
| `vitalia/frontend/src/components/shared/shell-organism/DelegateMarker.tsx` | ~89 | Delegation marker, thumbnail pill + agent name + mode |

**Total:** ~720 LOC (estimated 280 — richer per spec than estimated)

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | Always-on; runtime quality checklist | Confirmed: `"use client"` on all 4 (parent client boundary, imgError useState); no `useEffect` for data; no default exports |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, memoization | Applied: `aria-hidden` on avatar + status dot; `aria-busy` N/A (pure display atoms); stable keys per testid |
| `tessl__shadcn-ui` | Mode Pill in ChatHeader uses Shadcn Badge | Used `Badge variant="outline"` from `@/components/ui/badge`; no recreation |
| `tessl__tailwind` | No template literals for agent class names | Implemented `_agent-tw-classes.ts` with explicit switch statements per Tailwind JIT safety rule |
| `tessl__vitest` | Test setup, async patterns, mocking | Applied: RTL + happy-dom; `container.querySelector("img")` for `alt=""` presentation-role images; XSS assertions via `querySelector("script")` not `innerHTML.not.toContain` |

---

## Architecture Decisions

### 1. `_agent-tw-classes.ts` — DRY helper with underscore prefix
Internal to `shell-organism` folder (underscore signals module-private). Exports `agentBgClass`, `agentBgSoftClass`, `agentTextClass`, `agentDotBgClass` as switch statements. Eliminates template literal class names that Tailwind JIT cannot detect statically.

### 2. XSS safety
`MessageBubble` renders `content` as JSX text children — React auto-escapes. `NEVER dangerouslySetInnerHTML`. Test verifies: `bubble.querySelector("script") === null` + `bubble.textContent.toContain("alert('xss')")`.

### 3. Avatar onError fallback (ChatHeader)
Uses `useState(false)` for `imgError`. On error: shows `<span>{descriptor.initial}</span>` in agent-colored circle. Requires `"use client"` (hence all shell-organism atoms are client — they compose into a single client subtree).

### 4. `alt=""` images are `role="presentation"` in RTL
`getByRole("img", { hidden: true })` does NOT find `alt=""` images — they're `role="presentation"`. Fixed ChatHeader tests to use `container.querySelector("img")` directly.

### 5. TypingIndicator + DelegateMarker — no separate test files
Per `06-tickets.yaml` T-3 note: "TypingIndicator + DelegateMarker átomos puros — covered en T-5 integration tests. tsc + ESLint smoke validation suffices." Architecture tests + TypeScript strict cover structural correctness.

---

## Quality Gates

| Gate | Status | Detail |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors (strict) |
| ESLint | PASS | 0 errors, 0 new warnings |
| Vitest unit | PASS | 130 test files, 1139 tests all GREEN |
| Coverage | PASS | Statements 72%, Branches 89%, Functions 57%, Lines 72% (all > 20% threshold) |
| Architecture fitness | PASS | 83 tests across 16 files — all GREEN |
| Cross-brand mirror | PASS | 0 matches for MessageBubble/ChatHeader/TypingIndicator/DelegateMarker in nicolify/comunify/lupulo |
| No hardcoded colors | PASS | _agent-tw-classes.ts uses CSS custom property tokens (no hex literals) |
| Server-first | PASS | `"use client"` justified (useState in ChatHeader, parent client boundary for all) |
| Spanish neutro | PASS | No voseo in user-facing strings; tildes correct |

---

## Test Summary

**MessageBubble.test.tsx — 13 tests:**
- Bot variant: bg-card + border-border + rounded-bl-sm + rounded-2xl + whitespace-pre-wrap
- Bot wrapper: self-start max-w-[80%]
- Footer: "Valeria · 09:01" (default) + "Camila (via Valeria) · 09:05" (agent + footerLabel)
- Content text render
- User variant: bg-agent-valeria + text-white + rounded-br-sm
- User wrapper: self-end + max-w-[80%] + items-end
- User footer: time only, no agent name
- whitespace-pre-wrap preserves newlines
- XSS: `<script>alert('xss')</script>` — `querySelector("script") === null`, textContent contains literal
- XSS: `<img onerror='alert(1)' src='x'>` — textContent contains literal markup (no execution)
- data-testid='msg-bubble' + data-role='bot'|'user'

**ChatHeader.test.tsx — 12 tests:**
- data-testid='chat-header' renders
- Avatar img src=/agents/valeria/thumbnail.png (via container.querySelector)
- Name 'Valeria'
- Status text matches /En línea · Tu secretaria virtual/
- Status dot: bg-vitalia-success + aria-hidden='true'
- Mode Pill: data-testid='chat-mode-pill' + "🤖 Modo agente"
- Avatar container: aria-hidden='true'
- Custom agent='camila': Camila name + Fidelización role text
- Camila thumbnail src (via container.querySelector)
- onError: fireEvent.error(img) → "V" initial letter visible
- After onError: img removed from DOM + avatarDiv.textContent contains "V"

---

## Gherkin Coverage Map

| Scenario | Test file | Status |
|---|---|---|
| SC-1 happy · ChatHeader avatar + name + status + Mode Pill | ChatHeader.test.tsx | GREEN |
| SC-4 adversarial · avatar onError fallback | ChatHeader.test.tsx | GREEN |
| SC-1 happy · MessageBubble bot/user variants | MessageBubble.test.tsx | GREEN |
| SC-4 adversarial · XSS guard JSX text-children | MessageBubble.test.tsx | GREEN |
| TypingIndicator + DelegateMarker shape | (T-5 integration tests per ticket note) | deferred |

---

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (per project context note 2026-05-15). Escalating to Chris staging gate manual verification:

**Manual verification steps:**
1. `cd vitalia/frontend && npm run dev` (port 3002)
2. Navigate to `/test-stack/shell-layout`
3. Verify ChatHeader renders with Valeria avatar + "En línea · Tu secretaria virtual · coordinadora general" + "🤖 Modo agente" badge
4. Verify MessageBubble bot/user variants render with correct colors
5. Verify TypingIndicator 3-dot animation plays (CSS keyframes from globals.css T-1)
6. Verify DelegateMarker shows italic centered delegation marker with agent thumbnail

---

## Next Ticket

T-4: ChatComposer molécula (depends on T-2 chat-store)
T-5: ValeriaChat organism (depends on T-2 + T-3 + T-4)
