---
story_id: vitalia-ds-showcase
title: Design-system showcase fiel (best-of-best dentro del shell) — demostrador R-FID para ratificación Chris
brand: vitalia
type: ui-story            # mockup/showcase dentro del shell-organism
state: done
owner: /po-ux
created: 2026-06-07
completed: 2026-06-11
architecture_pattern: ADR-vitalia-004   # citado por gate brand (shell-feature); showcase vive dentro del shell
program: design-system-homologation     # cuelga de ADR-014 + proposal 2026-06-07 (platform)
program_inventory: docs/architecture/luana-platform/design-system-inventory-best-of-best.md
dod_live_verified: true
dod_live_verified_skip_reason: "Showcase técnica pura — renderizado HTML derivado, no user-facing app flow. Ratificación Chris vía mockup visual en docs/architecture/luana-platform/design-system-inventory-best-of-best.md"

# Propósito
purpose: |
  Producir el PRIMER artefacto HTML FIEL POR CONSTRUCCIÓN que Chris pueda abrir y ratificar — el
  "best of best" del inventario renderizado DENTRO del shell-organism real, con los tokens REALES de
  globals.css (no copia a mano). Sirve 3 fines: (1) Chris ratifica la dirección viendo HTML confiable
  (R-FID); (2) demuestra el mecanismo de fidelidad por construcción que reemplaza al _shared.css copiado;
  (3) corrige el drift detectado (--agent-mateo 56°→53°).

# Requisitos cementados por Chris (2026-06-07, 2ª ronda)
requisitos:
  R-FID: "Ratificar = ver HTML fiel por construcción (deriva de fuente única). Durable = /showcase route que renderiza componentes reales. Estático = espejo derivado, NO dibujo a mano."
  R-SHELL: "Toda funcionalidad user-reachable se entrega DENTRO del shell-organism (lift de ADR-vitalia-003 a regla platform)."
  R-1SRC: "Consolidar duplicación de tokens en globals.css (dos --radius 0.625 vs 0.5 línea 51 vs 151 + sistema --vitalia-* legacy paralelo al Shadcn) — feed de la story de adopción, no de esta."

# Scope
scope:
  - "Showcase HTML fiel dentro del shell: átomos canónicos + EntityWorkspaceLayout (N3) + EntityInfoCard (8 slots) + grupo info-agrupada+autosave + page-primitives + estados (empty/error/loading)"
  - "Tokens derivados/inlineados verbatim de vitalia/frontend/src/app/globals.css (NO _shared.css copiado) — fix drift mateo"
  - "Shell wrapper reusado de la fuente canónica (ADR-vitalia-003 § wrapper-verbatim)"
out_of_scope:
  - "Construir los componentes reales (EntityInfoCard, átomos sync) — eso es S-CORE-DS-LAYOUT-PRIMITIVES/ATOMS-SYNC (platform build)"
  - "/showcase route en la app real — story posterior (cuando existan los componentes)"
  - "Consolidación de tokens R-1SRC + migración de los 650 arbitrary — story de adopción"
  - "nicolify/comunify"

# Picks a renderizar (del inventario platform, file:line ahí)
picks:
  atoms: "@luana/ui-kit canónico (versión mergeada: input/textarea/badge vitalia + dropdown/tooltip nicolify)"
  n3_list_detail: "nicolify EntityWorkspaceLayout + EntitySubNavBar"
  grouped_autosave: "contenedor nicolify Group + autosave vitalia use-autosave(600ms+coalesce) + FloatingAutosaveIndicator vitalia"
  entity_card: "anatomía 8 slots, base vitalia StaffCard + ícono agent-color nicolify IcpCard"
  page_primitives: "PageContainer/PageHeader/Section/Toolbar/FilterBar/EmptyState/ErrorState/Pagination/skeletons"

