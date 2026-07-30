---
paths:
  - "**/frontend/src/**"
  - "**/frontend/next.config.ts"
  - "**/frontend/tsconfig.json"
description: Frontend FSD-Lite (per-brand)
---

# Frontend FSD

> **Tier-2 `paths:` (W1-Phase2 2026-06-09 · tier: project).** Esta rule NO carga always-on — inyecta al leer un archivo que matchea `paths:` (test empírico #16299 OK — `harness-refactor-w1/W1-phase2-execution.md §3`; el viejo `globs:` era mecanismo MUERTO, CC lo ignora). Caveat #23478: no dispara en write puro de archivo nuevo — el gate mecánico (eslint/tsc/ruff/arch-tests) cubre ese hueco.

Cada brand tiene su propio `{brand}/frontend/` independiente (nicolify, vitalia, comunify, lupulo).

```
{brand}/frontend/src/
  app/                 # Next.js App Router (thin)
  components/{ui,shared}/
  features/{domain}/   # api/, components/, hooks/, config/, context/, types/, utils/
  lib/                 # API client, tokens, utils
  hooks/               # Global hooks
```

Shared TS packages cross-brand viven en `core/luana-core-*/` (TS) y se consumen vía `@luana/*` imports (registrados en `pnpm-workspace.yaml`).

## Boundary matrix (`boundaries/dependencies: error`, 0 violations)

| From \ To | feature | feature:own | shared | ui | lib | util | hooks | providers |
|---|---|---|---|---|---|---|---|---|
| app | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| feature | — | own only | ✅ | — | ✅ | ✅ | — | — |
| feature:own | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| shared | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| lib | — | — | — | — | — | ✅ | — | — |

Excepciones: `feature:own` → `feature` (sub-components context). `shared` → `feature(:own)` (sidebar/tenant-switcher).

## Constraints
- Server Components default. `"use client"` solo cuando necesario.
- React Query (data fetch). RHF + Zod (forms). Tailwind + `cn()`.
- No `any` (`unknown` + type guards). No default exports (excepto Next pages).
- `fetchClient` auto-inyecta `X-Tenant-ID`.

## Cross-feature / cross-brand imports
- Cross-feature dentro del mismo brand: Forbidden default. Excepción: `copilot` (infra-like). Shared → `components/shared/` o `lib/`.
- Cross-brand: absolutamente prohibido (`vitalia/frontend/` NUNCA importa `nicolify/frontend/`). Compartir via `@luana/*` engine packages.

## Studio section pages
Patrón lazy-loading per-section (brand-studio, offer-studio, futuros) per brand. Detalle + arch tests + factory pattern → `frontend-expert` skill (`references/studio-section-pages.md`).

## Multibrand awareness (post reorg 2026-05-15)

- Engine TS packages (`@luana/*` exportados desde `core/luana-core-*/`) modificación requiere `/pm-luana` promotion gate.
- Cada brand tiene su `next.config.ts`, `tailwind.config.ts`, `tsconfig.json` independiente.
- Brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow) heredan este FSD-Lite al bootstrap.
