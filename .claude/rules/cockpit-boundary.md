# Cockpit Boundary (luana ↔ prenter · consumo versionado · cero fork · triage genérico/específico)

> **tier: project.** El cockpit NO es código de luana — es el binario del repo separado **prenter-harness** (`github.com/alpacapurpura/prenter-harness`, carpeta `~/Proyectos/prenter-harness`). luana lo **consume**, no lo contiene. Su **home base** (el launcher + el registry multi) vive en **chris-corp** (`~/Proyectos/chris-corp`, I-48). Esta rule protege el límite: que mejorar el cockpit (prenter) con el tiempo NO desfase luana, y que pedidos al cockpit desde una marca NO filtren lo luana-específico al motor genérico. **Origen:** 2026-06-17 (temor de Chris: fork/drift + fuga de vocabulario "Marca" vs "Sistema/proyecto").

## Modelo mental (cementado)

El cockpit (prenter) = **motor** (un programa). NO se instancia dentro de luana. Se **corre apuntándolo a un workspace** — como `python tu_script.py`. Hay **un** binario del cockpit; le pasás los datos de luana. Lo durable que luana posee = **config + datos** (`project.config.yaml`, `cockpit.config.yaml`, los `.md`/`.yaml`); el cockpit corriendo es un **proceso desechable**. Filesystem-as-DB: los `.md`/`.yaml` SON la base; git = el respaldo.

**El cockpit (prenter) es a luana lo que `core/` es a una marca.** Mismo *promotion gate*, un nivel más arriba (límite de repo). No filtrás brand-specific al `core/` compartido → no filtrás luana-specific al motor prenter genérico.

## Regla cardinal — 5 contenciones

| # | Regla | Enforcement |
|---|---|---|
| 1 | luana **NUNCA** contiene código del cockpit (un `.go` de prenter en luana = alarma) | grep: `git ls-files \| grep -E 'cockpit-go\|\.go$'` sobre tooling cockpit = vacío |
| 2 | el cockpit se consume **por versión**, no por "último build local" | `toolchain.cockpit_min_version` en `project.config.yaml` + warn en el daemon de chris-corp (`cockpit-daemon.sh` → `check_cockpit_version`) |
| 3 | Todo pedido de cambio al cockpit se **triagea**: ¿genérico o luana-específico? | Específico → seam de luana (config/datos). Genérico → repo prenter, diseñado **configurable** |
| 4 | Cambio genérico pasa el **test del segundo cliente** | "¿`demo-environment` (u otro proyecto) también lo querría, y puede apagarlo?" Si no → es luana disfrazado → va al seam |
| 5 | Etiquetas/vocabulario = **config**, nunca hardcode genérico | La fuga "Marca" (el cockpit horneó vocabulario de luana) es el caso testigo → mover a `vocabulary.axis_label` del seam |

## Cómo subir el pin (upgrade deliberado)

1. Mejorás el cockpit en su repo (`~/Proyectos/prenter-harness`), taggeás release (`git tag vX.Y.Z`), rebuild (`./build-ui.sh && go build -o cockpit .`).
2. Probás el cockpit nuevo contra luana (levantás, verificás los tabs que usás).
3. Subís `cockpit_min_version` en `project.config.yaml` a la tag nueva. **Recién ahí** queda "bendecido".
4. Sin paso 3, `cockpit-daemon.sh` avisa al arrancar (no bloquea) — drift visible, no silencioso.

## Editar el cockpit (prenter) desde una sesión de luana (cuándo SÍ, cómo)

Default: **NO**. Un cambio genérico al cockpit es trabajo del repo prenter — idealmente en una sesión/worktree de prenter, no mezclado con producto de marca. Si el cambio es legítimamente genérico (pasó triage regla 3+4): se **propone**, se ratifica con Chris, y se ejecuta **en `~/Proyectos/prenter-harness`** (otro repo, otros commits). El límite de repo te protege mecánicamente — tocar prenter obliga a cruzar a otro git, no pasa por accidente.

## Anti-patterns prohibidos

- ❌ Copiar/vendoring de código del cockpit (`.go`, la UI) dentro de luana → crea el fork que desfasa
- ❌ Hornear una necesidad luana-específica en el motor genérico (lo que pasó con "Marca") en vez de seamizarla
- ❌ Bumpear el cockpit y dar por bueno sin testear + sin subir `cockpit_min_version` (upgrade accidental)
- ❌ Diseñar un feature del cockpit que `demo-environment` no podría apagar (rompe el test del segundo cliente)
- ❌ Editar `~/Proyectos/prenter-harness` mid-feature de marca sin triage + ratificación (mezcla producto con motor)

## Referencias

- `~/Proyectos/chris-corp/harnesses/scripts/cockpit-daemon.sh` § `check_cockpit_version` — el warn de pin (launcher = home base chris-corp)
- `project.config.yaml` § `toolchain.cockpit_min_version` — el pin
- `cockpit.config.yaml` — seam de nav (qué tabs muestra luana)
- `CLAUDE.md` § Tools operativas — descripción del cockpit + rebuild del binario
- `docs/promotion-protocol/README.md` — el gate brand→core (mismo patrón, un piso abajo)
