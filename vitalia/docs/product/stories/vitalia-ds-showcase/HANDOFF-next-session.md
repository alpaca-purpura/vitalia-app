# HANDOFF — Design System Homologation (showcase iteration) · para conversación nueva

> Bootstrap para retomar SIN perder la esencia. Owner del programa: `/pm-luana` → `/pm-vitalia` → `/po-ux` (iterando el showcase). Sesión origen: 2026-06-07/08. Worktree: `~/Proyectos/luana-vitalia` (wip/vitalia). **Todo vive en disco (uncommitted) → la sesión nueva lo ve.**

## La esencia (no perder esto)

Chris: *"el dev-team crea cada interfaz a su forma → se siente otra app"*. Queremos **homologar TODA la UI cross-brand por enforcement MECÁNICO** (no por criterio — vitalia ya tiene tokens+skill+rule D1 y aun así driftea 368 veces). Programa de **5 capas** en `core/@luana/` + plantillas obligatorias por átomo + las **mismas plantillas en `/po-ux`** para que **el mockup = lo construido**. **Ratificado por Chris (ADR-014 accepted).**

3 requisitos duros de Chris (2ª ronda):
- **R-FID** — ratificar = ver **HTML fiel POR CONSTRUCCIÓN** ("lo que veo ES lo que es"). Durable = un **`/showcase` route en la app real** que renderiza los componentes reales; el `.html` estático es un espejo derivado, NO un dibujo a mano (eso es lo que driftó).
- **R-SHELL** — `/po-ux` entrega TODA funcionalidad user-reachable **dentro del shell-organism** (lift de `ADR-vitalia-003` a regla platform).
- **R-1SRC** — UNA fuente de tokens: `globals.css` hoy tiene **duplicación** (dos `--radius` 0.625 vs 0.5 · sistema `--vitalia-*` legacy en paralelo al Shadcn `--primary/--agent-*`). Consolidar antes de declarar "fuente única".

## Dónde estamos (skill chain)

`/pm-luana` abrió el programa → `/pm-vitalia` owna la ejecución vitalia → **`/po-ux` iterando el showcase** (`vitalia-ds-showcase`, state: `refining`, NO ratificado). El showcase es el artefacto que Chris ratifica para destrabar el build.

## El showcase (artefacto vivo)

**Archivo:** `vitalia/docs/product/stories/vitalia-ds-showcase/mockups/showcase.html`
**Servir:** `cd vitalia/docs/product/stories/vitalia-ds-showcase/mockups && python3 -m http.server 8893` → `http://localhost:8893/showcase.html`
**Fidelidad por construcción:** tokens inlineados VERBATIM de `globals.css` (líneas 30-67), `--agent-mateo` en **53° real** (corrige el 56° drifteado). Shell chrome reusado del canónico (topbar/ribbon 5 agentes+Plataforma/Valeria sidebar/sub-nav). Dark mode + splitter states funcionan. Navegación = franja N3 con 6 secciones.

### Estado por sección (lo que Chris YA decidió iterando)

| Sección | Estado |
|---|---|
| **Átomos** | button ×7 variantes · inputs con estados · badge/chip/switch/checkbox/avatar. **+ Tooltips** (tratamiento `ⓘ`+bubble flecha + **política**) **+ Color por agente** (política: la acción primaria adopta el color del agente activo via `--agent-active`; texto por contraste — Mateo amarillo→oscuro; semántico NUNCA cambia; global=`--primary` cian). *Tooltip+color = propuestos, falta OK explícito.* |
| **N3 Lista/Detalle** | EntityWorkspaceLayout (nicolify). ✅ Ajustes Chris: **sin** botón "‹ Especialistas" (redundante) · "Especialistas"+"＋Nuevo" en header del listado · **buscador** debajo del header. Tercera franja del detalle = identidad + leaf-tabs (Perfil/Agenda/Servicios). |
| **EntityInfoCard** | ✅ **Opción B ELEGIDA** + comportamiento ratificado: grid responsivo (a ese ancho **4 por fila**, `minmax(250px)`, varía 3-5) · **todas circulares** · **indicadores repartidos a lo ancho** (como A) · **card entera clickeable** · **kebab ⋮** arriba-derecha con menú (Editar/Eliminar/contextual). Opción A colapsada en `<details>` de referencia. |
| **Info + Autosave** | Group (nicolify) + autosave (vitalia 600ms+coalesce) + **una sola píldora flotante** por página (✅ Chris: **sin** badge por-grupo, redundante) + **barrita de color del agente** a la izquierda (✅ le gustó). |
| **Page-primitives** | PageHeader · Toolbar/FilterBar · Section · Pagination (faltan ~8 de 10 en código real). |
| **Estados** | empty · error · skeleton. |

## Decisiones cementadas (Chris)

1. **Fase 0 lock scope** = ejes tokenizados (spacing+radius+font-size+color-hex); **allowlist** w/h/min/max sizing; ratchet shrink-only. (vía AskUserQuestion)
2. **Escala spacing** = Tailwind 4px-base as-is.
3. **EntityInfoCard** = **Opción B** + comportamiento (responsive 4@ancho/3-5, circular, indicadores repartidos, clickeable, kebab).
4. **Autosave** = 1 píldora flotante (sin badge por-grupo) + barrita de agente.
5. **N3** = sin back button, buscador en listado, header "Especialistas".
6. **Piloto** = vitalia.

