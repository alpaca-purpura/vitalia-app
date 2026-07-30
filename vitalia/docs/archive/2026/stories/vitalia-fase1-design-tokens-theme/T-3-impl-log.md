# T-3 impl-log — vitalia-fase1-design-tokens-theme

## Ticket
T-3: tailwind.config.ts — verify/complete extend + darkMode config

## Surface
`vitalia/frontend/tailwind.config.ts`

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `tessl__tailwind` | Tailwind v4 darkMode config with attribute selectors | `darkMode: ['class', '[data-theme="dark"]']` |
| `frontend-expert` | Verify F1-S0 already has complete colors extend | F1-S0 had full colors; only darkMode line missing |

## Implementation

F1-S0 already installed complete `colors.extend` (background, foreground, primary, secondary, muted, accent, card, popover, border, input, ring, destructive, agent.*, vitalia-* brand tokens) + `borderRadius` + `backgroundImage` + `fontFamily`.

F1-S1 addition:
- Added `darkMode: ['class', '[data-theme="dark"]']` as first property in config object.
- This activates Tailwind `dark:` utility variants when either `.dark` CSS class OR `[data-theme="dark"]` HTML attribute is present — honoring next-themes `attribute="data-theme"` mode (D4 ratificada).
- Without this, Tailwind would use default `darkMode: 'media'` (OS preference), which contradicts D1 (`enableSystem: false`).

## Validators
- val-tw-1: `tailwind.config.ts` has `darkMode: ['class', '[data-theme="dark"]']` ✅
- val-tw-2: All Shadcn-standard color tokens present in `theme.extend.colors` ✅
- val-tw-3: Agent palette tokens present ✅
- val-tw-4: `borderRadius` lg/md/sm present ✅

## Files modified
- `vitalia/frontend/tailwind.config.ts` — added `darkMode: ['class', '[data-theme="dark"]']`

## Status: DONE
