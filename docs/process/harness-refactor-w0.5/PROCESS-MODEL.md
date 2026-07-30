# Luana Process Model — the requirements layer (W0.5 SSoT)

> **Status: RATIFIED by Chris · 2026-06-08.** Harness Refactor program, workstream A.5 (W0.5). This is the **requirements layer**: the harness exists to protect the development process, so the process model is what rules/skills/agents/hooks/cockpit/templates IMPLEMENT. **This doc GATES W1+** — no surface refactor (W1-W10) starts until the process it implements conforms to this model (charter §6 critical path).
>
> **Provenance:** built from the 8 AS-IS reconstructions (`as-is/`) consolidated in `AS-IS-MAP.md`, walked + ratified decision-by-decision with Chris (full log: `RATIFICATIONS.md`). Detail/`file:line` lives in those; this is the forward model. Dogfood: lean, pointer-first, one SSoT per concern.
>
> **How to use this:** §0 the two processes · §1 the vocabulary · §2 the spine · §3 the 7 work-type profiles (the heart) · §4 the seam contract · §5 cross-cutting doctrine · §6 the conformance checklist W1+ validates against · §7 cockpit contract.

---

## 0 · The two processes + the work-type taxonomy

Luana models **two** development processes, both first-class, both visible in the cockpit:

1. **Product-dev process** — how capabilities get built for the project/brands (work-types WT1-6). Rides the **10-state spine** (WT1-5) or sits **off-spine** (WT6 promotion).
2. **Harness-improvement process** — how the dev-OS improves itself (WT7). The harness **self-hosts** this (dogfood). Its own lifecycle (HLP+CIL), not the 10-state spine.

**Work-type taxonomy (RATIFIED — 5 story types + 2 off-spine processes):**

| WT | Work type | Story type | Rides | Refiner / owner |
|---|---|---|---|---|
| WT1 | UI / functional capability | `ui-story` | spine | `/po-ux` |
| WT2 | Service capability (no UI) | `service-story` | spine | `/po` |
| WT3 | Agentic (conversational flow) | `agentic-story` | spine | `/po` → `/ux-agentico` |
| WT4 | Bugfix / hotfix | `bugfix` | spine (lite) | `/po` or `/po-ux` (lite) |
| WT5 | **Technical capability** (infra/obs/security/perf) | **`technical-story`** ★NEW | spine (contract-first) | **`/architect`** (pm opens) |
| WT6 | Promotion (brand→core lift) | — | **off-spine** | `/pm-luana` |
| WT7 | Harness improvement | — | **off-spine** (HLP+CIL) | `/pm-luana` |

★ WT5 `technical-story` is the W0.5 deliverable: the previously-undefined lane is now first-class (D5). The cockpit's pre-existing `tech` slot now has a real producer.

---

## 1 · The unified state/phase vocabulary (X6 resolution)

Before W0.5 an operator had to hold **5** overlapping vocabularies. Ratified: **one operator-facing vocabulary per process.**

### Product-dev process — 10 macro states + 4 named phases

```
idea → refining → refined → ready → developing → developed ─[G]─[R]→ reviewing → done → archive
                                                      └ parked / dropped (off-ramps) ┘
```

- **10 macro states** (SSoT `lifecycle.md`): `idea · refining · refined · ready · developing · developed · reviewing · done` (+ `parked · dropped`).
- **4 named phases** (live as `checkpoint.md::phase`, NOT new states):
  - **G — `AWAIT_CHRIS_VERIFY`** (under `developed`): Chris exercises the kit live, signs `chris_verify.signoff`, **before** the auditor. Skipped if `autonomous_mode: true`. **Exempt from the WIP cap** (anti-deadlock).
  - **R — reconcile** (between `developed` and `reviewing`): `/pm-{brand}` aligns `01-spec`/`03-arch`/`04-validators`/cap to built reality, writes `reconciled: true` (auditor reads it as a precondition).
  - **C — fix-loop** (under `reviewing`, on CHANGES_REQUESTED).
  - **D — gherkin Phase D** (embedded in `reviewing`).
- **RETIRED as operator-facing** (X6): the `A-F` letter-phase labels and `phase_workflow` (`PO_SPEC`…). Letters become internal/historical only; `phase_workflow` is folded into the named phases. **One vocabulary: 10 states + {G,R,C,D}.**
- **WIP cap (D-X2):** ≤ 1 per `code:{module}` bucket for `developing|developed|reviewing` (NOT per-worktree). Exempt: `AWAIT_CHRIS_VERIFY` + `defer_audit: true`. The "per-worktree" text is purged.

