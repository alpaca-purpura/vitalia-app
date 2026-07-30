# W0.5 · Ratifications log (Step 2 walk)

> Running log of decisions ratified BY CHRIS during the TO-BE walk. Verbatim source for the Step-3 `PROCESS-MODEL.md` SSoT. Each entry: decision · resolution · Chris's riders. Walk order ratified 2026-06-08: **cross-cutting de-tanglers first (D-X2→X5), then WT1→WT7.**

---

## D-X2 · One SSoT per concern — RATIFIED (all 6) · 2026-06-08
Ratified all six designations:
1. WIP-cap → SSoT `story-closure-gate` (per-`code:{module}`); purge "per-worktree" text (lifecycle.md:50, pm-redesign).
2. story-closure-gate → fold G/R into one canonical doc; other 2 → pointers.
3. demo-signoff → ONE field `chris_verify.signoff`; retire `demo_signoff`; `dev_app_verified` = vitalia instance of generic `dod_evidence`.
4. `02-design-ui.md` → DEAD; UI visual contract = design-system canon + `01-spec § Wireframes`; purge 8 stray refs.
5. eval-policy → new SSoT `agentic-eval-policy.md`; 5 restatements → pointers.
6. `/po` → add inline prior-art-scan block (LSP parity w/ po-ux).

