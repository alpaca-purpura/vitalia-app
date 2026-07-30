---
title: "Modelo de 3 zonas como dimensión de capability (map_box/map_zone derivada de SYSTEM-MAP)"
date: 2026-05-30
type: business
brand: vitalia
promotable: candidate
origen: "story vitalia-paradigm-map-zones (DONE 2026-05-30) + ADR-010 + PARADIGM.md"
ratified_by: chris
tags: [paradigm, zonas, capability, map_box, map_zone, system-map, cockpit, promotion-candidate]
---

# Modelo de 3 zonas como dimensión de capability

## Contexto

La story `vitalia-paradigm-map-zones` cementó el paradigma de 3 planos (`PARADIGM.md` + `ADR-010`) y migró el mapa de vitalia a **3 zonas** (Agentes · Plataforma · Infraestructura) con un registro SSoT `vitalia/docs/architecture/SYSTEM-MAP.yaml` v2.0 que el cockpit LEE para renderizar por zona + 2 lentes. 68 caps fueron re-taggeadas con `map_box`/`map_zone`, y los pseudo-`agent_owner` `config`/`infra` quedaron muertos.

## Aprendizaje

El mapa del producto se modela como **3 zonas estables → cajas (per-brand) → áreas funcionales**, donde:
- La capability declara su **caja** (`map_box`); su **zona** (`map_zone`) se **DERIVA** del registro `{brand}/docs/architecture/SYSTEM-MAP.yaml`, nunca se escribe a mano (evita campos desincronizados).
- `agent_owner` aplica solo a la zona **Agentes** (lisa/valeria/adrian/lucas/camila/mateo + supervisora). Las caps NO-agénticas viven en Plataforma/Infraestructura vía `map_box`.
- El cockpit es **lector** del registro: componentes `ZoneColumn`/`BoxCard`/`AreaGroup` + `MapView` (zonas + 2 lentes: trabajadores · proceso) son cross-brand y solo necesitan que cada marca provea su `SYSTEM-MAP.yaml`.

## Aplicación práctica

- **Cuándo aplica:** al organizar el mapa de producto de cualquier marca (taxonomía de capabilities + render del cockpit).
- **Cómo aplica:** crear `{brand}/docs/architecture/SYSTEM-MAP.yaml` (3 zonas + cajas) → taggear caps con `map_box` → la zona se deriva → el cockpit renderiza.
- **Cuándo NO aplica:** marca sin caps todavía (lupulo placeholder) — nace con el scaffold pero sin contenido.

## Promotion candidate

La **estructura** (3 zonas + dimensión `map_box`/`map_zone` derivada de registro) es transversal y candidata a lift al protocolo compartido `docs/process/capability-protocol.md`. El **contenido** del SYSTEM-MAP (qué agentes/cajas) es per-brand. Proposal: `docs/promotion-protocol/proposals/2026-05-30-lift-zone-model.md` (state: proposed · recomendación ACCEPT · awaiting ratificación Chris). NO migrar otras marcas hasta ratificar.

## Referencias

- `docs/architecture/luana-platform/PARADIGM.md` — modelo 3 planos / 3 zonas (platform-wide)
- `docs/architecture/luana-platform/ADR-010-orquestacion-agentica.md` — decisión
- `.claude/rules/paradigm-arquitectura.md` — rule enforce-able (#36)
- `vitalia/docs/architecture/SYSTEM-MAP.yaml` — registro v2.0 vitalia
- `docs/promotion-protocol/proposals/2026-05-30-lift-zone-model.md` — proposal de lift
- `docs/process/capability-protocol.md` § 7 — dimensiones de cap (target del lift)
