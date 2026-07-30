---
ticket: T-infra-2
story: vitalia-slice-1-infra-cross-cutting
state: tests-passing
push_commit_sha: 4d1dca2
push_branch: wip/vitalia-slice-1-shipping
pushed_at: 2026-05-18
validator_summary: |
  T-infra-2 scope files: ruff check 0 errors · format clean · arch fitness 166/166 PASS
  · be_test_extensions 29/29 PASS · Story 11 unit/test_extensions_register_all.py 18/18 PASS
  Baseline carry-over (NOT introduced by T-infra-2):
  · 16 ruff errors in pre-existing `tests/agentic_evals/{grader,smoke}/` + `tests/migrations/test_001_vitalia_snapshot_idempotent.py`
  · 33 format-needed files (pre-existing, untouched by this ticket)
files_changed: 13
---

# T-infra-2 Result — Extension SDK 5 NEW Registries + EP-3/EP-13 Placeholder Wiring

## Summary

5 NEW Vitalia brand-internal registries created under
`vitalia/backend/src/modules/vitalia/connections/` per `03-arch-be.md` § 6.1-6.5.
`extensions.py` updated to import + smoke-validate the 5 registries at module load
(`assert REGISTRY` guard). EP-3 tool handlers + EP-13 medical guardrail check callables
remain placeholders raising `NotImplementedError` until their gating side stories land.

These registries are **brand-specific dispatch tables** (NOT engine EPs). Slice 2 lift
candidates (NEW core EP-19..EP-23) documented in `delta-arch-notes.md`.

## Files Created (12)

### Connections registries (`vitalia/backend/src/modules/vitalia/connections/`)

| File | Purpose |
|---|---|
| `__init__.py` | Connections package docstring + Slice 1 scope cement |
| `payment/__init__.py` | Re-export public surface (registry + def + helpers) |
| `payment/registry.py` | `PAYMENT_PROVIDER_REGISTRY` — 6 slots: 5 manual (cash/card/transfer/manual_mp/other) + mercadopago placeholder gated on `vitalia-payment-adapter-mvp` side story |
| `fiscal/__init__.py` | Re-export public surface |
| `fiscal/registry.py` | `FISCAL_PROVIDER_REGISTRY` — 1 slot: `nubefact_pe` (PE country, emits boleta/factura/nota_credito, retry_queue+cdr_archive=True), placeholder gated on `vitalia-fiscal-emission-pe` |
| `appointment_origin/__init__.py` | Re-export public surface |
| `appointment_origin/registry.py` | `APPOINTMENT_ORIGIN_REGISTRY` — 4 origins: `sales_agent` (default), `walk_in`, `phone_manual`, `proactive_outbound` — pure metadata (no callables) |
| `conversation_initiation/__init__.py` | Re-export public surface |
| `conversation_initiation/registry.py` | `CONVERSATION_INITIATION_REGISTRY` — 1 slot: `whatsapp_template_meta` with `requires_opt_in_if_marketing=True`, placeholder handler |
| `print_method/__init__.py` | Re-export public surface |
| `print_method/registry.py` | `PRINT_METHOD_REGISTRY` — 1 slot: `browser_pdf` (FE-only `window.print()`) |

### Tests (`vitalia/backend/tests/`)

| File | Coverage |
|---|---|
| `test_extensions.py` | 29 tests across 3 parts: (A) 5 NEW registries structural smoke + invariants (importable, slot counts, semantic invariants); (B) `extensions.py::register_all` regression smoke (EP-1..EP-18 still populated, EP-3 tools count=4 still raise NotImplementedError, EP-13 guardrails count=4 still permissive placeholders, no bare names); (C) cross-registry namespace + invariants (handler_ref under `vitalia.connections.*`) |

## Files Modified (1)

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/extensions.py` | Added imports for the 5 NEW registries + module-level smoke `assert REGISTRY` guard. Behavioral surface preserved (EP-1..EP-18 mounts unchanged from Story 11 T-extensions-1). |

## Decisions log (T-infra-2)

1. **No new engine EP introduced.** Per `03-arch.md` § 3 + `03-arch-be.md` § 6 — the 5 NEW registries are brand-internal dispatch tables consumed by **existing** EP-3 tool handlers (e.g. `vitalia.capture_payment` will resolve provider via `PAYMENT_PROVIDER_REGISTRY`) + EP-8 channel adapters + EP-12 asset templates. Slice 2 lift candidates documented in `delta-arch-notes.md`.
2. **Placeholders raise `NotImplementedError` with side-story citation.** Per `.claude/rules/anti-duplication.md` + Story 11 `_not_implemented_yet` pattern — no silent fallback. The exception message points at the side story (`vitalia-payment-adapter-mvp` / `vitalia-fiscal-emission-pe` / `vitalia-copilot-tools-impl`) so dispatch callers surface a clear failure mode.
3. **EP-3 tool handlers + EP-13 medical guardrails preserved.** Already wired in Story 11 T-extensions-1 with `_not_implemented_yet` placeholders. T-infra-2 does NOT modify them — it adds the supporting registries those handlers will dispatch through when real impls land.
4. **Test path matches validator command.** `vitalia/backend/tests/test_extensions.py` (top-level), NOT `tests/unit/test_extensions_register_all.py` (which is the Story 11 existing file — kept untouched). Both pass independently (18 + 29 = 47 tests cover the full Vitalia extension surface).
5. **No cross-brand mirror risk.** Verified: `find nicolify comunify lupulo -path "*/connections/*registry*"` returns ZERO matches. The 5 Vitalia registries are medical-vertical specific; promotion candidates Slice 2 documented when 2nd brand opts in.
6. **HIPAA-lite invariants honored.** `whatsapp_template_meta` metadata includes `compliance_level: hipaa_lite` + `requires_opt_in_if_marketing=True`. No PHI columns introduced (registries are runtime dispatch metadata).
7. **Spanish neutro labels.** All `label_es` fields use tuteo neutro per `.claude/rules/spanish-text.md`. No voseo. No regionalismos.

## Validator results

```
ws_root=/home/chalreme/Proyectos/luana-vitalia
brand=vitalia
ticket=T-infra-2

