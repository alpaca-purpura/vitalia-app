# T-8 IMPL-LOG — FE Zod Schemas IMPORT nicolify + ADAPT salud overlay

**Story:** vitalia-fase2-lisa-marca  
**Ticket:** T-8  
**Commit:** fa37c721  
**Branch:** wip/vitalia  
**Date:** 2026-05-27  

## Summary

Created 9 Zod v4 schemas for the lisa/marca feature domain, split into two categories:

**IMPORT verbatim from nicolify (adapted to Zod v4):**
- `identity-schema.ts` — brand identity fields (brand_name, tagline, description, industry, website, founding_year, language, timezone)
- `contact-schema.ts` — contact information (email, URLs, phone, WhatsApp, social channels)
- `visuals-schema.ts` — visual identity + clinicVisualsSchema with D4-extract STUB
- `team-schema.ts` — team member array (≤3 sub-fields → cards mode)
- `testimonial-item-schema.ts` — testimonial array (tags array, rating 1-5, media type enum)

**ADAPT salud overlay (NEW vitalia-specific):**
- `personality-schema.ts` — 4 Jung archetypes ONLY: caregiver, sage, healer, hero (OQ-B, D5-archetype). Voice 6 blocks compiler v2.
- `prohibited-phrase-schema.ts` — phraseSeverityEnum (warning/block) + prohibited phrase form
- `trust-signals-schema.ts` — hybrid catalog (certificationEntrySchema ≥4 fields → split mode) + trustSignalsSchema
- `presence-schema.ts` — locationEntrySchema + socialMediaSchema + presenceSchema (website/social/locations)
- `voice-preview-schema.ts` — voicePreviewRequestSchema (UUID fields) + voicePreviewResponseSchema (sample outputs)

**Barrel:** `types/marca/index.ts` — named exports only, no default exports.

**Tests:** `__tests__/marca-schemas.test.ts` — 55 tests GREEN including arch gates:
- `fe_arch_test_personality_schema_4_archetypes`: SALUD_ARCHETYPES.length === 4, correct values
- `fe_arch_test_no_phi_in_schemas`: no PHI field names in any schema
- `fe_test_schemas_messages_spanish_neutro`: no voseo in any error message

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite structure, barrel pattern, arch fitness | Named exports only; `types/marca/` path under `features/lisa/` |
| `tessl__zod` | Zod v4 schema patterns, RHF resolver, form validation | Used `z.enum(array, {message})` not `{errorMap}` (Zod v4 breaking change) |
| `tessl__react-patterns` | No PHI in schemas, accessible error messages | Confirmed no PHI field names in schemas |
| `brand-expert` | form-runtime-array.md defaults for array fields | team (1 field → cards), certifications (3 fields → cards), locations (2 fields → cards, presenceSchema as whole ≥4 → split) |

## Key Decisions

1. **Zod v4 API**: `errorMap` removed → use `message: "..."` directly in enum params. `invalid_type_error` → `error`. `result.error.errors` → `result.error.issues`. `_def.shape` is an object (not a function).

2. **D4-extract STUB**: `clinicVisualsSchema` adds `extract_from_url_stub` field (optional URL). This is a UI hint for the disabled button — no backend roundtrip in FE. Button disabled with tooltip until `/pm-luana` promotion proposal accepted.

3. **SALUD_ARCHETYPES = 4**: caregiver, sage, healer, hero. Excluded from nicolify's 12: outlaw, magician, lover, innocent, explorer, creator, ruler, jester, everyman. Arch test verifies length === 4 AND forbidden archetypes not present.

4. **Voice blocks compiler v2**: 6 fields in voiceBlocksSchema (identity, context, asi_hablo, asi_no_hablo, tech_context, format). Library-only — no LLM dispatch in FE.

5. **voseo-allowed magic comment**: Test file uses regex patterns like `/configurá/` to detect voseo in error messages. Added `// voseo-allowed: test fixture` to satisfy pre-commit hook per spanish-text.md § Magic comment escape.

## Quality Gate Results

```
tsc --noEmit:    0 errors
eslint src/features/lisa/types/: 0 errors, 0 warnings
vitest run:      55/55 PASS (16ms)
```
