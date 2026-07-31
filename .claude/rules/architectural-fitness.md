---
globs: "**/backend/tests/architecture/**/*.py,core/luana-core-*/tests/architecture/**/*.py"
description: Stub — invoca backend-expert skill
---

# Architectural Fitness Tests

Tests viven en dos niveles:

| Nivel | Path | Scope |
|---|---|---|
| Engine | `core/luana-core-*/tests/architecture/` | Reglas internas de cada package + contratos Extension SDK |
| Brand | `vitalia/backend/tests/architecture/` | DDD boundaries brand, registros Extension SDK válidos, no mirrors del engine |

Enforzan reglas estructurales que linters no catch (DDD boundaries, API contracts, conventions). **Ratchet pattern** — `KNOWN_*` allowlists shrink only.

```bash
WS=$(git rev-parse --show-toplevel)

# Per brand:
cd ${WS}/{brand}/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q --tb=short

# Per core package:
cd ${WS}/core/luana-core-{pkg} && ${WS}/.venv/bin/pytest tests/architecture/ -x -q --tb=short

# Full (engine + vitalia) — NO existe `make arch-test`; usar:
make ci-parity    # engine + vitalia (equivalente a CI; corre tests/architecture/)
```

Auto vía gate-runner shortcuts `arch-test-{brand}` / `test-{brand}` (corren `tests/architecture/`) + `make ci-parity` (mandatory pre-push-to-main) + `/pase-produccion`.

Common fixes (cross-module/domain framework imports/missing response_model/hard deletes/SA 1.x query) en `backend-expert` skill → `references/architectural-fitness.md`.

**No-skip:** new violation = build fail. Allowlists shrink only — fix + remove. Add to allowlist requiere justificación commit.

## Engine awareness

- Engine arch tests cubren reglas del paquete + contracts del Extension SDK.
- Brand arch tests (vitalia) cubren registros válidos + no mirrors (ver `anti-duplication.md`).
- Allowlists per package — no compartir allowlist file entre core y brand (cada uno tiene su `KNOWN_*`).
