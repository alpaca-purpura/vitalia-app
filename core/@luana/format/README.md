# @luana/format

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/frontend/src/lib/format/`  
**Lift commit:** `b1bdb3a` (feat(luana-ts-batch1): lift @luana/design-tokens, @luana/hooks, @luana/format)

## Overview

Formatting utilities for money, dates, strings, and channel/currency constants.
Supports multi-currency LatAm tenants (PEN, USD, MXN, COP).

## Key exports

- `"."` — barrel: `formatMoney`, `formatMoneyDual`, `formatTenantDate`, `formatTenantDateShort`
- `"./utils"` — general string/number utilities
- `"./case-conversion"` — camelCase ↔ snake_case converters
- `"./format-date"` — date formatting helpers
- `"./format-money"` — currency formatting with locale awareness
- `"./constants/currencies"` — supported currency codes + display config
- `"./constants/channel-colors"` — per-channel color palette constants
