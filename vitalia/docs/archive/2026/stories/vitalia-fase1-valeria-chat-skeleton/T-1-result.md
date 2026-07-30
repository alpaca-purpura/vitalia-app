# T-1 Result — agent-catalog lib + mateo-soft tokens + typing-dot animation

**Story:** vitalia-fase1-valeria-chat-skeleton (F1-S6)
**Ticket:** T-1
**State:** pushed
**Commit:** c2ba2b89
**Branch:** wip/vitalia
**Builder:** claude-sonnet-4-6
**Date:** 2026-05-24

---

## Files Produced

### NEW

| File | LOC | Purpose |
|---|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` | ~95 | AgentSlug type, AgentDescriptor interface, AGENT_CATALOG (6 agents), DEFAULT_CHAT_AGENT='valeria', AGENT_SLUGS |
| `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` | ~125 | 12 Vitest tests — TDD RED→GREEN. SC-1 gherkin coverage |

### MODIFIED

| File | Change |
|---|---|
| `vitalia/frontend/src/app/globals.css` | Added `--agent-mateo-soft: 53 90% 90%` in `:root`; `--agent-mateo-soft: 53 80% 18%` in `.dark/[data-theme="dark"]`; `@keyframes typing-dot` + `.typing-dot` + nth-child delay rules |
| `vitalia/frontend/tailwind.config.ts` | Added `"mateo-soft": "hsl(var(--agent-mateo-soft))"` in agent color section |
| `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_colors.test.ts` | Added `src/lib/agent-catalog.ts` to `KNOWN_COLOR_VIOLATIONS` allowlist (hex fields are metadata-only) |

---

## Validator Results

| Validator | Status | Notes |
|---|---|---|
| val-fe-tsc | PASS | 0 errors, strict mode |
| val-fe-lint | PASS | 0 errors, 0 new warnings |
| val-fe-prettier | PASS | All touched files formatted |
| val-fe-vitest-unit | PASS | 12/12 tests passing |
| val-fe-arch-fsd | PASS | FSD boundaries respected (lib/ is cross-feature SSoT) |
| val-fe-arch-no-hex | PASS | allowlist updated with documented justification |
| Full arch suite | PASS | 83/83 tests passing (16 test files) |

---

## TDD Trace

1. **RED** — `agent-catalog.test.ts` written first. Run `vitest run src/lib/__tests__/agent-catalog.test.ts` → FAIL (module not found).
2. **GREEN** — `agent-catalog.ts` written with verbatim data from spec § 5.1. Run vitest → 12/12 PASS.
3. **CSS MODIFY** — `globals.css` and `tailwind.config.ts` updated.
4. **ARCH FIX** — `KNOWN_COLOR_VIOLATIONS` allowlist updated.
5. **PRETTIER** — All 5 touched files formatted.
6. **COMMIT** — `c2ba2b89` on `wip/vitalia`, pushed.

---

## SC-1 Gherkin Coverage

| Scenario | Test | Status |
|---|---|---|
| AGENT_CATALOG contains 6 agentes | agent-catalog.test.ts::AGENT_CATALOG contains 6 agentes | PASS |
| DEFAULT_CHAT_AGENT equals 'valeria' | agent-catalog.test.ts::DEFAULT_CHAT_AGENT equals 'valeria' | PASS |
| each agent shape complete (9 keys) | agent-catalog.test.ts::each agent shape complete | PASS |
| AGENT_SLUGS array 6 entries | agent-catalog.test.ts::AGENT_SLUGS array has 6 entries | PASS |
| valeria.hex equals '#7b2d91' | agent-catalog.test.ts::valeria.hex equals '#7b2d91' | PASS |
| thumbnail paths /agents/{slug}/thumbnail.png | agent-catalog.test.ts::thumbnail paths match | PASS |
| adrian.transparent ends with .jpeg | agent-catalog.test.ts::adrian.transparent ends with .jpeg | PASS |
| colorToken format 'agent-{slug}' | agent-catalog.test.ts::colorToken format | PASS |
| colorSoftToken format 'agent-{slug}-soft' | agent-catalog.test.ts::colorSoftToken format | PASS |
| initial is single uppercase letter | agent-catalog.test.ts::initial is single uppercase letter | PASS |
| all other agents transparent .png | agent-catalog.test.ts::all other agents transparent ends with .png | PASS |
| slug field matches catalog key | agent-catalog.test.ts::each agent slug field matches | PASS |

---

## Architecture Decisions

- **lib/ location**: `agent-catalog.ts` lives in `lib/` (cross-feature SSoT registry) per frontend-fsd.md boundary matrix. FSD-correct: `lib/` is reachable from `features/`, `components/shared/`, and `app/`.
- **LIFT CANDIDATE**: `agent-catalog.ts` is first-occurrence brand-local per `anti-duplication.md`. When a second brand needs agent catalog, lift to `@luana/agent-catalog` via `/pm-luana` promotion gate.
- **hex as metadata-only**: `AgentDescriptor.hex` field documents agent brand color for design tooling. Styling uses `colorToken` → Tailwind CSS var chain. Hex in `agent-catalog.ts` is exempt from arch color test (KNOWN_COLOR_VIOLATIONS, same pattern as `src/lib/agents.ts`).
- **AGENT_SLUGS derived**: `Object.keys(AGENT_CATALOG) as AgentSlug[]` — avoids manual sync drift between catalog and slugs array.

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| frontend-expert | FSD-Lite location for cross-feature registry | `lib/` confirmed correct per boundary matrix |
| tessl__react-patterns | Baseline for any new TS lib file | Pure functions, no hooks, no client state — no patterns apply; types correct |
| tessl__vitest | TDD RED→GREEN pattern | Used `describe/it/expect` pattern, no async needed for synchronous catalog |
| tessl__tailwind | CSS token addition | `--agent-mateo-soft` added in correct H S% L% format; consumed via `hsl(var(...))` in tailwind.config.ts |
| tdd-mandatory.md | RED before GREEN mandatory | Confirmed: test file created and failed before implementation |
| anti-duplication.md | First-occurrence check | grep cross-codebase confirmed no prior agent-catalog pattern; LIFT CANDIDATE documented |

---

## Next: T-2

T-2 is unblocked. Scope: `chat-store.ts` (Zustand) + `_mock-messages.ts` (6 MOCK_MESSAGES + 4 MOCK_RESPONSES Valeria canned). Depends on T-1 `AgentSlug` type (now available at `src/lib/agent-catalog.ts`).
