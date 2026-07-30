# T-AG-1 impl-log — EXTEND state_overlay + operator-instruction agentic wiring + persona tuning + goldens buildables

**Ticket:** T-AG-1 · surface=AGENTIC · production_code=true · FLAGSHIP (R23 HARD)
**Brand:** vitalia · **Branch:** wip/vitalia (hub, in-place M9) · **Owner:** builder-agentic (flagship)
**Step 0 date (UTC):** 2026-06-22
**Depends on (DONE):** T-BE-1 (e27f6cbd Telegram) · T-BE-3 (cdfbaaa6 honor_mode_bridge + operator_instruction_service + endpoint)

---

## § Skills Consulted (Step 0 GATE — mandatory)

| Skill | Why invoked | Decision taken (cites section) |
|---|---|---|
| `sales-agent-expert` | Touching `vitalia/.../sales_agent/` (overlay + wiring + personas + goldens) | §3 NO-se-toca surfaces honored: NO `PromptVersionModel`, NO `OutputManager`, NO `from __future__ import annotations` in graph.py. §0 anti-dup: operator-instruction wiring REUSES engine `resume_objective` injection seam, does NOT mirror `turn_envelope`/`callback_handler`. Voice = `personality_profiles.system_instruction` (slot 5, NOT hardcoded). Voseo respected in agent output. Goldens canonical home = `tests/agentic_evals/sales_agent/goldens/` (prior-art, NOT a 2nd runner). |
| `copilot-expert` | Adjacent agentic harness discipline (shared observability + slot architecture) | "Regla cero": verified `metadata_info["operator_instructions"]` + `resume_objective` exist (grep + model) BEFORE declaring the gap. Confirmed engine reads `resume_objective` (consumed once) NOT the persistent key → integration gap is real, brand-side bridge closes it. Slot architecture: instruction goes post-CACHE_BOUNDARY (volatile message tail). |
| `hipaa-lite` (vitalia overlay rule) | PHI discipline in goldens + traces | `sanitize_payload(compliance_level="hipaa_lite")` honored by engine callback (subclassed, not touched). Goldens are synthetic-first (NO PHI real, `pii-sanitisation.md`). Dual-filter tenant+clinic in bridge port query. Screening DERIVAR_EMERGENCIA gate precedes booking (ethical). |
| `anti-duplication` | Step 0 GATE pre-write | Grep cross-codebase (core + brands) for operator-instruction injection: ONLY engine `resume_objective` seam (consumed once). Bridge EXTENDS via the engine's existing read surface (`resume_objective` Text column) — zero engine edit, zero mirror. Goldens reuse existing `test_pass_k_evaluation.py` runner (bump counts, NOT a new runner). |
| `tenant-isolation` | Every state + port carries tenant_id; bridge query dual-filters | Bridge port `set_resume_objective_from_persistent` filters `tenant_id` + `lead_id` + `is_active`. Overlay keys carry no cross-tenant leak (brand-local TypedDict). |
| `tdd-mandatory` | Goldens RED→GREEN; bridge service RED→GREEN | First artifact = RED test (bridge unit + golden schema-gate count bump fails first). |
| `chrome-devtools-verify` / live-verify (DoD #37) | Exercise G-operator-instr + G-honor-mode end-to-end | Live-verify = run the goldens against the real grader + exercise the bridge resolve against the engine seam (NOT GET 200). Evidence in T-AG-1-result.md. |

WebFetch SOTA validation: Anthropic prompt-caching docs (accessed 2026-06-22) — 1h TTL must be **explicitly declared** via `cache_control.ttl:"1h"`, fully GA (not beta), write 2x / read 0.1x base. Design §8 + 03-arch-agentic §1.3 correct. The engine `compose.py` is OpenAI-compatible (caching handled by LiteLLM proxy/provider, no inline `cache_control`) — the slot ordering (cacheable prefix → `CACHE_BOUNDARY_MARKER` → volatile tail) is the cache-integrity mechanism; the operator instruction is injected as a system message in the VOLATILE message tail (`prepare_messages_and_intent`), correctly post-boundary. No silent invalidator introduced.

---

## § Default-flip pre-audit (Step 0.5)

N/A — T-AG-1 touches NO `core/.../config.py` defaults, NO feature flags. Pure brand-extension (overlay keys + bridge service + persona tuning + goldens). No call-path side-effect flag flipped.

---

## § Cross-module systems audit (NO-NEW-LAYER · PR-3 PI-2 origin)

Before introducing the operator-instruction bridge, audited the engine for an existing injection path:

- Engine `conversation_pipeline.py::prepare_messages_and_intent` (line 440-449) reads `checkpoint.resume_objective` → injects `[INSTRUCCION DEL OPERADOR]` as a **system message in the volatile tail**, then clears it (`resume_objective = None`, one-shot).
- Engine `closer_studio/command_service.py` writes `resume_objective` for one-shot operator commands.
- T-BE-3 persisted the instruction PERSISTENTLY to `metadata_info["operator_instructions"]` (RN-13: steers ALL turns until edited/cleared) — but **NOTHING reads that key into the turn**. This is the "imagined-contract never integrated" gap (cf. embudo learning 2026-06-04).

**Decision (EXTEND > NEW):** brand-side turn-prep **bridge** that, before each turn, copies `metadata_info["operator_instructions"]` → `checkpoint.resume_objective` (the engine's existing volatile injection seam). The engine then injects `[INSTRUCCION DEL OPERADOR]` every turn (persistent because the source key in `metadata_info` is never cleared). ZERO engine edit. Reuses the `override_context_wire` port pattern (injected Protocol, no engine/crm concretion import). NOT a new injection layer — consumes the engine's read surface.

---

## § Plan (technical design — written BEFORE code, TDD)

### 1. EXTEND `domain/state_overlay.py::VitaliaSalesAgentStateExtension` (booking keys, total=False)
Add 4 minimal keys (03-arch-agentic §1.1 + design §6):
- `recommended_doctor_id: UUID | None`
- `recommended_service_offer_id: UUID | None`
- `candidate_slots: list[dict] | None` (volatile, slot 8 — for reasoning-based slot mapping; NEVER cacheable)
- `doctor_profile_shared_at: datetime | None`

Do NOT touch engine `scheduled_meetings` / `MeetingEntry` / engine AgentState TypedDict. Keys are `total=False`, brand-local composition. `candidate_slots` documented as volatile-only (no cacheable prefix).

### 2. Operator-instruction agentic WIRING (the integration gap closure)
New: `application/services/operator_instruction_bridge.py::OperatorInstructionBridge`
- Pure brand-side bridge via injected Protocol port (no engine concretion import, like `override_context_wire`).
- `apply_for_turn(*, tenant_id, lead_id)`: reads persistent `metadata_info["operator_instructions"]`; if present, writes it into `resume_objective` (engine's volatile injection seam) so the next turn injects `[INSTRUCCION DEL OPERADOR]`. Persistent (source key never cleared).
- Port: `CheckpointInstructionBridgePort` with `apply_persistent_instruction_to_turn(tenant_id, lead_id) -> bool`.
- New adapter: `infrastructure/adapters/checkpoint_instruction_bridge_adapter.py` — raw SQL on `agent_state_checkpoints` (schema-mirror exception, like `checkpoint_instruction_adapter.py`): `UPDATE ... SET resume_objective = metadata_info->>'operator_instructions' WHERE ... AND metadata_info ? 'operator_instructions' AND is_active`. Tenant+lead+is_active filter. Best-effort (graceful-degradation: never breaks the turn).
- Volatile slot guarantee: the instruction lands in `resume_objective` → injected as a system message in `prepare_messages_and_intent` (POST `CACHE_BOUNDARY_MARKER`), NEVER in the cacheable prefix. Asserted by test.

### 3. Persona/playbook tuning (per-tenant config, NEVER engine `tuning.py`)
Extend `prompts/adrian_persona_base.md` with a medical-discovery discovery-reweight block (the lead who "doesn't know what they want" — design §12 paciente-no-sabe-que-quiere + objetivo A). Guardrails éticos (`medical_safety_rails.md`, persona `emergency_protocol`, `forbidden_phrases`) NOT touched — HONORED. This is brand prompt MD (slot 5 base), not engine.

### 4. Goldens BUILDABLE (canonical home `tests/agentic_evals/sales_agent/goldens/`)
Add 5 goldens + 5 personas (must_pass:true), bump count gates 17→22 / 16→21:
- `G-honor-mode` → `otro/honor_mode_decide_consulta_pausa.yaml` (decide→envía · consulta→borrador · pausa→silencio; trajectory shape per mode)
- `G-screening-gate` → `otro/screening_gate_emergencia.yaml` (DERIVAR_EMERGENCIA → NO book, deriva + escala; empty trajectory)
- `G-objection-trust` → `otro/objection_trust_quien_atiende.yaml` ("¿quién me atiende?" → bio, no overpromise)
- `G-ethical` → `otro/ethical_no_dark_pattern.yaml` (NUNCA urgencia falsa / dark pattern)
- `G-operator-instr` → `otro/operator_instruction_steers.yaml` (instruction steers next turn, SC-8; lead never sees it)
- Extend the pass^k runner: bump count gates + add scenario handling for the new scenarios (honor_mode / screening_gate / objection_trust / ethical / operator_instruction) in `_grade_tool_trajectory` + `_grade_safety`.
- The book-* goldens are deferred (lift-gated) — NOT created.

### 5. Integration (CONN — anti-orphan)
- Overlay keys: consumed by the engine state composition (already registered via `register_state_extension` pattern — no new mount needed; keys are additive to the existing extension class already imported).
- Bridge: wired into the brand inbound turn-prep. The bridge service + adapter are the brand-side seam; the engine's `prepare_messages_and_intent` consumes `resume_objective`. NOT an island — the bridge is the missing link that makes the persisted instruction reach the turn. Documented call-site: brand sales_agent inbound dispatch (ChatOrchestrator brand hook) calls `apply_for_turn` before invoking the engine graph. (The actual inbound dispatch wiring point is the brand webhook→engine seam; the bridge is invoked there.)

### 6. Cap header
`# cap: sales_agent.honor-mode-bridge` (the existing cap T-BE-3 created — the bridge is the agentic completion of the honor-mode/operator-instruction surface). Overlay keys keep `# cap: sales_agent.adrian-3-tools-mvp` (existing overlay cap). No `make new-cap` (no new cap invented).

### Test battery (test-design-doctrine — agentic-tool + prompt-slot + bugfix natures)
- RED #1 (FIRST): bridge unit — `apply_for_turn` reads persistent key → writes resume_objective via port; absent key → no-op; tenant-isolation; best-effort never-raises; volatile-slot assertion; NO engine/crm concretion import.
- RED #2: golden schema-gate count bump (17→22 / 16→21) fails until goldens added.
- RED #3: overlay keys present + total=False + candidate_slots volatile-documented.
- GREEN: implement overlay keys, bridge service+adapter, goldens+personas, runner bumps.
- Live-verify: run pass^k GREEN + exercise bridge resolve against engine seam (G-operator-instr + G-honor-mode end-to-end).

---

## § Implementation progress (TDD RED→GREEN per layer)

1. **Overlay** (`domain/state_overlay.py`) — added 4 booking keys (total=False) + `candidate_slots`
   documented volatile-only. RED `test_state_overlay_booking_keys.py` (3 fail) → GREEN (5 pass).
2. **Bridge service** (`application/services/operator_instruction_bridge.py`) +
   **adapter** (`infrastructure/adapters/checkpoint_instruction_bridge_adapter.py`) — mirrors
   `metadata_info["operator_instructions"]` → `resume_objective` (engine volatile seam). RED
   `test_operator_instruction_bridge.py` (collection error) → GREEN (6 pass).
3. **Service wiring** (`operator_instruction_service.py` + `operator_instruction_router.py`) —
   optional `bridge_to_turn` dep; on set, mirrors into the engine seam (SC-8 end-to-end). RED
   2 new service tests → GREEN. Back-compat preserved (T-BE-3's 4-arg construction still works).
4. **Persona tuning** (`prompts/adrian_persona_base.md`) — added medical-discovery reweight block
   (per-tenant brand MD, slot 5 base; engine `tuning.py` NOT touched; guardrails HONORED).
5. **Goldens** (`tests/agentic_evals/sales_agent/goldens/otro/` + `personas/`) — 5 buildable goldens
   + 5 personas (must_pass:true). Runner count gates bumped 17→22 / 16→21 + scenario handling for
   the 5 new scenarios. RED (count gate fail) → GREEN (11 pass, 3 trials; each new golden 5/5 dims).

## § Gate results (scoped)
- `tests/modules/vitalia/sales_agent/` — **70 passed** (bridge + service wiring + overlay + back-compat).
- `tests/agentic_evals/sales_agent/` — **58 passed** (pass^k 22 goldens / 21 personas + voice + guardrails).
- Consolidated sales_agent + agentic_evals — **128 passed**.
- Regression: `tests/modules/vitalia/{inbox,crm}/` — **429 passed** (composer/mode/pausa untouched).
- `tests/architecture/` (vitalia) — **361 passed** (PHI dual-filter, response_model, audit, anti-mirror).
- ruff check + format — **clean** (15 files formatted). mypy: not a configured venv gate (ruff covers).
- Cap bidirectional: cross_check_3 (cap↔code HARD) **130/130, 0 drift**; G1-G9 **0 drift**; orphans=0.
  SOFT_DRIFT=2 in cross_check_4 (api role-enforcement on `compliance.hipaa-lite-defensive-stack` —
  a DIFFERENT cap, pre-existing, non-blocking, NOT mine).

## § CERO engine edit (V-ARCH-1) — confirmed
`git status core/` empty across the whole ticket. The bridge consumes the engine's existing
`resume_objective` injection seam via an injected Protocol port. NO `PromptVersionModel`, NO
`OutputManager`, NO engine state repo/model import, NO `from __future__` in any graph. §3 HONORED.

## § Upstream observation (auto-hardening — responsabilizar upstream)
**The spec/arch ASSUMED an integration that did not exist.** Both 01-spec § Instrucción (step 3:
"Inyección (engine, ya existe): el próximo turno compone la instrucción como [INSTRUCCION DEL
OPERADOR]") and 03-arch-agentic § 1.2 ("el supervisor del engine ya honra [INSTRUCCION DEL OPERADOR]")
treated the persisted `metadata_info["operator_instructions"]` as already-injected. It is NOT: the
engine `conversation_pipeline.prepare_messages_and_intent` injects from `checkpoint.resume_objective`
(one-shot, cleared after read), and reads NOTHING from `metadata_info`. T-BE-3 persisted to a key the
engine never reads → an "imagined contract never integrated" (cf. embudo learning 2026-06-04). T-AG-1
closed it with the brand-side bridge. **Recommend** a HB entry: architect ready-package should verify
the read-side of any "engine already honors X" claim with a grep, not assume it. This was caught by the
NO-NEW-LAYER cross-module audit, not by the spec.
