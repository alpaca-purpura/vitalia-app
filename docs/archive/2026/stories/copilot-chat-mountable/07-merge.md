<!-- voseo-allowed: merge artifact interno -->
---
story_id: copilot-chat-mountable
brand: platform
release: null                          # platform technical-story (engine fix, sin release de marca)
merged_at: 2026-06-16
merged_by: /pm-luana
commit_squash_sha: e9f16d06            # squash-merge wip/core-copilot-mountable → main
checkpoints_path: "./CHECKPOINTS.md"
story_type: technical-story
verification_nature: técnica
demo_required: false
---

# 07-merge — copilot-chat-mountable (platform technical-story · engine fix)

> Owner: `/pm-luana` (es core/engine, no PM de marca). Escrito tras `/auditor` CHECKPOINTS.md **APPROVED**.
> Naturaleza **técnica** → §§ Gherkin/Playwright/capabilities/modules **NO aplican** (excepción documentada: technical-story sin UI ni cap user-facing — `cap_change_type: fix`, `cap_target: null`). La verificación es **por-efecto** (driver import + R3).

## § 1 — Verificación técnica (validators · reemplaza Gherkin matrix)

| Validator | Qué prueba | Status |
|---|---|---|
| `v_no_eager_module_settings` (`test_lazy_settings_no_eager`, 6) | importar config.py + database.py NO instancia Settings/engine/redis a module-load (T-1) | ✅ PASS |
| `v_chat_import_multibrand_env` (`test_chat_import_multibrand_env`, subprocess) | **acceptance:** `import luana_core_copilot.api.chat` con env multibrand-only NO levanta ValidationError (T-2) | ✅ PASS |
| `be_platform_unit` | suite platform (290) | ✅ PASS |
| `be_copilot_unit` | suite copilot (1641 / 25 skip) | ✅ PASS |
| `be_iam_unit` (regression must_stay_green) | suite iam | ✅ PASS |
| events (76) · assets (58) | paquetes tocados | ✅ PASS |
| ruff (copilot/platform/events/assets) | lint + format | ✅ PASS |
| `v_changelog_bumped` + pyproject | platform 0.5.0 · copilot 0.3.0 + CHANGELOG | ✅ PASS |
| `v_4brands_boot` (R3-light) | vitalia/nicolify/comunify importan `src.main` con env multibrand · lupulo placeholder | ✅ PASS |

**Deferidos (T-4/T-5, ratificados Chris G · reconciliados a `must_pass:false` en 04-validators):** `v_no_global_settings_import` (end-state C, 49 off-path vía shim), `be_all_touched_pkgs_*` (T-4), `v_chat_401_200` + `be_downstream_4brands_arch` (T-5, /chat 401/200 mounted = verificado al re-montar en comunify). Ver `04-validators.yaml § Scope reconciliation` + `FOLLOWUP-T4-complete-C.md`.

**Coverage:** scope unblock (T-1/T-2/T-3) 100% verde. 0 NO_COVERAGE en scope. 0 FAIL.

## § 2 — Playwright E2E run

N/A — story sin UI (engine refactor). `gherkin_coverage_note: "technical-story platform, sin E2E targeted"`.

## § 3 — Capabilities updated/created

Ninguna. `cap_change_type: fix` · `cap_target: null` — corrige comportamiento del engine (import-time eager Settings), no crea/modifica cap user-facing. El contrato del router brand-mountable se documenta en `docs/core-modules/copilot.md` (no en un cap YAML).

## § 4 — Modules MD refreshed

Ninguno (no toca módulos de marca). Doc de engine actualizado: `docs/core-modules/copilot.md` (NEW — contrato `/chat` brand-mountable).

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)   # worktree core
cd ${WS} && uv sync                    # venv propio del worktree

# 1. Acceptance (el unblock) — driver subprocess, env multibrand-only
cd ${WS}/core/luana-core-copilot && ${WS}/.venv/bin/pytest tests/test_chat_import_multibrand_env.py -q