ratified_by_chris: true
ratified_at: 2026-06-08
ratified_iter: 8
ratified_decisions:
  - "N3 = patrón único 1-panel: master = grilla de EntityInfoCard + búsqueda/filtro; entrar a una caja → workspace full-width (NO 2-col persistente)"
  - "Franja N3 = TERCER RIBBON full-bleed (sticky, bg-card + border-bottom, mismo lenguaje que Ribbon N1/SubTabs N2), NO card con borde redondeado"
  - "EntityPicker: nombre-entidad = selector ▾ con buscador + tope por lote + lazy-load → cambiar de entidad sin volver atrás. Contrato build real: búsqueda server-side debounced + fetch paginado (cap ~20, cursor) + render windowed/virtualizado + a11y combobox"
  - "‹ Especialistas (con flechita) = vuelta a la grilla (matiza el 'N3 sin back' previo: el root-pill con flecha ES la vuelta)"
  - "Contenedor HOJA: 100% ancho full-responsive (sin max-width) · franjas full-bleed · contenido en PageContainer (padding 1.25/1.5rem) + PageContentStack"
  - "EntityInfoCard = Opción B (responsive 4@ancho/3-5, circular, indicadores repartidos, card clickeable, kebab ⋮)"
  - "Autosave = 1 píldora flotante + barrita de color del agente (sin badge por-grupo)"
  - "Select canónico Shadcn-style reemplaza <select> nativo (chevron + panel + check en activo + agent-color)"
  - "Tooltip policy + color-por-agente policy ratificadas"
  - "Page-primitives + Estados (empty/ErrorState/ListPageSkeleton/FormPageSkeleton) OK"
  - "Picks canónicos confirmados: N3 nicolify-EWL · autosave vitalia (600ms+coalesce+indicador flotante) · átomos @luana/ui-kit merge · EntityInfoCard B sobre StaffCard"
  - "Mecanismo durable = /showcase route en la app real (R-FID por construcción)"

next_action: "/pm-vitalia — cementar picks canónicos en inventario/ADR + construir ENFORCEMENT mecánico (templates + scripts + skill bindings) que /po-ux (mockups) y /dev-team (build) DEBEN respetar, de una vez por todas + reforzar /harnesses-improvement"

chris_verify:
  required: true   # es user-reachable (Chris lo abre y ratifica)
  signoff:
    signed_by: Chris
    date: 2026-06-08
    result: SATISFIED
    notes: "Ratificó el showcase completo iterando 8 rondas /po-ux: N3 1-panel + contenedor-hoja full-bleed + EntityPicker lazy + Select canónico + picks + durable=/showcase route. Ratificación de DIRECCIÓN visual sobre el mockup fiel — no es story de código (los componentes reales se construyen en las stories del programa)."
    open_items: []
reconciled: false
---

# vitalia-ds-showcase — log

## 2026-06-07 · apertura (/pm-vitalia, handoff /pm-luana)
Home vitalia del programa design-system-homologation. Primer deliverable = showcase HTML fiel
(best-of-best dentro del shell) para que Chris ratifique la dirección viendo HTML confiable (R-FID).
NO se construyen componentes reales acá — es el mockup fiel que precede al build platform.
Las 2 stories abiertas (adrian-embudo, lisa-doctores) NO se tocan.

## 2026-06-08 · RATIFICADO (/po-ux, 8 rondas) → handoff /pm-luana
Chris ratificó el showcase completo (ver `ratified_decisions` en frontmatter + log en chris-input.md).
Iteración clave de las últimas rondas: N3 reconstruido a patrón único 1-panel (master grilla ↔ detalle
workspace), franja = tercer ribbon full-bleed (no card), EntityPicker con buscador+tope+lazy-load,
Select canónico Shadcn-style (mató los <select> nativos feos), y lineamientos del **contenedor HOJA**
(100% ancho + franjas full-bleed + contenido PageContainer). Mecanismo durable = `/showcase` route real.

Chris pidió EXPLÍCITO: que `/pm-luana` garantice que TODO esto lo **respeten mecánicamente** `/po-ux`
(al mostrar funcionalidad en mockups) y `/dev-team` (al programar) — "de una vez por todas" — generando
las plantillas/scripts/bindings necesarios + reforzando `/harnesses-improvement`. Handoff a /pm-luana.
