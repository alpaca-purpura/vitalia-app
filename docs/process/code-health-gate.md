# Code Health Gate — mantenibilidad BE + FE (dead-code · duplicación · docstrings · vuln)

**Origen:** HB-61 (2026-06-08) — consulta de Chris sobre `fallow` (dead-code/dup detector TS). Auditoría honesta destapó que las tools de mantenibilidad estaban **declaradas pero nunca cableadas**: FE corría 3/8 gates (jscpd/knip/madge sin config/deps/scripts), BE declaraba jscpd/interrogate/pip-audit (gates 11-13) pero el shortcut `test-{brand}` solo corría pytest/ruff/format/mypy, y BE **no tenía ninguna detección de dead-code** (ruff solo caza unused imports/vars, no funcs/clases/módulos). Este gate cierra el gap. **Owner:** `/pm-vitalia` (tooling cross-brand = plataforma).

## Qué corre (decidido sobre evidencia real, no teoría)

| Surface | Check | Tool | Tipo de gate | Estado vitalia 2026-06-08 |
|---|---|---|---|---|
| **FE** (TS/JS) | dead-code (archivos/exports/types sin usar) | **fallow** `dead-code` | baseline-ratchet (bloquea NUEVO) | baseline 128 unused |
| **FE** | duplicación | **fallow** `dupes` (src only, e2e/specs excluidos) | threshold HARD <8% | 2.9% ✓ |
| **FE** | ciclos / boundaries | fallow | info | — |
| **BE** (Python) | duplicación | **jscpd** | threshold HARD <5% | 2.85% ✓ |
| **BE** | dead-code | **vulture** (min-confidence 80) | baseline-ratchet (bloquea NUEVO) | baseline 31 |
| **BE** | docstrings | **interrogate** | threshold HARD ≥80% | 90.9% ✓ |
| **BE/env** | vulnerabilidades deps | **pip-audit** (`--skip-editable`) | allowlist-ratchet (bloquea CVE nuevo) | 10 pre-existentes en allowlist |

### Por qué fallow para FE y NO para BE
- **fallow es JS/TS-only** (Rust-native, 0.1-0.2s, zero-config, `--baseline`/`--threshold`/`--format json` nativos). Reemplaza la tripleta knip+jscpd+madge que nunca se cableó. → FE.
- **fallow no toca Python** → BE usa el equivalente Python-native: jscpd (lenguaje-agnóstico) + vulture (dead-code) + interrogate (docstrings) + pip-audit (vuln).
- **deptry se descartó** (probado 2026-06-08): genera 1318 falsos-positivos DEP003 en el uv workspace (no entiende los editable installs ni los transitivos del monorepo). vulture cubre el dead-code real sin ese ruido.

## Filosofía: baseline shrink-only (no rompe day-1)

Sobre un codebase legacy, prender dead-code/dup como HARD-block day-1 = muro de rojo (vitalia FE: 128 archivos / 18k líneas dup brutas). Por eso, igual que el ratchet de arch-fitness (`KNOWN_*` allowlists shrink-only):
- **dead-code (vulture/fallow) + vuln (pip-audit)** = baseline-ratchet → verde HOY, bloquea SÓLO findings NUEVOS. El baseline sólo puede ENCOGER (mejora), nunca crecer sin `--update-baseline` justificado.
- **dup (jscpd/fallow) + docstrings (interrogate)** = threshold HARD (los valores actuales ya pasan con margen).

Baselines viven en `scripts/quality/baselines/{brand}-{be-vulture.count,fe-deadcode.json}` + `pip-audit-ignore.txt` (allowlist de CVEs pre-existentes = **deuda de seguridad documentada**, se bumpea y se borra, no se agrega a la ligera).

## Uso

```bash
make code-health BRAND=vitalia                 # BE + FE
make code-health BRAND=vitalia SURFACE=fe      # solo FE
bash scripts/quality/code-health.sh nicolify be
make code-health-baseline BRAND=vitalia        # re-graba baselines (tras arreglar/justificar)
```

