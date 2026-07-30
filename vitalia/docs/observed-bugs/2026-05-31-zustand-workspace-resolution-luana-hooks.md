# Observed bug — FE 500: zustand unresolved from core/@luana/hooks

**Observed during:** vitalia-fase2-lisa-doctores autonomous build (pre-T-E2E live check, 2026-05-31).
**Origin:** promotion commit cf19d1f5 "lift SSR-safe persisted store factory to @luana/hooks" — NOT this story.
**Symptom:** FE :3002 → HTTP 500. Turbopack: `Module not found: Can't resolve 'zustand'` in
`core/@luana/hooks/src/create-ssr-safe-persisted-store.ts:34`. Import trace: tenant-store.ts → useSignOutCleanup.ts
→ TenantStoreBootstrap.tsx → app/layout.tsx (all pre-existing shell code).
**Root cause:** pnpm workspace hoisting — `@luana/hooks` workspace pkg declares zustand but it's not resolvable
from its own context in the current install state (correlates with churning untracked pnpm-lock.yaml files).
**Scope discipline:** cross-cutting workspace/env issue, NOT lisa-doctores code. Our staff code (staff-ui-store.ts)
uses zustand correctly; unit/vitest pass (2411/2411) because vitest resolves it fine — only the dev-server turbopack
build breaks. NOT fixed inline (shared workspace + parallel-session risk).
**Fix (Chris/ops):** `pnpm install` at root to repair @luana/hooks hoisting + restart FE dev server.
Likely also resolves the pnpm-lock.yaml churn.
**Blocks:** live FE render → live E2E (T-E2E) → ADR-vitalia-008 dev_app_verified gate.
