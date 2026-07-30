---
title: "Brand design-system skill — el SSoT visual debe llegar al builder vía must_load_skills"
date: 2026-05-29
type: technical
brands_affected: [vitalia, nicolify, comunify, lupulo]
brand: vitalia
origen: "session 2026-05-29 (Chris: 'el shell organism / colores / átomos se pierden en desarrollo')"
ratified_by: chris
tags: [design-system, skill, builder, must-load-skills, shell-organism, frontend, sub-agent-channel, brand-scoped]
---

<!-- voseo-allowed: learning doc interno; cita verbatim a Chris ("mirá cómo se hizo"), no user-facing -->

# Brand design-system skill

## Contexto

Vitalia tiene su design system bien documentado (`design-system.md` 581 líneas, `SHELL-DESIGN-CONTRACT.md` 665 líneas, ADR-003/004, tokens vivos en `globals.css`+`tailwind.config.ts`, ~50 componentes shell-organism). Aun así, "se perdía en desarrollo": los builds reinventaban el wrapper del shell, usaban grises en vez de tokens, Chris tenía que repetir "mirá cómo se hizo este módulo".

## Aprendizaje

El problema NO era falta de documentación — era **falta de un canal de carga al builder**. El `builder-frontend` es un **sub-agente** y **NO hereda el `CLAUDE.md` overlay ni la memoria** del orquestador. Su único canal de entrada es `06-tickets.yaml → assignment.must_load_skills + must_load_artifacts`. Los gates de design system (ADR-003/004) vivían en refining/review (`/po-ux`, `/architect`, `/auditor`), nunca en el que construye.

Solución (clase generalizable): un **skill brand-scoped `{brand}-design-system`** que es un **índice narrado + router sobre los SSoT existentes** (NO duplica doc ni código), cableado obligatoriamente:
- `/architect` (architect-fe) lo lista en `must_load_skills` de todo ticket FE de la brand.
- `builder-frontend` lo carga y reporta "Skills consulted".
- `auditor-frontend` lo usa como inventario para cat 9 (Visual fidelity) + 13 (Anti-duplication).
- overlay `{brand}/CLAUDE.md` lo nombra (ayuda al orquestador/refinador, no al builder).

## Aplicación práctica

- **Cuándo aplica:** cualquier brand con design system propio (shell, átomos, tokens) que se pierda en build. Piloto = `vitalia-design-system`.
- **Cómo aplica:** crear `.claude/skills/{brand}-design-system/SKILL.md` como índice pointer-first; cablear en architect-fe + auditor-frontend + overlay + regla 34 (D0).
- **Cuándo NO aplica:** no duplicar contenido — el skill apunta a docs/código, no los copia. ⚠️ `core/@luana/design-tokens` solo exporta z-index; los tokens de color son brand-local (`globals.css`).
- **Generalización:** clase `{brand}-{dominio}` (mismo convenio que `pm-{brand}`). Otras instancias futuras: `{brand}-agents`, `{brand}-domain`. Rollout cross-brand vía `_pm-brand-template` después de validar el piloto.

## Referencias

- `.claude/skills/vitalia-design-system/SKILL.md` — piloto
- `.claude/skills/architect-fe/SKILL.md` § Brand design-system SSoT
- `.claude/agents/auditor-frontend.md` cat 9/13
- `.claude/rules/frontend-visual-fidelity.md` § D0
- `vitalia/.claude/rules/shell-mockup-per-component.md § Shell wrapper fidelity` (síntoma origen)
