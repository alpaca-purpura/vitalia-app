---
ticket: T-7
story: vitalia-fase2-lisa-marca
brand: vitalia
surface: FE
title: "FE Presencia sub-sub-tab — PresenciaView + WebsiteCard + SocialMediaLinksEditor + TrustSignalsEditor + LocationsCard"
state: pushed
commit: d53b4753
---

# T-7 Implementation Log — Presencia sub-sub-tab

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, studio section page lazy-loading pattern, barrel exports | Confirmed: `features/lisa/components/marca/presencia/` nesting; barrel via `index.ts`; page imports from `@/features/lisa` (barrel) |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys | Applied: `aria-busy`, `role="status"`, `role="list"`, semantic `<section>` with `aria-labelledby`, error alert fallback |
| `tessl__shadcn-ui` | Component selection — reuse from `components/ui/` | Reused: `Badge`, `Button`, `Input`, `Textarea`, `Skeleton`, `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormMessage` |
| `tessl__tailwind` | Semantic tokens, `cn()`, no inline hex | All colors via `var(--social-*)` CSS variables defined in `globals.css`; no hex in TSX |
| `tessl__zod` | Form schemas for website + social media validation | Reused existing `presenceSchema` + `socialMediaSchema` from T-8 |
| `tessl__nextjs-app-router-modularization` | page.tsx Server Component + PresenciaView "use client" split | Applied: page.tsx = thin Server Component; PresenciaView.tsx = "use client" root |
| `tessl__graceful-degradation` | React Query retry + loading/error states on each async boundary | Applied: `isLoading` skeleton, `isError` alert, `enabled` guard |
| `chrome-devtools-verify` | Live verification gate | DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Escalated to Chris staging gate. Dev environment requires `make dev-vitalia` + manual browser check. |

## Architecture Pattern

ADR-vitalia-004 v1.1 — N3-static SubSubTabsBar. Route: `(shell-organism)/lisa/marca/presencia/page.tsx`.

## Files Created

| File | Purpose |
|---|---|
| `vitalia/frontend/src/features/lisa/api/marca-presence-api.ts` | API client: GET/PUT contact, GET trust-signals, POST/DELETE trust-signal, GET trust-catalog, GET locations |
| `vitalia/frontend/src/features/lisa/hooks/useContactAutosave.ts` | Autosave hook: 600ms debounce → PUT /lisa/marca/contact |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/PresenciaView.tsx` | "use client" root — composes all 4 cards + section header + AutosaveBadge |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/InfoBannerLandingDescoped.tsx` | Info callout — landing pública deferred to future story |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/WebsiteCard.tsx` | URL input + conn-status (ok/error/missing) + hint; autosave on change |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/SocialMediaLinksEditor.tsx` | 5 social rows (Instagram/TikTok/Facebook/Google/WhatsApp) + disabled "+ Agregar otra red" |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/TrustSignalsEditor.tsx` | OQ-D hybrid: active chips + `<details>` catalog grid (PE 8 entries) + free-text "Otra" + años/pacientes/premios |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/LocationsCard.tsx` | Read-only sedes from clinics module; Editar + Agregar sede disabled (future story) |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/index.ts` | Barrel exports |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/__tests__/PresenciaView.test.tsx` | 7 unit tests |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/__tests__/WebsiteCard.test.tsx` | 6 unit tests |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/__tests__/SocialMediaLinksEditor.test.tsx` | 7 unit tests |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/__tests__/TrustSignalsEditor.test.tsx` | 10 unit tests including A1 (PE 8-entry catalog) |
| `vitalia/frontend/src/features/lisa/components/marca/presencia/__tests__/LocationsCard.test.tsx` | 7 unit tests |

## Files Modified

| File | Change |
|---|---|
| `vitalia/frontend/src/features/lisa/api/marca.ts` | Extended `marcaKeys` factory: contact, trustSignals, trustCatalog, locations |
| `vitalia/frontend/src/features/lisa/api/marca-presence-api.ts` | Fixed `updateContact` to use `BrandContactPatchPayload` (camelCase API keys) |
| `vitalia/frontend/src/features/lisa/index.ts` | Added PresenciaView + API response types to barrel |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/presencia/page.tsx` | Replaced T-7 placeholder with `<PresenciaView tenantId={tenantId} />` |
| `vitalia/frontend/src/app/globals.css` | Added `--social-{instagram,tiktok,facebook,google,whatsapp}-*` CSS variables |