### Harness-improvement process — HLP 5-state

```
reported → triaged → ratified → applied → verified   (+ deferred, parked out-of-band)
```

- SSoT `harness-lifecycle.md`. Items routed across **CIL 4 lanes** (L1 harness-backlog · L2 learnings · L3 tech-debt · L4 capability-desfasada auto-detect).
- **The bridge (D6⑤):** the cockpit renders a **legend** distinguishing the 10 product states from the 6 HLP states — the two boards no longer look identical-but-mean-different.

---

## 2 · The shared spine (WT1-5 ride it; WT6-7 don't)

The canonical backbone. One owner skill per hop, one HARD gate per hop. Detail+`file:line`: `as-is/SPINE-as-is.md` §2-5. The **invariant**: a story closes only when (a) built TDD-first, (b) Chris exercised it live (G), (c) docs reconciled (R), (d) auditor verified the reconciled spec + gherkin matrix + ≥1 live write, (e) cap ledger + archive updated in the merge commit. **Verde / build / GET-200 ≠ done.**

| Hop | Owner | Gate(s) |
|---|---|---|
| idea → refining | Chris → `/pm-{brand}` | chris-input.md present from idea |
| refining → refined | refiner (per WT) → `/pm` closes | prior-art-scan · cap_target declared · (UI) Design-System-Canon |
| refined → ready | `/architect` | ready-package-complete (per WT) + `§ Integration design (CONN)` |
| ready → developing | `/dev-team` | WIP cap · repro-first (bugfix) |
| developing → developed | `/dev-team` | Phase-D-local coverage · **DoD live-verify (`dod_evidence`)** · ledger PISO |
| developed → [G] | Chris + `/dev-team` | **`chris_verify.signoff`** (unless `autonomous_mode`) |
| [G] → [R] → reviewing | `/pm-{brand}` | **`reconciled: true`** precondition |
| reviewing (audit) | `/auditor` (+ sub-auditors) | gate-output preflight · gherkin-MISSING-blocks · **LIVE_VERIFY_MISSING auto-FAIL** · verdict |
| reviewing → done | `/pm-{brand}` | merge-REFUSE conditions · cap ledger F.3 · **archive-on-done** (git mv, same commit) |

The spine keys all gates off **`verification_nature`** (técnica/funcional/ambas), never off the WT label — its core virtue.

---

## 3 · The 7 work-type profiles (the heart)

Each card = the **ratified** {lifecycle · refiner/actors · gates · artifacts · verification · cockpit-view · core/project/brand}. These are what the surface refactors (W1+) must implement.

### §3.0 · Requirement-taking doctrine (W0.5-bis · RATIFIED Chris 2026-06-08)

W0.5 ratified the refinement *skeleton*; **W0.5-bis ratifies HOW requirements are taken per input type** — the detail that **gates W2 (refinement skills) + W6 (spec templates)**. Full SSoT: **`REQ-TAKING-DETAIL.md`**. The cross-cutting doctrine (CORE):

