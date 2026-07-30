# T-inbox-agentic-1 — Result

> Story: vitalia-slice-1-inbox · Brand: vitalia · Ticket: T-inbox-agentic-1
> Surface: agentic · production_code: true · Builder: Claude Opus 4.7 (R23 mandatory)
> State: tests-passing → handoff /auditor for verdict (per story-closure-gate.md)
> Completed: 2026-05-20 UTC

## Summary (1-3 sentences)

Created `retract_last_message` Adrián sales_agent tool wrapping the already-shipped
`RetractMessageService` (T-inbox-be-3) — Adrián can autonomously revert its own
last sent message within the 5-minute action-receipt window when ComplianceService
flags a post-send violation or self-detected misalignment. Added 12 unit tests
(happy + 5 edges + adversarial + 4 schema gates + 1 surface metadata) and
1 reinforcement dental golden (`T-inbox-retract-1.yaml`) covering voice fidelity
+ tool trajectory + compliance integration. All validators GREEN, no engine
modification, no cross-brand mirror.

## Skills consulted (must_load enforcement v4.1)

13 skills declared in caller prompt + all 13 invoked + decisions captured in
`T-inbox-agentic-1-impl-log.md § Step 0`. Verbatim list:

1. `sales-agent-expert` — followed canonical 3-tool pattern (screening/payment/reschedule)
2. `copilot-expert` — anti-duplication §0 verified; tool registration deferred to T-inbox-be-6
3. `tessl__langgraph` — `@tool` decorator + Pydantic v2 args_schema + async coroutine
4. `claude-api` — cache prefix invariance preserved (no timestamps/IDs in description)
5. `tessl__graceful-degradation` — tool NEVER raises; 6 deterministic Spanish summary returns
6. `.claude/rules/copilot-resilience.md` — best-effort observability; no PII in logs
7. `.claude/rules/copilot-observability.md` — engine `SalesAgentObservabilityContext` consumed (NEVER mirror)
8. `.claude/rules/sales-agent-brand-voice.md` — Spanish neutro tool returns; agent voice exempt downstream
9. `.claude/rules/anti-duplication.md` — cross-codebase grep clean; NO engine equivalent; NO cross-brand mirror
10. `.claude/rules/tenant-isolation.md` — tenant_id + clinic_id MANDATORY in input schema
11. `vitalia/.claude/rules/hipaa-lite.md` — 4 PHI obligations honored (dual filter + audit + sanitize + encryption)
12. `.claude/rules/tdd-mandatory.md` — RED → GREEN cycle (ModuleNotFoundError → 12/12 PASS)
13. `.claude/rules/auditor-self-fix-policy.md` — count gate bump 12→13 within whitelist #9

Each skill's decision captured verbatim in IMPL-LOG.md § Step 0 table.

## Files delivered (3 in-scope + 3 scaffold/cement-update)