## Pendientes (lo que falta ratificar)

- **Tooltip policy** + **agent-color policy** → OK explícito (están propuestos en el showcase).
- Seguir puliendo el showcase (Page-primitives + Estados aún no comentados por Chris en detalle).
- **DECISIÓN GRANDE 1 — Picks canónicos:** confirmar los ganadores del inventario (N3 nicolify · autosave vitalia · átomos @luana/ui-kit sincronizado · EntityInfoCard B · page-primitives).
- **DECISIÓN GRANDE 2 — Mecanismo durable:** `/showcase` route en la app real (recomendado, fiel por construcción + guard de regresión) vs estático generado.
- Tras ratificar el showcase: el programa se desbloquea → ready packages de las stories de build (ATOMS-SYNC, LAYOUT-PRIMITIVES, POUX-KIT) + adopción comprehensiva.

## Hallazgos clave (grounding, no teoría)

- **@luana/ui-kit** ya tiene ~21 átomos 100% token-based (cero hex/px crudo). El drift NO vive en los átomos → vive en el **contenido maquetado a mano** (capas 3-4) + arbitrary sueltos. Medido vitalia FE: **650 arbitrary** (font-size 182 · sizing w/h 189 · color-hex 64 · radius 32 · spacing ~10 **ya casi limpio**).
- **Átomos desincronizados:** liftear a core las mejores versiones (input/textarea/badge vitalia · dropdown/tooltip nicolify) + exportar checkbox/switch/card/popover/alert-dialog (existen en core, las marcas los reinventan con `<div>`).
- **Mockups NO parten de lo mismo "por construcción":** los de servicios/cuenta portan el shell fiel pero vía `_shared.css` **copiado a mano** → ya driftó (mateo 56 vs 53). doctores/embudo (8) están **aislados** sin shell. → el mockup-kit debe **derivar de globals**, no copiar.
- `ADR-vitalia-003` ya exige mockup-dentro-del-shell + `_shared.css` espejo — **vitalia-only** + fidelidad por copia. Liftear el principio a platform + cambiar a fidelidad por construcción.

## Artefactos / paths (SSoT)

| Qué | Path |
|---|---|
| Doctrina | `docs/architecture/luana-platform/ADR-014-design-system-homologation.md` (accepted) |
| Plan core+lift | `docs/promotion-protocol/proposals/2026-06-07-design-system-homologation.md` (accepted) |
| **Inventario best-of-best + ADDENDUM** (★ SSoT del programa) | `docs/architecture/luana-platform/design-system-inventory-best-of-best.md` |
| Fase 0 spec (lock) | `docs/product/stories/core-ds-tokens-lock/01-spec.md` |
| **Showcase + story** | `vitalia/docs/product/stories/vitalia-ds-showcase/` (checkpoint · chris-input · mockups/showcase.html) |
| Handoff previo | `docs/architecture/luana-platform/design-system-homologation-HANDOFF.md` |
| Tokens reales | `vitalia/frontend/src/app/globals.css` (líneas 30-67) |
| Shell CSS fiel (fuente a reusar) | `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/mockups/_shared.css` |
| Rule mockup-in-shell (a liftear) | `vitalia/.claude/rules/shell-mockup-per-component.md` |
| Learning N3 | `vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md` |

## Stories de build (cuelgan del programa, post-ratificación)

`core-ds-tokens-lock` (Fase 0 lock, refining) · `S-CORE-DS-ATOMS-SYNC` · `S-CORE-DS-LAYOUT-PRIMITIVES` (incl. EntityWorkspaceLayout + EntityInfoCard-B + autosave + page-primitives) · `S-CORE-DS-POUX-KIT` (mockup-kit + atar /po-ux) · `S-{brand}-DS-ADOPTION` (comprehensiva). Las 2 stories vitalia abiertas (`vitalia-fase2-adrian-embudo` developed · `vitalia-fase2-lisa-doctores` developing) **NO se tocan** — Track A es independiente.

## Resume protocol (sesión nueva)

```bash
# 1. Servir el showcase
cd ~/Proyectos/luana-vitalia/vitalia/docs/product/stories/vitalia-ds-showcase/mockups
python3 -m http.server 8893    # → http://localhost:8893/showcase.html

# 2. Leer SSoT (en este orden)
cat vitalia/docs/product/stories/vitalia-ds-showcase/HANDOFF-next-session.md   # este file
cat docs/architecture/luana-platform/design-system-inventory-best-of-best.md   # inventario + ADDENDUM
cat vitalia/docs/product/stories/vitalia-ds-showcase/chris-input.md            # log de decisiones iteradas
```

Continuá con `/po-ux vitalia vitalia-ds-showcase` para seguir iterando el showcase, hasta que Chris ratifique → entonces `/pm-luana` arma los ready packages del build.