## Key Implementation Decisions

### OQ-D Hybrid Trust Catalog
- Active trust signals fetched via `GET /lisa/marca/trust-signals`
- PE catalog fetched via `GET /lisa/marca/trust-catalog/PE` (staleTime 10min — catalog rarely changes)
- Expandable via native HTML `<details>/<summary>` (no Shadcn Accordion — avoids anti-pattern of nested components just for this toggle)
- Checkbox grid: checking = POST trust signal; unchecking = DELETE trust signal (mutation per item)
- Free-text "Otra" adds with `catalogCode: null` via POST

### Social Icon Colors
- Arch fitness test `test_no_hardcoded_colors` blocked inline hex literals in TSX
- Solution: added CSS custom properties `--social-{name}-bg/gradient` to `globals.css` (globals.css is the exempt file per arch test)
- TSX uses `style={{ background: "var(--social-instagram-gradient)" }}` (no hex)

### ContactPatchPayload
- Hook defines `ContactPatchPayload = BrandContactPatchPayload` (re-export alias)
- API uses camelCase per 03-arch.md § 4.3 (`websiteUrl`, `instagramHandle`, `tiktokHandle`, `facebookPage`, `googleBusinessUrl`, `whatsappBusiness`)
- Form field names (snake_case from Zod schema) mapped to camelCase in `handleFieldChange`

### autosave on-change
- `scheduleAutosave` wired in PresenciaView via `handleScheduleAutosave` (stable `useCallback` ref)
- WebsiteCard, SocialMediaLinksEditor: autosave on each field change
- TrustSignalsEditor: años/pacientes/premios autosave via `onScheduleAutosave`; certifications use independent mutations (not debounced — immediate ADD/REMOVE per OQ-D spec)
- LocationsCard: read-only — no autosave

### Form hydration pattern
- `useEffect([serverValue, form])` calls `form.reset(...)` to hydrate from server on initial load
- Follows same pattern as `IdentidadView.tsx` (T-5)

## Quality Gates

| Gate | Result |
|---|---|
| tsc --noEmit | 0 errors |
| eslint src/ | 0 errors |
| vitest run | 2081/2081 PASS (196 test files) |
| Architecture tests | 196/196 PASS (test_no_hardcoded_colors FIXED, test_no_cross_feature_imports FIXED) |
| ESLint warning baselines | check-file / jsdoc / react-perf — no increase |

## Acceptance Criteria Status

| AC | Status |
|---|---|
| A1: PE catalog 8 entries | PASS — TrustSignalsEditor.test.tsx verifies 8 PE catalog codes: DIGESA, MINSA, SUSALUD, COLEGIO_MEDICO, ISO_9001, JCI, ACHS, WHO_SAFE |
| A2: Zod validation for social+website | PASS — socialMediaSchema + presenceSchema used via RHF zodResolver |
| A3: Spanish neutro | PASS — unit tests assert no voseo imperatives in labels/hints |
| A4: tsc + eslint GREEN | PASS |

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint host (requires WSL2+Windows bridge rewrite). Manual verification steps escalated to Chris staging gate:

1. `make dev-vitalia` — start stack
2. Navigate to `http://localhost:3002/{tenantId}/lisa/marca/presencia`
3. Verify: section header + AutosaveBadge + InfoBanner + 4 cards render
4. Verify: website URL input autosaves on typing (check Network tab → PUT /lisa/marca/contact after 600ms)
5. Verify: social rows show correct brand-colored icons
6. Verify: TrustSignalsEditor details expand + catalog items render with checkboxes
7. Verify: no console errors
