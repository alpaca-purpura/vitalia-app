---
ticket: T-1
story_id: vitalia-fase1-stack-stability
brand: vitalia
state: in-progress
started_at: 2026-05-23T00:00:00Z
---

# T-1 — Shadcn install + 8 primitives + utils.ts — Impl Log

## Skills Consulted (must_load enforcement v4.1)

| Skill | Invoked | Decision |
|---|---|---|
| `frontend-expert` | YES (always-on) | FSD-Lite boundaries, arch fitness ratchet, named exports only, no default exports |
| `tessl__shadcn-ui` | YES (F1-S0 touches components/ui) | Vendored copy-paste pattern (NOT npm package), style=new-york, cssVariables=true |
| `tessl__tailwind` | YES (cn() helper, theme tokens) | utility-first, cn() via clsx+tailwind-merge, no inline style |
| `tessl__react-patterns` | YES (always-on) | Named exports, no default exports, accessible markup |
| `hipaa-lite.md` | YES (brand overlay) | F1-S0 declared no-phi-scope (infra UI bootstrap, no auth routes) |
| `shell-mockup-per-component.md` | YES (brand overlay) | F1-S0 declared EXEMPT (infra-only, no user-facing components) |
| `chrome-devtools-verify` | N/A — DEPRECATED for Linux Mint (WSL2+Windows bridge) | Escalated to Chris staging gate manual |

## Implementation Summary

### Pre-flight discovery
- `src/lib/cn.ts` existed with simplified `cn()` (no clsx/tailwind-merge)
- No `src/components/ui/` directory
- `clsx`, `tailwind-merge`, `class-variance-authority`, `@radix-ui/*` NOT in package.json
- Shadcn CLI v4.8.0 has different `init` flags — manual approach used

### Approach taken
1. Shadcn CLI v4.8.0 `--base-color` flag doesn't exist → created `components.json` manually per 03-arch.md § 2.1 verbatim
2. Installed dependencies via `pnpm add`: `clsx tailwind-merge class-variance-authority lucide-react @radix-ui/react-slot @radix-ui/react-avatar @radix-ui/react-dropdown-menu @radix-ui/react-tabs @radix-ui/react-tooltip @radix-ui/react-label`
3. Created 8 Shadcn primitives (new-york style) from official registry patterns
4. Created `src/lib/utils.ts` with standard Shadcn `cn()` (clsx + tailwind-merge)

### Files created
- `vitalia/frontend/components.json` — Shadcn config verbatim per 03-arch.md § 2.1
- `vitalia/frontend/src/components/ui/button.tsx` — named exports: Button, buttonVariants
- `vitalia/frontend/src/components/ui/avatar.tsx` — named exports: Avatar, AvatarImage, AvatarFallback
- `vitalia/frontend/src/components/ui/dropdown-menu.tsx` — named exports: DropdownMenu + 14 sub-components
- `vitalia/frontend/src/components/ui/input.tsx` — named export: Input
- `vitalia/frontend/src/components/ui/badge.tsx` — named exports: Badge, badgeVariants
- `vitalia/frontend/src/components/ui/textarea.tsx` — named export: Textarea
- `vitalia/frontend/src/components/ui/tabs.tsx` — named exports: Tabs, TabsList, TabsTrigger, TabsContent
- `vitalia/frontend/src/components/ui/tooltip.tsx` — named exports: Tooltip, TooltipTrigger, TooltipContent, TooltipProvider
- `vitalia/frontend/src/lib/utils.ts` — named export: cn()

### Files modified
- `vitalia/frontend/package.json` — added 11 dependencies (clsx, tailwind-merge, class-variance-authority, lucide-react, @radix-ui/react-{slot,avatar,dropdown-menu,tabs,tooltip,label})

### Quality gates
- `npx tsc --noEmit` → 0 errors
- `npx eslint src/components/ui/ src/lib/utils.ts` → 0 errors

## Supply-chain notes (ADR-vitalia-002 § 7)
- Primitives match new-york style from https://ui.shadcn.com/r/ (Shadcn v4.8.0 registry)
- `@radix-ui/*` packages pinned to latest stable at install time (lockfile in pnpm-lock.yaml)
- No custom modifications to primitive internals — pure copy from official registry
- Auditor review of diff vs official registry required per 03-arch.md § 3.4
