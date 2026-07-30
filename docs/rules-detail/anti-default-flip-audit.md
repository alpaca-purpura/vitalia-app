# Anti-Default-Flip Audit

**Origen:** failed `/pase-produccion` 2026-05-04. Commit `64738354` (PR-1 Sub-E PI-2, 2026-04-29) flipeó `USE_OUTBOX_PATTERN_*` False→True sin auditar tests que mockean path legacy `EventBus.publish` → 25 BE failures + 1 polluter no identificable + ~3h investigación + ~500k tokens. Ver PI-11 PR.md.

## Regla cardinal

ANTES de flipear default de feature flag (`USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, `ENABLE_*`, etc.) que cambia call path side-effect (events, persistence, logging, observability, LLM provider routing, agent orchestration) → **OBLIGATORIO 4 STEPS**:

### Step 1 — Grep tests path viejo (cross-codebase)

WS=`$(git rev-parse --show-toplevel)` (root del workspace `luana-platform/`).

```bash
# Para cada call path afectado por el flip, grep mocks legacy en CORE + TODAS las brands activas:
grep -rn "<legacy_call_path>" \
  ${WS}/core/luana-core-*/tests/ \
  ${WS}/{nicolify,vitalia,comunify,lupulo}/backend/tests/ \
  2>/dev/null | grep -v __pycache__

# Ejemplo flag USE_OUTBOX_PATTERN_*:
grep -rln "luana_core_events.EventBus.publish" \
  ${WS}/core/luana-core-*/tests/ \
  ${WS}/{nicolify,vitalia,comunify,lupulo}/backend/tests/

# Ejemplo provider direct adapter (legacy histórico):
grep -rln "OpenAIService\|KimiService\|DeepSeekService" \
  ${WS}/core/luana-core-*/tests/ \
  ${WS}/{nicolify,vitalia,comunify,lupulo}/backend/tests/
```

Output capture obligatorio en commit body sección `## Tests audited`.

### Step 2 — Update mocks path nuevo

Para cada test detectado:
- Migrar mocks al `<new_canonical_path>` (e.g., `adapter_bus.publish` for outbox)
- O capturar via observability/persistence sink (outbox table, traces, etc.)
- O bypass explícito si test prueba capability legacy mismo (magic comment `# arch-bypass: testing legacy capability`)

### Step 3 — Run full suite con BOTH old+new flag values

Si el flag vive en `core/luana-core-*/` → correr suite del core package AFFECTED + suite de cada brand consumer activa.
Si el flag vive en `{brand}/backend/` (override per-brand) → correr suite de esa brand + arch tests.

```bash
WS=$(git rev-parse --show-toplevel)

# Core package affected (ejemplo: outbox vive en luana-core-events):
cd ${WS}/core/luana-core-events && ${WS}/.venv/bin/pytest -x -q --tb=short
USE_OUTBOX_PATTERN_DEFAULT=false ${WS}/.venv/bin/pytest -x -q --tb=short

# Cada brand consumer activa (post-flip default + pre-flip legacy):
for B in nicolify vitalia comunify lupulo; do
  cd ${WS}/${B}/backend && ${WS}/.venv/bin/pytest -x -q --tb=short
  USE_OUTBOX_PATTERN_DEFAULT=false ${WS}/.venv/bin/pytest -x -q --tb=short
done
```

Ambos valores deben pasar 100% en core + todas las brands consumer. Si UNO falla → stop, no flip until fix.

### Step 4 — Documentar commit body

Bloque obligatorio en commit body cuando aplique flip:
```
flag <NAME> flipped <OLD_VALUE>→<NEW_VALUE>

## Tests audited
- N tests migrated to new canonical path
- M tests use bypass for legacy capability (magic comment)
- 0 tests use `monkeypatch.setattr(<flag>=<old_value>)` band-aid

## Path old: <full_path>
## Path new: <full_path>
## Verification: pytest passed both values (logs attached)
```

## Inventario flags side-effect (SSoT — actualizar al agregar nuevos)

| Flag | Default actual | Side-effect path | Path viejo | Path nuevo | Tests probe canonical |
|---|---|---|---|---|---|
| `USE_OUTBOX_PATTERN_SALES_AGENT` | `True` (post 2026-04-29) | events emission | `luana_core_events.EventBus.publish` | `luana_core_events.outbox.adapter_bus.publish` (→ outbox table) | adapter_bus mock OR `select(DomainEventOutboxModel)...` |
| `USE_OUTBOX_PATTERN_COPILOT` | `True` (post 2026-04-29) | events emission | idem | idem | idem |
| `USE_OUTBOX_PATTERN_BRAND` | `True` (post 2026-04-29) | events emission | idem | idem | idem |
| `USE_OUTBOX_PATTERN_DEFAULT` | `False` | events emission (fallback per-module unspecified) | idem | idem | idem |
| `USE_DEEPAGENTS_*` (futuros) | TBD | agent orchestration | LangGraph plain `StateGraph.compile()` | deepagents `task` subagent harness | both paths probed (per-test or fixture parametrize) |
| Otros `ENABLE_*` flags | varies | varies | varies | varies | varies |

> Note: `LITELLM_PROXY_ENABLED` row removed PI-12 S1 sales-agent-litellm-canonicalization T-5
> (legacy adapters deleted T-4). The LiteLLM Proxy is now the only runtime LLM dispatch path —
> there is no fallback toggle to audit.

**Cuando agregar nuevo flag side-effect → editar este inventario en mismo commit.** Auditor Cat 14/13 valida.

## Anti-patterns prohibidos

- ❌ Flipear default sin grep tests path viejo (Step 1 omitido)
- ❌ Flipear default sin run full suite con ambos valores (Step 3 omitido)
- ❌ Commit body sin sección "Tests audited" (Step 4 omitido)
- ❌ Mockear path viejo cuando flag default es path nuevo (test no prueba nada real — passes silenciosamente)
- ❌ Usar `monkeypatch.setattr(USE_*=False)` por test sin migrar mock al path nuevo — band-aid temporal solo (D2 PI-11)
- ❌ Bypass arch fitness sin magic comment justificado
- ❌ Agregar nuevo flag side-effect sin actualizar inventario SSoT este file

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 PM PR.md | Bloque "Default flips audited" mandatory cuando aplique flip | `/pm-{brand}` o `/pm-luana` (si flag vive en core) |
| 2 Architect CONTRACT.md | Bloque "Tests audit: paths mockeados antes/después" obligatorio si CONTRACT propone flip | `/architect` |
| 3 Builder Step 0 | Grep tests path viejo antes flip code cross-core + brands | `/dev-team` (builder-{backend,agentic}) |
| 4 Auditor Cat review | Cat 14 (business) / Cat 13 (agentic) "Default flip side-effect coverage" | `/auditor` (auditor-{backend,agentic}) |
| 5 Arch fitness test | `test_no_legacy_eventbus_mock_when_outbox_on.py` (PR-3) bloquea automatic | `core/luana-core-*/tests/architecture/` + `{brand}/backend/tests/architecture/` |
| 6 TDD rule | `.claude/rules/tdd-mandatory.md` § "Default flag flips" obligatoria | `/pm-luana` / `/pm-{brand}` |
| 7 Runtime warning | `LegacyEventBus.publish` DeprecationWarning cuando flag True (PR-1 § 5) | `core/luana-core-events/src/luana_core_events/__init__.py` |

> Pattern análogo: `anti-duplication.md` (cross-module mirror detection). Anti-default-flip
> detecta side-effect path mismatch via flag flip + test-mock drift. Ambos defense in depth
> (PM PR.md → Architect CONTRACT.md → Builder Step 0 → Auditor Cat review → Arch fitness test).

## Penalizaciones

- Builder skip Step 1 grep → REVERT
- Auditor skip Cat 14/13 → re-audit
- Architect CONTRACT sin "Tests audit" cuando propone flip → REJECT, re-spawn
- Arch fitness violation = build fail (gate hard)
- Skip inventario update al agregar nuevo flag → process-learnings.md case study

## Ejemplos

### Ejemplo CORRECTO (commit hipotético):

```
feat(observability): flip LITELLM_PROXY_ENABLED default False→True

## Tests audited
- 12 tests migrated from `OpenAIService.generate_response` mock → `LiteLLMService.generate_response` mock
- 2 tests use `# arch-bypass: testing legacy capability` for adapter direct call validation
- 0 tests use `monkeypatch.setattr(LITELLM_PROXY_ENABLED=False)` band-aid

## Path old: core/luana-core-llm/src/luana_core_llm/providers/{openai,kimi,...}.py direct
## Path new: core/luana-core-llm/src/luana_core_llm/providers/litellm.py via proxy
## Verification:
- core suite + all brand consumer suites PASS (default True)
- `LITELLM_PROXY_ENABLED=false` PASS en core + todas las brands (legacy fallback)

[arch-fitness core+brands PASS]
```

### Ejemplo INCORRECTO (lo que rompió 2026-05-04):

```
feat(events): switch emisores to outbox event bus adapter

# Sin sección "Tests audited"
# Sin grep tests path viejo
# Sin verify both flag values
# → 25 tests stale post-merge, polluter no detectado, 3h investigación
```

## Multibrand awareness (post reorg 2026-05-15)

- Flag default flip en `core/luana-core-*/` (engine) → impacto cross-brand. Auditar suites de **todas** las brands consumer activas (nicolify, vitalia, comunify, lupulo) además del core package.
- Flag override per-brand en `{brand}/config/brand.yaml` o `{brand}/backend/src/.../config.py` → audit scope = sólo esa brand + arch tests.
- Promotion gate: flip que afecta `core/` requiere `/pm-luana` ratification antes merge (ver `docs/promotion-protocol/README.md`).
- Brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow) deben revalidar este inventario al opt-in al engine package afectado.
