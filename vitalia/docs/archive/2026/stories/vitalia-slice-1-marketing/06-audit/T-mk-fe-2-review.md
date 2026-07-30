<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-mk-fe-2

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-fe-2 (Wave 5 — Bowtie SVG + StageTabs + Layout + StageDispatcher + ActivityFooter + page.tsx)
**Date:** 2026-05-20
**Brand:** vitalia
**Commits range:** ac7b3e9, aad4469
**Files Reviewed:** 11 (6 components + 1 page + 1 globals.css edit + 1 barrel append + 2 test files)
**Domains touched:** marketing FE layout shell + Bowtie SVG pixel-invariante
**Skills consulted:** frontend-expert, tessl__react-patterns (Server Component delegation, sticky layout), tessl__nextjs-app-router-modularization (page.tsx pure Server)
**Live-verified:** N/A (deferred to T-mk-fe-7 + Chris staging gate)
**Verdict:** **PASS**

## /test-frontend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint | PASS | 0 errors |
| Vitest marketing | PASS | 11 new tests (MarketingLayout + MarketingStageTabs SC-MK-03) |
| Arch fitness (42 tests) | PASS | 42/42, no allowlist growth |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | `app/marketing/page.tsx` pure Server Component; `MarketingLayout` correctly `"use client"` for nuqs |
| 3 | React Patterns | PASS | error/loading states present; stable keys (`stage.slug`); no array index for dynamic list |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | `<figure aria-label>`, `<svg role="img">`, `<nav role="tablist">`, `role="tab" aria-selected aria-controls`; count badge `aria-label` |
| 6 | Forms (RHF + Zod) | N/A | no forms in this ticket |
| 7 | Multitenancy | PASS | inherited from T-mk-fe-1 hook (`useBowtieSummary`); page redirects unauth `/sign-in` |
| 8 | Master Data / Spanish | PASS | all strings via `MARKETING_COPY`; no toLocaleDateString in this ticket |
| 9 | Security / Deps | PASS | no `dangerouslySetInnerHTML`, no inline `<script>` |
| 10 | Tests / TDD | PASS | 11 tests RED→GREEN per T-mk-fe-2-result.md |
| 11 | Domain Alignment / Agentic UI | PASS | bowtie geometry matches mockup pixel-invariante (viewBox 0 0 900 180) |
| 12 | Architecture Fitness | PASS | 42/42 |
| 13 | Mirror detection | PASS | scaffolds in `components/shared/marketing/` remain unused stubs (documented Slice 2 ui-kit lift candidate per 03-arch-fe.md § 1) |
| 14 | Decisions honored cite (R6) | N/A | no decisions_applicable |

## Strengths

- **page.tsx pure Server Component** with `auth()` redirect; `MarketingLayout` is the only Client boundary delegated to. Metadata exported at top — correct Next.js 16 App Router pattern. No premature `"use client"` on page.
- **SVG geometry pixel-invariante:** STAGE_GEOMETRY tuples (cx,cy,rx,ry) + ARROW_CONNECTORS + COUNT_FONT_SIZES are constants matching mockup. CSS vars (`var(--vitalia-cian-color)`, `var(--vitalia-azul-marino-color)`, `var(--vitalia-purpura-color)`, `var(--vitalia-verde-lima-color)`, `var(--vitalia-text-color)`, `var(--vitalia-text-muted-color)`) — zero hardcoded HEX.
- **Loading / error / empty states all implemented** in Bowtie SVG (text overlays) and MarketingLayout (`role="alert"` on error). `aria-busy` set during load.
- **Bowtie sticky-top SC-MK-03 implemented:** `sticky top-0 z-10` on container div + `data-testid="bowtie-sticky-container"`. Tab change uses nuqs `replace` history.
- **Tab a11y:** `role="tablist"` with `aria-label="Etapas del embudo"`; per-tab `aria-selected`, `aria-controls`, `id` for tabpanel linkage. Counts have descriptive `aria-label` ("182 en Atracción").
- **Stable keys**: `stage.slug` (not array index). `key={stage.slug}`.
- **forwardRef + displayName** correctly applied.
- **globals.css change additive** (`--vitalia-text-color` + 3 vt-* utility classes); pre-commit hook would catch regressions.

## Findings

(no FAILs)

(no WARNs)

## Contract / UI-SPEC Compliance

- [x] Bowtie matches `02-design-ui-mockup.html` (viewBox 0 0 900 180, 5 ellipses, 4 arrow connectors)
- [x] Sticky top per `02-design-ui.md § 1` layout diagram
- [x] Tabs per `02-design-ui.md § 1` (5 stages with count badges)
- [x] Activity footer per `02-design-ui.md § 4` template
- [x] Server/Client split per `03-arch-fe.md § 1` (page.tsx server, MarketingLayout client)

## Allowlist Movement / Native-First / Live Verification

- [x] No FE arch fitness allowlist grew
- [x] No docker/make e2e in commits
- [x] No `git add .`/`-A`/`-u`
- [x] Live verification deferred to T-mk-fe-7 (E2E Playwright smoke covers SC-MK-03 via mockup)

## Verdict Math

- 0 FAILs · 0 WARNs · → **PASS**

**Result:** APPROVED.