| # | File | Type | LOC | Purpose |
|---|---|---|---|---|
| 1 | `vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py` | NEW | 207 | Tool surface (R23 Opus production) — `@tool` decorated async function delegating to RetractMessageService |
| 2 | `vitalia/backend/tests/modules/vitalia/sales_agent/tools/test_retract_last_message.py` | NEW | 295 | 12 unit tests (TDD RED first) covering happy + 5 edges + adversarial + 4 schema gates + 1 surface metadata |
| 3 | `vitalia/backend/tests/agentic_evals/sales_agent/goldens/dental/T-inbox-retract-1.yaml` | NEW | 90 | Reinforcement dental golden — Adrián price-correction with retract within 5min window |
| 4 | `vitalia/backend/tests/modules/vitalia/sales_agent/__init__.py` | NEW (trivial) | 0 | pytest test-discovery scaffold (project pattern) |
| 5 | `vitalia/backend/tests/modules/vitalia/sales_agent/tools/__init__.py` | NEW (trivial) | 0 | pytest test-discovery scaffold (project pattern) |
| 6 | `vitalia/backend/tests/agentic_evals/sales_agent/test_pass_k_evaluation.py` | EDIT (4 lines) | n/a | Count gate cement bump 12 → 13 goldens (auditor whitelist self-fix #9) |

**Total Python LOC NEW:** ~502 + golden YAML 90 + cement edit 4 = ~596 lines.
Spec estimate ~350. Overhead +70% justified by:
- 12 unit tests (vs estimate likely 5-7) covering all 6 exception paths exhaustively
- Comprehensive docstrings (auditor-readable, references all relevant rules)
- Schema gates for Pydantic v2 ConfigDict invariants (extra=forbid + length bounds)

## Gherkin verification matrix (Phase D for auditor)

| Scenario (from 06-tickets.yaml::gherkin_coverage) | Test path | Status |
|---|---|---|
| SC-01 happy — Adrián retract action receipt within 5min | `test_retract_last_message.py::test_happy_5min_window` | ✅ PASS |
| SC-03 edge — 5min expired | `test_retract_last_message.py::test_expired` | ✅ PASS |
| SC-03 edge — patient replied | `test_retract_last_message.py::test_patient_replied` | ✅ PASS |
| SC-03 edge — channel unsupported (email) | `test_retract_last_message.py::test_channel_unsupported` | ✅ PASS |
| Voice fidelity + compliance integration | `goldens/dental/T-inbox-retract-1.yaml` (executed via `test_pass_k_evaluation.py`) | ✅ PASS (3 trials, deterministic synthetic grader) |

All 5 gherkin scenarios have executable tests passing.

## Validators run (per 04-validators.yaml::T-inbox-agentic-1::acceptance.validator_ids)

```
be_lint_ruff_check                 → ✅ All checks passed!
be_format_ruff_check               → ✅ 42 files already formatted
be_arch_fitness_brand              → ✅ 265 passed (incl. test_no_observability_mirror_copilot)
be_test_inbox                      → ✅ 59 passed (47 pre-existing + 12 new)
agentic_pass_k_adrian_goldens      → ✅ 11 passed (3 trials × pass^k + count + schema + persona refs)
agentic_voice_fidelity_adrian      → ✅ 9 passed
```

Additional validators (defense-in-depth, beyond ticket's acceptance set):
```
full agentic_evals/sales_agent     → ✅ 43 passed (pass^k + voice fidelity + medical guardrails)
spanish_neutro_voseo_check         → ✅ 0 voseo in tool source (Spanish neutro)
anti_duplication_cross_brand_mirror_scan → ✅ no mirror cross nicolify/comunify/lupulo
```

## Architecture cleanliness

| Concern | Status | Evidence |
|---|---|---|
| Cross-brand pollution | ✅ ZERO | Only `vitalia/` paths touched; cross-brand grep clean |
| Engine modification | ✅ ZERO | engine paths only READ; no `core/luana-core-*/src/` writes |
| Anti-duplication §0 | ✅ CLEAN | Tool consumes `RetractMessageService` (T-inbox-be-3) which transitively consumes engine adapters. NO mirror of observability/cost/pricing/turn_envelope/callback_handler |
| Tenant isolation | ✅ ENFORCED | `tenant_id` + `clinic_id` MANDATORY in Pydantic v2 input schema; service dual-filter inherited from `CompoundScopeRepositoryBase` |
| HIPAA-lite (vitalia overlay) | ✅ 4/4 obligations | Dual filter + audit log sync write (service) + sanitize_payload (engine) + encryption (transport) |
| Voice fidelity ≥0.85 (Adrián) | ✅ PRESERVED | Tool returns Spanish neutro (system observations); agent's post-tool response (golden YAML) preserves Aurora-dental-AR voseo voice |
| Cache slot architecture | ✅ INVARIANT | Tool description uses Pydantic Field descriptions (resolved at registration); NO timestamps/conv_id/tenant_name in description |
| Graceful degradation | ✅ ENFORCED | Tool NEVER raises; 6 deterministic Spanish summaries cover all exception paths |
| Tests TDD (RED before GREEN) | ✅ CONFIRMED | Initial pytest run showed `ModuleNotFoundError`; after impl 12/12 PASS |

## Downstream handoff

- **T-inbox-be-6** (already declared `blocked_by: [T-inbox-agentic-1]` in 06-tickets.yaml):
  Registers this tool via `registry.sales_agent_tool_register(ToolDef(...))` in
  `vitalia/backend/src/modules/vitalia/extensions.py`. Pattern verbatim from
  3 sibling tools cementadas at lines 469-571.

- **DI resolver bootstrap** (part of T-inbox-be-6): call
  `set_retract_message_service_resolver(...)` at engine sales_agent runtime
  orchestrator init. Pattern verbatim from `set_payment_link_service_resolver`.

- **Auditor (auto-handoff)** — per story-closure-gate.md Fase B AUDIT, this
  ticket completion triggers `/auditor` spawn on next story-level cycle.
  Audit categories: C1 Code (DDD layers, async-first, Pydantic v2) · C2 Spec
  (gherkin matrix above) · C3 Architecture (fitness gates 265/265, no mirrors,
  no engine edits) · C4 Cross-cutting (HIPAA-lite, tenant isolation, voice
  fidelity) · C5 Trace (this result.md + impl-log.md).

## Process metrics

- **Native pytest run time:** 0.19s (12 tool tests) + 0.79s (43 agentic evals) + 2.85s (265 arch tests)
- **R23 compliance:** Opus 4.7 used (production_code=true mandatory)
- **Skills declared vs invoked:** 13/13 (must_load v4.1 enforcement)
- **TDD discipline:** RED confirmed; GREEN verified; REFACTOR via ruff format only
- **Self-fix usage:** 1 instance (count gate bump 12→13), within whitelist #9, scope strictly contained (4 lines, 1 file)

## Last line (per anti-telephone-game)

done -> vitalia/docs/product/stories/vitalia-slice-1-inbox/T-inbox-agentic-1-result.md
