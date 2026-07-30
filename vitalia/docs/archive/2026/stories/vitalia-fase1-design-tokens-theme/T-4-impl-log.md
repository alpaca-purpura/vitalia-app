# T-4 impl-log — vitalia-fase1-design-tokens-theme

## Ticket
T-4: layout.tsx — wrap with ThemeProvider + suppressHydrationWarning

## Surface
`vitalia/frontend/src/app/providers.tsx` + verify `vitalia/frontend/src/app/layout.tsx`

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `tessl__nextjs-app-router-modularization` | Server/Client boundary split for ThemeProvider | Add ThemeProvider inside providers.tsx (already "use client") not layout.tsx |
| `tessl__react-patterns` | SSR safety for theme provider | suppressHydrationWarning already present in layout.tsx from F1-S0 |
| `frontend-expert` | Where to place ThemeProvider in existing provider chain | providers.tsx is correct — layout.tsx stays pure Server Component |

## Implementation

**layout.tsx**: No changes needed. F1-S0 already added `suppressHydrationWarning` on `<html lang="es">`. This is required by next-themes to silence the legitimate SSR/client mismatch warning when it injects `data-theme` attribute via inline head script before React hydration.

**providers.tsx**: Added ThemeProvider import + wrap around `{children}` inside QueryClientProvider:
- `attribute="data-theme"` — sets `<html data-theme="light|dark">` (D4)
- `defaultTheme="light"` — explicit light default (D1)
- `enableSystem={false}` — no OS preference sync (D1)
- `storageKey="vitalia-theme"` — namespaced localStorage key (D4 multi-brand defense)

ThemeProvider wraps inside QueryClientProvider (outermost data provider) since theme is independent of auth/queries.

## Provider tree (post T-4)
```
RootLayout (Server Component)
  <html lang="es" suppressHydrationWarning>
  <body>
    <Providers> (Client Component)
      <ClerkProvider>
        <QueryClientProvider>
          <ThemeProvider attribute="data-theme" defaultTheme="light" enableSystem={false} storageKey="vitalia-theme">
            {children}
```

## Validators
- val-provider-1: ThemeProvider wraps entire subtree ✅
- val-provider-2: suppressHydrationWarning on <html> ✅
- val-provider-3: attribute="data-theme" (not class) ✅
- val-provider-4: enableSystem={false} ✅
- val-provider-5: storageKey="vitalia-theme" ✅

## Files modified
- `vitalia/frontend/src/app/providers.tsx` — added ThemeProvider wrap
- `vitalia/frontend/src/app/layout.tsx` — no changes (suppressHydrationWarning already present)

## Status: DONE
