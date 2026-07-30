# T-6 Result — Voz y tono sub-sub-tab

**Ticket:** T-6  
**Story:** vitalia-fase2-lisa-marca  
**Date:** 2026-05-27  
**State:** pushed

## Verdict: PASS

All 6 acceptance criteria satisfied. All quality gates GREEN.

## Acceptance Criteria

| # | Criterion | Result |
|---|-----------|--------|
| A1 | Exactly 4 archetype cards (Caregiver/Sage/Healer/Hero) — NO Outlaw/Magician | PASS |
| A2 | Alert variant=warning + "Aplicar sugerencia" + "Guardar igual" (soft, no block) | PASS |
| A3 | Single BrandVoicePreview footer instance (OQ-E) | PASS |
| A4 | debounceHash in BrandVoicePreview for React Query key stability | PASS |
| A5 | Spanish neutro LatAm, no voseo in any UI string | PASS |
| A6 | tsc + eslint GREEN | PASS |

## Test Coverage

- **23 new tests**: ArchetypeSelector (6) + VoiceTextareaWithWarning (6) + BrandVoicePreview (6) + VozTonoView (5)
- **191 total test files, 2044 tests**: ALL PASS (0 regressions)
- **24 architecture fitness tests, 149 checks**: ALL PASS

## Key Deliverables

| Deliverable | Status |
|-------------|--------|
| `VozTonoView.tsx` — "use client" root | ✓ |
| `ArchetypeSelector.tsx` — 4 archetypes radio cards | ✓ |
| `VoiceCompilerBlocks.tsx` — 6 compiler v2 textareas | ✓ |
| `VoiceTextareaWithWarning.tsx` — soft warning alert | ✓ |
| `TreatmentLanguageCard.tsx` — tratamiento + idioma | ✓ |
| `BrandVoicePreview.tsx` — OQ-E footer, Valeria + Camila | ✓ |
| `usePersonalityAutosave.ts` — 600ms debounce PUT | ✓ |
| `useVoicePreview.ts` — React Query GET preview | ✓ |
| `useVoiceBlocklist.ts` — prohibited phrases query | ✓ |
| `prohibitedPhraseDetector.ts` — substring scan utility | ✓ (pre-session) |
| `marca-voice-api.ts` — API client | ✓ (pre-session) |
| `voz-y-tono/index.ts` — barrel | ✓ |
| `lisa/index.ts` — updated with T-6 exports | ✓ |
| `voz-y-tono/page.tsx` — wired VozTonoView | ✓ |
| Shadcn Select installed | ✓ |

## Anti-creep Confirmations

- NO `health_voice_validator` reference anywhere
- NO client-side voice compile (BrandVoicePreview calls BE endpoint)
- `detectProhibitedPhrases` = substring scan only
- 4 archetypes ONLY (SALUD_ARCHETYPES SSoT from personality-schema.ts)
- BrandVoicePreview = single instance in DOM (OQ-E enforced by test)

## Commit Info

See git log for commit SHA after push to wip/vitalia.
