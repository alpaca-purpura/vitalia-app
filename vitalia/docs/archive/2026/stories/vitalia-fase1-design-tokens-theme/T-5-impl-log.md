# T-5 impl-log — vitalia-fase1-design-tokens-theme

## Ticket
T-5: ThemeToggle TDD RED→GREEN + vars introspection test

## Surface
- `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` (NEW)
- `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.test.tsx` (NEW)
- `vitalia/frontend/src/__tests__/tokens/test-shadcn-vars-resolvable.test.ts` (NEW)

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `tessl__react-patterns` | Error boundaries, accessible markup, aria attrs | aria-label dynamic + aria-pressed boolean + sr-only span |
| `tessl__vitest` | Test setup with ThemeProvider wrapper, async theme resolution | `act()` + `setTimeout(0)` for next-themes async init |
| `tessl__shadcn-ui` | Button ghost icon variant reuse | `<Button variant="ghost" size="icon">` from @/components/ui/button |
| `frontend-expert` | Named export enforcement, "use client" justification | Named export ✅, "use client" needed for useTheme hook |

## Implementation

### TDD cycle

**RED phase**: Created `ThemeToggle.test.tsx` with 7 tests before `ThemeToggle.tsx` existed.
Ran vitest → 1 test file failed (module not found). ✅ Confirmed RED.

**GREEN phase**: Created `ThemeToggle.tsx` with:
- `"use client"` directive (required by useTheme hook)
- `import { useTheme } from "next-themes"` direct (D5 — no wrapper hook)
- `import { Button } from "@/components/ui/button"` (Shadcn primitive reuse)
- `import { Moon, Sun } from "lucide-react"` (already installed via Shadcn F1-S0)
- Named export `export function ThemeToggle()`
- `aria-label` dynamic Spanish neutro: `"Cambiar tema (actual: claro/oscuro)"`
- `aria-pressed` boolean toggle state
- `data-testid="theme-toggle"` stable Playwright selector
- Conditional Sun/Moon icon per isDark state
- `<span className="sr-only">Cambiar tema</span>` a11y defense-in-depth

Ran vitest → 7/7 tests passed. ✅ Confirmed GREEN.

### Vars introspection test
Created `test-shadcn-vars-resolvable.test.ts` with 59 tests:
- Reads `globals.css` file content directly
- Verifies all 20 Shadcn-standard light tokens present
- Verifies all 12 agent light tokens present
- Verifies dark mode has `[data-theme="dark"]` selector
- Verifies all 20 Shadcn-standard dark tokens have ≥2 occurrences (light + dark)
- Verifies 5 agent-soft dark tokens have ≥2 occurrences
All 59 tests passed. ✅

## Test results
- `ThemeToggle.test.tsx`: 7/7 PASS
- `test-shadcn-vars-resolvable.test.ts`: 59/59 PASS

## Files created
- `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.test.tsx`
- `vitalia/frontend/src/__tests__/tokens/test-shadcn-vars-resolvable.test.ts`

## Status: DONE
