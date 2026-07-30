---
brand: vitalia
date: 2026-05-28
slug: chris-input-at-idea-doctrine-gap
type: process-doctrine
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: doctrina (no es lift de código — es cambio de proceso cross-brand)
ratified_by: chris
tags: [chris-input, idea, refining, brand-docs-schema, R4, pm-skill, pre-commit, doctrine]
---

# chris-input.md debe nacer con la idea (state=idea), no recién en refining

## Qué aprendimos

Chris quiere volcar ideas en `chris-input.md` **desde el momento en que crea la idea**
(`state=idea`), aún antes de refinarla. La doctrina actual lo crea recién al pasar a
`refining` → fricción: no hay dónde acumular notas/referencias durante la fase `idea`.

**Origen:** sesión 2026-05-28 revisando el cockpit (`/pm-vitalia` + remote-control).
Chris ratificó explícitamente el cambio.

## Estado actual (lo que hay que cambiar)

| Superficie | Comportamiento hoy | Comportamiento deseado |
|---|---|---|
| `docs/process/chris-input-protocol.md` | chris-input.md creado al pasar `idea → refining` | creado **junto con la idea** (`state=idea`) |
| `.claude/rules/brand-docs-schema.md` § R4 | obligatorio desde `refining`; ideas que nunca refinan no lo requieren | obligatorio **desde `idea`** (toda story que existe tiene chris-input.md) |
| `.claude/skills/pm-{brand}/SKILL.md` + `_pm-brand-template` | "idea {x}" crea **solo** `checkpoint.md` | "idea {x}" crea `checkpoint.md` **+ `chris-input.md`** (mismo template del cockpit) |
| `scripts/git-hooks/pre-commit` § 14 | exige chris-input.md en `state ∈ {refining…reviewing}` | extender check a `state = idea` (advisory en wip/*, hard en main) |

## Lo que YA está bien (no tocar)

- **Cockpit** rutas `extend-cap` + `from-done` → `createNewStoryDocs`
  (`tools/luana-cockpit/app/api/_lib/story-templates.ts:43-111`) **ya** crea
  `chris-input.md` con `state=idea`. El template (Notas + Referencias + Conversación)
  es el canónico a reutilizar en el skill `/pm-{brand}`.

## Why

`chris-input.md` es la "cocina" de la story (notas + refs + conversación Chris↔Claude).
Si nace recién en refining, las ideas crudas del periodo `idea` no tienen hogar tracked
→ se pierden en el chat o en la cabeza de Chris. Crear el archivo desde `idea` lo hace el
buzón único de ideas desde el día cero.

## How to apply

`/pm-luana` cementa el cambio en sesión dedicada (worktree `protocol`):
1. Editar `chris-input-protocol.md` + `brand-docs-schema.md` R4 (idea como trigger).
2. Actualizar los 4 `/pm-{brand}` activos + `_pm-brand-template` ("idea {x}" scaffold dual).
3. Extender pre-commit § 14 a `state=idea` (advisory wip, hard main).
4. Backfill opcional: ideas vitalia existentes sin chris-input.md → crear con template vacío.

## Referencias

- `tools/luana-cockpit/app/api/_lib/story-templates.ts` — template canónico (reusar)
- `.claude/rules/brand-docs-schema.md` § R4 — regla a extender
- `docs/process/chris-input-protocol.md` — doc canónico
- `.claude/skills/pm-vitalia/SKILL.md` § "Comandos típicos" fila "idea {x}"
