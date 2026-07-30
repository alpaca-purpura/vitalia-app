---
brand: vitalia
date: 2026-05-22
slug: shell-mockup-per-component-protocol
promotable: candidate
applies_to_other_brands_potentially: [comunify, nicolify, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: ".claude/rules/ (raíz) o core/luana-core-ui/protocols/ (futuro)"
severity: MEDIUM
origin_story: vitalia-fase1-stack-stability
origin_session: 2026-05-22 /po-ux refining loop (batch 3 conclusion)
ratified_by_chris: true
---

# Shell mockup-per-component como gate visual bloqueante pre-/architect

## Qué aprendimos

Durante el refining loop de F1-S0 con `/po-ux`, Chris ratificó una preocupación que el paradigm v4 base no atrapa: **el wireframe inline en `01-spec.md` (ASCII/HTML/Figma link) NO es suficiente cuando una story construye componentes UI que se reutilizan downstream**. La granularidad del wireframe integral en el spec no cementa el contrato visual fino componente-por-componente.

Aplicado al shell-organism Vitalia: el mockup integral `dual-mode-shell.html` (1439 líneas, ratificado 2026-05-22) compone organismos en su contexto integral pero NO muestra cada componente en isolation con todas sus variantes (Button default/secondary/ghost/destructive/outline, ValeriaSidebar collapsed/rail/full, Ribbon active per agente, etc.). Sin ratificación visual componente-por-componente ANTES de `/architect`, el builder puede derivar sutilmente del intent visual y los goldens Playwright se auto-aprueban (comparan el componente implementado consigo mismo, no contra el mockup esperado).

## Origen

- **Story:** `vitalia-fase1-stack-stability` (F1-S0) — la story que establece la base UI de toda la aplicación Vitalia.
- **Trigger:** Chris explicitó durante refining batch 3 conclusion: "considera que la construcción debe tener check visuales con playwright para asegurar que no se rompe la parte visual y quede como hemos revisado en el mockup, obviamente que todo desde los átomos pero en general un vistazo del cumplimiento visual debe ser parte" + "antes de lanzar el arquitect afinar detalles visuales y revisar cada componente como quedaría en la nueva estructura con mockups html para que ya tengas todo bien listo y aprobado por mi".
- **Decisión cementada:** opción (A) — 3 lugares simultáneos (spec § 13.1 + ADR-vitalia-003 + rule overlay) para máxima defensa en profundidad.

## Why

El paradigm v4 actual asume que el wireframe integral en `01-spec.md` es suficiente input para `/architect`. Esto funciona razonable para CRUD lists/forms estándar donde el design system Shadcn + Tailwind constrain las variantes. **Pero falla cuando la story construye componentes shell que se reutilizan en 20+ sub-tabs downstream**: cualquier drift sutil en un organismo (TopBarGlobal, ValeriaSidebar, Ribbon) propaga a TODAS las pantallas que lo consumen, sin remediación per-pantalla.

Costo asimétrico:
- **Mockup HTML mini ratificación pre-`/architect`:** ~20 min `/po-ux` + ~10 min Chris revisión local.
- **Refactor visual post-implement** (si Chris detecta proporciones/spacings/tints incorrectos en review final): ~3-8h tocar componente + tests + goldens + re-aprobar Auditor.

Multiplicado por 10 componentes Fase 1 + ~10 componentes Fase 2 (organismos sub-tab-specific) = potencial savings 40-80h netos.

## How to apply (en contexto Vitalia, cementado)

Cuando `/po-ux` refina una story Vitalia Fase 1+2 que construye componentes UI shell-organism:

1. Redactar `01-spec.md` con § 3 Atomic Design Layers + § 4 Reuse Map.
2. Generar mockup HTML por componente nuevo en `vitalia/docs/product/stories/{story-id}/mockups/{component}.html` (Tailwind CDN + tokens Vitalia via CSS vars + datos LatAm + Spanish neutro + dark mode si soporta).
3. Levantar `python3 -m http.server 8888` desde `mockups/` y compartir URL local con Chris.
4. Iterar componente-por-componente hasta ratify whole-spec.
5. Update `checkpoint.md::ratified_visual_by_chris: true` + `ratified_visual_mockups: [paths]` SOLO al ratify final.
6. Transition `state: refining → refined` SOLO si flag visual ratificado.
7. `/architect` REFUSE arrancar si flag ausente.

**Excepciones documentadas en ADR-vitalia-003:** F1-S0 (infra-only), service-stories, agentic-stories conversacionales puras, stories Fase 2 que solo agregan data a componentes ya ratificados Fase 1.

## Why "promotable: candidate" cross-brand

Cualquier brand que construya un **shell agéntico complejo con componentes reutilizables downstream** va a sufrir el mismo gap:

- **Comunify** (creator economy + educación) — eventualmente va a tener su propio shell con tabs per módulo (Courses, Community, Authority Vault, Offer Ladder). Mismo riesgo de drift entre wireframe spec y componente implementado.
- **Nicolify** (agencias B2B) — actualmente tiene CopilotSidebar (single component) pero si refactoriza a paradigma shell-organism, mismo problema.
- **Saasora/InmoFlow/Retailly/Fixia/Guestly/FitFlow** (brands pendientes bootstrap) — todas construirán sus shells eventualmente.

**Threshold lift (per `.claude/rules/anti-duplication.md`):** cuando N≥2 brands adopten patrón análogo, `/pm-luana` evalúa lift del protocolo a:
- `.claude/rules/shell-mockup-per-component-protocol.md` (raíz) — enforcement universal multibrand
- O bien `core/luana-core-ui/protocols/mockup-per-component.md` si decide encapsularlo en el futuro package UI compartido

**Hoy:** 1 brand consumer (Vitalia) → cement brand-local. Anti-duplication no aplica todavía.

## Referencias

- `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` — autoridad arquitectónica brand-local (SSoT del por qué + criterios evaluados)
- `vitalia/.claude/rules/shell-mockup-per-component.md` — rule overlay enforcement máquina
- `vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md` § 13.1 — referencia al protocolo dentro del spec base shell
- `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` — mockup integral SSoT visual (ratificado 2026-05-22)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — atomic design SSoT del shell
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md` v2.0 — outcome master Fase 1+2
- `.claude/rules/anti-duplication.md` § lift shared — threshold N≥2 brands
- `docs/promotion-protocol/README.md` — workflow promotion candidate

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-22 | Captura inicial post-refining F1-S0. `promotable: candidate` pendiente scan-promotables `/pm-luana`. |
