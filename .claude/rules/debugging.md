# Debugging

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Diagnóstico completo (comandos docker per-brand, top-12 patterns, fix quality) en `docs/rules-detail/debugging.md` — cargalo al debuggear. Runbook stack: `docs/process/docker-dev-multibrand.md`.

Trigger: bug/error/traceback en el stack dev (containers `luana-dev-{brand}_{service}_dev-1`).

No-skip 1-liner: root cause only · una hipótesis por fix · regression test FIRST (RED→GREEN) · engine bug → reproducir en cada brand consumer · ports: nicolify=8001/3001 · vitalia=8002/3002 · comunify=8003/3003 · lupulo=8004/3004.
