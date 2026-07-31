# Promotion Proposal: Modelo de 3 zonas (map_zone/map_box + SYSTEM-MAP registry)

---
state: accepted                    # proposed | under_review | accepted | rejected | migrated
proposed_date: 2026-05-30
target_package: docs/process/capability-protocol.md  # protocol/process lift (NO es code package)
origin_brand: vitalia
origin_learnings:
    - "vitalia/docs/learnings/2026-05-30-paradigma-3-zonas-cap-dimension.md"
category: data-model              # dimensión de capability + registro SSoT (process-level)
semver_impact: minor              # campo nuevo opcional por cap; brands opt-in con su propio SYSTEM-MAP
consumers_viable: [nicolify, comunify, lupulo, + 6 brands futuras]
recommendation: ACCEPT            # RATIFICADO Chris 2026-06-06 → accepted
ratified_by: Chris
ratified_date: 2026-06-06
---

## /pm-luana review (under_review · 2026-06-06)

**Recomendación: ACCEPT** — lift barato (process-level, a `capability-protocol.md`), self-recommended ACCEPT, doctrina ya platform-wide (`PARADIGM.md`/ADR-010). Consumers: nicolify/comunify/lupulo + 6 futuras. Sin riesgo de regresión de código (es mecánica de capability + scaffold `SYSTEM-MAP.yaml` per-brand). NO es esfuerzo de semanas como el shell.

**Para ratificar (Chris):** APPROVED para promover la mecánica `map_box`/`map_zone` (derivada de registro) al protocolo compartido + agregar scaffold `SYSTEM-MAP.yaml` a `_pm-brand-template`.

---

## Pattern Summary

El **modelo de 3 zonas** organiza el mapa del producto en **Agentes · Plataforma · Infraestructura**. Cada capability declara su **caja** (`map_box`) y su **zona** se **deriva** (no se escribe a mano) de un registro SSoT por marca: `{brand}/docs/architecture/SYSTEM-MAP.yaml` (`zones[].boxes[].functional_areas`). El cockpit LEE ese registro y renderiza por zona (3 columnas) con 2 lentes (trabajadores · proceso). Reemplaza los pseudo-`agent_owner` `config`/`infra` (muertos) por cajas reales en las zonas Plataforma/Infraestructura. La doctrina (`PARADIGM.md` + `paradigm-arquitectura.md` + `ADR-010`) **ya es platform-wide**; lo que esta proposal evalúa promover es la **mecánica de capability** (dimensión `map_box`/`map_zone` derivada de registro) al protocolo compartido `capability-protocol.md`, para que cualquier marca adopte su propio `SYSTEM-MAP.yaml` por zonas.

## Origin Story

Emergió en **vitalia**, story `vitalia-paradigm-map-zones` (DONE 2026-05-30, commit `d12e4e0a`/`4d6bdd09`, archivada). Cementó `PARADIGM.md` + `ADR-010-orquestacion-agentica.md` + rule `paradigm-arquitectura.md` (#36) y migró el mapa de vitalia a v2.0: SYSTEM-MAP con 3 zonas (Agentes = 5 especialistas + Valeria supervisora + Mateo · Plataforma = acceso/onboarding/configuracion · Infraestructura = 4 cajas), **68 caps re-taggeadas** con `map_box`/`map_zone`, cockpit renderizando por zona + 2 lentes.

## Why Promote?

- [x] Used in ≥2 brands OR clear future need — usado en vitalia; **necesidad transversal clara**: toda marca tiene un mapa de producto que hoy se modela ad-hoc.
- [x] Genuinely transversal — la **estructura** (3 planos → 3 zonas → cajas → áreas) es del paradigma platform-wide, NO lógica de negocio brand-specific. El **contenido** del SYSTEM-MAP (qué agentes/cajas) sí es per-brand.
- [x] Stable API — la doctrina ya está cementada en `PARADIGM.md`/ADR-010 (no cambia cada sprint).
- [x] Worth the abstraction cost — evita que cada marca reinvente taxonomía de mapa + que el cockpit tenga 4 renders distintos.

## Cross-Brand Audit

| Brand | Current State | Would Use? | Notes |
|---|---|---|---|
| vitalia | ✅ implementado (SYSTEM-MAP v2.0, 68 caps tagueadas, cockpit por zona) | origen | brand de referencia |
| nicolify | sin SYSTEM-MAP; rebuild agentic-first en curso (5 agentes Luana/Abel/Brenda/Christian/Norvil) | **sí** (alto fit: ya es agentic-first) | adoptar al rebuild |
| comunify | sin SYSTEM-MAP; 18 caps con dimensiones v3 (agent_owner config/infra legacy) | **sí** | migración de caps config/infra → cajas |
| lupulo | placeholder (sin caps) | sí (al bootstrap) | nace con el modelo |
| 6 brands futuras | bootstrap pendiente | sí | `_pm-brand-template` debería incluir SYSTEM-MAP scaffold |

## API Surface (proposed)

**Lift al protocolo compartido** `docs/process/capability-protocol.md`:

1. **Dimensión `map_box` (declarada) + `map_zone` (derivada)** como 5ª/6ª dimensión de cap, junto a las 4 existentes (`tech_module`/`agent_owner`/`functional_area`/`user_visible`). `map_zone` NUNCA se escribe a mano — se deriva de `SYSTEM-MAP.yaml`.
2. **Convención `{brand}/docs/architecture/SYSTEM-MAP.yaml`** como registro SSoT por marca (schema: `zones[].boxes[].{id,label,agent_owner?,functional_areas,supervisor}`). Las 3 zonas (agentes/plataforma/infraestructura) son estables (del paradigma); las cajas/áreas son per-brand.
3. **Enum `agent_owner`** restringido a la zona Agentes; `config`/`infra` **deprecados** (→ cajas de Plataforma/Infraestructura vía `map_box`).
4. **Cockpit** `lib/system-map.ts` + componentes `ZoneColumn`/`BoxCard`/`AreaGroup` + `MapView` (zonas + 2 lentes) ya son **cross-brand** (el cockpit es tool cross-brand, lee el SYSTEM-MAP del worktree) — no requieren lift adicional, solo que cada marca provea su `SYSTEM-MAP.yaml`.

## Migration Plan (si ACCEPTED — NO ejecutar ahora)

1. `capability-protocol.md`: agregar sección dimensión `map_box`/`map_zone` + schema SYSTEM-MAP (lift de la doctrina vitalia, generalizada).
2. `_pm-brand-template/`: scaffold `SYSTEM-MAP.yaml` (3 zonas vacías) al bootstrap de marca nueva.
3. Por marca activa (comunify primero, nicolify al rebuild): crear su `SYSTEM-MAP.yaml` + migrar caps `agent_owner: config/infra` → `map_box` en zonas Plataforma/Infraestructura. **Una story `bugfix`/migración por marca** (no big-bang).
4. Validators: extender `validate_code_cap_bidirectional.py` para derivar `map_zone` del SYSTEM-MAP de cada marca.

## Decisión pendiente (Chris)

Recomendación: **ACCEPT** (la estructura es claramente transversal + ya cementada platform-wide). Al ratificar Chris → `state: accepted` + handoff a story de lift en `capability-protocol.md`. NO se migran otras marcas en esta proposal — solo la decisión de lift.
