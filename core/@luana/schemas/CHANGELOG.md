# @luana/schemas — CHANGELOG

## 0.2.0 — 2026-05-30

### Added
- **`AutosaveContract`** — tipos TypeScript para la primitiva de autoguardado compartida (ADR-012,
  `build-autosave-primitive-luana` T-1).
  - `AutosaveStatus` — union `"idle" | "dirty" | "saving" | "saved" | "error"`.
  - `UseAutosaveOptions<TValues>` — contrato de configuración del hook (save inyectada, getToken inyectado,
    onSaved, onError, debounceMs, telemetry opt-in, authReadyAttempts).
  - `UseAutosaveReturn<TValues>` — interfaz retornada por `useAutosave` (status, savedAt, scheduleSave,
    cancel, retry).
- Exports en `src/index.ts` (barrel, sin romper el estado anterior que era solo `export {}`).

### Origin
ADR-012 `docs/architecture/luana-platform/ADR-012-autosave-primitive-platform.md`. Tipos compartidos
consumibles por cualquier brand vía `@luana/schemas`. La implementación del hook vive en `@luana/hooks`.

---

## 0.1.0 — 2026-05-15

### Added
- Versión inicial: placeholder `export {}` en `src/index.ts`. Zod como dependencia para schemas futuros.
  (Schemas de módulos específicos se liftarán en historias 4/5 del outcome autosave-primitive-platform.)
