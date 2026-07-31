# Release Protocol — Entity SSoT (v4 cement 2026-05-29)

**v4 (cement 2026-05-29):** dos ejes explícitos. Eje **integración** (`backlog → … → shipped`) + eje **despliegue** (`not_deployed → scheduled → in_production`, FUTURO). `shipped` ahora exige un **gate de comportamiento** (prueba de integración verde) además de stories cerradas. Ver § 5 + § 8.

**v3 (cement 2026-05-28):** outcome+phase ELIMINADOS. Release es el único contenedor temporal. Ver `docs/process/lifecycle.md`.

**Cement-date v4:** 2026-05-29.
**Cement-date v3:** 2026-05-28.
**Cement-date v2:** 2026-05-27.

> **Release** es THE contenedor temporal del modelo: no hay outcome por encima. Agrupa stories que se mergean juntas a main. State machine (eje integración): `backlog → planning → in_progress → ready_to_merge → shipped`. Eje despliegue separado (futuro): `not_deployed → scheduled → in_production`.

## Los dos ejes (v4)

El release tiene **dos ejes ortogonales** que NO deben mezclarse:

| Eje | Estados | Pregunta que responde | Estado hoy |
|---|---|---|---|
| **Integración** (`status`) | `backlog → planning → in_progress → ready_to_merge → shipped` | ¿Esto funciona y está integrado a main + staging? | ✅ activo |
| **Despliegue** (`production_status`) | `not_deployed → scheduled → in_production` | ¿Esto está realmente lanzado al servidor de producción? | 🟡 futuro (placeholder) |

**Por qué separados:** `shipped` = "la base sólida sobre la que todo funciona bien" (verificada, en main + staging). Eso es distinto de "lo que realmente lancé a producción". Un release puede quedarse `shipped` días/semanas y recién pasarse a producción cuando Chris lo decida (inmediato o agendado). Mezclarlos perdería esa separación.

---

## Sección 1 · Release como entidad SSoT

Un **Release** es una agrupación temporal de stories que se mergean juntas a main + se despliegan juntas. Es el **único contenedor temporal** del modelo: no existe ningún concepto por encima del release (outcome y phase fueron eliminados · ver `docs/process/lifecycle.md`).

**Cuándo crear un release:** Chris define un bloque de trabajo coherente (~2 semanas típico) con un objetivo claro y un set de stories que entregan ese objetivo. Ejemplo: F2 "Migración progresiva · primer valor Valeria + Lisa" agrupa 5 stories que materializan el primer valor end-to-end.

**Path canónico:** `{brand}/docs/product/releases/{release_id}.yaml`.

**Por qué NO base de datos:** mantenemos filesystem-as-DB. El cockpit lee + escribe estos YAMLs directo. `/pm-vitalia` también.

---

## Sección 2 · State machine

| Estado | Significado | Transition trigger |
|---|---|---|
| `backlog` | Release identificado pero no priorizado | Chris crea con "+ Nuevo release" en cockpit |
| `planning` | Stories asignadas, sin desarrollo activo | Chris asigna ≥1 story |
| `in_progress` | ≥1 story de la release en state ∈ {refining, refined, ready, developing, developed, reviewing} | recompute auto al asignar story refining+ |
| `ready_to_merge` | TODAS las stories del release en state=done O dropped | recompute auto post Fase F MERGE de la última story |
| `shipped` | `ready_to_merge` **+ gate de comportamiento verde** (prueba de integración + E2E smoke, sin regresión) confirmado por Chris | `/pm-{brand}` o cockpit (botón "Cerrar → shipped" con check de verificación · ver § 5) |

**`shipped` es TERMINAL en el eje de integración** — un release entregado es inmutable: no se demota, no se editan name/description/stories (correcciones excepcionales solo vía `/pm-{brand}`). El cockpit bloquea PUT/DELETE sobre releases shipped.

**Recompute logic:** WIP por release se calcula leyendo el state actual de cada story del release. Una story en `idea` NO cuenta como in_progress (es backlog del release). Una story en `refining/refined/ready/developing/developed/reviewing` SÍ cuenta como in_progress. El recompute **nunca demota un `shipped`** (es terminal).

---

## Sección 3 · Schema release YAML