# 2. Invariante T-1 — no eager module-load
cd ${WS}/core/luana-core-platform && ${WS}/.venv/bin/pytest tests/test_lazy_settings_no_eager.py -q

# 3. Suites de paquetes tocados
cd ${WS}/core/luana-core-copilot  && ${WS}/.venv/bin/pytest -q -p no:warnings   # 1641
cd ${WS}/core/luana-core-platform && ${WS}/.venv/bin/pytest -q -p no:warnings   # 290
cd ${WS}/core/luana-core-events   && ${WS}/.venv/bin/pytest -q -p no:warnings -o addopts=""   # 76
cd ${WS}/core/luana-core-assets   && ${WS}/.venv/bin/pytest -q -p no:warnings   # 58

# 4. R3 — las 4 marcas importan limpio con env multibrand
for b in vitalia nicolify comunify lupulo; do
  [ -f $b/backend/src/main.py ] && (cd ${WS}/$b/backend && ${WS}/.venv/bin/python -c "import sys; sys.path.insert(0,'src'); import main") && echo "$b OK"
done   # lupulo = placeholder

# 5. Lint
cd ${WS} && ${WS}/.venv/bin/ruff check core/luana-core-{copilot,platform,events,assets}
```

**Expected:** exit 0. Fallo post-merge → regression, hot-fix ticket (`.claude/rules/hotfix-repro-mandatory.md`).

## § 6 — DoD (técnica · verificación-por-efecto, NO live UI)

`verification_nature: técnica` + `demo_required: false` → la DoD NO es live-verify Chrome (no hay UI/endpoint user-facing nuevo). El equivalente de "ejercer la acción real" es el **driver subprocess** (importar `chat.py` con env multibrand-only, cold-start real en intérprete fresco) + **R3 import** de las marcas — **ejercidos por el auditor**, no auto-reportados.

```yaml
dod_live_verified: true
dod_env: "verificación-por-efecto: driver subprocess (intérprete fresco, env multibrand-only) + R3 import 4 marcas — sin UI/live-app (técnica)"
dod_evidence:
  - action: "import luana_core_copilot.api.chat en subprocess con env multibrand-only (sin POSTGRES_*/WHATSAPP_*/QDRANT_URL)"
    observed: "returncode 0 · sin pydantic ValidationError · driver GREEN (test_chat_import_multibrand_env)"
    backend_log: "n/a (import-time refactor; el efecto es 'no crash en import' + Settings NO instanciado a module-load — test_lazy_settings_no_eager GREEN)"
  - action: "import src.main de vitalia/nicolify/comunify con env multibrand (R3)"
    observed: "los 3 importan limpio (lupulo placeholder sin src/main.py)"
    backend_log: "n/a (cold import; sin ValidationError)"
dod_verified_at: 2026-06-16
```

## Story → archive

- `docs/product/stories/copilot-chat-mountable/` → `docs/archive/2026/stories/copilot-chat-mountable/` (`git mv`, MISMO commit del merge — R2).

## Handoffs post-merge (NO en esta sesión)

1. **Proposal `migrated`:** `2026-06-16-copilot-chat-brand-mountable.md` vive en `wip/comunify` (no en este worktree) → la sesión `/pm-comunify` que re-monte el `/chat` la marca `accepted → migrated` al integrar.
2. **comunify-shell-organism T-agentic v2** (`/pm-comunify`, sesión aparte): re-montar `/chat` del engine (quitar guard try/except → endpoint deja de ser 404).
3. **T-4 follow-up** (`/pm-luana` cuando convenga): completar approach C + retirar shim. Scope en `FOLLOWUP-T4-complete-C.md`. NO tocar acá.

## Cross-references

- `00-contract-spec.md` · `03-arch.md` · `04-validators.yaml` (reconciliado) · `CHECKPOINTS.md` (APPROVED) · `docs/core-modules/copilot.md` (contrato router) · `.claude/rules/story-closure-gate.md`
