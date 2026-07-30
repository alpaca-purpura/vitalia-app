---
brand: vitalia
date: 2026-05-27
slug: shell-mockup-wrapper-fidelity
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, fitflow, guestly]
target_core_package: null   # No es código — es proceso/skill. /pm-luana decide si promueve a .claude/rules/ raíz o /po-ux skill body
---

# Shell mockup wrapper fidelity — port verbatim, no reinventes

## Qué aprendimos

Cuando un mockup HTML per-component vive **dentro del shell-organism** (sub-tab / sub-sub-tab Fase 2), el wrapper visual de contexto (TopBar global, Ribbon agentes, SubTabsBar, ValeriaChat) MUST ser portado **verbatim** desde las fuentes canónicas archivadas — NUNCA reinventarlo aunque sea "para simplificar".

## Origen

Story `vitalia-fase2-lisa-marca` — sesión 2026-05-27 phase `AWAITING_CHRIS_FEEDBACK_V2`. Producido v2 con 3 mockups que tenían:

1. Ribbon agentes con HTML custom diferente al shipped (Chris flag "regression flag")
2. ChatValeria simplificado (textarea + botón único) en lugar del componente shipped F1-S6 (avatar + status dot + mode pill + composer con adornos 📎🎙️⚡ + Cmd+K hint)
3. Layout 50/50 hardcoded sin permitir mostrar los 3 splitter states reales
4. Tokens HSL coherentes pero uso pobre: faltaba gradient mariposa en logo, faltaban acentos cian/púrpura en CTAs, paneles grisáceos
5. `.panel-inner { max-width: 680px }` hardcoded → contenido NO respondía al cambio del splitter

Chris flag los 4 puntos:
> "considera que la barra que separa el chat de valeria se agranda y achica así que todo el contenido de las secciones deben ser 'responsive' para aprovechar los espacios"
> "podrías buscar la historia de usuario donde ya hay mockups de todo esto en vez de darme una creación que se aleja de la verdad"

Refactor v2.1 (mismo turn) portó wrapper verbatim desde:
- `vitalia/docs/archive/2026/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` (1439 LOC) — shell integral SSoT
- `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html` (310 LOC) — chat canónico
- `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html` — rail canónico

Resultado: 3 mockups con wrapper idéntico cross-file + panel-content propio fluido + splitter control 3-estados + colores marca correctos.

## Why (motivación)

La regla `shell-mockup-per-component.md` (cementada 2026-05-22) ya decía "dual-mode-shell.html es referencia macro" pero **no enforce port verbatim**. El gap permitió que la sesión genere mockups con wrapper inventado simplificado — técnicamente "tailwind + tokens", técnicamente "data LatAm realista", pero divergente del shipped en estructura. Chris detectó la divergencia visualmente y pidió refactor inmediato.

Costo del re-trabajo: ~2 horas (lectura 3 fuentes canónicas + rewrite 3 HTMLs + rewrite `_shared.css` con shell estructural + verificación). Costo de evitarlo en futuras stories Fase 2: 0 (la regla actualizada lo bloquea pre-mockup).

## How to apply (próximas stories Fase 2 sub-tab)

**Pre-mockup checklist (`/po-ux` debe verificar Step 4 antes de servir mockup a Chris):**

```bash
WS=$(git rev-parse --show-toplevel)
# Verificar que existen las 3 fuentes canónicas
ls ${WS}/vitalia/docs/archive/2026/stories/vitalia-shell-organism/mockups/dual-mode-shell.html
ls ${WS}/vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html
ls ${WS}/vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html
```

**En el mockup nuevo:**

1. Crear `_shared.css` del story-folder copiando estructura del wrapper desde los canónicos (NO reinventar)
2. Asegurar tokens HSL idénticos a `vitalia/frontend/src/app/globals.css`
3. Cada `{component}.html` del story usa `_shared.css` + agrega solo styles del panel-content propio
4. Incluir `.splitter-control` en topbar (3 botones data-state)
5. `.panel-inner` SIN `max-width` hardcoded → fluido (`width: 100%`)
6. `.cards-grid` con `repeat(auto-fit, minmax(280px, 1fr))` para responsive

**Verificación visual con Chris:** servir local en :8888 + pedir feedback sobre `panel-content` (no sobre el wrapper — ese es SSoT).

## Cross-brand relevance

Las brands que adopten un shell-organism agéntico similar (`comunify` cohort dashboards · `lupulo` KDS · futuras `fitflow`/`guestly`) heredarán el patrón. El protocolo "port shell wrapper verbatim, customize panel-content" aplica idéntico cambiando solo las fuentes canónicas brand-local.

**Recomendación a `/pm-luana`:** evaluar promotion a `.claude/skills/po-ux/SKILL.md` (skill body cross-brand) o a `.claude/rules/` raíz como rule transversal "mockup wrapper fidelity per-brand-shell". Cada brand listaría sus canónicos en frontmatter de la rule overlay.

## Referencias

- `vitalia/.claude/rules/shell-mockup-per-component.md` § "Shell wrapper fidelity" — constraint cementada en mismo PR
- `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/mockups/_shared.css` — implementación de referencia
- `vitalia/docs/archive/2026/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` — fuente canónica shell
- `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` — autoridad arquitectónica brand-local (revisar si agrega cláusula § wrapper fidelity)
- `.claude/skills/po-ux/SKILL.md` — workflow Step 4 visual gate
