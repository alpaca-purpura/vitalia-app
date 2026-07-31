# Archivo — herencia multimarca luana-platform

**Archivado: 2026-07-31**, al quedar `vitalia-app` como repo standalone single-brand (extracción del monorepo `luana-platform`, snapshot 2026-07-30). Decisión ratificada por Chris: **archivar, no borrar** — todo esto sigue siendo prior-art consultable.

## Qué es esto

`vitalia-app` nació como una de las 4 marcas activas (nicolify, vitalia, comunify, lupulo, + 6 en bootstrap) del monorepo multimarca `luana-platform`, que compartía un engine (`core/luana-core-*`) con un promotion gate brand→core y protocolos de trabajo multi-worktree/multi-sesión. Al extraer vitalia a repo propio, esa maquinaria cross-brand dejó de aplicar: no hay otras marcas, no hay portfolio cross-brand, no hay gate de promoción cross-marca, y los worktrees paralelos fueron retirados. La vista master del producto ahora es `vitalia/docs/product/checkpoint.md`.

## Qué contiene

- `portfolio/` — vista master de los 11 universos (PORTFOLIO.md auto-gen), 1-pagers de cada marca (incl. los pointers `vitalia.md` y `vitalia-capabilities.md`, redundantes con `vitalia/docs/`) e INFRA-MATRIX. Todo era output auto-generado (R3).
- `promotion-protocol/` — el gate brand→core: README, 37 proposals y scans de promotables. En el repo standalone los cambios al engine se hacen directo en `core/` con los arch tests como gate.
- `architecture/luana-platform/` — auditorías del plan multimarca muerto: core-audit, core-purge, carve-out/migración desde nicolify, pending-migrations, cross-repo tooling.
- `product/` — BACKLOG platform auto-gen (snapshot stale 2026-05/06), los 14 `outcomes/` del flujo platform viejo y la story platform cerrada `platform-lift-sales-agent-graph-runtime` (state: done).
- `process/` — protocolos retirados: multi-sesión/worktrees (`parallel-sessions-protocol`, `worktree-protocol-v2-plan`), runbooks multibrand (git-workflow, CI/CD, warp handbook, GitHub environments 4-brands), el programa cerrado harness-refactor (w0.5–w10 + charter + audits) y handoffs/reviews de proceso puntuales.

## Referencias en docs vivos

Las menciones a nicolify/comunify/lupulo que persisten en docs vivos (learnings, ADRs, PARADIGM, rules) son **históricas**: contexto de decisiones y prior-art técnico del engine. No implican que esas marcas existan en este repo — viven en `luana-platform`.
