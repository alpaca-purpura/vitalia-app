# T-2 result — globals.css dark selector for data-theme

**Ticket:** T-2
**Story:** vitalia-fase1-design-tokens-theme (F1-S1)
**State:** done

## Summary

Updated `vitalia/frontend/src/app/globals.css` dark selector from `.dark` to `.dark, [data-theme="dark"]` so that CSS vars activate when next-themes sets `<html data-theme="dark">`.

Also added `html[data-theme="dark"] { color-scheme: dark; }` for browser UI elements (scrollbars, form controls) to adopt dark mode.

## Validators GREEN

- `.dark, [data-theme="dark"]` selector present in globals.css ✅
- `color-scheme: dark` rule present ✅
- All 20 Shadcn dark tokens correct ✅
- All 5 agent-soft dark tokens present ✅

## Files modified

- `vitalia/frontend/src/app/globals.css`
