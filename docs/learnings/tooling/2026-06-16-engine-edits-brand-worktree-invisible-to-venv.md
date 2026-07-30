---
title: Engine edits desde un worktree de marca son invisibles al venv compartido hasta el merge
date: 2026-06-16
type: tooling
scope: cross-brand
promotable: no
applied: applied
origin: sesión 2026-06-16 — lift Settings lazy 0.5.1 (luana-core-platform) ejecutado desde wip/vitalia
---

# Engine edits desde un worktree de marca — invisibles al venv hasta el merge

## Síntoma

Editás `core/luana-core-*/src/...` dentro del worktree de una marca
(`~/Proyectos/luana-vitalia`), corrés `${WS}/.venv/bin/pytest`, y el test falla
con el comportamiento VIEJO — como si tu edit no existiera. Peor: el traceback
apunta a un archivo en `/home/chalreme/Proyectos/luana-platform/core/...` (el
worktree **main**), no al que acabás de editar.

Caso origen: bajé `POSTGRES_HOST` a opcional en
`luana-vitalia/core/luana-core-platform/.../config.py`; el test seguía dando
`POSTGRES_HOST Field required` con la config de `luana-platform/core/...`.

## Root cause

`~/Proyectos/luana-{brand}/.venv` es un **symlink** a `~/Proyectos/luana-platform/.venv`
(venv único compartido entre worktrees). Sus editable installs (uv workspace,
`.pth` en `site-packages`) resuelven cada `luana_core_*` a la copia del worktree
**main** (`luana-platform/core/.../src`), NO a la copia del worktree de la marca.

```
luana-vitalia/.venv -> luana-platform/.venv
  _editable_impl_luana_core_platform.pth -> luana-platform/core/luana-core-platform/src
```

Cada worktree tiene su **propia** copia de `core/` (es un git worktree, árbol
completo), pero el intérprete importa SIEMPRE la de main. Entonces un edit a
`core/` en el worktree de marca vive en su filesystem pero el venv no lo ve
hasta que el cambio aterriza en main (donde apunta el editable). Es el espejo
runtime de por qué [[single-hub-worktree-adr009]] + parallel-safety mandan un
**worktree core efímero** (con su propio venv) para engine work.

## Fix / workaround

- **Validar in-place sin merge:** override del editable con `PYTHONPATH` apuntando
  al `src` del paquete tocado — gana sobre el `.pth`:
  ```bash
  WS=$(git rev-parse --show-toplevel)
  PYTHONPATH="${WS}/core/luana-core-platform/src" ${WS}/.venv/bin/pytest tests/... 
  ```
  Sirve para el RED→GREEN local y para R3 downstream (correr las suites de cada
  marca con el mismo override → testean TU engine, no el de main). Los subprocess
  tests heredan `PYTHONPATH` vía `os.environ.copy()`.
- **Camino canónico (engine work serio):** worktree core efímero
  (`wip/core-{slug}`) con `uv sync` propio → su venv apunta a su `core/`. Lo
  mandan parallel-safety + el lift gate.
- **Efecto en stacks corriendo:** el engine fix sólo toma efecto para los stacks
  dev de las marcas DESPUÉS del squash-merge `wip/{brand}` → main (el editable +
  el `core/` de cada marca vienen de main). La live-verify DoD #37 de un engine
  change hecho en un worktree de marca NO puede correr hasta ese merge.

## Por qué importa

- Un test "verde" o "rojo" sobre un engine edit NO es confiable sin saber qué
  `core/` resolvió el venv. Verde podía estar testeando el código viejo de main.
- Confirma la doctrina: engine edits desde el hub de una marca son una excepción
  (decisión Chris por lift) que paga este costo de testeo; el default sigue siendo
  worktree core efímero.

## Referencias

- `.claude/rules/parallel-safety.md` (topología worktrees · venv at root)
- `docs/promotion-protocol/proposals/2026-06-16-copilot-chat-brand-mountable.md` (bitácora: validado vía PYTHONPATH)
- [[single-hub-worktree-adr009]]
