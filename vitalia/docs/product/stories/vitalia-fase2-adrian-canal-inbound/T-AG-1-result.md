# T-AG-1 result — EXTEND state_overlay + operator-instruction agentic wiring + persona tuning + goldens

**State:** tests-passing · **Owner:** builder-agentic (flagship · R23) · **Branch:** wip/vitalia (hub, in-place M9)
**Surface:** AGENTIC · production_code=true · **CERO engine edit** (V-ARCH-1 confirmed: `git status core/` empty)

---

## Delivered (all in `vitalia/backend/src/modules/vitalia/sales_agent/` + canonical goldens home)

1. **EXTEND `domain/state_overlay.py::VitaliaSalesAgentStateExtension`** — 4 booking keys (total=False):
   `recommended_doctor_id`, `recommended_service_offer_id`, `candidate_slots` (★ documented volatile-only,
   slot 8, never cacheable prefix), `doctor_profile_shared_at`. Engine `scheduled_meetings`/`MeetingEntry`/
   AgentState TypedDict NOT touched (referenced, not duplicated).

2. **Operator-instruction agentic WIRING** — closes the integration gap (T-BE-3 persisted to
   `metadata_info["operator_instructions"]`; the engine reads `checkpoint.resume_objective`, a one-shot Text
   column, and reads NOTHING from `metadata_info`):
   - `application/services/operator_instruction_bridge.py::OperatorInstructionBridge` — injected-Protocol
     bridge (no engine/crm concretion import); `apply_for_turn` mirrors the persistent instruction into the
     engine's VOLATILE `resume_objective` seam so the engine injects `[INSTRUCCION DEL OPERADOR]` (slot 7,
     post CACHE_BOUNDARY) every turn. Persistent (source key never cleared, RN-13). Best-effort (never breaks turn).
   - `infrastructure/adapters/checkpoint_instruction_bridge_adapter.py` — raw SQL on `agent_state_checkpoints`
     (schema-mirror exception): `SET resume_objective = metadata_info->>'operator_instructions'` guarded by
     `metadata_info ? 'operator_instructions'` + tenant+lead+is_active dual-filter. Idempotent.
   - Wired into `operator_instruction_service.py` (optional `bridge_to_turn` dep — back-compat with T-BE-3) +
     `operator_instruction_router.py` (composition root). On set → mirrors immediately → SC-8 end-to-end.

3. **Persona tuning** (`prompts/adrian_persona_base.md`) — added medical-discovery reweight block (the lead
   who "doesn't know what they want", design §12). Per-tenant brand MD (slot 5 base). Engine `tuning.py` NOT
   touched; guardrails (`medical_safety_rails.md`, persona `emergency_protocol`, forbidden_phrases) HONORED.

4. **Goldens BUILDABLE** (canonical home `tests/agentic_evals/sales_agent/goldens/otro/` + `personas/`) — 5
   goldens + 5 personas, all `must_pass:true`, each scoring **5/5 dims** against the real pass^k grader:
   `honor_mode`, `screening_gate` (DERIVAR_EMERGENCIA→no book+deriva+escala), `objection_trust`, `ethical`
   (no dark patterns), `operator_instruction` (SC-8). Runner count gates bumped 17→22 / 16→21 + scenario
   handling for the 5 new scenarios. The book-* goldens are lift-gated — NOT created.

## Gates (scoped)
- `tests/modules/vitalia/sales_agent/` — **70 passed** · `tests/agentic_evals/sales_agent/` — **58 passed**
  (consolidated **128 passed**). pass^k: 22 goldens / 21 personas, 3 trials GREEN.
- Regression `tests/modules/vitalia/{inbox,crm}/` — **429 passed** (composer/mode/pausa untouched, AC-11).
- `tests/architecture/` (vitalia) — **361 passed** (PHI dual-filter, response_model, audit, anti-mirror).
- ruff check + `ruff format --check` — **clean** (15 files).
- Cap bidirectional: cross_check_3 (cap↔code HARD) **130/130, 0 drift** · G1-G9 **0 drift** · orphans=0.
  SOFT_DRIFT=2 = pre-existing api role-enforcement on a DIFFERENT cap (`compliance.hipaa-lite-defensive-stack`).

