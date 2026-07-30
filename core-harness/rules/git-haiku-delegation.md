# Git Haiku Delegation Pattern

> **Slim stub (context-rot pass 2026-05-30).** Cuerpo operativo completo en `.claude/skills/commit-push/references/haiku-delegation.md` — carga on-demand. **Origen:** 2026-05-09 — análisis report.html; ~10709 git Bash uses = top tool, waste de Opus 4.8.

## Regla cardinal

Cuando orchestrator (Opus 4.8) llega a fase commit+push con >2 archivos, MUST delegar la ejecución a un sub-agent Haiku 4.5 via Agent tool. Opus prepara el plan (qué archivos, qué mensaje, qué guardrails); Haiku ejecuta el git workflow. Commits en hub único (ADR-009): siempre por pathspec (`git commit <rutas-exactas>`), NUNCA `git add .` + commit suelto — el índice es compartido entre sesiones.

## Cuándo carga el detalle

- Necesitás el guardrail verbatim completo para el prompt del worker Haiku
- Necesitás el pre-spawn checklist (categorizar MINE vs OTHERS, branch type, secrets check)
- Necesitás el spawn template o el failure handling matrix

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Opus ejecuta `git commit -m` directo cuando hay >2 files → debió delegar
- ❌ Opus pasa "commit todos los cambios" a Haiku sin explicit file list (Haiku usaría `git add .`)
- ❌ Haiku worker recibe prompt sin guardrails verbatim (el guardrail es el safety net)

## Referencias

- `.claude/skills/commit-push/references/haiku-delegation.md` — **cuerpo operativo completo** (guardrails verbatim, pre-spawn checklist, spawn template, failure handling)
- `.claude/rules/git-safety.md` — git fundamentals + prohibiciones absolutas
- `.claude/rules/parallel-safety.md` — multi-session WIP protection + M14 bucket locks
- `.claude/skills/commit-push/SKILL.md` — slash command wrapping este pattern
