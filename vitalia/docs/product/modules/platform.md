---
module: platform
brand: vitalia
last_updated: 2026-05-23
---

# platform — Extension SDK mount + Slice 1 foundations + Shell organism (Fase 1)

Punto único de montaje de la marca Vitalia sobre `core/luana-core-extension-sdk`. Define el contrato declarativo (`brand.yaml`) y registra los 18 extension points en un solo `register_all(registry)`.

Reference pattern: `apps/test-brand` (Story 8 cement).

Post Slice 1 (2026-05-18) incluye: design tokens foundation (globals.css + vt-* utility classes + Tailwind v4 + Shadcn pattern) y 15 migrations idempotent Slice 1 schema (12 tables + 4 column additions + pgcrypto BYTEA + audit_log PARTITIONED).

Post Fase 1 shell-organism (chain F1-S0..S3 COMPLETE 2026-05-23): Shadcn UI install + design tokens theme (light/dark + agent palette) + TopBarGlobal (LogoMark + ThemeToggle + TenantSwitcher slot) + TenantSwitcher organismo (Zustand persist + React Query useTenants + Clerk signOut cleanup + path preservation hard redirect).

## Capabilities

<!-- auto-list:start -->
- `vertical-medical-extension-sdk` (live)
- `vitalia-design-tokens-foundation` (live)
- `vitalia-design-tokens-theme` (live)
- `vitalia-migrations-slice-1-schema` (live)
- `vitalia-shell-foundation-shadcn-tailwind-v4` (live)
- `vitalia-tenant-switcher` (live)
- `vitalia-topbar-global` (live)
<!-- auto-list:end -->
