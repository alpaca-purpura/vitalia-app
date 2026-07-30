# T-ESC4-result.md — qualify engine relationship target (UNILATERAL: solo crm.py)

**State:** tests-passing (GREEN). **Builder:** builder-agentic (flagship). **Date:** 2026-06-22.

## Diff summary (production code)

Single line, `core/luana-core-platform/src/luana_core_platform/infrastructure/models/crm.py` `LeadModel.messages` (~L210):

```diff
     messages = relationship(
-        "MessageModel",
+        "luana_core_sales_agent.infrastructure.models.message_model.MessageModel",
         back_populates="lead",
         cascade="all, delete-orphan",
     )
```

★ **UNILATERAL confirmed:** `message_model.py:46` (`lead = relationship("LeadModel", ...)`) NOT touched — grep confirmed `"LeadModel"` is unique (only platform defines it; vitalia defines `LeadActivityModel`/`LeadStageTransitionModel`/`ConversationModel` but no `LeadModel` homonym). `appointments`/`tenant` lines NOT touched (latent finding, out of scope).

## Test created (TDD)

- `core/luana-core-sales-agent/tests/architecture/__init__.py` (NEW, empty)
- `core/luana-core-sales-agent/tests/architecture/test_esc4_relationship_module_qualified.py` (NEW — verbatim copy from `verified-arch-tests.md`, SUBPROCESS probe for deterministic import state)

## TDD evidence

- **RED** (test created before diff): `sqlalchemy.exc.InvalidRequestError: Multiple classes found for path "MessageModel" in the registry of this declarative base. Please use a fully module-qualified path.` (returncode 1) — matches architect spike + live error.
- **GREEN** (after diff): `CONFIGURE_OK`, returncode 0.

## Validator output (literal)

```
════════ VALIDATOR: esc4_relationship_module_qualified ════════
core/luana-core-sales-agent/tests/architecture/test_esc4_relationship_module_qualified.py::test_engine_leadmodel_messages_resolves_with_brand_homonym PASSED [100%]
======================== 1 passed, 8 warnings in 2.87s =========================
```

Command (literal from 04-validators.yaml):
```
PYTHONPATH=${WS}/core/luana-core-sales-agent/src:${WS}/core/luana-core-platform/src:${WS}/core/luana-core-scheduling/src:${WS}/core/luana-core-iam/src:${WS}/core/luana-core-offer-studio/src \
  ${WS}/.venv/bin/pytest core/luana-core-sales-agent/tests/architecture/test_esc4_relationship_module_qualified.py -v -p no:cacheprovider --override-ini='addopts='
```

`platform_suite_canonical` (advisory in-worktree): EXIT=0, progress 100%, zero FAILED/ERROR lines (architect-confirmed green with ESC-4 fix).
`ruff_check`: `All checks passed!` · `ruff_format`: my edited files (crm.py) `already formatted`.

## Skills consulted

- **sales-agent-expert** — invoked per `must_load_skills`. §3 "NO se toca" reviewed: `crm.py` `LeadModel.messages` is NOT in §3 protected list (`PromptVersionModel`, `model_pricing_snapshot`, `closer_studio`, etc. are; data-layer relationship target is not). Anti-pattern check: this is a late-bound string target (no Python import) → no cross-module import cycle, no §3 violation. Decided: apply the one-line qualifier as the engine declaring its explicit target (cohesion↑, no new coupling).
- **backend-expert** (via guidelines) — SQLAlchemy 2.0 relationship module-qualified path pattern for shared-`Base` homonym disambiguation. Confirmed: fully-qualified string target is the canonical SQLAlchemy fix for "Multiple classes found for path".
- **.claude/rules/tdd-mandatory.md** — RED (InvalidRequestError) before GREEN. Test reproduces the live mapper-init bug first.
- **.claude/rules/anti-duplication.md** — fix lives in the ENGINE (`core/luana-core-platform`), zero cross-brand mirror. No new abstraction; existing relationship disambiguated in place.
- **.claude/rules/auditor-downstream-regression.md** — engine shared by 4 brands; in-worktree gate = ESC-4 subprocess arch test (with synthetic homonym, reproduces the live break). Full downstream ×4 = canonical post-merge (`make ci-parity` + Postgres), documented in 04-validators `downstream_ci_parity`.

## Out-of-scope flagged (NOT fixed)

- `LeadModel.appointments` (crm.py:214) — same latent ambiguity class as ESC-4; safe in prod today (vitalia has no `AppointmentModel` homonym). Address in Story 8 lift. (03-arch § Latent finding.)
