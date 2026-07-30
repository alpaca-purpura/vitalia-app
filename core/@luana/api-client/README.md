# @luana/api-client

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/frontend/src/lib/api/` + `frontend/src/features/*/api/`  
**Lift commit:** `3282768` (feat(luana-ts-batch2): lift @luana/ui-kit, @luana/api-client, @luana/schemas)

## Overview

Typed HTTP client + per-module API adapters. `fetchClient` auto-injects
`X-Tenant-ID` from Clerk. All endpoints return typed Pydantic-mirrored
TypeScript interfaces.

## Key exports

- `src/http-client.ts` — `fetchClient(path, options)` base with tenant header injection
- `src/config.ts` — `API_BASE_URL` + request defaults
- `src/api/` — 20 module API adapters: `brand`, `offer`, `landing`, `analytics`,
  `connections`, `scheduling`, `social-media`, `copilot`, `crm`, `iam`,
  `assets`, `campaigns`, `advertising`, `ai-actions`, and more
