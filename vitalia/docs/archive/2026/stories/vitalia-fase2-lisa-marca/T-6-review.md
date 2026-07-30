<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->

# T-6 Frontend Code Review — FE Voz y tono sub-sub-tab

**Date:** 2026-05-27
**Ticket:** T-6
**Story:** vitalia-fase2-lisa-marca
**Brand:** vitalia
**State:** pushed
**Files Reviewed:** 9 components + 3 hooks + 1 view (VozTonoView read in full)
**Domains touched:** lisa/marca/voz-y-tono — voice compiler v2 consumption, archetype picker, brand voice preview
**Skills consulted:** frontend-expert, brand-expert, sales-agent-expert, tessl__react-patterns, tessl__zod, tessl__react-hook-form, tessl__shadcn-ui, tessl__tailwind, tessl__react-query-patterns
**Live-verified:** N/A; E2E spec SC-2 covers
**Verdict:** **WARN** (1 minor: setState-during-render hydration pattern)

## Gate Status

All 8 gates PASS per gate-output.json (fe_vitest WARN scope only).

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | FSD-Lite | PASS | `features/lisa/components/marca/voz-y-tono/*` + barrel + named exports |
| 2 | Server/Client | PASS | VozTonoView "use client" + props hydration from Server Component page.tsx |
| 3 | React Patterns | **WARN** | VozTonoView.tsx:103 calls `setHydrated(true)` inside conditional during render (lines 102-114). Works functionally but is React anti-pattern (should be `useEffect` or `useSyncExternalStore` pattern). Documented React docs as "OK if conditional + idempotent" — borderline but flag for future cleanup. **Otherwise:** error state aria-live, loading state per ArchetypeSelector, useCallback handlers, useMemo for debounceHash |
| 4 | Code Quality | PASS | tsc/eslint clean |
| 5 | Accessibility | PASS | Error `role="alert"`; alert variant=warning visible per A2; Spanish neutro labels |
| 6 | Forms (RHF + Zod) | PASS | personalitySchema 4 archetypes only enforced; voiceBlocksSchema 6 fields max 2000 chars; autosave 600ms via `usePersonalityAutosave`; NO Guardar button |
| 7 | Multitenancy | PASS | useAuth() → tenantId in React Query keys + propagated to API client; X-Tenant-ID auto-inject documented in api/marca.ts header |
| 8 | Master Data / Spanish | PASS | Zero voseo; archetype labels in spanish neutro ("Cuidador, Sabio, Sanador, Héroe"); error messages spanish |
| 9 | Security / Deps | PASS | No new deps; no dangerouslySetInnerHTML; PHI never in URL |
| 10 | Tests / TDD | PASS | 23 new tests (Archetype/VoiceTextareaWithWarning/BrandVoicePreview/VozTonoView); 191 files / 2044 tests overall green; 0 regressions |
| 11 | Domain Alignment | PASS | D2-voice: NO `health_voice_validator.py` created; soft warning only (override + audit log); D5-archetype: 4 archetypes enum enforced; sales-agent compiler v2 slot 5 LIBRARY-ONLY consumption; OQ-E single BrandVoicePreview footer; OQ-C debounceHash for cache invalidation |
| 12 | Architecture Fitness | PASS | 24 arch tests / 149 checks GREEN |
| 13 | Mirror detection | PASS | All 6 components net-new brand-local; `prohibitedPhraseDetector` brand-local utility (no cross-brand mirror); BrandVoicePreview consumes sales-agent compiler via API (no engine modify) |
| 14 | Decisions honored cite (R6) | PASS | result.md cites D2-voice + D5-archetype + OQ-B + OQ-C + OQ-E + A3 verbatim |

## Findings

### WARN: setState during render in hydration (non-blocking)

**Category:** 3 (React Patterns)
**File:** `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/VozTonoView.tsx:102-114`
**Issue:** Pattern:
```tsx
const [hydrated, setHydrated] = useState(false);
if (personality && !hydrated) {
  setArchetype(personality.archetype);
  setVoiceBlocks({...});
  setHydrated(true);
}
```
Calling `setState` during render is **conditionally allowed** by React (idempotent guard via `!hydrated`), but per `tessl__react-patterns` best practice this should use:
- `useEffect(() => { if (personality && !hydrated) {...} }, [personality, hydrated])`, OR
- `useSyncExternalStore` for server-state hydration, OR
- defer hydration via React Query `select` / initialData.

**Risk:** Low (idempotent + guarded). Works correctly, but increases re-render count slightly and is subtly fragile if `personality` reference changes pre-hydration.

**Fix suggestion (future cleanup, NOT blocking):**
```tsx
useEffect(() => {
  if (personality && !hydrated) {
    setArchetype(personality.archetype);
    setVoiceBlocks({ identity: personality.identityAnchor, ... });
    setHydrated(true);
  }
}, [personality, hydrated]);
```

**Skill ref:** `tessl__react-patterns` (avoid setState during render); React docs "you might not need an effect" exception is for derived state, not hydration with side effects.

**Action:** Flag for follow-up; NOT blocking merge. Builder can self-fix if desires (whitelist item 6 — type/control trivial fix; cap 2 files/10 lines).

## Anti-creep verification

- [x] NO `health_voice_validator.py` BE file (creep guard)
- [x] NO LLM dispatch in `/voice-preview` (LIBRARY-ONLY consumption)
- [x] NO `brand_voice_summary` table mirror
- [x] NO voice-rewriter LLM post-generation
- [x] NO `{tenant_name}` mid-block in cache prefix (debounceHash via hashVoiceBlocks)
- [x] BrandVoicePreview is SINGLE instance footer (OQ-E A3 satisfied)
- [x] 4 archetypes enum enforced (Caregiver default + Sage + Healer + Hero; NO Outlaw/Magician/Lover/Innocent)

## Verdict Math

- 0 FAIL → not FAIL
- 1 WARN (Category 3) → **WARN** overall
- Rule: "Two or more category WARNs → overall WARN" — only 1 WARN → could be PASS, but flagging WARN to make finding visible

**APPROVED with non-blocking WARN.** Recommended follow-up to convert setState-during-render to useEffect (low priority; can be batched with T-9 test cleanup or deferred to next story).

Last line: done -> vitalia/docs/product/stories/vitalia-fase2-lisa-marca/T-6-review.md
