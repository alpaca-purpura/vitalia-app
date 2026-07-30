---
paths:
  - "**/frontend/src/**"
  - "**/frontend/eslint.config.mjs"
  - "**/frontend/package.json"
description: Stub — invoca frontend-expert skill
---

# Frontend Quality

> **Tier-2 `paths:` (W1-Phase2 2026-06-09 · tier: project).** Esta rule NO carga always-on — inyecta al leer un archivo que matchea `paths:` (test empírico #16299 OK — `harness-refactor-w1/W1-phase2-execution.md §3`; el viejo `globs:` era mecanismo MUERTO, CC lo ignora). Caveat #23478: no dispara en write puro de archivo nuevo — el gate mecánico (eslint/tsc/ruff/arch-tests) cubre ese hueco.

- ESLint 0 errors. Config `{brand}/frontend/eslint.config.mjs`. 60+ rules. Plugins: sonarjs, boundaries, react-perf, prettier.
- TypeScript strict, 0 errors.
- Vitest tests + 20% coverage threshold per-brand.
- Architecture fitness tests `{brand}/frontend/src/__tests__/architecture/`. Ratchet allowlists shrink only.

```bash
WS=$(git rev-parse --show-toplevel)

# Per brand:
cd ${WS}/{brand}/frontend && npx tsc --noEmit
cd ${WS}/{brand}/frontend && npx eslint src/ --cache
cd ${WS}/{brand}/frontend && npx vitest run --coverage
```

Detalle (rules error/warn, per-file overrides, jscpd/knip/madge, FSD boundaries, arch tests list) en `frontend-expert` skill → `references/frontend-quality.md`.

**No-skip:** disable ESLint rule sin justification comment. `// eslint-disable-next-line` solo con explanation. Many violations → refactor, not disable.

## Multibrand awareness (post reorg 2026-05-15)

- Cada brand tiene su `{brand}/frontend/` independiente (nicolify, vitalia, comunify, lupulo).
- Shared TS packages: `core/luana-core-*/` (TS) via `@luana/*` imports — modificar requiere `/pm-luana` promotion gate.
- Brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow) heredan estos gates al bootstrap.
