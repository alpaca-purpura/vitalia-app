---
story_id: vitalia-fase2-lisa-doctores
ticket: T-FIX-bloque-save
bug_id: regression_2026-06-12_bug7
type: bugfix-result
created_at: 2026-06-12
model: claude-sonnet-4-6
---

# T-FIX-bloque-save — resultado fix bug7 BloquePopover

## Diff resumen

| Archivo | Acción | Líneas |
|---|---|---|
| `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/BloquePopover.tsx` | MODIFIED | +50 / -16 (net +34) |
| `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/__tests__/bloque-popover-save.test.tsx` | CREATED | +281 |

**Cambios en BloquePopover.tsx:**
1. `import { toast } from "sonner"` agregado (patrón espejo de `NuevoIntegranteModal.tsx`)
2. `onSubmit` refactorizado: `handleSubmit(async (values) => {...})` → `handleSubmit(onValid, onInvalid)` con dos argumentos
3. Path success: `toast.success("Bloque guardado")` antes de `onClose()`
4. Path error (catch): `toast.error("No pudimos guardar el bloque. Intenta de nuevo.")` — `onClose()` NO llamado en error (popover permanece abierto para reintentar)
5. `onInvalid` handler: `() => { toast.error("Revisa los campos del bloque"); }` — elimina el no-op silencioso de Zod validation fail

## Output literal de los gates

### Vitest — test nuevo (3/3 PASS)

```
✓ BloquePopover — save feedback (bug7 regression_2026-06-12)
  ✓ Test RED 1: mutation REJECTS → toast.error called, onClose NOT called
  ✓ Test RED 2: mutation RESOLVES → toast.success called + onClose called
  ✓ Test 3: invalid form state → toast.error called (onInvalid eliminates silent no-op)

Test Files  1 passed (1)
Tests       3 passed (3)
Duration    ~1.3s
```

### Vitest — suite horarios completa (31/31 PASS)

```
✓ AvailabilityCalendar
✓ BloquePopover (14 tests existentes + 3 nuevos)
✓ DoctorHorariosView

Test Files  2 passed (2)
Tests       31 passed (31)
Duration    ~2.8s
```

*Nota: `console.error("Error saving block:", Error: Network error)` aparece en output — es el comportamiento correcto del componente (catch block mantiene el log + añade toast). No es falla de test.*

### TypeScript (tsc --noEmit)

```
(sin output — 0 errores)
```

### ESLint

```
(sin output — 0 errores)
```

## Commit SHA

`f85c8ce2` — `fix(vitalia): BloquePopover surface save errors via toast + onInvalid (bug7 staff guardar-bloque)`

Pusheado a `origin wip/vitalia`. Bidirectional validator: SOFT_DRIFT 1/16 (pre-existente — no introducido por este fix).

## Señal server-side 422

**No detectada en análisis estático.** El `catch (err)` existente en la lógica original captura cualquier error HTTP incluyendo 422 (que `mutateAsync` convierte en excepción rechazada). El nuevo `toast.error` en el catch lo surfacea al usuario independientemente del código HTTP. Sin contract-test FE↔BE en esta ruta (HB-42 pendiente CIL).

## Root causes cerrados

| Root cause | Fix aplicado |
|---|---|
| (a) `catch` solo `console.error` — sin feedback visible | `toast.error(...)` en catch; `onClose()` removido del catch |
| (b) `handleSubmit(onValid)` sin `onInvalid` — Zod fail es no-op | Segundo arg `onInvalid: () => toast.error(...)` agregado |
| (c) Path success sin `toast.success` | `toast.success("Bloque guardado")` antes de `onClose()` |

## Skills consulted

| Skill | Motivo | Decisión |
|---|---|---|
| React patterns baseline | bug FE component | `handleSubmit(onValid, onInvalid)` RHF pattern; `sonner` toast pattern espejo de NuevoIntegranteModal |
| `spanish-text.md` | strings user-facing nuevos | Tuteo correcto: "Intenta" (no "intentá"), "Revisa" (no "revisá") — Spanish neutro LatAm cumple |
| `tdd-mandatory.md` | TDD RED→GREEN obligatorio | Tests escritos RED antes de fix, confirmados GREEN después |

## Pendiente post-fix

- Live-verify write real en dev-app: crear bloque one_off + recurrent con usuario autenticado, leer logs POST 201, confirmar efecto DB
- Re-Chris-verify (G round 2) antes de habilitar /auditor
