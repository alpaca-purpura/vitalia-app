---
ticket: T-7
story: vitalia-fase2-lisa-marca
brand: vitalia
surface: FE
state: pushed
commit: d53b4753
pushed_at: 2026-05-27
---

# T-7 Result — FE Presencia sub-sub-tab

## Summary

Implemented the last FE section of vitalia-fase2-lisa-marca: the Presencia sub-sub-tab.
Full ADR-vitalia-004 v1.1 N3-static compliance.

## Deliverables Shipped

| Deliverable | File | Status |
|---|---|---|
| `PresenciaView.tsx` | `features/lisa/components/marca/presencia/PresenciaView.tsx` | DONE |
| `InfoBannerLandingDescoped.tsx` | `features/lisa/components/marca/presencia/InfoBannerLandingDescoped.tsx` | DONE |
| `WebsiteCard.tsx` | `features/lisa/components/marca/presencia/WebsiteCard.tsx` | DONE |
| `SocialMediaLinksEditor.tsx` | `features/lisa/components/marca/presencia/SocialMediaLinksEditor.tsx` | DONE |
| `TrustSignalsEditor.tsx` | `features/lisa/components/marca/presencia/TrustSignalsEditor.tsx` | DONE |
| `LocationsCard.tsx` | `features/lisa/components/marca/presencia/LocationsCard.tsx` | DONE |
| `useContactAutosave.ts` | `features/lisa/hooks/useContactAutosave.ts` | DONE |
| `marca-presence-api.ts` | `features/lisa/api/marca-presence-api.ts` | DONE |
| Barrel `presencia/index.ts` | `features/lisa/components/marca/presencia/index.ts` | DONE |
| Unit tests (5 files, 37 tests) | `features/lisa/components/marca/presencia/__tests__/` | DONE |
| `presencia/page.tsx` wired | `app/[tenantId]/(shell-organism)/lisa/marca/presencia/page.tsx` | DONE |
| `lisa/index.ts` updated | Barrel exports for PresenciaView + API types | DONE |

## Acceptance Criteria

| AC | Criterion | Status |
|---|---|---|
| A1 | PE trust catalog 8 entries (DIGESA, MINSA, SUSALUD, COLEGIO_MEDICO, ISO_9001, JCI, ACHS, WHO_SAFE) | PASS |
| A2 | Zod validation for social media handles + website URL | PASS |
| A3 | All UI strings Spanish neutro LatAm, no voseo | PASS |
| A4 | tsc + eslint GREEN | PASS |

## Quality Gates

| Gate | Result | Detail |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors |
| `eslint src/` | PASS | 0 errors |
| `vitest run --coverage` | PASS | 2081/2081 tests pass (196 files) |
| Architecture tests | PASS | 196 test files — test_no_hardcoded_colors + test_no_cross_feature_imports FIXED |
| Pre-commit hook | PASS | voseo-allowed magic comments added to test fixtures per rules |

## Commit

`d53b4753` — `feat(vitalia/f2-s7): T-7 FE Presencia — sitio web + 5 redes + trust hybrid catalog + ubicaciones`

Branch: `wip/vitalia` (pushed)

## Files Changed (20)

- 15 new files (components + tests + hooks + API + barrel)
- 5 modified files (marc.ts keys, index.ts barrel, page.tsx, globals.css social vars, 06-tickets.yaml)
- 2414 insertions, 25 deletions

## Notes

- `chrome-devtools-verify` DEPRECATED for Linux Mint. Manual staging gate required (see impl-log § Live Verification).
- `LocationsCard` Editar + Agregar sede disabled — deferred to future story (read-only clinics module data).
- Instagram + TikTok + Facebook + Google + WhatsApp social icons use `--social-*` CSS vars from globals.css (arch fitness compliant; no hardcoded hex in TSX).
- OQ-D hybrid catalog: immediate ADD/DELETE mutations (not debounced); años/pacientes/premios use 600ms debounce.