### ★ Chris rider (D-X2) — Design-System Canon is a HARD end-to-end gate (the refine→deliver pain)
The brand **design-system** (atoms/molecules + tokens + shared TypeScript in `@luana/ui-kit`; each brand **re-skins/reuses**, brand-specific primitives allowed at builder's discretion) is the **UI SSoT**. Killing `02-design-ui.md` is correct *because* the visual contract is the canon + spec-wireframes-composed-from-it, NOT a free-form doc. The Process Model MUST bind this HARD, end-to-end — this is an explicit pain ("dolor fuerte al refinar y luego entregar"):
- **UX / `/po-ux`:** mockups **compose FROM** the design-system canon — never invent a primitive, never break the brand's system. No "design that breaks the system design."
- **Dev / `builder-frontend`:** build **FROM** `@luana/ui-kit` — paddings, curve/radius, fonts, **any** detail = tokens/canon, **never arbitrary**.
- **Auditor / `auditor-frontend`:** **reject** non-composed UI (arbitrary values, hand-rolled primitives, broken canon).
SSoT for the binding: `docs/architecture/luana-platform/design-system-canon.md` + `ADR-014` + `frontend-visual-fidelity.md` D1. The ratification: it is a **HARD process gate at po-ux + architect + dev + auditor**, NOT advisory. → carry into **D1 (WT1)** + seam slot `design_system_ref`.

## D-X4 · Silent-killer fixes — RATIFIED · 2026-06-08
All 3 acknowledged as must-fix in their surface workstreams. **Canonical key = top-level `verification_nature`** (fix the template's nested `verification.nature`). Promotion proposal → enforce YAML-frontmatter `state:` + schema-lint (kill table format). Cockpit read-schema → add G/R/`chris_verify`/`reconciled`/`dod_evidence` (→ D6).

## D-X5 · Smear → seam — RATIFIED (+2 slots) · 2026-06-08
Seam-slot contract = charter's 7 (`toolchain.* · brands[] · locale · engine_prefix · live_verify_infra[] · design_system_ref · domain_modules[]`) **+ `agent_roster` + `value_stream`** (cockpit smear needs them). No move in W0.5; ratifies the W5 contract.

## D-X3 · Phantom machinery — RATIFIED (purge default) · 2026-06-08
- **Default = purge the dangling reference now, build on demand.** Strike every phantom citation in the surface workstreams; point agentic validators at the REAL `pytest tests/agentic_evals/ --trials=3`. PURGE: `run_agent_evals.py`/`run_trajectory_eval.py`/`check_cost_budget.py`, `validate_chris_input.py`, `generate_release_notes.py`, the AST-similarity claim in `scan_promotables.py`.
- **Paper-rule enforcement = implement-or-drop:** auditor "Cat 11 repro" + autonomous-mode ⏳ layers — either implement the enforcement or drop the claim. No paper rules.
- **`graceful-degradation` → DEMOTE skill→rule/inline doctrine** (timeout/fallback/circuit-breaker is guidance, not invocable). Agentic surfaces cite the rule.
- **`generate_core_modules.py` → PURGE ref; `docs/core-modules/{pkg}.md` stays hand-maintained by `/pm-luana`** (current reality). Drop the auto-gen promise.

---
**Cross-cutting de-tanglers (D-X2..D-X5) — COMPLETE.** → proceeding WT1→WT7.

---

## D1 · WT1 (UI cap) — RATIFIED · 2026-06-08
Structure ratified: refiner `/po-ux` (2-round/2-signature: `input_spec_signed` → `mockup_final_signed` → executable) · builder-frontend · auditor-frontend · verification **funcional** · artifacts = mockup + `demo-script.md` · gates = demo (G) + anti-burbuja (`base.ts`) + **Design-System-Canon HARD (po-ux composes / dev builds-from-`@luana/ui-kit` / auditor rejects non-composed — see D-X2 rider)** + playwright-visual-scope · cockpit = /board + /map + Cap Drawer.
**Cockpit fork → Cap Drawer is the home.** Drop the phantom `/functionality` column from the charter; the Cap Drawer (N0-N4) IS the functionality view.

## D2 · WT2 (service cap) — RATIFIED as-is · 2026-06-08
Structure ratified: refiner `/po` (+ inline prior-art-scan, from D-X2) · builder-backend · auditor-backend · verification **técnica** (auto-skip — correct after the top-level `verification_nature` fix, D-X4) · minimal `01-spec` · technical_gates (Schemathesis for new endpoints, Hypothesis for invariants) · /board + /map. No demo, no anti-burbuja. No open forks beyond cross-cutting.

## D3 · WT3 (agentic) — RATIFIED · 2026-06-08
Structure ratified: refiner `/po` → **`/ux-agentico` (2nd pass)** — story stays `refining` until `02-design-agentic.md` exists · builder-agentic (Opus oblig R23, in-same-session, engine off-limits → `/pm-luana` lift) · auditor-agentic (behavior changes never self-fixed — Carril C) · verification = funcional live (real turn + `copilot_trace_event` traces) **+ pass^k eval gate** · `autonomous_mode` HARD-false for agentic prod · cockpit = /board + Diseño tab + /arquitectura.
**Agentic test plan → owned by `/ux-agentico` in `02-design-agentic.md`** (MF-22 fix): the conversation branch-tree `{happy · intent-out-of-scope · loop · recovery · prompt-injection · tool-failure} → {golden, rubric refs, tool-call asserts, pass^k config, persona}`, pointing at the `agentic-eval-policy.md` SSoT (D-X2). Architect's `04-validators` agentic category **references** it — NO Playwright-shaped plan for agentic. Builder builds goldens RED-first; auditor Phase D runs `pytest tests/agentic_evals/ --trials=3`. Kills the eval-design duplication.

### ★ Chris riders (D3)
- **Newest-Opus policy:** agentic surfaces (`/ux-agentico` design + `builder-agentic` + `auditor-agentic`) run on the **strongest/newest model**. CORE doctrine = "newest model for agentic"; PROJECT slot = "newest Opus = 4.8 today" (tracks upgrades, not pinned). Sits on R23.
- **Single-hub, no branch fragmentation:** `/ux-agentico` (like all refine/build skills) runs in the **same canonical hub worktree on `wip/{brand}`** — never opens a git branch or a separate worktree (ADR-009 single-hub; M14 bucket locks). Separate worktrees = exceptions only (lift core / hotfix / other brand). `builder-agentic` runs in-same-session. Subagent `isolation: worktree` not used for agentic build.

## D4 · WT4 (bugfix) — RATIFIED (5 fixes, walked individually) · 2026-06-08
Structure ratified: lite lifecycle (same 10 states, lighter ONLY on design, never on verification); repro-first HARD gate before `developing`; reclassification escape.
- **F1 — One repro doctrine, one SSoT (RATIFIED):** SSoT = `hotfix-repro-mandatory.md`, absorbing the bugfix-story requirement; **two altitudes** — story-level (`repro_evidence.repro_verified` in checkpoint before `developing`) + ticket-level R26 (any hotfix ticket from handoff/incident/escalation, any story type, before builder spawn). 4 skills (`/po`, `/po-ux`, `/dev-team`, `/architect`) POINT to it, don't restate.
- **F2 — Architect bugfix-lite mode (RATIFIED, Chris→my criterion + trace-evidence rider):** reduced package = `06-tickets` (+ `repro_evidence` per ticket) + `04-validators` (regression scenarios + `regression_guard`) ALWAYS; `03-arch`/`05-guidelines`/`dispatch-plan` SKIPPABLE when no arch decision (not forced — ADR-011 straight-to-tickets); escape = full-`03-arch` OR reclassify (bugfix→ui/service/agentic/technical). Verification gates (CONN/DoD/gherkin) unchanged.
  - **★ Repro/diagnosis evidence broadened (Chris rider):** the repro gate accepts EITHER **(a) live local reproduction** OR **(b) trace evidence** — docker compose logs, Sentry, agentic conversation logs (`copilot_trace_event`/`copilot_llm_call`) — when live repro is hard/flaky/prod-only. Gate = "diagnosis grounded in evidence," not strictly "reproduced locally." **SOLID/DIP:** CORE declares the abstraction `repro_evidence: reproduced_local | trace_evidence{source, ref}`; PROJECT fills concrete sources (docker-logs/Sentry/trace-tables) → core carries no provider dependency. → adds an **`observability_evidence`** facet to the seam (alongside `live_verify_infra[]`).
- **F3 — po-ux bugfix entry (RATIFIED):** add `bugfix (UI)` to the `/po-ux` matrix → lite spec (short, regression scenarios, repro, happy-path optional); NO 2-round/2-signature unless genuinely new UI.
- **F4 — Cockpit wiring (RATIFIED):** add `bugfix` to `StoryType` + `TYPE_META` (🩹) + `typeMetaOf` + board filter; `repro_verified` badge on BoardCard (W4b).
- **F5 — Schema (RATIFIED):** canonical key = **`repro_evidence`** (rename checkpoint `hotfix_metadata`→`repro_evidence`); add top-level `type:` field to `checkpoint-template` (enum ui/service/agentic/bugfix [+technical pending D5]).

## D5 · WT5 (technical capability) — RATIFIED · 2026-06-08 ★ CHARTER HEADLINE — THE VOID CLOSED
The de-facto void (no type/refiner/template; 4 improvised paths; ghost `technical-story`) is replaced by a first-class lane:
- **① Identity — RATIFIED:** cement **`type: technical-story`** as the 5th first-class story type (enum becomes ui/service/agentic/bugfix/**technical**). Wires the cockpit's existing `tech` slot to a real producer.
- **② Spec = contract, not behavior — RATIFIED:** the `01-spec` analog for an infra cap = a **contract-spec**: *contract/interface/extension-point provided · consumers · invariant enforced · verification-by-effect.* Teach `new_cap.py` an infra mode. No Gherkin behavior spec for pure infra.
- **③ Refiner = `/architect` — RATIFIED:** flow = **pm opens+frames the need → `/architect` writes the contract-spec + reduced ready-package → build → verify → done.** Technical-story SKIPS po/po-ux/ux-agentico (infra = design, not behavior). brand-infra opened by `/pm-{brand}`; core-infra by `/pm-luana`.
- **④ Net-new core infra — RATIFIED:** = technical-story `cap_change_type: new` targeting `core/`, owned by `/pm-luana`. The technical-story IS the use-case justification → promotion's "no research in core" applies only to LIFTS (WT6), not deliberately-planned core infra. **Worktree:** core-targeting technical-story runs in the **ephemeral core worktree** (`wip/core-{slug}`, the documented single-hub exception); brand-infra runs in the brand hub.
- **⑤ WT5 builds / WT6 lifts — RATIFIED:** a technical-story BUILDS an infra cap (on `/board`, WIP-cap, closure-gate, archive — incl. net-new core); a promotion-proposal is ONLY the brand→core LIFT transaction. **Retire proposal-as-lifecycle** (durable-flows "flujo excepcional" stops being how infra ships).
- **⑥ Verification = `técnica` — RATIFIED:** gates + **runtime evidence by effect**, no demo. Bar per sub-domain: encryption→decrypt round-trip · idempotency→replay dedup · observability→trace row written · durable-flow→persist+resume · audit→audit row + access-denied path. (Reads its own effect/logs — ties to D4 trace-evidence.) The one already-working piece — protected.
- **⑦ Spec-first — RATIFIED:** forbid build-first/document-later for technical caps; contract-spec RED-first; EXCEPT `nature: scaffold` (exempt by definition).
- **⑧ Cockpit — → D6:** wire the `tech` slot + surface in-flight technical work (not just finished caps in the collapsed Infra zone).

## D6 · Cockpit unification — RATIFIED · 2026-06-08 ★ CHARTER HEADLINE
- **① Surface proceso-v5 gates (RATIFIED, highest priority):** add `phase`/`chris_verify.signoff`/`reconciled`/`dod_live_verified`/`dod_evidence` to the cockpit read-schema (`types.ts` + RICH_FIELDS); render a **"blocked on Chris"** badge for `phase: AWAIT_CHRIS_VERIFY` + signoff/reconciled/dod indicators. Closes silent read-schema drift (MF-03) — a story awaiting Chris no longer looks identical to one being audited.
- **② WT4 + WT5 type wiring (RATIFIED, consequence):** bugfix 🩹 + `repro_verified` badge (D4.4); `technical` story type → real producer for the existing `tech` slot (D5.8).
- **③ WT6 promotion view (RATIFIED — build):** a brand→core **lift board** reading `docs/promotion-protocol/proposals/` (proposed→accepted→migrated) + `cap.license` transitions. 19 proposals become visible.
- **④ /harness boardify (RATIFIED):** boardify L2 (learnings) + L4 (drift) IN-PLACE inside `/harness` (not just count/link-out). Charter's "needs unified view" was stale → rescoped.
- **⑤ State-vocab legend (RATIFIED):** add a legend bridging `/board` (10 product states) vs `/harness` (6 HLP states) — keep the two lifecycles, make the difference visible.
- **⑥ De-smear read-schema (RATIFIED, via D-X5):** rosters/value-stream/roles → config (`agent_roster`/`value_stream` slots); `types.ts` schema = CORE seam. W4b/W5 work.

## D7 · WT6 (promotion) + WT7 (harness) — off-spine processes — RATIFIED · 2026-06-08
**WT6 (brand→core lift):**
- **lift-gate (RATIFIED):** **pre-edit WARNING** (pre-commit warns when touching `core/` without an accepted proposal — early signal, non-blocking) **+ auditor PR-time HARD catch stays** + **fix MF-02** (table-format `state:` → false-FAIL; enforce YAML-frontmatter + schema-lint).
- **cleanups (RATIFIED all):** (a) ONE SSoT for the 5-state machine (kill README↔pm-luana dup, other points); (b) **document the `deferred` 6th state**; (c) scope-discipline — promotion = brand→core LIFT only (stop using it as a generic cross-brand-change tracker); (e) **explicit auditor/reviewing pass on the lift** (not just folded into R3 downstream-regression); (f) **formalize WT6 as a first-class off-spine process** in the SSoT.
**WT7 (harness improvement — dogfood):**
- **cleanups (RATIFIED all):** (a) ONE SSoT for the apply-pipeline (reconcile HLP §6 ↔ harnesses-improvement skill's `machinery-check` addition); (b) **cross-walk** the two state vocabularies (HLP `reported→verified` ↔ audit `LOW/MED/HIGH`) + document the catalogue→HB-N mapping; (c) **confirm WT7 = the second modeled (self-host/dogfood) process** in the SSoT.

---
**WALK COMPLETE.** Cross-cutting (D-X2..D-X5) + per-WT (D1..D7) all ratified by Chris 2026-06-08. → Step 3: write `PROCESS-MODEL.md` SSoT.
