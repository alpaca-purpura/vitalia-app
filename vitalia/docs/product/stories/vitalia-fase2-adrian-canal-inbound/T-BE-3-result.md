# T-BE-3 result — Honor-mode bridge + operator-instruction endpoint

**State:** pushed · **Commit:** cdfbaaa6 · **Owner:** builder-backend (workhorse)
**Note:** builder agent dropped on a connection error AFTER tests went GREEN (109 tool uses); orchestrator finalized (ran gates, fixed main.py import-sort, created cap, committed by pathspec).

## Delivered
- `application/services/honor_mode_bridge.py` — HonorModeBridge: `decide`→envía · `consulta`→borrador (intercepta outbound pre-send) · `pausa`→skip. Lee `handler_mode`/`proposal_required`/`pause_until` de la cap adrian-inbox shipped (no inventa modos). Cero engine.
- `application/services/operator_instruction_service.py` — persiste instrucción PERSISTENTE en `agent_state_checkpoints.metadata_info[operator_instructions]` vía patrón `override_context_wire` (sin cambio de schema) + audit row sync pre-response + activity NON-PHI.
- `infrastructure/adapters/checkpoint_instruction_adapter.py` — adapter al checkpoint metadata_info.
- `api/routers/operator_instruction_router.py` + `api/dtos/operator_instruction_dtos.py` — `POST /api/v1/adrian/conversations/{conversation_id}/instruction` (Bearer + X-Tenant-ID, response_model). include_router en main.py.

## Gates
- Ticket tests: 24/24 PASS (`test_honor_mode_bridge.py` + `test_operator_instruction_service.py`).
- Arch validators: `test_audit_log_sync_write.py` (V-NF-3) + `test_response_model_required.py` (V-NF-4) PASS.
- ruff check + format: clean (main.py I001 autofixed by orchestrator).
- Bidirectional cap validator: SOFT_DRIFT advisory (empty `api/__init__.py` markers — non-blocking).

## Cap
- Created `sales_agent.honor-mode-bridge` (status: planned) via `make new-cap` — architect deferred cap creation (BLOCKED-PARTIAL focus on lift). **Taxonomy to confirm in R-reconcile** (extend adrian.inbox vs new derived cap).

## Live-verify (DoD #37) — PENDING (G phase)
Not exercised live yet: needs dev stack + `POST /instruction` against running app (observe metadata_info row + audit + activity + 0 outbound to lead). Deferred to the consolidated OLA-1 live-verify before `developed`.

## Validators covered
V-NF-3, V-NF-4, V-FN-2 (SC-2 consulta), V-FN-3 (SC-3 pausa), V-FN-7 (SC-8 instruction) — unit-level GREEN; live SC verification at G.
