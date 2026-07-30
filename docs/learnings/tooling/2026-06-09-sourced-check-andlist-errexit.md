# `[ cond ] && exit 1` como último statement de un check SOURCEado = aborto silencioso bajo errexit

**Fecha:** 2026-06-09 · **Carril CIL:** L2 (tooling transversal) · **Severidad:** silent-killer

## Problema

El squash-merge wip/vitalia→main moría con `EXIT=1` SIN ningún mensaje de error — todas las secciones del pre-commit imprimían PASS/advisory y el commit igual abortaba.

## Causa

`core-harness/hooks/checks/17-checkpoint-dupkeys.sh` terminaba con:

```bash
[ "$DUPKEY_FOUND" = "1" ] && exit 1
```

Cuando NO hay dups (`DUPKEY_FOUND=0`), el `[` devuelve rc=1; al ser el ÚLTIMO statement, el `source` del dispatcher retorna 1; el dispatcher corre `set -euo pipefail` → errexit mata el hook sin imprimir nada. El check solo "funcionaba" cuando la rama del archivo no se ejecutaba (sin checkpoints staged) — el merge gigante fue el primer commit que recorrió el loop completo con 0 dups.

## Fix

`if [ ... ]; then exit 1; fi` (commit `8b39ff64`, incluido en el squash). Grep del patrón en todos los checks → era el único caso.

## Refuerzo (regla durable)

En cualquier script que va a ser **SOURCEado** bajo `set -e`: el patrón `cond && action` NUNCA puede ser el último statement de un path alcanzable — usar `if`. Al escribir un check nuevo del dispatcher, smoke con el caso NEGATIVO (gate no dispara) además del positivo: el modo de falla es exactamente el caso "todo OK".

## Relacionado

- `docs/learnings/tooling/2026-06-08-harness-refactor-stub-against-the-gate.md` (validate-after-apply)
- W4b learning: "gate dead-by-drift + masked = peor que sin gate" — variante: gate que mata al CALLER en su caso feliz.
