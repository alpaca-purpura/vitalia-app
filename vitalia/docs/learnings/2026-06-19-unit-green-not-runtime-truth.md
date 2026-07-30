---
brand: vitalia
date: 2026-06-19
slug: unit-green-not-runtime-truth
promotable: candidate
applied: pending
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo]
target_core_package: n/a (regla de test-design · candidate a .claude/rules/test-design-doctrine.md)
origin: vitalia-fase2-lisa-servicios (G round 2 · 4 findings de la live-verify de Chris)
---

# El verde del unit-test no reproduce el runtime (4× en una tanda)

**Qué aprendimos:** en una sola tanda de G (live-verify de Chris) cuatro bugs reales pasaron con su
unit-test EN VERDE. El patrón común: **el test no ejercía el path real del runtime**. Cuatro formas distintas
de la misma trampa:

1. **Mockear el hook/componente bajo prueba congela su ciclo** (G2-F11): `ResumenView.test.tsx` mockeaba
   `use-autosave` → el `status` quedaba `idle` → el loop de re-render (que en runtime forzaba el value al
   server atrasado) **no existía en el test**. Verde imposible de romper sobre un ciclo que el mock eliminó.
2. **Fixtures con el tipo equivocado ocultan el shape del wire** (G2-F14b): el BE serializa `Decimal` money
   como **string** JSON (`"amount":"100"`); el fixture del test usaba `number` → `Number.isFinite(100)` true,
   verde. En runtime llega `"100"` → `Number.isFinite("100")` false → input vacío al recargar.
3. **Renderizar sin reproducir el timing de `values`** (G2-F14): el test renderizaba `pricing` null en verde
   pero no reproducía la transición `undefined → defined` de objetos anidados del primer render post-load,
   que en runtime crasheaba (`reservation.enabled` sobre undefined).
4. **No construir el VO por el path real** (G2-F12b): el test BE "agregar par vacío no rompe" no construía
   el VO `FaqPair` por el path que el endpoint ejercía → no veía el `ValueError` del `__post_init__`.

**Why:** un unit-test que sustituye (mock) o simplifica (fixture del tipo cómodo) justo la pieza bajo prueba
mide un mundo que el runtime no vive. El verde se vuelve un **falso positivo estructural**: pasa siempre
porque la condición que rompe fue eliminada del setup. Es la misma raíz de
[[verification-real-not-200]] y [[dod-live-verify]], un nivel más abajo (el unit, no el HTTP).

**How to apply (regla emergente para `test-design-doctrine.md`):**
- **Regression con el SHAPE REAL del wire.** Si el BE manda `string`/`Decimal`/`null`, el fixture del test
  manda eso — nunca el tipo cómodo. Idealmente derivar el fixture del DTO real (`jsonable_encoder`), no escribirlo a mano.
- **No mockear el componente/hook BAJO prueba.** Mockeá dependencias externas (red, time), nunca la pieza
  cuyo ciclo es lo que querés verificar. Si tenés que mockear el hook para que pase, el test no prueba el hook.
- **Reproducir el timing real** (estados `undefined → defined`, primer render post-load, re-render por status).
- **Cerrar el bucle con la acción real** (DoD #37): el unit verde es necesario, no suficiente — la live-verify
  de Chris cazó los 4. Falta el **contract-test FE↔BE** (HB-42) que habría cazado #2 (Decimal-string) y el
  embudo (camelCase) sin depender de la live-verify humana.

**Evidencia:** commits `e6f97173` (F11) · `2dc86a85` (F14b) · `c0e89ca1` (F14) · `5bfa7d4a` (F12b).
ADR-vitalia-009 (autosave field contract) + arch-test `test-autosave-value-from-local-state.test.ts` cementan #1.
