# Anti-Orphan Integration (guardián CTO — nada llega a `done` como isla)


> **Slim stub (context-rot pass 2026-05-30).** Cuerpo operativo completo en `.claude/skills/architect/references/anti-orphan-integration.md` — carga on-demand cuando `/architect` se activa. **Origen:** sesión 2026-05-28 — Chris detectó funcionalidades huérfanas desde el cockpit; rule codifica el rol CTO como gate idea→done. **Cement-date:** 2026-05-28.

## Regla cardinal

Ninguna story alcanza `done` si su salida es una **isla**. Toda funcionalidad MUST cumplir las **4 contenciones CONN**: **C**onsumed (≥1 consumidor real) · **O**n the map (vive en un `capability` YAML con hogar declarado) · **N**avigable/reachable (hay un camino de acceso explícito) · **N**otarized/registered (cableada donde el runtime la descubre: `include_router`, nav tree, tool registry, Extension SDK EP). Si una de las 4 falta → isla → NO `done`.

## Cuándo carga el detalle

- Story crea/modifica cualquier surface (BE endpoint, FE page/component, agentic tool) → leer `anti-orphan-integration.md § 03-arch.md § Integration design` para el schema obligatorio (reachability path, consumers, registration points, home cap)
- Architect va a cerrar `state: ready` → verificar que `03-arch.md` tenga la sección `Integration design` con reachability path concreto; sin ella NO cierra `ready`
- `/auditor` corre categoría Connectivity → leer `anti-orphan-integration.md § Detección de isla` para el algoritmo de grep verbatim

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ `03-arch.md` sin sección `Integration design` / sin reachability path concreto (ready package incompleto)
- ❌ Builder crea el archivo pero NO lo registra (`include_router`/nav/DI/tool registry) en el mismo ticket
- ❌ Funcionalidad sin `cap_target` (sin hogar en el map) llegando a `developing`

## Referencias

- `.claude/skills/architect/references/anti-orphan-integration.md` — **cuerpo operativo completo** (tabla CONN ×4, gates idea→done, schema Integration design, algoritmo detección isla, anti-patterns ×9, enforcement layers, rationale CTO)
- `.claude/rules/anti-duplication.md` — no recrear (la isla suele ser duplicación)
- `.claude/rules/anti-duplication-refining.md` — prior-art scan en refining
- `.claude/rules/paradigm-arquitectura.md` — zona/caja del mapa (la O de CONN se concreta aquí)
- `docs/process/capability-protocol.md` — cap = hogar permanente + `dev_preview`
- `docs/process/lifecycle.md` — modelo 4-ejes (Release→Story→Capability→Scenario)
