---
id: ADR-vitalia-003
title: Protocolo mockup-per-component como gate bloqueante pre-/architect (shell-organism)
status: Superseded
superseded_by: "Storybook = SSoT visual — design-system-canon.md § 5 (2026-06-22, ratificado Chris)"
date: 2026-05-22
deciders: [/po-ux, /pm-vitalia, Chris]
brand: vitalia
supersedes: []
references:
  - vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
  - vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md
  - vitalia/.claude/rules/shell-mockup-per-component.md
  - vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html
  - vitalia/docs/specs/templates/01-spec-shell-template.md
  - vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md
---

# ADR-vitalia-003 — Protocolo mockup-per-component como gate bloqueante pre-/architect

## Contexto

El shell-organism Vitalia (`vitalia-mvp-ui-foundation` outcome v2.0) es la base UI de toda la aplicación: **5 especialistas (Lisa, Mateo, Adrián, Lucas, Camila) + tab Plataforma** en el Ribbon N1, con Valeria como sidebar supervisora permanente (★ v1.2 2026-05-30: Valeria salió del Ribbon; Mateo entró como especialista Operar; ConfigTab "Configurar" → "Plataforma"). Los 8+ componentes del shell (TopBarGlobal, ValeriaSidebar, ValeriaRail, ValeriaHistory, ValeriaChat, Ribbon, SubTabsBar, ShellOrganismLayout) se construyen en stories F1-S1..S10 durante Fase 1 y se REUSAN en ~22 sub-tabs durante Fase 2 (F2-S1..S22 aprox según outcome master).

El mockup HTML integral `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` (1439 líneas) está ratificado por Chris 2026-05-22 como SSoT visual del shell completo. Sin embargo, este mockup compone organismos en su contexto integral — NO muestra componentes individuales en isolation con todas sus variantes (Button default/secondary/ghost/destructive/outline, ValeriaSidebar collapsed/rail/full, Ribbon active per agente, etc.).

El paradigm v4 (CLAUDE.md § SDD Level 3 + Conv 1 DISCOVERY) prevé que `/po-ux` produce `01-spec.md` con wireframes inline (ASCII / HTML / Figma link) pero NO obliga mockup HTML POR COMPONENTE individual. El workflow actual permite que `/architect` arranque con un spec que tiene wireframes ASCII pero sin ratificación visual fina componente-por-componente. Si el componente implementado deriva del intent visual de Chris, el catch típicamente ocurre durante `/auditor` review visual al cierre del PR — momento donde un fix requiere refactor visual costoso (~3-8h dependiendo del componente) en vez de un ajuste de mockup (~20 min).

## Problema

Sin gate visual estricto componente-por-componente entre `/po-ux` y `/architect`:

1. **Drift entre mockup integral ratificado y componente implementado.** Chris ratifica el shell completo; el builder implementa cada componente; el componente puede desviar sutilmente del intent visual (proporciones, spacings, tints) sin que el spec en texto lo detecte.
2. **Goldens Playwright se generan del componente implementado, no del mockup esperado.** Esto convierte el visual golden en "test que se autoaprueba" — pasa siempre porque compara X consigo mismo. Pierde su rol de contrato anti-drift.
3. **Auditor llega tarde para detectar desvíos visuales.** Si el componente está implementado + integrado + en tests, el costo de cambiarlo escala. Detectar en mockup es ~20× más barato.
4. **Fase 2 hereda los desvíos.** Cada sub-tab Fase 2 reusa los organismos del shell (Ribbon, SubTabsBar, ValeriaSidebar). Si un organismo deriva del mockup, las 22 sub-tabs heredan el drift sin remediación per-sub-tab.

## Criterios evaluados

### 1. Modelo "implement-first then review" vs "mockup-first then implement"

| Opción | Pro | Contra |
|---|---|---|
| **Implement-first then review** (status quo paradigm v4) | Builder arranca rápido. Iteración técnica primero. Auditor revisa el resultado final integrado. | Costo refactor visual post-implement ~3-8h por componente. Drift sutil pasa goldens auto-aprobados. Auditor llega tarde para vetar componentes que no matchean mockup integral. |
| **Mockup-first then implement** (este ADR) | Chris ratifica visual fino por componente ANTES de gastar Opus en `/architect` + builder. Costo mockup mini ~20 min. Auditor compara componente real vs mockup-per-componente (golden side-by-side). Imposible que builder derive del visual sin detección. | Loop `/po-ux` se extiende (1-2 horas adicionales por story para mockups). Requiere disciplina Chris ratificación interactiva. |

### 2. Costo absoluto: 20 min mockup vs 3-8h refactor visual post-implement

Tomando F1-S2 `topbar-global` como ejemplo:
- **Mockup HTML mini** (`topbar-global.html` con Tailwind CDN + tokens Vitalia): ~20 min `/po-ux` + ~10 min Chris revisión local.
- **Refactor visual post-implement** (si Chris detecta proporción incorrecta del LogoMark o spacing del TenantSwitcher): tocar `TopBarGlobal.tsx` + adjusting test fixtures + regenerar goldens + re-aprobar Auditor = ~3-5h end-to-end.

Multiplicado por 10 componentes Fase 1 + ~10 componentes Fase 2 (organismos sub-tab-specific) = potencial savings 40-80h netos.

### 3. Mockup HTML como golden source-of-truth Playwright

