---
story_id: vitalia-fase2-marca-especialidad-clinica
type: ui-story
agent_owner: lisa
map_zone: agentes
map_box: lisa
module: brand
capability: lisa.marca
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: "2026-06-07T01:20:00.000Z"
ratified_by_chris: false
parallel_safe: true
priority: medium
estimated_dev_days: 2-3
dependencies:
  hard: []
  soft:
    - vitalia-fase2-onboarding-clinica
    - vitalia-fase2-lisa-marca
blocks_hard: []
blocks_soft:
  - vitalia-fase2-lisa-servicios
reuse_map_summary: 'EXTEND lisa-marca (done) con un atributo de marca "especialidad(es) de la clínica" + EXTEND onboarding-clinica con el paso que lo declara al alta (set once). El atributo vive a nivel tenant/brand; lo consumen lisa-servicios (seed presets + ejemplos del rung-picker + opciones del dropdown de categoría per-servicio) y la capa agéntica de Lisa (ejemplos/sugerencias condicionados a la especialidad). Posible refinamiento engine: expandir OFFER_LADDER_HINTS (hoy fila genérica PROFESIONAL_SALUD) a filas por sub-vertical → /pm-vitalia si aplica.'
spawned_at: 2026-06-07T01:20:00Z
spawned_from: vitalia-fase2-lisa-servicios
created_by: /po-ux (capture — pendiente formalizar /pm-vitalia)
next_action: '/pm-vitalia formaliza: release + priority + cap lineage (extend lisa.marca) + decidir si el paso de CREACIÓN se implementa dentro de vitalia-fase2-onboarding-clinica o como parte de esta story · luego /po-ux refina (mockup del campo en Lisa → Marca + el paso en onboarding)'
release: F3
cap_target: lisa.marca
cap_change_type: extend
parent_story: null
---
# checkpoint · vitalia-fase2-marca-especialidad-clinica

> **★ Capturada por `/po-ux` durante el refinamiento de `vitalia-fase2-lisa-servicios` (round 3, 2026-06-07).**
> Es un **idea capture** — `/pm-vitalia` la formaliza (release/priority/cap lineage + decide el split con onboarding-clinica) antes de refinar.

## Idea (1 frase)

La **clínica/centro declara su(s) especialidad(es)** (qué tipo de centro es: odontología cosmética · medicina estética · oftalmología · dermatología · multi-especialidad) como **atributo de marca a nivel tenant**, **creado en el Onboarding** (set once al dar de alta) y **editable después en Lisa → Marca**. Otras superficies lo **consumen** (no lo recrean).

## Por qué (origen)

En `lisa-servicios` (round 3) Chris preguntó dónde se genera "la especialidad". Quedó claro que hay **dos** distintas:
- **Especialidad de la CLÍNICA** (tenant-level) → debe vivir en un solo lugar canónico, no recrearse en cada feature. **Decisión Chris 2026-06-07: se crea en Onboarding, se edita en Lisa Marca.**
- **Especialidad/categoría del SERVICIO** (per-servicio) → ya vive en `lisa-servicios` (su dropdown se alimenta de la especialidad de la clínica).

`lisa-servicios` la **consume** (seed presets + ejemplos del selector de peldaño + opciones del dropdown). La capa agéntica de Lisa la usa para dar ejemplos/sugerencias más acertados a esa clínica.

## Scope tentativo (lo afina /pm-vitalia + /po-ux)

- **Modelo:** atributo `especialidad(es)` a nivel tenant/brand (1 o varias — un centro puede ser multi-especialidad). Catálogo de especialidades alineado a los verticales Vitalia (Tier 1-3 de `vision.md`).
- **Crear (Onboarding):** paso en `vitalia-fase2-onboarding-clinica` — "¿qué tipo de clínica eres?" (multi-select). *(/pm-vitalia decide si se implementa dentro de onboarding-clinica o de esta story.)*
- **Editar (Lisa → Marca):** campo en la identidad de marca (extiende `lisa-marca`, done).
- **Consumir:** `lisa-servicios` (read-only) + capa agéntica de Lisa.
- **Engine (posible, /pm-vitalia):** expandir `OFFER_LADDER_HINTS` de la fila genérica `PROFESIONAL_SALUD` a filas por sub-vertical, para mejores hints del rung-picker.

## AC tentativos

- **AC-1** · El atributo "especialidad(es) de la clínica" se declara en el Onboarding (set once) y persiste a nivel tenant/brand.
- **AC-2** · Es editable después en **Lisa → Marca** (extiende la identidad de marca).
- **AC-3** · `lisa-servicios` lo consume read-only (seed presets + ejemplos del rung-picker + opciones del dropdown de categoría) — NO lo recrea.
- **AC-4** · Soporta multi-especialidad (un centro con dental + estética).

## Relación con otras stories

- **Consumida por:** `vitalia-fase2-lisa-servicios` (bloquea-soft — servicios funciona sin ella con presets genéricos, mejora con ella).
- **Extiende:** `vitalia-fase2-lisa-marca` (done) + `vitalia-fase2-onboarding-clinica` (activa).
