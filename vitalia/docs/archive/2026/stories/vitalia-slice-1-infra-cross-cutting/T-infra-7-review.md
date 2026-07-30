# T-infra-7 review — APPROVED

> Auditor: Claude Opus 4.7 (orchestrator-direct)
> Date: 2026-05-18
> Surface: FE shell components + format helpers + fetchClient + PHI components
> Commit SHA: 347672c + 4545c22 (production .tsx token refactor)

## Scope
37 NEW files: format helpers (formatMoney / formatTenantDate / formatTenantDateTime / formatTenantRelative) + fetchClient (HIPAA-lite dual filter: X-Tenant-ID + X-Clinic-ID) + global hooks (useTenantLocale / useCurrentUser / useClinicId / useFeatureFlag / usePiiRoleGate) + agent components (agent-names / AgentAvatar / AgentAttribution) + PHI components (PiiMaskedSpan / RequireRole / AuditedSection) + shell (AppShell / Sidebar / TopBar) + copilot-rail (CopilotRail / CopilotChat) + domain widgets (NPSTagBadge / ContactSidebar / ActivityStreamSticky) + tests (26 component tests) + test-setup.ts.

Modified: globals.css (vt-* CSS utility classes — post-4545c22 expanded con 12 wrapped color vars + 6 NEW utility classes), vitest.config.ts, package.json (testing-library deps).

Post-defer-audit (4545c22): 3 production .tsx refactor de hsl literales a tokens:
- `AttributionMatrixWidget.tsx`: 1 hsl() opacity dinámica → `color-mix(in srgb, var(--vitalia-cian-color) ${opacity * 100}%, transparent)`
- `MarketingBowtieSVG.tsx`: 8 hsl() SVG fills/stops → `var(--vitalia-{cian,purpura,text-muted,text-faint}-color)`
- `WizardChatThread.tsx`: 2 hsl() inline styles → vt-bg-cian utility class

## Categorías scoring (8 FE categories)
1. **FSD-Lite boundaries** — ✅ shared/, hooks/, lib/format/, lib/api/, components/shared/ correctly scoped. No cross-feature imports
2. **Server-First** — ✅ AppShell / Sidebar / TopBar / CopilotRail son Server Components default. Hooks usePiiRoleGate / useFeatureFlag son client (correcto)
3. **Forms RHF+Zod** — N/A (T-infra-7 son layout components) ✅
4. **Master-data/currency** — ✅ formatMoney + formatTenantDate consume useTenantLocale (NEVER hardcoded 'USD' / hardcoded TZ)
5. **Spanish neutro** — ✅ Copy en tuteo. Test test_no_voseo_in_copy PASS
6. **Accessibility** — ✅ AppShell tiene roles ARIA. PiiMaskedSpan + RequireRole aria-label correctos
7. **Design tokens consumption** — ✅ Post-4545c22 zero hsl/hex literals en TSX. Wrapped vars usados solo en SVG/inline-style donde class no aplica
8. **HIPAA-lite PHI components** — ✅ PiiMaskedSpan field-type-aware masking (name/dni/phone/email/address/dob). RequireRole gate 3-role (doctor/nurse/admin_clinic). AuditedSection fires audit beacon on mount. fetchClient dual-filter (X-Tenant-ID + X-Clinic-ID) per `vitalia/.claude/rules/hipaa-lite.md`

## Findings count
- FAIL: 0
- WARN: 0

## Validators acceptance.validator_ids
- fe_typecheck_tsc: PASS (0 errors)
- fe_lint_eslint: PASS (0 errors post-fix)
- fe_arch_fitness: PASS 38/38 (test_no_hardcoded_colors + test_phi_pii_components_used GREEN)
- fe_test_shared: PASS 245/245 (coverage 64.19% ≥20%)

## Downstream regression
- Surface: vitalia/frontend/src/lib/ + components/shared/ + hooks/ → consumido por TODAS las features siguientes Slice 2 (onboarding-wizard, inbox, pipeline, agenda, fidelizacion, marketing)
- Engine consumer: cada brand tiene su FE independiente (NO cross-brand TS imports)
- Cross-brand mirror scan: ✅ ZERO matches (fetchClient + format helpers son brand-specific — cada brand tiene su propia versión per FSD-Lite rule)

## Self-fix log
Post-defer-audit (4545c22): 3 production .tsx refactor a tokens. Color-mix() para opacity dinámica (CSS standard 2023+). vt-bg-cian utility class agregado a globals.css.

## Verdict
**APPROVED**. T-infra-7 establece shell + componentes shared + PHI components con architectural HIPAA-lite enforcement. fetchClient dual-filter cardinal rule. Post-fix garantiza zero color literals. Server-First respect, FSD-Lite respect.