Gate-runner shortcut: `code-health-<brand>` (lo invoca el auditor/dev-team en la fase de gates). Parser: línea final `code-health: PASS|FAIL`.

## Dónde se enforce (placement)

- **Primario:** gate-runner shortcut `code-health-{brand}` → auditor (Phase 2 gate execution) + dev-team (quality gate antes de `developed`). El builder NO reporta "done" sin `code-health: PASS` (builder-frontend.md / builder-backend.md actualizados).
- **NO en pre-commit/pre-push:** correr fallow/jscpd vía `npx` en cada commit = fricción + riesgo de red. El enforcement vive en el flujo de review por-story (donde ya viven tsc/eslint/pytest).
- **Degrada advisory** si la tool no está disponible (npx offline) — no rompe ci-parity (mismo patrón que el mutation-gate v5).

## Estado de rollout (2026-06-08)

| Brand | BE+FE baselines | code-health | Nota |
|---|---|---|---|
| vitalia | ✓ | **PASS** | referencia; verificado end-to-end + negative-test (ratchet con dientes) |
| nicolify | ✓ | **PASS** | vulture 0, dup FE 2.4% |
| comunify | ✓ | **PASS** | vulture 70, dup FE 3.0% |
| lupulo | ✓ (registrado) | FAIL (docstrings <80%) | **placeholder — NO enforced** hasta bootstrap de código real |

## Deuda de seguridad — RESUELTA en la misma sesión (2026-06-08)

Los 12 CVEs que destapó pip-audit se **bumpearon de una** (`uv lock --upgrade-package`, workspace-wide — un solo lock, las 4 marcas + 26 core packages quedan igual):

| Paquete | de → a | CVEs cerrados |
|---|---|---|
| pyjwt | 2.12.1 → 2.13.0 | PYSEC-2026-175/177/178/179 (AUTH) |
| starlette | 1.0.0 → 1.2.1 | PYSEC-2026-161 |
| aiohttp | 3.13.4 → 3.14.1 | CVE-2026-34993/47265 |
| idna | 3.14 → 3.18 | CVE-2026-45409 |
| langchain-openai | 1.1.10 → 1.2.2 (+litellm 1.88, openai 2.41 transitivos) | PYSEC-2026-76 |
| **py** | — | PYSEC-2022-42969 **sin fix upstream** (deprecado) → único en allowlist |

**Companion fix (pyjwt 2.13):** pyjwt ≥2.13 valida el scheme del JWKS URI en `PyJWKClient.__init__` (antes era lazy). `core/luana-core-iam/.../auth.py` construye el client a nivel módulo; con `CLERK_ISSUER` ausente (URL vacío) crasheaba al import. Fix mecánico: agregar `jwt.exceptions.PyJWKClientError` al `except` tuple ya existente (preserva semántica `jwks_client=None`; prod con env seteado no cambia). Verificado: core-iam GREEN · vitalia `test_auth_stub_env_gate` 4/4 · import defensivo sin env.

Pendiente real (NO este gate): FE dead-code baseline alto (128 unused vitalia) → burn-down incremental (el ratchet impide que crezca).

## Tools: instalación

- BE: `vulture`, `interrogate`, `pip-audit` agregados a root dev-deps (`uv add --dev`). jscpd vía `npx` pinned.
- FE: `fallow@2.89.0` vía `npx` pinned (sin churn de lockfile per-brand; promovible a root devDeps para offline). Config: `{brand}/frontend/.fallowrc.jsonc` (template = vitalia).

## Referencias
- `scripts/quality/code-health.sh` — el runner
- `scripts/quality/baselines/` — baselines per-brand + `pip-audit-ignore.txt`
- `.claude/agents/gate-runner.md` — shortcut `code-health-<brand>` + parser
- `.claude/agents/builder-{frontend,backend}.md` — quality gate (false-green corregido)
- `.claude/rules/test-design-doctrine.md` — jscpd+arch-fitness first-class
- `docs/process/harness-backlog.md` HB-61
