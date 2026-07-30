<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — platform-lift-sales-agent-graph-runtime (Phase 1: ESC-4/5/6 + T-DEBT1)

> Auditor: `auditor-agentic` (flagship) — independent engine-lift review. Invariants validated as of 2026-06-22.
> Iter: 1
> Build commit: `5120881a`
> Verdict: **APPROVED**
> Generated: 2026-06-22

## Inputs
- CONTEXT-BRIEF.md: not present — read 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml + checkpoint.md + chris-input.md + migration_notes.md + verified-arch-tests.md + 4 result docs directly.
- Promotion proposal: `2026-06-22-sales-agent-multibrand-graph-runtime.md` — **verified `state: accepted`, `ratified_by: Chris 2026-06-22`** via `git show wip/vitalia:...` (lives in wip/vitalia, NOT synced to main yet — checkpoint L49 documents this; read via git). Authorization for engine edits is REAL.
- Skills invoked: copilot-expert=Y (engine boundary discipline), sales-agent-expert=Y (PromptVersionModel §3, slot architecture, anti-duplication).
- gate-output.json: none — re-ran arch tests + platform suite + no-regression probe MYSELF with PYTHONPATH override (`.venv` symlinks to main).

## Authorization preface (read before scoring)
This is an **authorized engine lift**. The accepted promotion proposal sanctions edits to `core/luana-core-sales-agent/` + `core/luana-core-platform/`. I did **NOT** auto-FAIL them as unauthorized engine edits — I verified they match the accepted proposal's Phase-1 scope (ESC-4/5/6) + Chris-ratified T-DEBT1. `verification_nature: técnica`, `demo_required: false`, runtime effect deferred to vitalia post-merge (Chris) — no brand stack to live-verify in this engine worktree, so LIVE_VERIFY_MISSING is **not applicable** here (correctly skip-reasoned in checkpoint L20).

## Gate status (re-run by auditor, PYTHONPATH override)
| Gate | Status | Evidence |
|---|---|---|
| ruff check | PASS | `All checks passed!` (3 prod files + 3 arch tests + T-DEBT1) |
| ruff format --check | PASS | `6 files already formatted` |
| ESC-4 arch test | PASS | `1 passed in 3.44s` (subprocess probe — configure_mappers OK with brand homonym) |
| ESC-5 + ESC-6 arch tests | PASS | `5 passed in 2.27s` (3 ESC-5 + 2 ESC-6) |
| suite_collects (T-DEBT1) | PASS | `476 tests collected, 0 collection errors` (was ModuleNotFoundError pre-T-DEBT1) |
| platform downstream suite | PASS | `294 passed, 0 failed` (ESC-4 crm.py downstream) |
| sales-agent full suite (PYTHONPATH-hack) | FLAKY-DOCUMENTED | not a regression — see § Downstream regression scope |

## 8-check audit results

### Check 1 — Diffs match architect-proven exact diffs → PASS
- **ESC-4** (crm.py): `numstat 1 1` (exactly 1 line). `"MessageModel"` → `"luana_core_sales_agent.infrastructure.models.message_model.MessageModel"`. Nothing else changed (appointments + tenant relationships untouched, confirmed L210-218 current state).
- **ESC-5** (prompts/base.py): `__init__` default `templates_dir: str | None = None` + engine-relative branch `Path(__file__).resolve().parent / "templates"` + override branch (absolute as-is / relative against cwd). EXACT match to 03-arch § TL;DR.
- **ESC-6** (prompt_version_model.py): `tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)` placed after `metadata_info`, no FK. `UUID` import already present (`from sqlalchemy.dialects.postgresql import JSONB, UUID`). EXACT match.
- **T-DEBT1** (test_chat_orchestrator_snapshot.py): L27 import only `tests.modules.sales_agent.orchestrator._chat_flow_snapshot_helpers` → `tests.orchestrator._chat_flow_snapshot_helpers`. Single-line.

### Check 2 — ESC-4 unilateral correct → PASS
- `message_model.py` is **NOT in the changed files** (confirmed `git show 5120881a --name-only`). Zero changes.
- `grep -rn "class LeadModel"` across core + 4 brands → **exactly ONE definition** (`core/luana-core-platform/.../crm.py:144`). `LeadModel` is unique, so the reverse side `MessageModel.lead → "LeadModel"` needs no qualifying. The architect's correction (proposal said bidirectional; build is unilateral) is empirically justified.
- `grep -rn "class MessageModel"` → engine + vitalia brand homonym + test fixtures = the exact ambiguity ESC-4 resolves.

