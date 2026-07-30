---
ticket: T-1
story_id: vitalia-fase1-stack-stability
brand: vitalia
state: pushed
validator_ids: [val-t1-shadcn-components-json, val-t1-8-primitives-exist, val-t1-utils-cn, val-t1-tsc-clean, val-t1-eslint-clean]
---

# T-1 — Shadcn install + 8 primitives + utils.ts — Result

## Deliverables

### components.json
- Path: `vitalia/frontend/components.json`
- Style: new-york, baseColor: slate, cssVariables: true, rsc: true, tsx: true
- Alias `@/lib/utils` → `src/lib/utils.ts`

### 8 Shadcn primitives (named exports only, no default exports)
| # | Primitive | Path | Named exports |
|---|---|---|---|
| 1 | Button | `src/components/ui/button.tsx` | Button, buttonVariants |
| 2 | Avatar | `src/components/ui/avatar.tsx` | Avatar, AvatarImage, AvatarFallback |
| 3 | DropdownMenu | `src/components/ui/dropdown-menu.tsx` | DropdownMenu + 14 sub-components |
| 4 | Input | `src/components/ui/input.tsx` | Input |
| 5 | Badge | `src/components/ui/badge.tsx` | Badge, badgeVariants |
| 6 | Textarea | `src/components/ui/textarea.tsx` | Textarea |
| 7 | Tabs | `src/components/ui/tabs.tsx` | Tabs, TabsList, TabsTrigger, TabsContent |
| 8 | Tooltip | `src/components/ui/tooltip.tsx` | Tooltip, TooltipTrigger, TooltipContent, TooltipProvider |

### utils.ts
- Path: `src/lib/utils.ts`
- Exports: `cn()` (clsx + tailwind-merge)

### package.json additions
- clsx@^2.1.1, tailwind-merge@^3.6.0, class-variance-authority@^0.7.1, lucide-react@^1.16.0
- @radix-ui/react-slot@^1.2.4, @radix-ui/react-avatar@^1.1.11, @radix-ui/react-dropdown-menu@^2.1.16
- @radix-ui/react-tabs@^1.1.13, @radix-ui/react-tooltip@^1.2.8, @radix-ui/react-label@^2.1.8

## Validators

| Validator | Status |
|---|---|
| val-t1-shadcn-components-json | PASS — components.json exists with correct schema |
| val-t1-8-primitives-exist | PASS — all 8 tsx files in src/components/ui/ |
| val-t1-utils-cn | PASS — src/lib/utils.ts exports cn() using clsx+tailwind-merge |
| val-t1-tsc-clean | PASS — `npx tsc --noEmit` 0 errors |
| val-t1-eslint-clean | PASS — `npx eslint src/components/ui/ src/lib/utils.ts` 0 errors |

## Gherkin coverage
- SC-01 "Shadcn init produces components.json" → PASS
- SC-02 "8 primitives exist as named exports" → PASS
- SC-03 "cn() helper uses clsx+tailwind-merge" → PASS