```yaml
---
release_id: F2
brand: vitalia
name: "Migración progresiva · primer valor Valeria + Lisa"
description: "Sub-tabs valeria-agenda + lisa-marca con ADR-vitalia-004 cementado · primer valor real shipped."
status: in_progress                    # planning | in_progress | ready_to_merge | shipped | backlog
target_date: null                       # ISO date · null hasta que Chris la llene
shipped_date: null                       # ISO date · solo cuando status=shipped
order: 2                                  # int para ordenamiento Roadmap (menor = primero)
created_at: 2026-05-15T10:00:00-05:00
created_by: chris

# Gate de shipped (eje integración) — sellos de la prueba de comportamiento
verified_by: null                         # 'chris' cuando confirmó el check de integración verde
verified_at: null                          # ISO timestamp del check verde
verification_note: null                    # nota libre (qué corrió, resultado, gotchas)

# Eje DESPLIEGUE (FUTURO · placeholder reservado · ver § 8)
production_status: not_deployed            # not_deployed | scheduled | in_production
production_version: null                    # semver del pase a prod, ej "v0.3.0"
production_scheduled_at: null               # ISO · inmediato (now) o fecha-hora futura
deployed_at: null                           # ISO · cuándo se completó el deploy real
release_branch: null                        # ej "release/vitalia-v0.3.0"

# Lista de stories asignadas (denormalizada para cockpit · source-of-truth sigue siendo checkpoint.md de cada story)
stories:
  - vitalia-fase2-valeria-agenda          # state: done
  - vitalia-fase2-lisa-marca              # state: done
  - vitalia-fase2-valeria-pacientes       # state: idea
  - vitalia-fase2-lisa-marca-v2           # state: refining
  - vitalia-fase1-shell-layout-5050-race-fix  # state: idea
---

# Resumen markdown opcional
```

**Campos editables Chris:** `name, description, target_date, order, stories[]` (drag entre releases) — **solo mientras NO esté shipped**.
**Campos auto-calc / sellados al cerrar:** `status` (recompute from story states), `shipped_date`, `verified_by`, `verified_at`, `verification_note` (los escribe el flujo "Cerrar → shipped", no Chris a mano).
**Campos read-only:** `release_id` (no se renombra), `brand, created_at, created_by`.
**Campos eje despliegue (futuro):** `production_*`, `deployed_at`, `release_branch` — reservados, hoy default `not_deployed`/null. Los escribirá el flujo "pase a producción" cuando exista (§ 8).

---

## Sección 4 · WIP caps + recompute logic

WIP cap del release es la suma de stories en `refining/refined/ready/developing/developed/reviewing`. Caps del paradigm v4 aplican (refining ≤3, refined ≤5, etc.) — el release NO impone un cap propio, lo hereda del state-machine cross-platform.

**Recompute trigger:**
- Story transition state change → recompute status de su release.
- Story moved entre releases (drag en cockpit) → recompute ambos releases (origen + destino).
- Story creada/dropped → recompute release del que se quitó/agregó.

**Algorítmo:**
```python
def recompute_release_status(release: Release) -> str:
    states = [s.state for s in release.stories]
    if all(s in {'done', 'dropped'} for s in states):
        return 'ready_to_merge'
    if any(s in {'refining', 'refined', 'ready', 'developing', 'developed', 'reviewing'} for s in states):
        return 'in_progress'
    if all(s == 'idea' for s in states):
        return 'planning'
    return release.status  # no-op si estado intermedio raro
```

---

## Sección 5 · Cerrar release → shipped (gate de comportamiento + 5 operaciones)

### Gate de comportamiento (qué hace que un release pase a `shipped`)

`shipped` exige **DOS condiciones**, no una:

1. **Stories cerradas** — todas las stories del release en `{done, dropped}` (validado server-side, da `ready_to_merge`).
2. **Prueba de comportamiento verde** — Chris confirma que corrió la suite de integración + E2E smoke y **todo pasa sin romper lo anterior** (regresión). Es el `verified` gate del cockpit.

El cockpit (botón "Cerrar → shipped" → `MergeReleaseModal`) le da a Chris el **prompt exacto** para correr la verificación en Claude Code y un checkbox de confirmación. Sin el check, el endpoint `merge-release` responde `409 verified=false` y NO marca shipped.

**Prueba de comportamiento canónica** (lo que cubre "funciona + no rompe lo anterior"):

```bash
WS=$(git rev-parse --show-toplevel)
# 1) Suite full cross-brand (lint + arch-fitness + tests + coverage) — regresión:
cd ${WS} && make ci-parity
# 2) E2E smoke del brand (humo de los flujos) — ej. vitalia (3002):
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke
```

Verde en ambos = base sólida verificada. El cockpit sella `verified_by: chris` + `verified_at` + `verification_note` en el release.yaml al confirmar.

> **Nota (modo solo-bootstrap):** mientras GH Actions está deferred (`.claude/rules/github-actions-deferred.md`), el gate es **manual-confirmado** (checkbox), no un runner automático. Cuando haya CI real, el runner puede pasar a bloquear duro.

### Las 5 operaciones del merge

Cuando release.status = `ready_to_merge` + verified, `/pm-{brand}` (o el cockpit endpoint `merge-release`) ejecuta:

### Operación 1 — Squash-merge git
Por cada story `done` del release, su branch ya fue squash-merged en su propio Fase F MERGE individual. El "merge release" es una sub-operation que consolida la entrega: NO es un git merge nuevo (eso ya pasó por story).

### Operación 2 — Archive stories
```bash
YEAR=$(date +%Y)
for STORY in $(grep '^- ' release.yaml | awk '{print $2}'); do
  git mv {brand}/docs/product/stories/${STORY} {brand}/docs/archive/${YEAR}/stories/${STORY}
done
```

### Operación 3 — Cap YAML ledger update (ya hecho en Fase F.3 individual)
Verificación: cada cap target de las stories del release tiene `change_log[]` actualizado con la story correspondiente.

