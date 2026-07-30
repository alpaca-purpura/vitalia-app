---
brand: vitalia
date: 2026-05-17
slug: tooling-auto-regen-backlog
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: scripts/git-hooks/pre-commit (cross-brand tooling)
origin_story: vitalia-ux-discovery (sesión 2026-05-17 detección stale backlog)
---

# Auto-regen BACKLOG per-brand on pre-commit when docs/product/** touched

**Qué aprendimos:** el BACKLOG.md per-brand quedó stale entre sesiones (last regen 2026-05-16 vs sesión 2026-05-17 con cambios significativos: outcome creado + story v0 ratificada + 5 stories spawned). Sin auto-regen, el SSoT funcional brand pierde fidelidad rápido — "qué tenemos vitalia" deja de reflejar realidad.

**Origen:** `/pm-vitalia` sesión 2026-05-17 — Chris pidió estado real backlog. BACKLOG.md estaba desfasado por 24+ horas vs cambios reales en `outcomes/`, `stories/`, `capabilities/`. Required manual `python3 scripts/generate_backlog.py --brand vitalia` para sincronizar.

**Why:** humanos olvidan correr generators después de editar SSoT. El BACKLOG auto-gen pierde su valor si no refleja el último estado al momento de consulta. Mantenerlo actualizado debe ser automático, no disciplina.

**How to apply:**

- Trigger: `scripts/git-hooks/pre-commit` detecta archivos modificados/added/deleted en path regex `^[a-z]+/docs/product/(outcomes|stories|capabilities|modules)/.+\.(md|yaml)$`
- Acción: extraer brand slug del path (primer componente) → ejecutar `python3 scripts/generate_backlog.py --brand $SLUG` automáticamente → si BACKLOG.md / BACKLOG.yaml / BACKLOG-TLDR.md cambian, stage + commit en mismo commit (no separado)
- Escape hatch: magic comment `# backlog-regen-skip: <reason>` en commit body para bypass casos especiales
- Cross-brand: si el commit toca múltiples brands (raro), regen ambos
- Para `docs/` raíz (platform cross-brand) → trigger también `make portfolio` (regen `docs/portfolio/PORTFOLIO.md` + 12 brand 1-pagers)

**Promotion candidate cross-brand:**

Todos los 10 brands sufren mismo problema (BACKLOG stale entre sesiones). Es candidate clarísimo a tooling cross-brand vía `/pm-luana`. NO crear story per-brand para esto — lift al pre-commit hook compartido.

Propuesta para `/pm-luana`: agregar Section N a `scripts/git-hooks/pre-commit` (después de Section 4 freshness gate ya existente para shared abstractions) que dispare backlog regen cuando aplique. Tests cubre escenarios en `core/luana-core-platform/tests/scripts/test_pre_commit_hook.py` (donde ya viven los tests del hook).

**Related:**
- Tests existentes hook: `core/luana-core-platform/tests/scripts/test_pre_commit_hook.py`
- Bug header fixeado mismo sesión: `scripts/generate_backlog.py` línea 606 dejaba "Nicolify" hardcoded en BACKLOG.md per-brand — fix aplicado 2026-05-17.
