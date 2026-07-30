## 0.4.0 — 2026-06-08 (core-ds-foundation)
### Added
- useAutosave: `coalesce` option (merge rapid edits into one payload) + `flush()`. Back-compat preserved (defaults coalesce:false, debounceMs:2000).
### Changed
- use-copilot-offset: decoupled from `@/features/copilot/*` (app-coupled) → reads optional `--copilot-offset` CSS var (default 0). Removed from the barrel (subpath-only). Makes @luana/ui-kit consumable in any brand. Zero regression (no current barrel consumer).

# @luana/hooks — CHANGELOG

## 0.3.0 — 2026-05-30

### Added
- **`useAutosave<TValues>`** — primitiva de autoguardado compartida (ADR-012, `build-autosave-primitive-luana` T-1).
  Consolida los hooks idénticos `use{Identity,Personality,Contact,Visuals}Autosave.ts` de vitalia + base del
  form-runtime de nicolify en un contrato único inyectable.
  - `getTokenReady()` interno: espera hasta `authReadyAttempts × 200ms` a que el token no sea null (robustez
    ante la ventana Clerk donde `isSignedIn=true` pero `getToken()→null` transitoriamente).
  - Debounce default `2000ms` (Chris 2026-05-31); `scheduleSave` cancela el timer previo (last-wins).
  - Máquina de estados: `idle → dirty → saving → saved | error`; `savedAt` en cada éxito.
  - `onSaved` / `onError` callbacks; `telemetry` opt-in `{ type, durationMs }`.
  - `retry()` re-dispara el último conjunto de valores fallido.
  - Cleanup en unmount: cancela el timer + guard setState post-unmount.
  - **NO importa `@clerk/*`** — `getToken` inyectado por el consumer (desacopla auth provider).
- Exports: `useAutosave`, `AutosaveStatus`, `UseAutosaveOptions<T>`, `UseAutosaveReturn<T>` en barrel `src/index.ts`.

### Tests
- 11 tests unitarios Vitest con fake timers + mocks en `src/__tests__/useAutosave.test.ts`:
  debounce-coalesce, save-success, auth-ready (token null transitorio→espera), error+retry,
  concurrent-edits last-wins, network-failure, unmount-cancels, telemetry opt-in (×3).

### Origin
ADR-012 `docs/architecture/luana-platform/ADR-012-autosave-primitive-platform.md`. Promotion from vitalia +
nicolify. Stories consumer (adopción vitalia/nicolify) son separadas.

---

## 0.2.0 — 2026-05-29

### Added
- **`createSsrSafePersistedStore`** — factory for SSR-safe Zustand 5 persisted stores under Next.js App Router.
  Wraps `persist` with `skipHydration:true` + a storage wrapper whose `setItem` is a NO-OP until `_hasHydrated`
  (neutralizes the spurious default-write during SSR/skeleton/pre-hydration that clobbers localStorage on reload)
  + `onRehydrateStorage` flag flip. Exports `SsrSafeHydration` interface.
- **`useStoreHydration(store)`** — idempotent client-side rehydration hook (StrictMode-safe via ref guard).
- Subpath exports `@luana/hooks/create-ssr-safe-persisted-store` + `@luana/hooks/use-store-hydration`
  (leaf imports that bypass the feature-coupled barrel — required by consumers without `@/features/copilot`).
- `peerDependencies.zustand >=5`.

### Origin
Lift desde `vitalia/frontend/src/lib/store/` (story `vitalia-shell-state-persistence` / `ADR-vitalia-006`,
promotion `docs/promotion-protocol/proposals/2026-05-29-lift-ssr-safe-persisted-store.md`). vitalia consume
ahora vía subpath. nicolify (`dismiss-store`) es consumer candidate (opt-in via `/pm-nicolify`).

### Consumers
- `@luana/vitalia-web` — 4 persisted stores (shell, tenant, agenda, agenda-filters) + shell layout client.
