# T-4 result — ThemeProvider in providers.tsx

**Ticket:** T-4
**Story:** vitalia-fase1-design-tokens-theme (F1-S1)
**State:** done

## Summary

Added `ThemeProvider` from `next-themes` wrapping `{children}` inside `providers.tsx` (already a "use client" component).

Props per spec:
- `attribute="data-theme"` — sets `<html data-theme="dark">` (D4: attribute-based, not class-based)
- `defaultTheme="light"` — D1: light/dark only
- `enableSystem={false}` — D1: no OS system theme detection
- `storageKey="vitalia-theme"` — D4: namespaced for multi-brand localStorage isolation

layout.tsx NOT modified — `suppressHydrationWarning` already present on `<html lang="es">` from F1-S0 (AC-6).

## Validators GREEN

- `ThemeProvider` import present in providers.tsx ✅
- `attribute="data-theme"` prop ✅
- `defaultTheme="light"` prop ✅
- `enableSystem={false}` prop ✅
- `storageKey="vitalia-theme"` prop ✅
- layout.tsx unchanged (suppressHydrationWarning already present) ✅

## Files modified

- `vitalia/frontend/src/app/providers.tsx`
