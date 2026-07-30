# T-6 Implementation Log — Voz y tono sub-sub-tab

**Ticket:** T-6  
**Story:** vitalia-fase2-lisa-marca  
**Date:** 2026-05-27  
**Builder:** Claude Sonnet 4.6  
**State:** pushed

## Summary

Implemented the Voz y tono sub-sub-tab within Lisa's Marca section per ADR-vitalia-004 v1.1 N3-static pattern. Full component hierarchy built TDD-first (23 RED tests → 23 GREEN).

## Files Created / Modified

### New files (implementation)
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/ArchetypeSelector.tsx` — 4 salud archetypes (OQ-B)
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/VoiceTextareaWithWarning.tsx` — soft warning + "Aplicar sugerencia" + "Guardar igual"
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/VoiceCompilerBlocks.tsx` — 6 compiler v2 blocks
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/TreatmentLanguageCard.tsx` — tratamiento + idioma selects
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/BrandVoicePreview.tsx` — OQ-E single footer, Valeria + Camila bubbles
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/VozTonoView.tsx` — "use client" root
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/index.ts` — barrel
- `vitalia/frontend/src/features/lisa/hooks/usePersonalityAutosave.ts` — 600ms debounce autosave
- `vitalia/frontend/src/features/lisa/hooks/useVoicePreview.ts` — React Query voice preview
- `vitalia/frontend/src/features/lisa/hooks/useVoiceBlocklist.ts` — prohibited phrases query

### Pre-existing files (created in prior session, TDD RED tests)
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/__tests__/ArchetypeSelector.test.tsx`
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/__tests__/VoiceTextareaWithWarning.test.tsx`
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/__tests__/BrandVoicePreview.test.tsx`
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/__tests__/VozTonoView.test.tsx`
- `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts`
- `vitalia/frontend/src/features/lisa/utils/marca/prohibitedPhraseDetector.ts`

### Modified files
- `vitalia/frontend/src/features/lisa/api/marca.ts` — extended `marcaKeys` with personality/voicePreview/prohibitedPhrases
- `vitalia/frontend/src/features/lisa/index.ts` — added T-6 barrel exports
- `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/voz-y-tono/page.tsx` — wired VozTonoView

### Installed Shadcn component
- `vitalia/frontend/src/components/ui/select.tsx` — `npx shadcn add select` (not previously installed)

## Acceptance Criteria Verification

| AC | Status | Notes |
|----|--------|-------|
| A1: Exactly 4 archetype cards | PASS | Caregiver/Sage/Healer/Hero; no Outlaw/Magician/Lover/Innocent |
| A2: Alert warning + override button | PASS | Soft warning only; textarea never disabled |
| A3: Single BrandVoicePreview | PASS | OQ-E: 1 instance per VozTonoView |
| A4: debounceHash in BrandVoicePreview | PASS | hashVoiceBlocks() → data-hash attr + React Query key |
| A5: No voseo | PASS | All UI strings use Spanish neutro tuteo |
| A6: tsc + eslint GREEN | PASS | 0 errors, 0 warnings |

## Architecture Decisions

### OQ-B (4 archetypes): Used `SALUD_ARCHETYPES` from `personality-schema.ts` (T-8) as SSoT.
ArchetypeSelector renders only from that array — no hardcoded labels outside the component.

### OQ-C (BE preview): BrandVoicePreview calls `getVoicePreview` BE endpoint. NOT client-side compile.
`debounceHash` from `hashVoiceBlocks()` changes when blocks autosave → React Query key changes → refetch.

### OQ-E (single preview): BrandVoicePreview is rendered exactly once, as footer of VozTonoView.
Test `getAllByTestId("brand-voice-preview")` verifies length === 1.

### Anti-creep: `detectProhibitedPhrases` is a substring scan. NOT a LLM call. NOT `health_voice_validator`.

### Tailwind colors: Used `text-agent-valeria` / `text-agent-camila` / `bg-agent-*-soft` Tailwind utilities
(defined in `tailwind.config.ts`) instead of `hsl()` literals — avoids arch test FE-A1 violation.

### TDD flow: 4 test files (23 tests) written RED first. GREEN implementation built to pass.
Test design: component renders without loading skeleton visible synchronously (sections always mount;
ArchetypeSelector shows "Arquetipo principal" label even during skeleton state).

## Quality Gates

- tsc --noEmit: 0 errors
- ESLint: 0 errors, 0 warnings
- Vitest: 191 test files, 2044 tests ALL PASS (no regressions)
- Architecture fitness: 24 arch tests ALL PASS (149 tests)
- Coverage: maintained above 20% threshold

## Skills Consulted

| Skill | Invoked for | Decision |
|-------|------------|---------|
| `frontend-expert` | FSD-Lite boundary matrix, ESLint ratchet, barrel exports | Used `features/lisa/components/marca/voz-y-tono/` FSD path; barrel via `index.ts`; no default exports |
| `tessl__react-patterns` | Error boundaries, loading/empty states, accessible markup, stable keys | Per-section loading (ArchetypeSelector isLoading prop); role="radiogroup" + role="radio"; aria-label on regions; stable keys via archetype value |
| `tessl__shadcn-ui` | Component selection | Used existing Alert, Badge, Button, Skeleton, Textarea, Label; installed missing Select |
| `tessl__tailwind` | Token consumption | Used `text-agent-valeria`, `bg-agent-valeria-soft/20` etc. instead of `hsl()` literals |
| `tessl__zod` | Form schema | Used `personalitySchema` / `voiceBlocksSchema` from `personality-schema.ts` (T-8) |
| `tessl__nextjs-app-router-modularization` | Server/Client split | `page.tsx` = Server Component; `VozTonoView.tsx` = "use client" root (ADR-vitalia-004 § 3) |
| `brand-expert` (implicit via 03-arch.md) | PersonalityProfile voice compiler v2, 6 blocks | Implemented 6 blocks: identity/context/asi_hablo/asi_no_hablo/tech_context/format mapping to BE DTO |
| `sales-agent-expert` (anti-creep check) | NO health_voice_validator | Confirmed: soft warning only via substring scan; NO LLM validator |

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Manual verification steps escalated to Chris staging gate per role instructions.

Manual verification checklist:
1. Navigate to `/[tenantId]/lisa/marca/voz-y-tono` — VozTonoView renders
2. Verify 4 archetype cards visible (Cuidador, Sabio, Sanador, Héroe)
3. Click archetype — verify autosave badge shows "Guardando..." then "Guardado"
4. Type prohibited phrase in "Así no hablo" textarea — verify Alert with suggestion appears
5. Click "Aplicar sugerencia" — verify textarea value replaced
6. Click "Guardar igual" — verify alert dismissed, save proceeds
7. Scroll to footer — verify single BrandVoicePreview with Valeria + Camila bubbles
