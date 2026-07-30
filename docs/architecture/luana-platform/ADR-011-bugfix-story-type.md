# ADR-011 — Story type `bugfix` (lightweight)

**Status:** accepted · **Date:** 2026-05-30 · **Decider:** Chris (ratificado) · **Scope:** platform-wide (cross-brand) · **Owner del cambio:** `/pm-luana`

## Contexto

Hasta hoy los tipos de story de primera clase eran `ui-story` | `service-story` | `agentic-story` (SSoT `docs/process/lifecycle.md` § Tipos de story). Cada uno arrastra la ceremonia completa de refinement: spec con Gherkin AI-resistant, a veces mockups (`02-design-ui.md`) o diseño conversacional (`02-design-agentic.md`), ready package de 5 artefactos (`03-arch` + `04-validators` + `05-guidelines` + `06-tickets` + `dispatch-plan`).

En la práctica aparece con frecuencia un trabajo que NO encaja en esa ceremonia: **arreglos de comportamiento roto** y **completions de cableado incompleto** — scope quirúrgico (1-N archivos, ≤1-2 días), sin diseño nuevo. Forzarlos por la ceremonia completa es fricción desproporcionada; meterlos ad-hoc (se usó "infra-migration" informalmente) rompe la trazabilidad del `type:` y deja a los skills/cockpit sin un enum coherente.

Ya existe `.claude/rules/hotfix-repro-mandatory.md` (repro-first para hot-fix) pero a nivel de **ticket**, no como **tipo de story** con su propio flujo lite.

## Decisión

Se agrega un cuarto tipo de story de primera clase: **`bugfix`** (lightweight).

- **Definición:** story que **arregla un comportamiento roto** o **completa algo cableado a medias**, scope quirúrgico (1-N archivos, ≤1-2 días), **sin diseño nuevo**.
- **Mismos 10 estados macro** (`idea → refining → refined → ready → developing → developed → reviewing → done`, + `parked`/`dropped`). Lo que se reduce es la **ceremonia de diseño**, nunca la **verificación**.
- **Gate repro-first (HARD):** hereda `hotfix-repro-mandatory.md`. `checkpoint.md::repro_verified: true` antes de `developing`. Para un **bug** = test RED que reproduce la falla. Para una **completion** = "el comportamiento X falta / Y no renderiza" verificado **en vivo** (ejercer la acción real + leer logs, NUNCA un GET 200 — `test-design-doctrine.md` § Verificación REAL).
- **Refinador:** `/po` (BE/servicio) o `/po-ux` (UI), ambos en **modo lite**: `01-spec.md` corto con **scenarios de regresión**, sin mockups salvo UI nueva, sin `02-design-*`.
- **`/architect` lite:** ready package reducido (`06-tickets` + `04-validators` con scenarios de regresión; `03-arch`/`05-guidelines`/`dispatch-plan` opcionales o inline). Puede ir directo a tickets si no hay decisión arquitectónica.
- **`cap_change_type`:** `fix` por default (append `change_log` type=fix, sin scenarios nuevos). Si la fix **completa** una cap agregando ≥1 scenario → `extend`.
- **No se reduce:** TDD (RED→GREEN), story-closure-gate (developed→reviewing→done auto-handoff), anti-orphan (CONN), gates de calidad (lint/arch-fitness/coverage/jscpd).
- **Escape de reclasificación:** si durante refinement/arch se descubre que el trabajo requiere diseño nuevo (mockups, decisión arquitectónica, ≥1 scenario de feature) → `/pm-{brand}` reclasifica `type` (bugfix → ui/service/agentic) antes de cerrar `ready`.

## Consecuencias

**Positivas:** trabajo chico fluye con menos fricción manteniendo trazabilidad `type:` + cap ledger; el cockpit gana un enum coherente; el repro-first queda blindado a nivel story (no solo ticket).

**Riesgos / mitigación:** riesgo de que features grandes se disfracen de `bugfix` para saltar ceremonia → mitigado por el escape de reclasificación + el criterio "sin diseño nuevo / ≤1-2 días". El repro-first evita que se shippeen "fixes" sin reproducir la causa.

## Cementado en

- `docs/process/lifecycle.md` § Tipos de story (+ subsección `bugfix` lite) — **SSoT**
- `docs/process/capability-protocol.md` § Sección 3 (bugfix → cap_change_type fix/extend)
- `docs/specs/templates/checkpoint-template.md` (`type` enum + `repro_verified` field)
- `.claude/skills/{po,po-ux,architect}/SKILL.md` (scope decision + ready lite)
- `.claude/skills/{pm-vitalia,pm-comunify,pm-nicolify,pm-lupulo}/SKILL.md` + `_pm-brand-template/SKILL.md` (tabla tipos + auto-chain)
- `CLAUDE.md` § SDD Level 3 (pointer)
- `.claude/rules/hotfix-repro-mandatory.md` (gate heredado) · `.claude/rules/test-design-doctrine.md` (verificación real)

## Referencias

- `docs/process/lifecycle.md` — modelo 4 ejes + tipos de story
- `.claude/rules/hotfix-repro-mandatory.md` — repro-first (gate heredado)
- `.claude/rules/test-design-doctrine.md` § Verificación REAL ≠ HTTP 200
- `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md` — autonomy v4.1 (base de los 10 estados)