Con mockup HTML por componente: el spec § 7 Visual Goldens declara mapping `mockup HTML → golden file → componente React`. Playwright `@project=visual` monta AMBOS lado a lado en viewport idéntico y compara screenshots. Diff > 0.1% pixel ratio = FAIL. Esto convierte el mockup en contrato ejecutable, no en doc de referencia que el código puede ignorar.

Sin mockup HTML por componente: el golden se genera del componente implementado y siempre pasa (no detecta drift del mockup integral). Pierde su rol arquitectónico.

### 4. Escalabilidad cross-brand (promotion candidate)

Comunify (Story 12 done + WIP recovery) eventualmente va a construir su shell agéntico. Nicolify ya tiene patterns shell (CopilotSidebar) — si refactoriza a paradigma shell-organism. Las 6 brands pendientes bootstrap (SaaSora, InmoFlow, Retailly, Fixia, Guestly, FitFlow) van a construir sus shells.

Pattern aplicable N-brand: `promotable: candidate` para lift a `.claude/rules/shell-mockup-per-component-protocol.md` raíz cuando N≥2 brands lo adopten. Captured como learning `vitalia/docs/learnings/2026-05-22-shell-mockup-per-component-protocol.md`.

## Decisión

**Protocolo mockup-per-component aplica como gate BLOQUEANTE pre-`/architect`** para:

- Toda story Vitalia Fase 1 que construye componente UI shell-organism (F1-S1..S10 — F1-S0 exenta por ser infra-only sin componentes user-facing nuevos).
- Toda story Vitalia Fase 2 que construye sub-tab con UI nueva (≈22 stories según outcome master `vitalia-mvp-ui-foundation` v2.0).

**Workflow obligatorio:**

1. `/po-ux` redacta `01-spec.md` con § 3 Atomic Design Layers + § 4 Reuse Map (de template SHELL).
2. `/po-ux` genera mockup HTML por componente nuevo en `vitalia/docs/product/stories/{story-id}/mockups/{component}.html`. Una excepción: si la story produce >5 componentes, agruparlos en max 3 mockup pages contextualmente (ej. `topbar-and-tenant-switcher.html`).
3. `/po-ux` levanta `python3 -m http.server 8888` desde `mockups/` y comparte URL local con Chris.
4. Chris revisa visual + interactivo (hover states, dropdowns, dark mode toggle si aplica) + ratifica componente-por-componente o pide cambios.
5. `/po-ux` itera mockups hasta ratify whole-spec.
6. Spec transitions `refining → refined` SOLO si `checkpoint.md::ratified_visual_by_chris == true`.
7. `/architect` REFUSE arrancar si `mockups/` vacío o `ratified_visual_by_chris != true`.

**Excepciones explícitas (NO aplica protocolo):**

- F1-S0 `vitalia-fase1-stack-stability` (infra-only — sin componentes user-facing).
- Service-stories (BE only, sin UI).
- Agentic-stories conversacionales puras (usar `/ux-agentico` flow design en su lugar).
- Stories Fase 2 que solo conectan data a componentes ya ratificados de Fase 1 (e.g., una sub-tab que reusa Ribbon F1-S7 + SubTabsBar F1-S8 + adds solo contenido placeholder).

## Consecuencias

### Positivas

- Chris ratifica visual fino componente-por-componente antes de gastar Opus en `/architect` + builder.
- Visual goldens Playwright se convierten en contrato ejecutable (mockup HTML side-by-side vs componente real).
- Drift entre mockup ratificado y componente implementado se cattchea en `/po-ux` loop, no en `/auditor` review post-merge.
- Mockups HTML quedan como documentación visual viva del componente — auditor + futuros devs los consultan.
- Fase 2 hereda organismos pre-ratificados visualmente; no propaga drift downstream.

### Negativas

- Loop `/po-ux` se extiende ~1-2 horas por story (mockups + revisión Chris interactiva).
- Requiere disciplina Chris para ratificación visual en cada story Fase 1+2 (~30 stories totales).
- Mockup HTML mantenimiento: si el componente final difiere intencionalmente del mockup, debe actualizarse el mockup mismo PR (sino genera ratchet roto).

### Neutras

- Auditor Phase D gherkin matrix se extiende: además de scenarios funcionales, valida mockup-golden-component triple.

## Implementación

3 artifacts cementan este ADR simultáneamente:

1. **Este ADR** (`vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md`) — autoridad arquitectónica brand-local.
2. **Rule overlay** (`vitalia/.claude/rules/shell-mockup-per-component.md`) — enforcement de máquina vía skills carga rule automáticamente cuando trabajan en stories Vitalia Fase 1+2.
3. **Spec F1-S0** § 13.1 — referencia al protocolo como parte del bootstrap shell, ya que F1-S0 es la story que establece la base UI de toda la aplicación.

## Promotion candidate

Pattern documentado como `promotable: candidate` en `vitalia/docs/learnings/2026-05-22-shell-mockup-per-component-protocol.md`. `/pm-luana` corre `make scan-promotables` periódicamente; cuando N≥2 brands adopten patrón análogo (Comunify shell o Nicolify refactor a shell-organism), lift a `.claude/rules/shell-mockup-per-component-protocol.md` raíz o a `core/luana-core-ui/protocols/`.

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-22 | Decisión inicial. Ratificada por Chris durante refining loop F1-S0 (sesión `/po-ux` batch 3 conclusion). |