## Live-verify (DoD #37) — real Postgres, real code path (NOT GET 200, NOT mocks)
Exercised the ACTUAL `CheckpointInstructionBridgeAdapter` + `OperatorInstructionBridge` against a live
Postgres (port 5435) seeded with a real `agent_state_checkpoints` row:
- `bridge.apply_for_turn` → **True** · `resume_objective` mirrored = `'Ofrecele 10% de descuento'` (engine
  injects `[INSTRUCCION DEL OPERADOR]` next turn — **G-operator-instr / SC-8 proven**).
- 2nd turn re-applies → **True**; `metadata_info["operator_instructions"]` **preserved** (RN-13 persistent, not one-shot).
- Cross-tenant decoy (other tenant, same lead): `resume_objective` stays **NULL** (tenant isolation proven).
- All 5 buildable goldens graded **5/5 dims GREEN** by the real pass^k grader (G-honor-mode + G-operator-instr
  + G-screening-gate + G-objection-trust + G-ethical).
- ⚠️ Honest limitation: a full engine-turn end-to-end live-verify is NOT yet exercisable — the engine
  `agent_state_checkpoints` table is not yet migrated into `vitalia_dev` (sales_agent inbound pipeline not yet
  deployed; it's part of this same story's BE tickets, in progress). The bridge was therefore live-verified
  against a schema-identical real-Postgres table running the actual SQLAlchemy code path. NO masking.

## Skills consulted
sales-agent-expert · copilot-expert · hipaa-lite · anti-duplication · tenant-isolation · tdd-mandatory ·
chrome-devtools-verify (live-verify). WebFetch: Anthropic prompt-caching (accessed 2026-06-22) — 1h TTL must
be explicitly declared, GA. Full citations in `T-AG-1-impl-log.md § Skills Consulted`.

## Upstream deficiency (auto-hardening) — HB-92 captured
The ready package ASSUMED the engine already injected the persisted instruction (01-spec § Instrucción step 3
+ 03-arch-agentic § 1.2). It does NOT — the engine reads `resume_objective`, not `metadata_info`. "Imagined
contract never integrated" (5th of the HB-44/74/82 family). Captured as **HB-92** in harness-backlog.md with
the fix recommendation (architect must grep the READ-side of any "engine already honors X" claim).

## Diff (files touched — pathspec)
PROD: `sales_agent/domain/state_overlay.py` · `sales_agent/application/services/{operator_instruction_bridge,
operator_instruction_service}.py` · `sales_agent/infrastructure/adapters/checkpoint_instruction_bridge_adapter.py`
· `sales_agent/api/routers/operator_instruction_router.py` · `sales_agent/prompts/adrian_persona_base.md`
TESTS: `tests/modules/vitalia/sales_agent/test_{operator_instruction_bridge,state_overlay_booking_keys}.py` ·
`tests/modules/vitalia/sales_agent/test_operator_instruction_service.py` (2 new tests) ·
`tests/agentic_evals/sales_agent/test_pass_k_evaluation.py` (count bumps + scenarios) ·
`tests/agentic_evals/sales_agent/goldens/otro/*.yaml` (5) · `.../personas/otro_*.yaml` (5)
DOCS: story `T-AG-1-impl-log.md` + `T-AG-1-result.md` + `chris-input.md` · `docs/process/harness-backlog.md` (HB-92)

**Commit SHA:** `52dab5b6` (brand work, by pathspec) + `c818a325` (HB-92 harness capture, transversal).
Pushed to `wip/vitalia` (`2daf7379..c818a325`). All pre-commit gates green (incl. cap cross_check_3 HARD).
