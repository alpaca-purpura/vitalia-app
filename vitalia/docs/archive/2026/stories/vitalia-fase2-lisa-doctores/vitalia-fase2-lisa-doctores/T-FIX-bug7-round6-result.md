<!-- voseo-allowed: doc interno de proceso -->
# T-FIX-bug7-round6-result — "N repeticiones" = N ciclos completos del patrón

> **Round 6** del bug7. Chris (dev-app, doctor 2b0d9466): bloque "Mar y Jue, 3 veces, 2-5pm" → la 1ra semana bien (Mar+Jue) pero las siguientes solo 1 (Mar). Inspeccioné la DB → confirmado: el BE interpretaba `occurrences=N` como **N turnos totales** (rrule `count=N` → Mar,Jue,Mar) → dejaba el último ciclo a medias. Chris ratificó (AskUserQuestion 2026-06-15): **"N repeticiones" = N ciclos COMPLETOS del patrón** (cada repetición incluye TODOS los días). Fix inline + verificado real-backend + DB + live.

## Root cause + fix

| | |
|---|---|
| **Síntoma** | "Mar+Jue, 3 veces" → Mar16, Jue18, **Mar23** (3 turnos); semana 2 sin jueves |
| **Root cause** | `AvailabilityProjectionService` mapeaba `occurrences` → `rrule(count=occurrences)`. Con varios `byweekday`, rrule cuenta ocurrencias INDIVIDUALES → N totales cross-día. El selector UI dice "Después de N **repeticiones**" (ciclos), pero el BE daba N totales → contradicción + último ciclo incompleto. |
| **Mismatch** | UI "repeticiones" (ciclos) ⟂ BE "count" (totales). |
| **Fix BE** | `count = occurrences × len(days_of_week)` → N ciclos completos. **Single-día**: `N×1 = N` (sin cambio). **Multi-día**: cada semana completa. |
| **Fix FE** | resumen "N veces" → "N **repeticiones**" (alineado al selector "Termina"). |

## Verificación (real-backend + DB)

- **Repro exacto** (Mar+Jue ×3, doctor de prueba): DB `count=6` · `dates = Mar16, Jue18, Mar23, Jue25, Mar30, Jul02` · ISODOW `[2,4]` · **3 martes + 3 jueves** = 3 semanas completas. Antes: 3 turnos (Mar,Jue,Mar).
- **e2e** (`bug7-r5-dow.spec.ts #R6`): Mar+Jue ×3 → DB 6 (3+3) + FE pinta ambos días. GREEN.
- **e2e** (`bug7-r4-dow.spec.ts case 18`): L+J biweekly ×8 → 16 ocurrencias (8 L + 8 J). GREEN.
- **e2e** (`bug7-r3-d3-matrix.spec.ts caso 6`): mismo bloque, ground truth migrado a DB (16). GREEN.
- **BE unit** (`test_availability_projection.py`): multi-día ciclos completos (Mar+Jue×3=6) + single-día sin cambio (×4=4). **14/14**.
- **BE SC-D3F** (`test_availability_occurrences.py`): SC-D3F-1 (L+J biweekly ×8 = 16) + SC-D3F-2 (7 días ×7 = 49 semanas completas) reescritos a la nueva semántica vía `project_block` (materialización completa, sin cap de ventana de 62d).
- **FE unit** (`recurrence-summary.test.ts`): "N repeticiones" (1 repetición / 4 repeticiones / 8 repeticiones). **11/11**.

## Gates

- **BE: clinics 457/457** (+2 nuevos unit; SC-D3F-1/2 actualizados) · ruff clean.
- **FE: tsc 0 · eslint 0** (limpié imports muertos en r3 matrix) · vitest recurrence-summary 11/11.
- **e2e: #R6 + case 18 + caso 6 = GREEN** real-backend.
- **Live-verify mía** (Chrome MCP locked → render real Chromium + screenshots vistos): semanas 1-3 cada una con **Mar + Jue** completos (14:00-17:00). `/tmp/bug7-r6-week{0,1,2}.png`.
- Cleanup: bloque de prueba borrado; doctor de prueba con solo los 3 bloques manuales de Chris.

## ⚠️ Datos pre-fix (no auto-corrigen)

Los bloques que Chris creó ANTES del fix mantienen su proyección vieja (el `count` se materializó al crear): doctor 2b0d9466 → `1c1f3a80` ([Mar,Jue]×3 = 3 turnos) + `73fe89d4` ([L,X,V]×1 = 1 turno). **Para corregirlos: editarlos (al editar se re-proyecta con la nueva semántica) o borrarlos y re-crearlos.** Single-día (`057a1e00` [L]×3 = 3) ya está correcto (sin cambio).

## Método

Inline (Opus) — fix quirúrgico post-diagnóstico (1 línea BE `count = occurrences × len(days)` + 4 líneas FE wording + actualización de tests que codificaban la semántica vieja). Análogo Carril-R, mismo patrón aceptado en round-3/4. Diagnóstico anclado en la DB real (no en el texto del reporte). Decisión de semántica ratificada por Chris (no improvisada).

## Archivos

**BE:** `availability_projection_service.py` (count = N×días) · `test_availability_projection.py` (+2 unit) · `test_availability_occurrences.py` (SC-D3F-1/2 reescritos).
**FE:** `BloquePopover.tsx` (resumen "repeticiones") · `__tests__/recurrence-summary.test.ts` (veces→repeticiones).
**e2e:** `bug7-r5-dow.spec.ts` (#R6 + hardening date-robust #2FE + #1c miércoles anti-solape) · `bug7-r4-dow.spec.ts` (case 18 → 16) · `bug7-r3-d3-matrix.spec.ts` (caso 6 → DB ground truth 16).

## Cómo correr

```bash
cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/clinics/ -q
cd ../frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r5-dow.spec.ts --project=smoke --workers=1 -g "#R6"
```
