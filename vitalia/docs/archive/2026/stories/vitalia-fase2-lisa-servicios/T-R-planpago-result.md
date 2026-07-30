# T-R-planpago — PlanPagoView rebuild (3-charge pricing)

## Verdict

done → `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/T-R-planpago-result.md`

## Commit

SHA: `91c01be9`
Branch: `wip/vitalia` (pushed)
Files changed: 3

## Diff summary

### `vitalia/frontend/src/features/lisa/types/servicios.types.ts`
- Added `ChargeKind`, `PriceMode`, `ReservationConfig`, `AdvanceConfig`, `FinancingConfig`, `ThreeChargePricing` interfaces
- Extended `ServiceDetail` with `pricing?: ThreeChargePricing | null`
- Extended `ServicePatchRequest` with `pricing?: ThreeChargePricing | null`

### `vitalia/frontend/src/features/lisa/components/servicios/leaves/PlanPagoView.tsx`
- Full rebuild from Sub-phase A stub to wired 3-charge model
- Zod schema with BE invariant: `financing.offered === true` requires `installments >= 1`
- RHF `values` prop (not `defaultValues`) for cache-update re-hydration (G2-F6)
- 4 sections: Precio del tratamiento / Reserva de la cita / Anticipo para iniciar / Financiamiento del saldo
- Dual-sync price: `{ price: v, pricing: { ...full, price: v } }` on headline price change
- Non-price patches: `{ pricing: { ...full } }` only — no stale top-level price override
- `GroupHeader.whatFor` for chip labels from mockup (la "seña" para apartar el turno / pago inicial del tratamiento / cuotas del resto)
- Client-side calculated fields:
  - `advance_equiv` = price × amount/100 (porcentaje) or amount (monto); shown disabled with FieldTooltip
  - `reservation_equiv` = same formula on reservation
  - `per_month` = (price − reservation_equiv − advance_equiv) / installments; shown disabled with FieldTooltip
- `useTenantLocale()` for currency fallback; `formatCalc()` uses `toLocaleString("es")`
- `FloatingAutosaveIndicator` exactly once (canon §2.6)
- Loading skeleton (4 animated placeholders) while `servicio` undefined

### `vitalia/frontend/src/features/lisa/components/servicios/leaves/__tests__/PlanPagoView.test.tsx`
- Removed all Sub-phase A assertions (disabled stubs, "Próximamente" text)
- 13 tests covering:
  - (a) Loading skeleton
  - (b) Enabled fields + 4 section headers present
  - (c) Hydration from `servicio.pricing` via RHF `values`
  - (d) Seeded defaults when `servicio.pricing` is null
  - (e) Calculated fields (advance_equiv 30% of 4500 = 1350; per_month (4500-0-1350)/6 = 525)
  - (f) Dual-sync patch behavior; non-price patch structure; full pricing object presence
  - (g) FloatingAutosaveIndicator exactly once
  - (h) Currency fallback to locale + explicit currency display

## Gate output

```
tsc --noEmit: 0 errors
eslint (3 files): 0 errors, 0 warnings
vitest PlanPagoView.test.tsx: 13/13 PASS
vitest servicios/ suite: 22 files, 152/152 PASS
```

## Skills consulted

- `frontend-expert` (FSD-Lite boundaries, RHF+Zod patterns, autosave canon §2.6)
- React patterns baseline (error boundary via loading guard, ARIA labels, stable keys)
- Shadcn UI / @luana/ui-kit conventions (GroupHeader.whatFor for chips, Switch, Select from ui-kit)
- Zod validation with cross-field superRefine (financing invariant)

## Known scope

- `chrome-devtools-verify` not run this session (live stack not available). Chris staging gate
  required before story moves to `done`.
- `finance_partner` field maps to BE `finance_partner` string; "medios de pago" has no BE field
  and was omitted per spec (static label only in mockup — outside scope).
- Currency is read-only in this leaf per RN-23; any currency change goes through Settings.
