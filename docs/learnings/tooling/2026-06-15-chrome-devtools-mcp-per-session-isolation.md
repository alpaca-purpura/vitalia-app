---
title: Chrome DevTools MCP debe aislar el perfil por sesión, no solo por worktree
date: 2026-06-15
type: tooling
scope: cross-brand
promotable: no
applied: applied
origin: sesión 2026-06-15 — Chris "chrome dev tools siempre falla en las pruebas"
---

# Chrome DevTools MCP — aislamiento per-sesión (no solo per-worktree)

## Síntoma

Chris reportó que Chrome DevTools MCP "siempre falla" al usarlo para pruebas/live-verify.
No daba un error legible — las tool-calls (navigate/snapshot/click) simplemente fallaban
o colgaban en una de las terminales.

## Root cause

La config global `~/.claude.json` → MCP `chrome-devtools` tenía el `userDataDir`
**hardcodeado a un único dir por worktree**:

```
--userDataDir=/home/chalreme/.cache/chrome-devtools-mcp/luana-vitalia
```

Per-worktree, **NO per-sesión**. Bajo el paradigma single-hub (ADR-009) Chris corre
**N sesiones Claude en paralelo sobre el mismo worktree** (`~/Proyectos/luana-vitalia`,
pts/0 + pts/1). Cada sesión auto-levanta su propio `chrome-devtools-mcp` apuntando al
**mismo perfil de Chrome**.

Chrome protege su `user-data-dir` con un `SingletonLock` (symlink a `<host>-<pid>` del
proceso dueño). La 1ª sesión toma el lock; la 2ª intenta lanzar Chrome sobre el perfil
ya bloqueado → no puede adquirir el SingletonLock → **toda tool-call de esa 2ª sesión
falla**. De ahí el "siempre falla": pasa cada vez que hay ≥2 sesiones vivas.

Modo de falla secundario: si una sesión crashea sin limpiar, el `SingletonLock` + el
Chrome huérfano quedan → bloquean el próximo arranque aunque no haya concurrencia.
Evidencia de que venía pasando: `pkill -9 chrome` + `rm -rf ~/.cache/chrome-devtools-mcp/*`
ya estaban whitelisteados en `settings.local.json` = firefighting manual recurrente.

## Fix aplicado

`~/.claude.json` (backup en `~/.claude.json.bak-chromemcp`):

```
--userDataDir=/home/chalreme/.cache/chrome-devtools-mcp/luana-vitalia-${LUANA_LANE:-solo}
```

Reusa la convención `LUANA_LANE` que el harness ya define para cockpit/session-locks
(CLAUDE.md § cockpit · `scripts/git/session-lock.sh`). Cada terminal exporta su lane
ANTES de lanzar `claude`:

| Caso | env | perfil |
|---|---|---|
| 1 sesión | (nada) | `…/luana-vitalia-solo` |
| 2 sesiones · term 1 | `export LUANA_LANE=A` | `…/luana-vitalia-A` |
| 2 sesiones · term 2 | `export LUANA_LANE=B` | `…/luana-vitalia-B` |

Dirs distintos → cero colisión de lock. Primer run de cada lane re-autentica Clerk una vez
(perfil nuevo) y después persiste.

## Lección durable

- **El aislamiento de un MCP que lanza un proceso con lock exclusivo (Chrome, un browser,
  un daemon con pidfile) tiene que ser per-sesión, no per-worktree**, en cuanto el paradigma
  permite N sesiones sobre el mismo árbol (single-hub ADR-009). Per-worktree alcanza para
  worktrees separados; se rompe apenas hay concurrencia same-hub.
- La pista diagnóstica fue `ps aux` mostrando **2 `npm exec chrome-devtools-mcp`** con el
  **mismo `--userDataDir`** + `SingletonLock -> <host>-<pid>` con el PID vivo. Cuando un MCP
  "siempre falla" con concurrencia, mirar locks de perfil compartido antes que la red/auth.
- La env var de un MCP stdio se **fija al arrancar el proceso `claude`** (el server la hereda);
  no se puede inyectar desde dentro de la sesión ni con `/mcp` reconnect → por eso el fix
  exige relanzar `claude` con el LANE exportado.

## Verificación live (2026-06-15, end-to-end)

Confirmado real, no por inferencia:

1. **Mecanismo** — con el lock viejo tomado (`luana-vitalia` → PID 108303), un Chrome
   lanzado en un dir lane'd (`luana-vitalia-laneTEST`) booteó en paralelo, su DevTools
   endpoint respondió (`Chrome/148.x`) y tomó su PROPIO `SingletonLock` (PID distinto).
   Cero colisión, lock viejo intacto.
2. **Repro del bug** — desde la sesión con el MCP viejo (sin lane), una tool-call real
   (`list_pages`) falló con el error textual: `The browser is already running for
   …/luana-vitalia. Use a different userDataDir or stop the running browser first.`
   = exactamente "siempre falla".
3. **Fix end-to-end** — Chris relanzó `claude` con `export LUANA_LANE=A`. El MCP vivo pasó
   a `…/luana-vitalia-A` (separado del viejo). La MISMA tool-call (`list_pages`) que antes
   tiraba el error de lock **respondió OK** (`about:blank`). Colisión eliminada.

Confirmación clave del modelo mental: el env del MCP se fija al arrancar `claude` → el fix
NO aplica retroactivo a la sesión corriendo; sólo activa en un `claude` nuevo lanzado con el
LANE exportado. Por eso es un paso de arranque humano, no algo que el agente pueda ejercer
sobre su propia sesión.

## Gap residual (HB-73)

El aislamiento depende de que Chris exporte `LUANA_LANE` a mano. Si dos sesiones quedan
ambas sin LANE → ambas caen en `…-solo` → la colisión vuelve. Hardening futuro: default
único por-PID (no expresable en la config estática actual) o documentar el requisito en
`parallel-safety.md` como paso de arranque de sesión paralela.

## Refs

- `docs/process/harness-backlog.md` → HB-73
- `.claude/skills/chrome-devtools-verify/SKILL.md` — consumidor principal
- `.claude/rules/definition-of-done-live-verify.md` (Critical #37) — DoD live-verify usa este MCP
- `~/.claude.json` `mcpServers.chrome-devtools` — config parcheada
- CLAUDE.md § Cockpit + `scripts/git/session-lock.sh` — origen de la convención `LUANA_LANE`
