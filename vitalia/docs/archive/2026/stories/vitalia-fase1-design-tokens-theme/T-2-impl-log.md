# T-2 impl-log — vitalia-fase1-design-tokens-theme

## Ticket
T-2: Complete CSS vars in globals.css verbatim Design Contract § 5.1

## Surface
`vitalia/frontend/src/app/globals.css`

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | Verify dark mode selector with next-themes attribute pattern | Add `[data-theme="dark"]` alongside `.dark` selector |
| `tessl__tailwind` | Tailwind v4 darkMode config + CSS vars activation | Both selectors needed for CSS vars + Tailwind `dark:` variants |

## Implementation

F1-S0 already installed complete `:root` and `.dark` CSS blocks verbatim Design Contract § 5.1.

F1-S1 additions:
1. Changed `.dark` selector to `.dark, [data-theme="dark"]` — next-themes with `attribute="data-theme"` sets `<html data-theme="dark">` (not `class="dark"`), so CSS vars require the attribute selector.
2. Added `html[data-theme="dark"] { color-scheme: dark; }` for proper browser UI rendering (scrollbars, form controls) in dark mode.

All token values unchanged — verbatim from Design Contract § 5.1.

## Validators
- val-css-1: `:root` block has all 20 Shadcn standard tokens + 12 agent tokens ✅
- val-css-2: `[data-theme="dark"]` block has all 20 Shadcn dark tokens + 5 agent-soft dark tokens ✅
- val-css-3: No `.vt-*` block modified ✅

## Files modified
- `vitalia/frontend/src/app/globals.css` — `.dark` → `.dark, [data-theme="dark"]` + color-scheme dark rule

## Status: DONE