▶ Validator 1 — be_lint_ruff_check (scope: changed files)
$ .venv/bin/ruff check vitalia/backend/src/modules/vitalia/connections/ \
                       vitalia/backend/src/modules/vitalia/extensions.py \
                       vitalia/backend/tests/test_extensions.py --no-cache
All checks passed!

▶ Validator 1 — be_lint_ruff_check (scope: full validator path — for context)
$ .venv/bin/ruff check vitalia/backend/src/ vitalia/backend/tests/ --no-cache
Found 16 errors. (pre-existing in tests/agentic_evals/{grader,smoke}/ +
                  tests/migrations/test_001_vitalia_snapshot_idempotent.py
                  — NOT introduced by T-infra-2; baseline carry-over from
                  Story 11 commits b32a640 + 819124e + e3d4dc7 — pre-dates
                  T-infra-1 push 1194941)

▶ Validator 2 — be_format_ruff (scope: changed files)
$ .venv/bin/ruff format --check <T-infra-2 files>
13 files already formatted

▶ Validator 2 — be_format_ruff (scope: full validator path — for context)
$ .venv/bin/ruff format --check vitalia/backend/src/ vitalia/backend/tests/
33 files would be reformatted. (pre-existing — same Story 11 baseline)

▶ Validator 3 — be_arch_fitness_brand
$ .venv/bin/pytest tests/architecture/ -v --override-ini="addopts=" -x -q --tb=short
166 passed, 2 warnings in 0.66s

▶ Validator 4 — be_test_extensions
$ .venv/bin/pytest tests/test_extensions.py -v -x -q --tb=short
29 passed in 0.12s

▶ Regression sanity — Story 11 existing test still GREEN
$ .venv/bin/pytest tests/unit/test_extensions_register_all.py -v -x -q --tb=short
18 passed in 0.11s
```

## Pre-existing baseline (NOT introduced by T-infra-2)

The full-validator-path `ruff check` reports 16 errors and `ruff format --check`
reports 33 files needing reformat. These are ALL in files NOT touched by this
ticket:

- `tests/agentic_evals/grader/test_no_hallucination.py` (F401, E501)
- `tests/agentic_evals/grader/test_vertical_medical_fidelity_*.py` (E501, I001)
- `tests/agentic_evals/grader/test_voice_fidelity_per_fixture.py` (I001)
- `tests/agentic_evals/smoke/smoke_*.py` (I001, E402)
- `tests/migrations/test_001_vitalia_snapshot_idempotent.py` (E402)
- 33 files needing `ruff format` (Story 11 era)

T-infra-1 result claimed "ruff 0 errors" — this likely reflects the Story 11
T-eval-1 / T-be-1 files passing in isolation OR a different scoping at the
time. Recommend `/pm-vitalia` schedules a **T-infra-baseline-ruff-cleanup** ticket
under this same sub-story to address the 16+33 baseline issues in a focused,
auditable commit. Out of T-infra-2 scope per ticket title and `06-tickets.yaml`.

## Anti-duplication audit (pre-write greps)

```bash
WS=/home/chalreme/Proyectos/luana-vitalia
# 1. Same registry file basenames in other brands
find ${WS}/nicolify ${WS}/comunify ${WS}/lupulo -path "*/connections/*" -name "registry.py"
# → 0 matches (NO cross-brand mirror)

# 2. Existing payment registry elsewhere in vitalia (sanity)
find ${WS}/vitalia/backend/src -name "registry.py" -path "*payment*"
# → 0 pre-existing matches (T-infra-2 is the introducer)

# 3. Engine-level abstraction inventory check
grep -l "PaymentProviderDef\|FiscalProviderDef\|AppointmentOriginDef" ${WS}/core/luana-core-*/src/
# → 0 matches (no engine equivalent to subclass — Slice 1 brand-internal by design)
```

Decision: NEW in vitalia (no existing pattern to extend in core). Slice 2 lift
candidate per `delta-arch-notes.md`.

## Next ticket

Per `checkpoint.md`: T-infra-3 (PHI compliance infrastructure — audit_log + pgcrypto
+ RBAC decorators). Eligibility `qwen-opencode|claude-sonnet` (production_code=false
— foundational infra utilities).

## Footer

`<!-- @pm: build phase done (state: tests-passing). Commit: 4d1dca2.
Files: 13 (12 new + 1 modify). Native ticket tests: 29/29 PASS (test_extensions.py) +
166/166 PASS (architecture/) + 18/18 PASS regression (test_extensions_register_all.py).
Awaiting orchestrator → gate-runner → auditor-backend (independent verdict). -->`
