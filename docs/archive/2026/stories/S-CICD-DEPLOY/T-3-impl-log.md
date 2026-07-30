# T-3 — Impl Log
# cd-prod.yml orchestrator (parse release/* + dorny/paths-filter + deploy)

## Deliverables

- EXTENDIDO: `.github/workflows/cd-prod.yml` — el skeleton de CORE fue reemplazado con
  el orchestrator completo:
  - trigger: on: push: branches: ['release/**']
  - job parse-release: regex extrae brand+version, valida SemVer, whitelist brands
  - job detect-changes: dorny/paths-filter@v3 con filtro '{brand}/**' + 'core/**'
  - job deploy: if: needs.detect-changes.outputs.should_deploy == 'true', usa _deploy-brand.yml
  - job extract-changelog: post-deploy, extrae [Sin lanzar] y crea GitHub Release
  - mensaje error en español neutro, sin acentos en variables shell

- CREADO: `scripts/test_parse_release.py` — helper de test del regex parse-release

## Acceptance criteria result

- A1: actionlint cd-prod.yml → 0 errores → PASS
- A2: test fixture release/vitalia-v0.3.0 → brand=vitalia version=0.3.0 → PASS
- A3: test fixture release/invalido-vbroken → exit 1 → PASS
- A4: grep condicion if should_deploy == 'true' → PASS

## Fixtures adicionales verificados

- release/comunify-v1.0.0-rc1 → brand=comunify version=1.0.0-rc1 → PASS
- release/nicolify-v2.1.3 → brand=nicolify version=2.1.3 → PASS
- release/vitalia-1.2.3 (sin v) → exit 1 → PASS
- release/-v1.0.0 (brand vacío) → exit 1 → PASS

## State: DONE