### Check 3 — Forbidden surfaces untouched → PASS
`git show 5120881a --name-only`: 3 prod engine files + 3 new arch tests + 1 `__init__.py` + 1 T-DEBT1 test + 4 story docs. **Zero brand** (vitalia/nicolify/comunify/lupulo), **zero alembic/versions**, **zero application/**, **zero prompts/templates/**, **zero conftest.py**, **zero copilot base.py**. All forbidden_to_touch lists per ticket respected.

### Check 4 — Re-ran 4 arch tests myself → PASS
Literal output captured in § Gate status. ESC-4 (PP4 subprocess), ESC-5+ESC-6 (PP), suite_collects (476 / 0 errors). All GREEN independently.

### Check 5 — Downstream regression → PASS (see dedicated § below)
Platform suite `294 passed, 0 failed`. Full sales-agent suite flakiness is **documented env noise, NOT regression** — proven via pre-lift baseline diff (auditor ran it): pre-lift `24 failed/40 passed` vs post-lift `22 failed/42 passed` on identical subset → lift caused **2 FEWER failures, 0 new failures**.

### Check 6 — Migration discipline (ESC-6) → PASS
`migration_notes.md` DDL is idempotent: `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS tenant_id UUID`, `CREATE INDEX IF NOT EXISTS`. Column matches model (`tenant_id UUID` nullable, indexed, no FK). Backfill no-op (NULL = system default). Brand-authored — no alembic file in commit (confirmed). pgcrypto note documented. Conforms to `.claude/rules/backend-migrations.md`.

### Check 7 — Clean-arch / coupling → PASS
- **ESC-4**: NO Python import added to crm.py (`grep` for `import ... sales_agent` empty) — late-bound string only. Coupling is NOT expanded; the qualification only desambiguates an already-existing late-bound relationship. The kernel→sales-agent acoplamiento debt is documented (03-arch L99) and explicitly NOT expanded.
- **ESC-6**: `tenant_id` has **NO ForeignKey** — byte-identical column pattern to `MessageModel.tenant_id` (`Column(UUID(as_uuid=True), nullable=True, index=True)`). Engine persistence model stays decoupled from platform tenants table (hexagonal). No new bad coupling.

### Check 8 — Scope vs proposal → PASS
All changes within accepted proposal Phase-1 scope (ESC-4/5/6). ESC-1/2/3 correctly deferred to Phase 2 (not in this commit). T-DEBT1 ratified by Chris (chris-input.md L64: "agregá T-DEBT1, commiteá el package"). `reconciled: true`, `chris_verify.signoff: SATISFIED`, `rounds: []` — no scope-delta outside ratified scope.

## 15 categories (agentic)
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | n/a | CERO cambio al AgentState TypedDict (03-arch L45, verified — no graph/state files touched) |
| 2 | Tool registration | n/a | no tools touched (ESC-2/3 = Phase 2) |
| 3 | Prompt cache architecture | n/a | no cache slots / compose_system_prompt touched; ESC-5 = loader path only, no template content |
| 4 | deepagents subagent isolation | n/a | not touched |
| 5 | Observability | n/a | no LLM calls / trace recorder touched |
| 6 | Eval goldens | n/a | no specialist / prompt-content change (ESC-5 = path resolution, not prompt text) |
| 7 | RAG / Qdrant hygiene | n/a | not touched |
| 8 | LLM provider routing | n/a | not touched |
| 9 | Cost optimization | n/a | no cost surface touched |
| 10 | Channel format & brand voice | PASS | CERO cambio a voz/output (03-arch L193); ESC-6 prompt content unchanged |
| 11 | DDD compliance (engine) | PASS | engine edits authorized (proposal accepted); fixes in existing call-path; no cross-brand import; ESC-6 model in infrastructure/ (correct layer) |
| 12 | Tests / TDD | PASS | 3 RED-first arch tests (subprocess probe for ESC-4 determinism); architect-proven RED→GREEN; tests are genuine (not stubs — reference real base.py query branches) |
| 13 | Mirror detection | PASS | no cross-brand mirror of the 3 arch tests; fixes consume engine canonical paths; sales-agent-expert §3 PromptVersionModel touched ONLY for the ratified ESC-6 column (authorized exception) |
| 14 | Default-flip side-effect coverage | n/a | no feature flag flipped in this commit |
| 15 | Decisions honored cite (R6) | n/a | ticket frontmatter has no `decisions_applicable` field → skip |
| 16 | Connectivity (anti-isla) | PASS | 03-arch § Integration design (CONN) present: reachability path (msg→mapper init→prompt load→reply→DB row); fixes in EXISTING call-path (no new orphan surface); home = Infraestructura/motor-agentico |

## Downstream regression scope
SSoT `.claude/rules/auditor-downstream-regression.md`. ESC-4 touches `core/luana-core-platform/.../crm.py` (engine consumed by all 4 brands).

| Surface touched | Downstream target | Auditor status |
|---|---|---|
| core/luana-core-platform crm.py (ESC-4) | platform suite | **294 passed, 0 failed** ✓ |
| core/luana-core-sales-agent base.py / prompt_version_model.py (ESC-5/6) | sales-agent suite | flaky in PYTHONPATH-hack env (documented 03-arch § Realidad del entorno) — NOT a regression (see proof below) |
| brand consumers ×4 | ci-parity + Postgres | deferred to canonical post-merge (validator `downstream_ci_parity`, lupulo placeholder skip) |

**No-regression proof (auditor-executed, decisive):** I reverted the 3 production files to `5120881a~1` (pre-lift), ran the identical non-lift subset, then restored (git status clean post-restore):
- Pre-lift baseline: `24 failed, 40 passed`
- Post-lift (with the lift): `22 failed, 42 passed`
- Δ = **+2 passes, 0 new failures**. The lift strictly improves the state.

Remaining full-suite failures characterized:
- `sqlite3.OperationalError: no such table: booking_links` (scheduling/payment) — env `create_all`/fixture gap, pre-existing.
- `TemplateNotFound: agent_identity.j2 ...src/modules/sales_agent/...` (`test_knowledge_builder_personality.py`) — the **test builds its OWN jinja Environment** from a module-level `TEMPLATES_DIR` constant using the stale monolithic layout; it does NOT use the `PromptLoader` class ESC-5 fixed. File NOT touched by lift. Pre-existing test-fixture staleness, independent of ESC-5.

## Findings (file:line)

### FAIL
- (none)

### WARN
- (none)

### info
- [Latent] `crm.py:214` `LeadModel.appointments → "AppointmentModel"` (unqualified) = same ambiguity class as ESC-4; safe today (vitalia has no AppointmentModel homonym); correctly NOT touched (Story-8 stub-targeted FK). Already flagged in 03-arch § Latent finding + out_of_scope_findings.
- [Sibling bug-class] copilot `core/luana-core-platform/.../prompts/base.py:23` = same bug-class as ESC-5; out-of-scope (different package), flagged for `/harness-issue`.
- [Test-debt] `test_knowledge_builder_personality.py` builds its own loader from stale monolithic `TEMPLATES_DIR` constant → candidate for the same multibrand-path cleanup when copilot/test-env is hardened (`/harness-issue`).

## Cross-scope flags
- (none) — all changes within authorized engine lift scope.

## Research notes
- No novel pattern requiring live-doc validation: SQLAlchemy late-bound module-qualified relationship target + jinja FileSystemLoader package-relative path are standard, architect spike-proven RED→GREEN. Knowledge cutoff disclosure: the model has a static cutoff (Jan 2026); the audit relied on direct code/test execution (live), date-anchored 2026-06-22.

## Recommendations for builder fix-loop
- (none) — APPROVED, no fixes required.

## Drift detection (CONTRACT vs code)
- **NO drift.** The build commit == the architect-proven plan verbatim. ESC-4 unilateral correction (vs the proposal's initial bidirectional suggestion) is documented in 03-arch § TL;DR + chris-input.md and empirically justified (LeadModel unique). T-DEBT1 ratified by Chris. All within proposal Phase-1 scope + chris_verify ratification. `reconciled: true` accurate.

## Verdict
**APPROVED.** All 8 checks pass with independent auditor-executed evidence. Diffs are byte-exact to the architect-proven plan; ESC-4 unilateral is correct (LeadModel unique); forbidden surfaces untouched; 4 arch tests GREEN re-run; platform downstream 294/0; no-regression proven by pre-lift baseline diff (lift improves state by +2 passes, 0 new failures); migration idempotent + brand-authored; clean-arch coupling not expanded (late-bound string + no-FK). Engine edits are authorized by the accepted promotion proposal. Ready for chain → `/pm-luana` migrate (merge to main + sync vitalia) → Chris exercises the graph LIVE in vitalia (runtime-effect bar).
