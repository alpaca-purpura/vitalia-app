# T-12 Result — NPSTagBadge shared cross-feature component + Storybook + tests

> Brand: vitalia
> Ticket: T-12
> Story: vitalia-slice-1-fidelizacion
> Surface: frontend
> Completed: 2026-05-20

## Summary

Implemented the `NPSTagBadge` cross-feature shared component for Vitalia. The component displays NPS scores (0–10) with color-coded category badges in Spanish neutro LatAm. Fully accessible (WCAG AA), Server Component compatible, and covered by 21 Vitest tests (100% line/branch/function coverage on the component itself).

## Files Created / Modified

| Action | File | Description |
|---|---|---|
| MODIFIED | `vitalia/frontend/src/components/shared/nps/NPSTagBadge.tsx` | Full rewrite to spec: size/variant props, role="status", aria-label format, data-nps-category |
| MODIFIED | `vitalia/frontend/src/components/shared/nps/index.ts` | Added exports for NpsBadgeSize + NpsBadgeVariant types |
| NEW | `vitalia/frontend/src/components/shared/nps/__tests__/NPSTagBadge.test.tsx` | 21 TDD tests (RED first, then GREEN) |
| NEW | `vitalia/frontend/src/components/shared/nps/NPSTagBadge.stories.tsx` | 15 Storybook stories (categories × sizes × variants × boundaries × fallback) |
| NEW | `vitalia/frontend/src/components/shared/nps/README.md` | Usage docs + props table + accessibility notes |

## TDD Protocol

- RED phase: test file written first with 21 tests. Ran → 20 failed (missing role="status", wrong aria-label format, missing size/variant props). Confirmed RED.
- GREEN phase: component rewritten to full spec. Ran → 21/21 passed.

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS — 0 errors |
| `eslint src/components/shared/nps/` | PASS — 0 errors, 0 warnings |
| `vitest run` (all 330 tests) | PASS — 330/330 |
| Architecture fitness (9 test files, 38 tests) | PASS — 38/38 |
| Coverage global threshold (≥20%) | PASS — no threshold errors |
| NPSTagBadge.tsx coverage | 100% lines/branches/functions/statements |
| FE-A1: no hsl/hex/rgb literals in TSX | PASS — all colors via vt-* classes |
| FSD-Lite: no cross-feature imports | PASS |
| No default exports | PASS |
| Spanish neutro LatAm | PASS — "detractor", "pasivo", "promotor" |

## Component API

```tsx
import { NPSTagBadge } from "@/components/shared/nps";

<NPSTagBadge score={9} />                           // promotor, md, badge
<NPSTagBadge score={5} size="sm" variant="chip" />  // detractor, sm, pill
<NPSTagBadge score={null} />                        // "Sin NPS" fallback
```

**Props:**
- `score: number | null | undefined` — NPS 0-10; null/undefined → "Sin NPS" fallback
- `size?: "sm" | "md" | "lg"` — default "md"
- `variant?: "badge" | "chip" | "tag"` — default "badge"
- `className?: string` — CSS passthrough

**Categories:**
- 0-6 → detractor (vt-bg-danger-12 + vt-text-danger)
- 7-8 → pasivo (vt-bg-warning-12 + vt-text-warning)
- 9-10 → promotor (vt-bg-success-12 + vt-text-success)

**Accessibility:**
- `role="status"` on all rendered elements
- `aria-label="Calificación NPS {score}, categoría {labelEs}"`
- `aria-label="NPS: sin datos"` on null fallback
- `data-nps-category="detractor|passive|promoter"` for stable selectors

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | Required always — FSD-Lite boundaries, quality checklist, component patterns | Components/shared/ is correct FSD location for cross-feature shared components. No "use client" needed — pure rendering. TDD mandatory (RED→GREEN protocol followed). |
| `tessl__react-patterns` | Baseline always — error boundaries, loading/error/empty states, accessible markup, stable keys | Applied: role="status" on all states (including null fallback), aria-label descriptive, aria-hidden on decorative text. No useEffect, no useState — Server Component. |
| `tessl__shadcn-ui` | Component selection | No Shadcn primitive applies to a NPS badge. Implemented from scratch with Tailwind + cn(). No existing Shadcn primitive recreated. |
| `tessl__tailwind` | Utility-first + tokens | All classes via vt-* utilities from globals.css. cn() for conditional classes. No inline style={{}}. |
| `tessl__vitest` | New Vitest tests (21 tests) | happy-dom environment, @testing-library/react, @testing-library/jest-dom. getByRole("status") for accessible queries. dataset.npsCategory for stable attribute selectors. |
| `tessl__nextjs-app-router-modularization` | Checked Server/Client split | NPSTagBadge is pure rendering — no state, no effects, no event handlers. Stays Server Component (no "use client"). |
| `chrome-devtools-verify` | Live verification gate | DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Escalated to Chris staging gate — manual verification required before claiming feature correctness. |

## Downstream consumers (planned)

| Feature | Usage | Size | Variant |
|---|---|---|---|
| Inbox message list | inline filter chip | sm | chip |
| Fidelización stat card | NPS score display | lg | badge |
| Patient detail page | NPS history row | sm | tag |
| NPS table row | compact cell | sm | tag |

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge, requires rewrite for Linux Mint per project_context note). Manual verification escalated to Chris staging gate — component correctness verified via tsc + eslint + vitest (330 tests green) but feature correctness in real browser requires staging deployment.

## Storybook Stories (15 total)

- Detractor, Pasivo, Promotor (category representative values)
- SizeSm, SizeMd, SizeLg (size variants)
- VariantBadge, VariantChip, VariantTag (shape variants)
- Score0, Score6, Score7, Score8, Score9 (boundary values)
- SinNPSNull, SinNPSUndefined (fallback states)
