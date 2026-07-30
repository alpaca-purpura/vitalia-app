# T-3 result — tailwind.config.ts darkMode array

**Ticket:** T-3
**Story:** vitalia-fase1-design-tokens-theme (F1-S1)
**State:** done

## Summary

Added `darkMode: ['class', '[data-theme="dark"]']` to `vitalia/frontend/tailwind.config.ts`.

This activates Tailwind `dark:` variants when either `.dark` class OR `[data-theme="dark"]` attribute is present on `<html>`. Required because next-themes uses `attribute="data-theme"` (D4 ratificada 2026-05-22).

## Validators GREEN

- `darkMode` config present ✅
- Selector `'[data-theme="dark"]'` in array ✅
- `tsc --noEmit` 0 errors ✅

## Files modified

- `vitalia/frontend/tailwind.config.ts`