- **Cardinal stance:** the refiner is **never a stenographer** — proposes, puts Chris in all cases, **improves what exists instead of reinventing**; contradicts when the ask strays from vision or lacks value. **Refinement is the #1 phase** (the live-GO failures trace to missed holes here).
- **Hat per input type:** UI → **PO/PM user-advocate** · service → PO functional-contract · technical → **CTO-to-CEO** (research SOTA + propose; Chris decides) · agentic → **agentic-architecture expert** (not a chatbot; bar = **no fake `if`s**) · bugfix → **observability-first** (*no error without observability = bad design*).
- **Intake = conversational** in Claude Code (not cockpit-first): the refiner, **as system designer**, agrees zona/caja + extends-or-new + tells Chris what already exists; the **story is born from that conversation**; every ask → **`chris-input.md` ledger**.
- **Interrogation:** **one question at a time · reflect-what-understood FIRST · concise · no-cave · human bullets**; obligatory always = **the role (with recommendation)**; always pull **internet references** (UI patterns / technical SOTA).
- **UI functional-first:** cement views/fields(new-vs-existing)/AC/business-rules in **human bullets (NOT Gherkin)** in a **live cockpit-editable doc** (agreed **comment-marker** for Chris's notes) → **then** the creative mockup (full shell + leaf + atoms, compose-from-canon, may improve on the text) → **Gherkin + business-rules + design-spec are GENERATED at the final sign-off**.
- **Scope:** refiner proposes the slice **critical-path-first, zero-loss** (overflow → its destination story) — **never re-ask what was already discussed**.
- **Signatures:** UI = 2 internal (functional → mockup) where **the 2nd is the single final** that triggers Gherkin + architect; no-UI = **one signature on the human-language behavior/contract**; Chris's **live GO (G)** is separate.

### WT1 · UI / functional capability — `ui-story`
- **Req-taking (W0.5-bis):** hat = **PO/PM user-advocate**; **functional-first then mockup**; live cockpit doc + comment-marker + chris-input ledger; 2 internal signatures → mockup-final = the single final. (→ `REQ-TAKING-DETAIL.md` §4-5,7)
- **Refiner:** `/po-ux` (PO+UX fused, **2-round/2-signature**: `input_spec_signed` → `mockup_final_signed` → executable). **Builder:** builder-frontend. **Sub-auditor:** auditor-frontend.
- **Verification:** `funcional`. **Gates:** demo gate (G) · anti-burbuja (`base.ts`) · **Design-System-Canon HARD** (compose-from-canon, see §5) · playwright-visual-scope.
- **Artifacts:** `01-spec` (+ `§ Wireframes` composed from canon) · mockup · `demo-script.md`. **`02-design-ui.md` is DEAD** (D-X2).
- **Cockpit:** `/board` + `/map` + **Cap Drawer (= the functionality home; no `/functionality` route)**.
- **Tier:** branch=CORE; design-system-canon/`@luana/ui-kit`/Clerk/dev-app = PROJECT/BRAND.

### WT2 · Service capability (no UI) — `service-story`
- **Refiner:** `/po` (+ inline prior-art-scan, parity with po-ux). **Builder:** builder-backend. **Sub-auditor:** auditor-backend.
- **Req-taking (W0.5-bis):** PO functional-contract hat; no visual layer; **one signature on the behavior/contract in human bullets**. (→ `REQ-TAKING-DETAIL.md` §8)
- **Verification:** `técnica` (auto-skip — works now that the canonical key is **top-level `verification_nature`**, D-X4). **Gates:** technical_gates (Schemathesis for new endpoints, Hypothesis for invariants). No demo, no anti-burbuja.
- **Artifacts:** minimal `01-spec`. **Cockpit:** `/board` + `/map`.
- **Tier:** branch=CORE; FastAPI/SQLAlchemy/toolchain = PROJECT.

### WT3 · Agentic — `agentic-story`
- **Req-taking (W0.5-bis):** hat = **agentic-architecture expert** (not a chatbot — tools/state/guardrails); Chris gives behavior intent, refiner interrogates + puts him in all cases + iterates tools/path; **propose without destroying, improve what exists**; signature = expected behavior in human language; **quality bar = no fake `if`s** (inherited by architect/auditor). (→ `REQ-TAKING-DETAIL.md` §8)
- **Refiner:** `/po` (spec, rich graders) → **`/ux-agentico`** (2nd pass, owns `02-design-agentic.md`); story stays `refining` until the design exists. **Builder:** builder-agentic (**newest Opus** §5; in-same-session; engine `core/luana-core-{copilot,sales-agent}/` off-limits → `/pm-luana` lift). **Sub-auditor:** auditor-agentic (**behavior changes never self-fixed** — Carril C: prompt slots/goldens/state-machine/voice).
- **Verification:** funcional live (real turn + `copilot_trace_event` traces) **+ pass^k eval gate**. **Gates:** pass^k · engine-boundary lift · prompt-slot integrity · observability-wrapper mandatory · `autonomous_mode` HARD-false.
- **Test plan (MF-22 fix):** owned by `/ux-agentico` in `02-design-agentic.md` — conversation branch-tree `{happy · out-of-scope · loop · recovery · injection · tool-failure} → {golden, rubric refs, tool-asserts, pass^k, persona}` → points at **`agentic-eval-policy.md` SSoT**. Architect's `04-validators` **references** it (no Playwright-shaped plan for agentic). Real eval = `pytest tests/agentic_evals/ --trials=3` (phantoms purged).
- **Artifacts:** `02-design-agentic.md` · eval goldens · `delta-spec.md`. **Cockpit:** `/board` + Diseño tab + `/arquitectura`.
- **Tier:** design-pass+eval-gate+engine-boundary = CORE; LangGraph/deepagents/Anthropic-cache/Qdrant/trace-tables/roster = PROJECT/BRAND.

### WT4 · Bugfix / hotfix — `bugfix`
- **Req-taking (W0.5-bis):** **observability-first intake** — Chris hands the error message/symptom; the refiner reads ALL logs + observability until root cause, then decides repro. **INVARIANT: an error with no observability = bad software design (a finding itself).** (→ `REQ-TAKING-DETAIL.md` §8)
- **Lifecycle:** lite — same 10 states, **lighter only on design, never on verification**. Reclassification escape (→ ui/service/agentic/technical if real design emerges before `ready`).
- **Refiner:** `/po` or `/po-ux` (lite mode — **both now list bugfix**). **Builder/auditor:** per surface.
- **Gates:** **repro-first, one SSoT, two altitudes** (story-level `repro_evidence.repro_verified`; ticket-level R26). **Repro evidence = `reproduced_local` OR `trace_evidence{source,ref}`** (docker-logs / Sentry / agentic conversation logs) — diagnosis grounded in evidence, not strictly local repro (§5). regression-RED-first · regression_guard intact.
- **Architect bugfix-lite mode:** `06-tickets` + `04-validators` always; `03-arch`/`05`/`dispatch` skippable when no arch decision; escape to full-arch or reclassify.
- **Schema:** canonical key **`repro_evidence`**; checkpoint gains top-level `type:`.
- **Cockpit:** `/board` with **🩹 badge + `repro_verified` indicator** (was invisible).
- **Tier:** lite-repair-lane + repro-doctrine = CORE; debugging runbook (containers/ports/alembic) + observability sources = PROJECT/BRAND.

### WT5 · Technical capability — `technical-story` ★ NEW
- **Req-taking (W0.5-bis):** hat = **CTO recommending to his CEO** — research SOTA on the internet + propose options with a recommendation; **Chris takes the big decisions**; spec analog = the contract-spec (no Gherkin). (→ `REQ-TAKING-DETAIL.md` §8)
- **Identity:** 5th first-class story type (infra / observability / security / performance; `user_visible: false`, Infraestructura zone).
- **Refiner: `/architect`** — the spec analog is a **contract-spec** (*contract/interface/extension-point provided · consumers · invariant enforced · verification-by-effect*), NOT a Gherkin behavior spec. **Owner opens:** brand-infra → `/pm-{brand}`; **core-infra → `/pm-luana`**. **Skips** po/po-ux/ux-agentico.
- **Net-new core infra** = `technical-story` `cap_change_type: new` targeting `core/` (the story IS the use-case justification — promotion's "no research in core" applies only to lifts). **Worktree:** core-targeting → ephemeral core worktree (`wip/core-{slug}`); brand-infra → brand hub.
- **Verification = `técnica`** (gates + **runtime evidence by effect**, no demo). Bar per sub-domain: encryption→decrypt round-trip · idempotency→replay dedup · observability→trace row · durable-flow→persist+resume · audit→audit row + access-denied. **Spec-first** (contract-spec RED-first) **except `nature: scaffold`** (exempt).
- **WT5 builds / WT6 lifts** — proposal-as-lifecycle retired; infra ships as a real technical-story (on `/board`, WIP-cap, closure-gate, archive).
- **Artifacts:** contract-spec (`new_cap.py` infra mode) · reduced ready-package. **Cockpit:** `tech` slot wired + in-flight visibility + Infra zone (not collapsed-only).
- **Tier:** the technical-cap lane + verification-by-effect = CORE; the infra inventory (durable-flows/LiteLLM/outbox/observability/`core/luana-core-*`) = PROJECT; PHI/HIPAA = BRAND.

### WT6 · Promotion (brand→core lift) — off-spine
- **Owner:** `/pm-luana`. **State machine:** `proposed → under_review → accepted → migrated/rejected` (+ **`deferred` documented**), **one SSoT** (kill README↔pm-luana dup). **Scope-discipline:** promotion = brand→core LIFT only (not a generic cross-brand-change tracker).
- **Gates:** anti-dup mirror-scan · **pre-edit WARNING** on `core/` without accepted proposal **+ auditor PR-time HARD** + **MF-02 fix** (YAML-frontmatter `state:` + schema-lint) · **explicit auditor/reviewing pass on the lift** · downstream-regression ∀ consumer · semver.
- **Artifacts:** proposal `.md` · engine package change · Extension-SDK registration · `docs/core-modules/{pkg}.md` (**hand-maintained** — `generate_core_modules.py` purged).
- **Cockpit:** **a lift board** (D6③) reading `proposals/` + `cap.license` transitions (was zero-surface). **Formalized as a first-class off-spine process.**
- **Tier:** the lift mechanism = CORE; `engine_prefix`/brand enum/EP catalog = PROJECT (seam).

### WT7 · Harness improvement — off-spine, dogfood
- **Owner:** `/pm-luana`. **Lifecycle:** HLP 5-state + **CIL 4 lanes** (L1 backlog · L2 learnings · L3 tech-debt · L4 cap-desfasada auto-detect). **Capture:** `/harness-issue`. **Stop:** `/harnesses-improvement` (deep-sweep = `harness-audit-2026` workflow).
- **Gates:** **never mid-feature** (HLP golden rule) · verify-first (auditoría-sobreestima) · ratifiable batches · Chris ratify · commit-by-pathspec · machinery-check. **One apply-pipeline SSoT** (reconcile HLP §6 ↔ skill). **Cross-walk** the two state vocabularies + document catalogue→HB-N mapping.
- **Cockpit:** `/harness` CIL monitor — **boardify L2/L4 in-place** (D6④) + lane badges.
- **Tier:** the HLP+CIL mechanism = CORE (any adopting product inherits it); HB content/learnings/cap-detections = PROJECT. **Confirmed: the second modeled process** (self-host).

---

## 4 · The seam-slot contract (the DIP contract for W5)

The CORE is written against these abstract slots; the PROJECT fills them. **RATIFIED (D-X5): charter's 7 + 2.**

| Slot | Replaces (the smear) |
|---|---|
| `toolchain.{lint,format,typecheck,test,migrate}` | ruff/pytest/mypy/tsc/eslint/vitest/alembic/`.venv/bin` literals |
| `brands[]` | `for B in nicolify vitalia comunify lupulo` loops |
| `locale` | the voseo / Spanish-neutro gate |
| `engine_prefix` | `core/luana-core-*` path literals |
| `live_verify_infra[]` (+ **`observability_evidence`** facet) | dev-app URLs/creds/ports in rule #37 **+ the docker-logs/Sentry/trace sources** for repro/diagnosis evidence (D4) |
| `design_system_ref` | the design-system-canon binding |
| `domain_modules[]` | offer/copilot/analytics/… as process assumptions |
| **`agent_roster`** ★new | cockpit `agent-meta.ts` rosters + `MapView` VITALIA_ROLES |
| **`value_stream`** ★new | cockpit `map-zones.ts` VALUE_STREAM_STAGES |

---

## 5 · Cross-cutting doctrine (ratified)

- **One SSoT per concern (D-X2):** WIP-cap → `story-closure-gate` (per-module) · story-closure-gate → fold G/R into one doc · demo-signoff → single `chris_verify.signoff` (`demo_signoff` retired; `dev_app_verified` = vitalia instance of generic `dod_evidence`) · `02-design-ui.md` DEAD · eval-policy → `agentic-eval-policy.md` · `/po` gains prior-art-scan · `outcomes/` purged from brand-docs-schema.
- **★ Design-System-Canon — HARD end-to-end (the refine→deliver pain):** the brand design-system (atoms/molecules + tokens + `@luana/ui-kit`, each brand re-skins) is the UI SSoT. **HARD gate at po-ux (compose from canon — never invent a primitive / break the system) · architect (03-arch refs canon + 04-validators mechanical gates) · dev (build from `@luana/ui-kit` — paddings/radius/fonts = tokens, never arbitrary) · auditor (reject non-composed).** NOT advisory. SSoT: `design-system-canon.md` + `ADR-014` + `frontend-visual-fidelity.md` D1. Seam: `design_system_ref`.
- **Phantom machinery purged (D-X3):** default = strike the dangling reference; agentic validators → real `pytest tests/agentic_evals/`; `graceful-degradation` skill → rule; `generate_core_modules.py` → hand-maintain; paper-rule enforcement (auditor "Cat 11", autonomous ⏳) → **implement-or-drop** (no paper rules).
- **Silent-killer fixes (D-X4):** canonical `verification_nature` = **top-level** · promotion `state:` = YAML-frontmatter + schema-lint · cockpit read-schema gains the v5 gate fields.
- **Repro = evidence, not just local (D4):** `repro_evidence: reproduced_local | trace_evidence{source,ref}` — CORE declares the abstraction, PROJECT fills the sources (DIP).
- **Verification-by-effect (D5):** `técnica` = gates + runtime evidence (read the effect/logs), no demo.
- **Newest-Opus for agentic (D3):** ux-agentico design + builder-agentic + auditor-agentic run on the strongest/newest model (CORE doctrine; PROJECT slot = "Opus 4.8 today").
- **Single-hub, no branch fragmentation (D3):** refine/build/audit skills run in the same canonical hub worktree on `wip/{brand}`; separate worktrees = exceptions only (lift core / hotfix / other brand).

---

## 6 · Conformance checklist (every W1+ surface validates against this)

A surface refactor (rule/skill/agent/hook/cockpit/template/process-doc) is **W0.5-conformant** iff:

1. **Implements its WT correctly** — the lifecycle states / gates / artifacts / verification-nature it touches match §1-3 (e.g. a refiner skill runs prior-art-scan; an architect emits the right reduced package per story type; a FE surface enforces Design-System-Canon).
2. **Tagged `tier: core | project | brand`** (drives the W7 physical move).
3. **Reads the seam, not hardcoded tech** — any toolchain/brand/locale/engine/dev-app/roster/value-stream reference goes through a §4 slot (DIP; `grep` tech-tokens in core-tier = 0).
4. **One SSoT** — no restating a concern that lives elsewhere; point instead (§5).
5. **No phantom machinery** — every cited script/skill/tool exists, or the reference is struck.
6. **No paper rules** — every enforcement claim has a real mechanism (hook/test/gate), or the claim is dropped.

---

## 7 · Cockpit contract (read-schema = CORE, render = PROJECT)

- **CORE = the read-schema:** `types.ts` shape (Story/Capability/SystemMap/ComputedStatus + `CHRIS_ALLOWED_TRANSITIONS`) + the file globs it reads. A new product must emit these for the cockpit to work. **Must add (D6①):** the v5 gate fields (`phase`/`chris_verify`/`reconciled`/`dod_live_verified`/`dod_evidence`) + the `bugfix`/`technical` story types + `repro_verified`.
- **PROJECT = the render** (`tools/luana-cockpit/` React views) + the rosters/value-stream/roles (→ `agent_roster`/`value_stream` slots).
- **Views ratified:** WT1-3 as-is · WT4 🩹 badge · WT5 `tech` + in-flight + Infra · WT6 **lift board** · WT7 `/harness` boardified L1-L4 + vocab legend · all WTs show the v5 gate badges.

---

## 8 · What W0.5 changed vs AS-IS (quick diff for implementers)

| Change | From → To |
|---|---|
| Story types | 4 → **5** (add `technical-story`) |
| WT5 technical | no process → **architect-refined contract-first lane** (build) + WT6 lift boundary |
| Phase vocabulary | 5 overlapping → **10 states + {G,R,C,D}** (product) · HLP-5 (harness) + legend |
| `02-design-ui.md` | live (8 refs) → **DEAD** (canon + spec-wireframes) |
| Design-System-Canon | partly advisory → **HARD end-to-end gate** |
| `verification_nature` | nested (silently broken) → **top-level** |
| Repro evidence | local-only → **local OR trace** (DIP seam) |
| Phantom scripts | cited, missing → **purged / pointed at real pytest** |
| demo-signoff | 3 names, 2 phases → **single `chris_verify.signoff` in G** |
| WT4 bugfix | cockpit-invisible → **🩹 + repro badge**; architect bugfix-lite mode added |
| WT6 promotion | zero cockpit, PR-time-only gate → **lift board + pre-edit warning + auditor pass** |
| WT7 harness | "needs view" (stale) → **boardify L2/L4 + vocab legend** |
| Seam slots | 7 → **9** (+ `agent_roster`, `value_stream`) + `observability_evidence` facet |

---

## 9 · Pointers

- `RATIFICATIONS.md` — the verbatim decision log (D-X2..D7).
- `AS-IS-MAP.md` + `as-is/*` — the AS-IS reconstruction (`file:line` detail, 50+ findings).
- `docs/process/harness-refactor-charter-2026-06-08.md` — the constitution (3-layer model, seam, roadmap).
- **Next:** W1 (rules) + W2 (skills) + W3 (agents) + W4/W4b (hooks/scripts/cockpit) — each validates its surface against §6 + implements its WT per §3. **No surface refactor starts until its process is conformant to this SSoT.**

*End PROCESS-MODEL.md — the W0.5 deliverable. Ratified Chris 2026-06-08.*
