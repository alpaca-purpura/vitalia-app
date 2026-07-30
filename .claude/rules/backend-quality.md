---
paths:
  - "**/backend/src/**"
  - "**/backend/tests/**"
  - "**/backend/pyproject.toml"
  - "core/luana-core-*/**"
description: Stub — invoca backend-expert skill
---

# Backend Quality

> **Tier-2 `paths:` (W1-Phase2 2026-06-09 · tier: project).** Esta rule NO carga always-on — inyecta al leer un archivo que matchea `paths:` (test empírico #16299 OK — `harness-refactor-w1/W1-phase2-execution.md §3`; el viejo `globs:` era mecanismo MUERTO, CC lo ignora). Caveat #23478: no dispara en write puro de archivo nuevo — el gate mecánico (eslint/tsc/ruff/arch-tests) cubre ese hueco.

- Ruff 70+ rules, 0 errors. Config per-package en `core/luana-core-*/pyproject.toml` y `{brand}/backend/pyproject.toml`. Line 120, py312.
- Arch fitness gates en `core/luana-core-*/tests/architecture/` (engine packages) + `{brand}/backend/tests/architecture/` (per brand: DDD boundaries ratchet, API contracts, conventions, currency, ETL, master-data, naming, domain purity, Extension SDK contracts).
- Pytest asyncio auto, fail_under=43%. Markers: `integration`, `verify`.
- Native commands (NUNCA docker exec). Venv canónico **AT WORKSPACE ROOT**: `${WS}/.venv/bin/{ruff,pytest}` (uv workspace editable installs).

```bash
WS=$(git rev-parse --show-toplevel)

# Per brand:
cd ${WS}/{brand}/backend && ${WS}/.venv/bin/ruff check src/ tests/
cd ${WS}/{brand}/backend && ${WS}/.venv/bin/pytest tests/architecture/ -v

# Per core package:
cd ${WS}/core/luana-core-{pkg} && ${WS}/.venv/bin/pytest -v
```

Detalle (rules list completa, per-file overrides, jscpd/interrogate, naming conventions, todos los arch tests) en `backend-expert` skill → `references/backend-quality.md`.

## Multibrand awareness (post reorg 2026-05-15)

- Engine: `core/luana-core-*/src/luana_core_*/` — modificar requiere `/pm-luana` promotion gate.
- Brand backend: `{brand}/backend/src/modules/{brand}/...` per brand (nicolify, vitalia, comunify, lupulo).
- Venv único raíz: NUNCA `cd {brand}/backend && python -m venv .venv` (rompe resolución `luana_core_*`).
- Cada brand consumer corre su propia suite arch fitness además del engine core.
