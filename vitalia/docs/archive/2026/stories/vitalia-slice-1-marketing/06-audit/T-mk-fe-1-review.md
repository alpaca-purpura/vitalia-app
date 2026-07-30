<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-mk-fe-1

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-fe-1 (Wave 4 — FE foundation: types + Zod + nuqs + MARKETING_COPY + React Query hooks)
**Date:** 2026-05-20
**Brand:** vitalia
**Commits range:** 866079b..a2e1630
**Files Reviewed:** 23 (8 types + 1 Zod + 1 copy + 10 hooks + 1 store + 2 barrels)
**Domains touched:** marketing FE foundation (consumer-only of Lucas BE shipped)
**Skills consulted:** frontend-expert (FSD-Lite), tessl__react-patterns (hooks structure), tessl__zod (Zod schema for BE mirror)
**Live-verified:** N/A (data layer only — no rendered UI)
**Verdict:** **PASS**

## /test-frontend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint | PASS | 0 errors, 0 warnings |
| Vitest marketing | PASS | 7/7 marketing-parsers + Zod smoke tests (T-mk-fe-1) |
| Arch fitness (42 tests) | PASS | 42/42 |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 (correct `"use client"` only on hooks/store) |
| 3 | React Patterns | PASS | 0 (no useEffect for data fetch — React Query) |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | N/A | data layer only |
| 6 | Forms (RHF + Zod) | PASS | Zod schema mirrors Pydantic BE |
| 7 | Multitenancy | PASS | `useClinicId()` + `orgId` from Clerk passed to fetchClient on every hook |
| 8 | Master Data / Spanish | PASS | MARKETING_COPY neutro confirmed; no toLocaleDateString here |
| 9 | Security / Deps | PASS | no `dangerouslySetInnerHTML`, no `eval`, no secrets |
| 10 | Tests / TDD | PASS | 7 tests RED→GREEN documented per T-mk-fe-1-result.md |
| 11 | Domain Alignment / Agentic UI | PASS | Consumer-only of Lucas tools (sales-agent-expert invariant respected) |
| 12 | Architecture Fitness | PASS | 42/42 |
| 13 | Mirror detection | PASS | No cross-brand mirror (verified `find {nicolify,comunify,lupulo}/frontend/src -name "*marketing*"` = empty) |
| 14 | Decisions honored cite (R6) | N/A | ticket has no `decisions_applicable` field |

## Strengths

- **HIPAA-lite dual filter enforced:** every hook (10 total) destructures `useAuth() → { getToken, orgId }` + `useClinicId() → clinicId`, passes both into `fetchClient` so X-Tenant-ID + X-Clinic-ID flow consistently. `enabled: isLoaded && isSignedIn === true && Boolean(clinicId)` guard on every `useQuery`.
- **Idempotency-Key correct:** 4 mutation hooks (approve/reject/undo/sync) inject `crypto.randomUUID()` per call → BE idempotent semantics preserved.
- **nuqs URL state SSoT:** 7 marketingParsers configured with `withOptions({ history: "replace" })` for intra-route changes per SC-MK-03.
- **Zod runtime validation present:** `lucas-recommendation.ts` mirror of Pydantic snake_case DTO with `z.string().datetime({ offset: true })` for ISO 8601, `.nullable()` on optional fields, enum for stage/status/rejectReason.
- **Spanish neutro:** MARKETING_COPY uses tuteo only (`Aprobar`, `Cancelar`, `Selecciona`, `Intenta de nuevo`); no voseo terms. JSDoc comments document the rule explicitly.
- **HIPAA marker on ReferralsRow type:** `referrerPatientIdHash` documented with `NEVER patient.name per phi_fields.py` — defense in depth.
- **No default exports** in feature TS (`*.stories.tsx` exempt as Storybook convention).
- **No `any` types** anywhere in scope (uses `Record<string, unknown>` for rationale/payload JSON).
- **Barrel exports only** (`features/marketing/index.ts`, `features/marketing-shared/index.ts`).

## Findings

(no FAILs)

### WARN — `staleTime` deviates from guidelines

**Category:** 4 (Code Quality — alignment with 05-guidelines.md § 2.14)
**File:** all 6 query hooks (`use-bowtie-summary.ts:36`, `use-stage-detail.ts:38`, `use-channel-detail.ts:36`, `use-lucas-recommendations.ts:32`, `use-attribution-matrix.ts:37`, `use-referrals.ts:37`)
**Issue:** Guidelines § 2.14 specify `staleTime: 5 * 60 * 1000` (5 min). Implementation uses `30_000` (30s) for recommendations/channels and `60_000` (1min) for bowtie/stage/attribution/referrals. Likely a minor product trade-off (more frequent revalidation) — but undocumented divergence.
**Fix:** Either (a) align to 5min per guidelines, or (b) leave a short comment in each hook explaining why this surface uses shorter staleTime (e.g., "Lucas cron is daily but UI wants quicker poll-detection of new recommendations"). Auditor self-fix permissible (whitelist #5 comment add) but recommends builder ratify the deviation.
**Skill ref:** `frontend-quality.md` / 05-guidelines.md § 2.14 React Query patterns.

## Contract / UI-SPEC Compliance

- [x] All TypeScript types from `03-arch-fe.md § 2` implemented (camelCase mirror of Pydantic; ISO 8601 typed as `string`; optionals explicit `| null`)
- [x] nuqs parsers per `03-arch-fe.md § 3` (7 params, replace history)
- [x] React Query hook signatures per `03-arch-fe.md § 4`
- [x] Zustand store per `03-arch-fe.md § 5` (bowtieAnimating + pendingUndoTimers Map)
- [x] HIPAA-lite type marker on PHI-adjacent field (`referrerPatientIdHash`)

## Allowlist Movement / Native-First / Live Verification

- [x] No FE arch fitness allowlist grew
- [x] No `docker exec` or `make e2e*` in commits (native commands only)
- [x] No `git add .` / `-A` / `-u` (staged by name)
- [x] Live verification N/A (data-layer ticket — chrome-devtools-verify only required for user-facing UI changes)

## Verdict Math

- 0 FAILs → not FAIL
- 1 WARN (staleTime) → ≤ 1 WARN total → **PASS**

**Result:** APPROVED — proceed forward. Auditor can self-fix WARN with a 1-line comment in each hook if Chris prefers documentation over deviation flag.
