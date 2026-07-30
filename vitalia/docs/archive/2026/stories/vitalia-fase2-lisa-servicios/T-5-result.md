# T-5 result — FE · NumberWithUnit (shared) + field primitives (moléculas)

story: vitalia-fase2-lisa-servicios · ticket: T-5 · surface: frontend · agent: builder-frontend (workhorse) · phase: A

## Verdict: PUSHED · all validators GREEN

## Scope delivered
- **`vitalia/frontend/src/components/shared/NumberWithUnit.tsx`** — NEW vitalia-local shared molecule (lift-candidate `/pm-luana` to `@luana/ui-kit`, NOT lifted this story) + test. Unit-picker uses raw `Select` (RichSelect wraps trigger in FormControl → needs RHF context; not usable standalone).
- **`vitalia/frontend/src/features/lisa/components/servicios/`** (feature-local moléculas + tests): ModalidadPicker (discriminated reveal · RN-28), RungPicker (locked state · RN-30), VariantsRepeater (add/remove · RN-29), TestimonialsList (RN-33), FaqPairList, ObjecionPairList, TagInput (case-insensitive de-dupe · keywords), FichaCompletenessChip (AC-19), ChipOrigen (estandar/personalizado Badge variant).
- Barrel export `features/lisa/index.ts` (named, no default).

## Reconciliations applied (CONTEXT-BRIEF §11)
- M1: RichSelect real shipped contract is `{value,label?,description?}` + `onValueChange` (NOT `{value,title,description}`+`onChange` as spec § Mapa de campos wrote). CONSUMED from @luana/ui-kit, not recreated.
- Canon §0 (no arbitrary): 5 `text-[0.6xxrem]` micro-labels → `text-xs` token. Canon §2.7: array/picker raw layout `<div>` → `space-y-N` / responsive `sm:flex` / `flex gap` segmented — ratchet back to baseline (302→301, 122→121), zero new layout-div.
- cap header was wrongly `// cap: clinics.lisa.servicios` (the actual checkpoint cap is `lisa.servicios`) → fixed across all production + test files.

## Gate results (G5 pre-commit smoke gate)
- `npx tsc --noEmit` → 0 errors
- `npx eslint` (servicios + NumberWithUnit + index) → 0 errors
- `npx vitest run` (10 T-5 files) → 45/45 PASS
- `npx vitest run src/__tests__/architecture/` → 187/187 PASS (div-layout ratchet · native-select · ds-tokens-lock · FSD boundaries · no-default-export · react-query-keys · no-phi-url · no-clerk-organizations)

## Skills consulted (must_load enforcement v4.1)
| Skill / rule | Status | When |
|---|---|---|
| frontend-expert | ✅ loaded | Step 0 — component patterns |
| vitalia-design-system | ✅ loaded | atoms/tokens/canon |
| .claude/rules/frontend-visual-fidelity.md | ✅ loaded | canon §0/§2.7 + mockup adherence |
| .claude/rules/frontend-fsd.md | ✅ loaded | feature-local placement, barrel export |
| .claude/rules/spanish-text.md | ✅ loaded | neutro LatAm strings |
| .claude/rules/anti-duplication.md | ✅ loaded | consume ui-kit, NumberWithUnit lift-candidate |
| .claude/rules/tdd-mandatory.md | ✅ loaded | vitest RED-first |

## Engine boundary
CERO edit of `@luana/ui-kit/src` (NumberWithUnit built vitalia-local) · `components/ui` Shadcn untouched · no other features/brands. Moléculas expose `onChange` (caller owns autosave — wired in T-7).

done -> T-5-result.md
