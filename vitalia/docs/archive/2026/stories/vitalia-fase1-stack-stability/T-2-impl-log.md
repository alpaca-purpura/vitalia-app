---
ticket: T-2
story_id: vitalia-fase1-stack-stability
brand: vitalia
state: in-progress
started_at: 2026-05-23T00:05:00Z
depends_on: T-1
---

# T-2 — globals.css agent tokens + tailwind extend — Impl Log

## Skills Consulted
| Skill | Invoked | Decision |
|---|---|---|
| `frontend-expert` | YES | Preserve .vt-* legacy intact per ADR-vitalia-002 § 3, add @layer base |
| `tessl__tailwind` | YES | theme.extend.colors semantic tokens, no inline style |
| `tessl__shadcn-ui` | YES | CSS vars format H S% L% (no hsl() wrapper in :root vars) |

## Implementation Summary

### globals.css changes
- Added `@layer base { :root { ... } .dark { ... } }` block BEFORE the legacy `:root {`
- New block contains: Shadcn standard surface tokens (--background, --foreground, etc.) + 7 agent tokens + 6 soft variants
- Dark mode `.dark` block added with dark surface tokens + agent soft variants
- Existing legacy `:root { --vitalia-* }` and all `.vt-*` classes PRESERVED intact
- Added comment separating legacy block: "Legacy vitalia brand tokens (preserved — see ADR-vitalia-002 § 3)"

### tailwind.config.ts changes
- Added Shadcn semantic tokens to theme.extend.colors: background, foreground, primary, secondary, muted, accent, destructive, card, popover, border, input, ring
- Added `agent.*` nested tokens (lisa, lisa-soft, lucas, lucas-soft, adrian, adrian-soft, valeria, valeria-soft, camila, camila-soft, mateo, config)
- Preserved all existing `vitalia-*` color tokens
- Added `md` and `sm` borderRadius tokens for Shadcn compatibility (lg now maps to --radius per Design Contract)

### Quality gates
- `npx tsc --noEmit` → 0 errors
