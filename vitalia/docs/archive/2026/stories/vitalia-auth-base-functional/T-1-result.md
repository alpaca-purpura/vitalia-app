# T-1 Result — FE Clerk Middleware

**Story:** vitalia-auth-base-functional
**Ticket:** T-1 — FE — Clerk middleware (clerkMiddleware + createRouteMatcher)
**Surface:** frontend
**Brand:** vitalia
**Branch:** wip/vitalia

## Files Created

| File | Action | LOC |
|---|---|---|
| `vitalia/frontend/src/middleware.ts` | NEW | 38 |
| `vitalia/frontend/src/__tests__/middleware.test.ts` | NEW | 125 |

## Implementation Summary

`clerkMiddleware` + `createRouteMatcher` from `@clerk/nextjs/server` (Clerk v6.36.8).

Public routes configured:
- `/sign-in(.*)` — sign-in page
- `/sign-up(.*)` — sign-up page
- `/public(.*)` — public landing por clínica
- `/api/v1/vitalia/webhooks(.*)` — webhooks Clerk (BE valida con HMAC)
- `/api/health` — health check

All other routes → `auth.protect()` (Clerk handles redirect to `/sign-in` internally).

Constraints honored:
- No `NextResponse.redirect` manual to `/sign-in`
- No RBAC (role checks) in middleware
- No `"use client"` directive (Edge Runtime module)
- Matcher excludes `_next` + static assets (html/css/js/images/fonts/icons)

## TDD Flow

RED → GREEN per `.claude/rules/tdd-mandatory.md`:

1. Created `middleware.test.ts` with 7 test cases → RED (middleware.ts not found: 1 test failing)
2. Created `middleware.ts` → GREEN (7/7 tests passing)

## Validator Gate Outputs

### nf-fe-tsc (`npx tsc --noEmit`)
```
Exit code: 0 — 0 errors
```

### nf-fe-eslint (`npx eslint src/ --cache --max-warnings=0`)
```
Exit code: 0 — 0 errors, 0 warnings
```

### nf-fe-arch-fitness (`npx vitest run src/__tests__/architecture/`)
```
38 tests passed across 9 test files — EXIT 0
No new allowlist violations introduced (ratchet preserved).
```

### Full vitest suite with coverage (`npx vitest run --coverage`)
```
Tests: 306 passed (306)
Coverage (v8):
  All files | % Stmts: 26.46 | % Branch: 58.59 | % Funcs: 33.33 | % Lines: 26.46
  Threshold: ≥20% all categories — PASS
```

## Gherkin Coverage

Per `06-tickets.yaml::gherkin_coverage`:

| Scenario | Test | Status |
|---|---|---|
| SC-01 Usuario no autenticado → redirect `/sign-in` | `src/__tests__/middleware.test.ts` — "protege rutas no públicas via auth.protect()" | PASS |
| SC-02 Ruta pública `/public/*` → 200, sin redirect | `src/__tests__/middleware.test.ts` — "configura rutas públicas esperadas" | PASS |

Note: E2E validation (Playwright) for SC-01/SC-02 depends on T-3 (env vars + stack up). Structural unit tests confirm correct implementation per validator gate.

## Skills Consulted (Step 0 GATE)

| Skill | Invocada? | Decision |
|---|---|---|
| `frontend-expert` | ✅ yes (runtime-quality-checklist) | No useEffect for data fetch, no stale closures; middleware is Edge Runtime non-React module |
| `tessl__react-patterns` | ✅ yes (baseline) | N/A — middleware.ts is not a React component; no error boundaries needed |
| `tessl__nextjs-app-router-modularization` | ✅ yes | middleware.ts is pure Edge module, not a Server/Client page — no split needed |
| `chrome-devtools-verify` | N/A (deprecated for Linux Mint — skill marked DEPRECATED) | Escalated: manual verification pending T-3 (env setup) + Chris staging gate |

## Notes

- `Validator pass: PENDING` in CONTEXT-BRIEF.md noted (R24 gap). `Faithfulness flag: clean` → proceeded per R24 rules.
- `chrome-devtools-verify` skill deprecated for Linux (designed for WSL2+Windows bridge). Live verification documented for Chris staging gate once T-3 completes env setup.
- Background agent T-4 BE Admin Streamlit was running in parallel during this ticket — no cross-contamination (vitalia/frontend scope only per M13/parallel-safety).
