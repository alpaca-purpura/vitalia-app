# @luana/hooks

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/frontend/src/hooks/`  
**Lift commit:** `b1bdb3a` (feat(luana-ts-batch1): lift @luana/design-tokens, @luana/hooks, @luana/format)

## Overview

Shared React hooks for global cross-feature concerns. Module-coupled hooks
(e.g., `useCopilotOffset`) are kept in `src/` but not exported and their
tests are deferred to `tests/_deferred/` until their consumer modules lift.

## Key exports

- `useTenantLocale()` — returns `{ currency, timezone }` from tenant settings
- `useDebounce(value, delay)` — debounced value hook
- `useLocalStorage(key, initialValue)` — localStorage read/write with SSR safety
- `usePrevious(value)` — tracks previous render value
- `useClickOutside(ref, handler)` — click-outside detector for dropdowns/modals