### Operación 4 — Release YAML status + sellos de verificación
```yaml
status: shipped
shipped_date: 2026-MM-DDTHH:MM:SS-05:00
verified_by: chris
verified_at: 2026-MM-DDTHH:MM:SS-05:00
verification_note: "make ci-parity verde + smoke 12/12 · sin regresión"
production_status: not_deployed     # nace no-desplegado a prod (eje despliegue · § 6)
```

### Operación 5 — Generate release notes
`scripts/generate_release_notes.py --release F2 --brand vitalia` (futuro) o copy-paste manual a `{brand}/docs/product/releases/release-notes/F2.md` listando:
- Capabilities new/extended/fixed/derived
- Stories shipped (con merge SHA)
- Breaking changes (si los hay)
- Migration notes

---

## Sección 6 · Pase a producción (eje despliegue · FUTURO · placeholder)

> **Estado:** NO implementado. Esta sección **reserva el contrato** para que el día que se construya sea trivial. Alineado con `.claude/rules/github-actions-deferred.md` (`cd-prod.yml` deferred hasta servidor real).

### Concepto

Un release `shipped` es la **base sólida** (verificada, en main + staging). "Pasar a producción" es el acto separado de **lanzarlo al servidor de producción**. Esto separa lo que está probado y estable de lo que realmente está live de cara al usuario.

### Mecánica futura (cuando exista deploy real)

```
release shipped
   │  Chris: "pasar a producción"  (inmediato | agendado fecha/hora/día del mes)
   ▼
production_status: scheduled        (si agendado · production_scheduled_at = ISO futuro)
   │  llega el momento (o inmediato)
   ▼
crear branch release/{brand}-vX.Y.Z desde main  →  push  →  GitHub Actions cd-prod.yml
   │  deploy al servidor + medios que se determinen
   ▼
production_status: in_production    (deployed_at = ISO · release_branch sellado)
```

### Campos del schema (reservados hoy)

| Campo | Significado | Hoy |
|---|---|---|
| `production_status` | `not_deployed` → `scheduled` → `in_production` | `not_deployed` |
| `production_version` | semver del pase, ej `v0.3.0` (define la tag/branch) | null |
| `production_scheduled_at` | ISO · inmediato (now) o fecha-hora futura elegida por Chris | null |
| `deployed_at` | ISO · cuándo terminó el deploy real | null |
| `release_branch` | `release/{brand}-vX.Y.Z` que disparó el deploy | null |

### Estado actual en el cockpit

El botón **"Pase a producción"** aparece en releases `shipped` pero está **deshabilitado** con tooltip "próximamente". No dispara nada. Cuando se implemente: modal de scheduling (inmediato / fecha-hora) → endpoint que crea el branch `release/*` + registra `production_status`.

### Triggers para implementarlo (cuándo dejar de ser placeholder)

Los mismos que reactivan GH Actions (`github-actions-deferred.md`): servidor staging/prod provisionado, primera release `vX.Y.Z` planeada, o customer-paying contract. Al implementar → crear ADR + actualizar esta sección a estado activo.

---

## Sección 7 · Anti-patterns prohibidos

- ❌ Release con stories de brands distintas (cada release es brand-specific)
- ❌ `target_date` poblado sin owner asignado (Chris lo llena cuando hay compromiso)
- ❌ Merge release a main sin todas las stories en state ∈ {done, dropped}
- ❌ Editar `release_id` después de creación (es PK funcional)
- ❌ Stories del release con `release: F2` en checkpoint pero NO listadas en `release.yaml.stories[]` (inconsistencia)
- ❌ Status `shipped` sin `shipped_date` (hook bloquea)
- ❌ Status `planning` con stories en state ≥ refining (debe ser in_progress)
- ❌ Release sin descripción (Chris pone razón del bloque de trabajo)
- ❌ Marcar `shipped` sin gate de comportamiento (stories cerradas NO basta · falta el check verde sin regresión)
- ❌ Editar name/description/stories de un release `shipped` (es inmutable · correcciones vía `/pm-{brand}`)
- ❌ Mezclar los dos ejes: usar `shipped` para significar "está en producción" (shipped = base en main+staging, NO prod)
- ❌ Escribir `production_*` a mano hoy (placeholder reservado · lo escribe el flujo futuro § 6)

---

## Sección 8 · Referencias

- `docs/process/lifecycle.md` — SSoT del modelo 4-ejes · Release es el único contenedor temporal (outcome+phase muertos)
- `docs/process/capability-protocol.md` — caps que las stories del release tocan
- `docs/specs/templates/release-template.yaml` — template para nuevos releases
- `docs/process/checkpoint-protocol.md` — campo `release` en checkpoint.md de cada story
- `scripts/migrate_to_release_schema.py` — migration legacy → release
- `scripts/generate_backlog.py --brand {b}` — agrupa BACKLOG por release
- `tools/luana-cockpit/app/api/releases/route.ts` — CRUD endpoint
- `tools/luana-cockpit/app/roadmap/page.tsx` — vista Roadmap con drag entre releases
