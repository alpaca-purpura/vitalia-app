# W6 · Process-docs + Templates — Output (tier manifest + {SLOTS} + no-phantom verdict + conformance + Decision 3 + applied deltas + smoke + learnings)

**Date:** 2026-06-09 · **Session:** harness-refactor W6 (C-phase · STRUCTURAL · first structural WS post B-phase) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` (precedent: W0/W0.5/W0.5-bis/W1/W2/W3/W4/W4b HEAD here) · **Status:** APPLIED + cemented (path-stable + 2 grep-gated legacy moves).

> **North-star card:** *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens (the rest went to the seam). The goal is an extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*
>
> Charter §6 W6 done-when: *docs/templates tagged; generic vs luana.* Inputs: `PROCESS-MODEL.md §1,§3,§5,§6,§7` (10-state+{G,R,C,D} · one-SSoT · conformance checklist · cockpit read-schema) + `REQ-TAKING-DETAIL.md §10` (01-spec functional-first inversion) + charter §0.5 (option-b proxy) + `DECISIONS-PENDING.md` (3 ratified). **Per-file detail is pointer-first in the 3 RESEARCH siblings (`RESEARCH-batch-{T,P1,P2}.md`) — not duplicated here.**

---

## 0 · Scope + headline result

Scope = `docs/specs/templates/` (**26 templates**) + `docs/process/` (**37 top-level .md** + 4 subdirs). **Excluded** (out of W6 — refactor program's own meta-docs, governed at W9/W10): `harness-refactor-charter-2026-06-08.md`, `harness-refactor-w*/` subdirs, `harness-rules-audit-2026-06-08.md`. 3 Opus subagents classified read-only (Batch T templates · P1 live-SSoT docs · P2 runbook/archaeology); I owned the substantive judgment edits + Decision 3 + validation.

**Headline:** the templates + process-docs surface is **structurally sound** — the v5/W0.5 SSoT process-docs are CURRENT (they ARE the ratified outputs), and the templates already implement most of the spine. The real W6 work was the **classic propagation gap** (B-phase learning #1): the `spec-mapa-funcional.md` SSoT moved (W0.5-bis functional-first inversion), and the **`01-spec-template.md` lagged**; ditto `02-design-ui` DEAD / `demo_signoff`→`chris_verify` / `v4.2`→v5 / `phase_workflow` X6-retired scattered across templates. Tier shape mirrors W1→W4b: **core RARE + proxy-EARNED** (templates 6, process-docs P1 7), **brand ≈ 0** (OCP). **Decision 3 verify-first WIN:** its premise was **partly stale** (CHECK 11 already asserted G8/G9 since 2026-06-05) → implemented only the genuinely-needed parts (OCP registry-derivation + doc G8/G9), did **not** Frankenstein a fix for a non-problem.

**Validated after every edit (W1 non-negotiable):** `make machinery-check` **65 · 0 · 0** · `scan_harness_pointers.py` **NEW 0** (baseline 28) · edited validator ruff-clean · 04-validators/06-tickets YAML re-parse OK · CHECK 9/25/27 string-presence smoked on root + vitalia override · cap-gates registry still derives G1-G9.

> **machinery count 73→65 is EXPECTED + correct, not a regression:** Decision-3a refactored CHECK 11 from a frozen `("g1".."g9")` literal (20 sub-checks: 9 def-presence tautologies + 9 test + dispatcher + repro) to an OCP registry-derivation (12 sub-checks: floor + dispatcher + dispatch-match + 9 per-gate dispatch+test + repro). Fewer-but-stronger sub-checks, equal-or-better coverage (deletion caught by floor, addition auto-covered). No `73` is asserted anywhere (grep-verified); the invariant is **0 fallos**, which holds.

---

## 1 · Tier manifest (drives W7) — templates + process-docs

**Option-b proxy (charter §0.5, ratified):** `tier:core` EARNED only if the dependency-grep (`vitalia|nicolify|comunify|lupulo|ruff|pytest|mypy|alembic|clerk|next|tailwind|fastapi|sqlalchemy|core/luana-core|.venv|dev-app|hipaa|phi`) = **0 hits** (read hits in context — generic build-artifact names ≠ smear). Any token ⇒ `hybrid`. Full per-file tables in `RESEARCH-batch-{T,P1,P2}.md`.

### 1a · Templates (26) — `RESEARCH-batch-T.md`

| tier | count | files |
|---|---|---|
| **core** (proxy-clean skeleton) | **6** | `00-chris-input`, `00-research`, `00-story`, `01-spec` (body ex-inversion), `story-ui.yaml`, + (00-story/story-ui are placeholder-only) |
| **hybrid** (artefact SHAPE portable + project tokens → seam) | **18** | `02-design-agentic`, `03-arch`, `04-validators`, `05-guidelines`, `06-tickets`, `07-merge`, `checkpoint`, `demo-script`, `dispatch-plan`, `release`, `REVIEW-final`, `story-agentic.yaml`, `story-service.yaml`, `T-handoff`, `T-impl-log`, `T-result`, `T-review`, (+ `02-design-ui` post-tombstone) |
| **dead-tombstone** (DEPRECADO grave-headers · W9-delete) | **4** | `02-design-ui-template.md`, `PI-template.md`, `sprint-template.md`, `ticket-template.yaml` |
| project / brand | **0 / 0** | (brand overrides live at `{brand}/docs/specs/templates/` — out of root scope) |

### 1b · Process-docs (P1 live-SSoT 18 · P2 runbook/archaeology 17 + subdirs)

| group | core | hybrid | note |
|---|---|---|---|
| **P1 live-SSoT** | **6** (+INDEX) | 11 | core = `cockpit-permissions`, `continuous-improvement`, `harness-lifecycle`, `tech-debt`, `ticket-states`, `spec-mapa-funcional`, `INDEX`. The 6 hold portable doctrine; the 11 hybrids carry brand/toolchain/`engine_prefix` tokens. |
| **P2 runbook/archaeology** | **0** | 17 | all luana-stack ops or dated luana-history (runbooks naming `make dev-vitalia`/ports/`.venv`). 2 clean legacy-moves (§3). |
| **subdirs** | — | — | `audits/` (anchors a live machinery-gate provenance · keep) · `legacy/` (cooling window) · `metrics/` (LIVE write-target) · `tech-debt/` (uncited Apr-2026 archaeology · ≠ the live `tech-debt.md` file — naming collision flagged) |

**Same law as W1→W4b** (rules 18 core → skills 0 → agents 1 → hooks 5 → scripts ~6 → **templates 6 / process-docs 7**): the portable IP is the *artefact SHAPE / doctrine SKELETON*; every template that bakes in `ruff`/`pytest`/`.venv`/alembic/clerk/dev-app/brand-enum/`core/luana-core-*` is `hybrid` by construction.

### 1c · {SLOTS} mapping — manifest-authoritative (NOT inline-churned · the one-SSoT decision)

The per-template/per-doc seam-slot dependency is recorded in the **RESEARCH-batch `{SLOTS} needed` columns** (the authoritative record W5 wires from + W7 moves by). **Decision: NOT duplicated inline into 26+ files as `{slot}` header comments.** Rationale (charter's own principles): (a) **one-SSoT / high-cohesion** — the slot↔token mapping has ONE home (this manifest); inlining it into every template = a second store of the same mapping (the exact anti-pattern the charter forbids); (b) **option-b** (charter §0.5) — "a token-carrying file is re-tagged `hybrid`, NOT rewritten to `{slot}` notation now; the seam wiring stays W5"; (c) **W4b precedent** — explicitly chose manifest-authoritative over file-by-file inline-tag churn ("cockpit NOT inline-tagged file-by-file … this manifest is authoritative for W7"); (d) **YAML-safety** — half the templates are `.yaml` where an HTML-comment slot-header would break parse. The bootstrap's "templates reference the slot names now" is satisfied by the manifest **naming the slots per template** — the dependency is DECLARED, in the single place W5 reads. **Most-smeared slots** (W5 #1 lift): `brands[]` (the recurring enum/loop), `toolchain` (ruff/pytest/mypy/tsc/eslint/vitest/alembic/`.venv`), `engine_prefix` (`core/luana-core-*`), `live_verify_infra` (dev-app/ports/clerk/hipaa), `design_system_ref` (canon/`@luana/ui-kit`/SHELL-DESIGN-CONTRACT), `agent_roster`, `domain_modules[]`. `value_stream` = cockpit-only (no template carries it).

---

## 2 · No-phantom / no-paper-rules verdict (deliverable b · PROCESS-MODEL §6.5/§6.6)

`test -e`-verified every cited script/path/template/rule across the surface (3 subagents + my re-checks). **Mechanically sound** — the dead refs found:

| # | Dead/phantom ref | Where | Verdict / action |
|---|---|---|---|
| 1 ★ | `02-design-ui.md` (DEAD artifact · D-X2) cited as LIVE FE input | `03-arch-template:14`, `06-tickets-template:357` | **FIXED** → `01-spec.md § Wireframes` (the W3 finding for these 2 exact files). |
| 2 ★ | 5 phantom agentic eval scripts `scripts/{run_agent_evals,run_trajectory_eval,check_cost_budget,check_voice_fidelity,run_adversarial_suite}.py` (all self-`# MISSING`, absent) | `04-validators-template:240,253,261,273,291` | **FIXED** → real `pytest tests/agentic_evals/{m}/{story-id}.py -k {dim}` (D-X3 "agentic validators → real pytest"; the real dir exists vitalia+comunify; other templates already use it) + section banner pointing at the SSoT (`02-design-agentic.md` owner + `agentic-eval-policy.md`). `# MISSING` count now **0**. |
| 3 | `scripts/scan_cross_brand_mirror.sh` (self-`# MISSING`, absent) | `04-validators-template:321` | **FIXED** → real inline basename-collision grep (anti-duplication.md Step-0 pattern) + cite auditor Cat 12 / architect pre-builder (the real enforce). |
| 4 | `validate_chris_input.py` ("opcional") · `generate_release_notes.py` ("futuro") | `chris-input-protocol:210` · `release-protocol:178`/`lifecycle:202` | **LEFT (honest forward-refs)** — self-flagged optional/future, NOT presented as existing → not misleading phantoms. Build-or-strike = a future call (lifecycle #9 punch-list owns it). |

**Consumer wiring verified (not producer self-description, W1 learning):** CHECK 9 parses `01-spec-template` + the vitalia override (both green post-inversion); CHECK 2 (06-tickets assignment), CHECK 4 (dispatch-plan), CHECK 14 (checkpoint chris_verify), CHECK 19 (04-validators mutation), CHECK 25/27 (01-spec) — all survive (string-presence re-smoked). The 2 legacy-moved handoffs had **0 live citations** (grep-gated, §3).

---

## 3 · Process conformance (deliverable c · stale caught/fixed + functional-first 01-spec)

Method = the B-phase propagation-grep: grep the IMPLEMENTING templates/docs for the OLD token of every ratified-retired concept. **The v5/W0.5 SSoT process-docs are CLEAN** (faithful — they ARE the ratified outputs). Stale clustered in the **templates** (SSoT moved, template stayed) + 3 process-docs.

### 3a · `01-spec-template.md` — functional-first inversion (REQ-TAKING §10 · the headline)

The SSoT `spec-mapa-funcional.md` already had the W0.5-bis structure (§ Pantallas field-table + § Mockup FINAL before Gherkin + RONDA-2-GENERADA); **the template lagged** (mockup-borrador in RONDA 1, no § Pantallas, no § Mockup FINAL, no comment-marker, Gherkin framed as authored). **FIXED (surgical insertion + annotation, NOT rewrite):** (a) `> 🗨️ CHRIS:` comment-marker convention note; (b) removed the RONDA-1 mockup-borrador + "sin mockup en RONDA 1" note; (c) added **`§ Pantallas` (campos NUEVOS vs EXISTENTES · SIN mockup)** to RONDA 1; (d) added **`§ Dudas abiertas` (RONDA 1)**; (e) inserted **`§ Mockup FINAL` (compose-from-canon · BEFORE Gherkin)** opening RONDA 2; (f) "**GENERADO en FIRMA 2**" banner on the Gherkin/Matriz/business-rules. **PRESERVED** every machinery-asserted string: CHECK 9 (`Mapa funcional`/`Matriz de cobertura`/`FIRMA 1`/`FIRMA 2` — smoked on root + vitalia override), CHECK 25 (`LEDGER DE COBERTURA VIVO`/`✅ construido`), CHECK 27 (`PISO HARD`/`cap_change_type`).

### 3b · Stale-vocab in templates — caught + fixed

| token | files | action |
|---|---|---|
| `demo_signoff` (→ `chris_verify.signoff` in G · D-X2/§5) | `demo-script:31` (live block), `dispatch-plan:45,47` (REFUSE keys), `spec-mapa-funcional:129` | **FIXED** — point at `checkpoint.md::chris_verify.signoff` (G, before auditor); result values `APPROVED/APPROVED_WITH_NOTES`→`SATISFIED/SATISFIED_WITH_FOLLOWUPS` (the v5 values). |
| `phase_workflow`/`PO_SPEC`/A-F letter-phases (X6-retired) | `checkpoint:18` (live field), `checkpoint:78-93` (A-F table) | **FIXED** — `phase_workflow` demoted to `null`+DEPRECADO note (live phase = `phase` field + {G,R,C,D}); A-F table relabeled HISTÓRICO/NOT-operator-facing. CHECK 14 block untouched. |
| `v4.2` (auditor self-fix → v5 Responsable) | `dispatch-plan:14`, `T-review:5,10` | **FIXED** — v5 Carril R (default fix-and-own + TDD + live-verify, can write tests) + Carril C/C' stake-asimétrico + Caveat AGENTIC; caps `responsible_fix_iter<=6`. |

### 3c · Process-docs LIVE-STALE — fixed

| doc | gap | action |
|---|---|---|
| `lifecycle.md:50` | WIP-cap "≤1 **por worktree**" (X6/D-X2 purged) | **FIXED** → "≤1 por `code:{module}` bucket" + exime AWAIT_CHRIS_VERIFY/defer_audit + pointer to {G,R,C,D}. |
| `story-closure-gate.md` (rationale doc) | pre-v5 **6-phase A-F**, no G/R/`chris_verify`/`reconciled` | **FIXED (conform, not rewrite)** → v5 banner + TL;DR now names G/R/`chris_verify.signoff`/`reconciled`; declares the live SSoT = the hard rule (machinery CHECK 13-18) + `PROCESS-MODEL §1-2`. |
| `spec-mapa-funcional.md:129` | `demo_signoff` (→ `chris_verify.signoff`) | **FIXED** (see 3b). |
| `INDEX.md` | missing 5 live SSoT rows (cohesion gap) | **FIXED** → added `cap-deterministic-enforcement`, `code-health-gate`, `continuous-improvement`, `tech-debt`, `contributing`. |
| `pm-redesign-2026-05.md` (12-citer · P2 F1) | DEAD `02-design-ui` + purged `outcomes/` in its artifact-template | **FIXED (non-destructive, P2 option-a)** → SUPERSEDED-vocab banner pointing at the live SSoTs. The 12-citer **repoint (option-b) = FLAGGED for Chris** (don't silently rewrite a 12-citer doc). |

---

## 4 · Decision 3 — IMPLEMENTED with a verify-first correction (deliverable d · ratified W6)

**The ratified premise was partly STALE** (verify-first, the posture). DECISIONS-PENDING D3 (from W4b) claimed "CHECK 11 does NOT individually assert G8/G9". **VERIFIED FALSE:** `validate_machinery_consistency.py` CHECK 11 already iterated `("g1".."g9")` since commit `c77793f3` (2026-06-05, "F2a cap-levels — gates G8/G9 de PRESENCIA") — both gate-def AND negative-test, for all 9. W4b misread it. **Implementing "add G8/G9 assertion" would have been a Frankenstein fix for a non-problem.** Re-scoped to what was GENUINELY needed:

- **D3a OCP — IMPLEMENTED.** CHECK 11's frozen literal `("g1".."g9")` → **derive** the gate set from `re.findall(r"def gate_(g\d+)_", bidir_src)` + the `run_cap_gates` dispatcher keys, with a **floor `EXPECTED_MIN_CAP_GATES = 9`**. A future **G10** is now auto-covered (add gate + dispatch + `test_g10_red` → CHECK 11 exige it, no CHECK edit); deletion below the floor trips; defined-vs-dispatched mismatch trips. **Smoke:** derivation computes `[G1..G9]`, floor≥9 ✓, defined==dispatched ✓.
- **D3b doc-lag — IMPLEMENTED.** `cap-deterministic-enforcement.md` documented only **G1-G7** ("7 gates", no G8/G9 rows) while code had g1..g9. Added **G8/G9 rows** (visible-tiene-descripción / visible-tiene-scenario · PRESENCIA forward-looking) + updated "7 gates G1-G7"→"9 gates G1-G9" (×3) + the anti-rot note now documents the OCP derivation.
- **D3c the stale premise — REPORTED (no-op).** CHECK 11 already asserted G8/G9; nothing to add there.

**D1 (Stop-hook caps) + D2 (shared hook source)** — ratified to **register, implement at W5 / W7** respectively (see `DECISIONS-PENDING.md` header). No W6 code change; recorded.

---

## 5 · Applied changes + smoke evidence (deliverable d)

**~13 surfaces touched · all path-stable except 2 grep-gated legacy moves. Zero logic risk to live gates (each smoked).**

- **Decision 3 (2 files):** `validate_machinery_consistency.py` CHECK 11 OCP-derivation + `cap-deterministic-enforcement.md` G8/G9 doc. **Smoke:** derivation→G1-G9 · ruff clean · machinery 65/0/0.
- **Dead-ref repoints (3 templates):** `03-arch:14` + `06-tickets:357` (02-design-ui→Wireframes); `04-validators` (5 phantom scripts→`pytest agentic_evals` + mirror-scan→inline grep + banner). **Smoke:** YAML re-parse OK · 0 `# MISSING` left · CHECK 2/19 survive.
- **Stale-vocab (4 templates):** `checkpoint` (phase_workflow/A-F demote · CHECK 14 intact) · `demo-script` (demo_signoff→chris_verify) · `dispatch-plan` (demo_signoff + v4.2) · `T-review` (v4.2→v5). **Smoke:** machinery 65/0/0.
- **01-spec inversion (1 template):** functional-first per §3a. **Smoke:** CHECK 9 (4 concepts root+override) + CHECK 25/27 all green.
- **Process-docs (5):** `lifecycle` (WIP-cap) · `story-closure-gate` (v5 banner+TL;DR) · `spec-mapa-funcional` (demo_signoff) · `INDEX` (+5 rows) · `pm-redesign` (SUPERSEDED banner). **Smoke:** machinery 65/0/0 (none machinery-asserted as a body except via the v5 RULE, which is untouched).
- **Archaeology (2 git mv + 1 README):** `cap-deterministic-enforcement-HANDOFF.md` + `HANDOFF-cap-levels-cockpit-2026-06-06.md` → `docs/process/legacy/2026-06-09/` (grep-gated 0 live citations) + provenance README.

**Final validate-after-apply:** `make machinery-check` **65 · 0 · 0** · `scan_harness_pointers.py` **NEW 0** (baseline 28→28; moves had 0 pointer refs) · validator ruff-clean · 04-validators/06-tickets YAML OK · cap-gates registry G1-G9.

---

## 6 · Findings deferred / for downstream WS (honest scope)

- **W5 seam:** wire the manifest's per-file slots (`brands[]` #1 + `toolchain` + `engine_prefix` + `live_verify_infra` + `design_system_ref` + `agent_roster` + `domain_modules[]`) into `project.config.yaml` + repoint the templates' hardcoded tokens. **D1 (Stop-hook cap NUMBERS → `wip_caps` slot)** lands here.
- **W7 physical move:** the 6 core templates + 7 core process-docs → `core-harness/`; the hybrids' project-half behind the seam; `02-design-ui`/`PI`/`sprint`/`ticket-template` (dead-tombstone) are W9-delete. **D2 (canonicalize shared hook source on `main` + fix `install-hooks` `$TOP`→stable)** lands here.
- **W9 legacy delete:** `docs/process/legacy/2026-06-09/` (2 handoffs) + the 4 dead-tombstone templates + `tech-debt/` subdir (uncited Apr-2026 archaeology) — after W8.
- **FLAGGED for Chris (process decisions, not unilateral W6):**
  1. **`MANDATORY_SPEC_CONCEPTS` extension** — adding `§ Pantallas`/`§ Mockup final` to the CHECK-9 gate would **break the vitalia shell-override** (a shell story legitimately uses §3 Atomic Design / §4 Reuse Map, not a field-table). Decision: per-story-type MANDATORY sets, or leave as-is. (The root template HAS the sections; the gate just doesn't force them on shell overrides.)
  2. **vitalia shell-override own W0.5-bis lag** — `vitalia/docs/specs/templates/01-spec-shell-template.md` ALSO has "mockup BORRADOR in RONDA 1" (same lag the root just fixed). Brand-tier → `/pm-vitalia` or a follow-up should conform it.
  3. **`pm-redesign` 12-citer repoint (option-b)** — repoint the 12 skill citations from `pm-redesign-2026-05.md` → `lifecycle.md`/`PROCESS-MODEL.md` + demote `pm-redesign` to pure archaeology. (W6 added the non-destructive banner; the repoint is the deeper fix.)
  4. **borderline archaeology pairs (P2 F3)** — `REVIEW-process-v5` + `process-improvements-2026-05-05-investigation` are 0-live-mechanism-cited but pair with still-cited siblings; legacy-move the whole pair/set together or not at all (Chris call).
  5. **phantom forward-refs** — `validate_chris_input.py` / `generate_release_notes.py`: build or strike (lifecycle #9 punch-list).

---

## 7 · Learnings (charter §5 step 7 → feed §7)

1. **Verify-first caught a ratified-but-stale premise — and saved a Frankenstein.** Decision 3 was ratified by Chris on a W4b finding ("CHECK 11 doesn't assert G8/G9") that `git blame` proved FALSE (the F2a commit added g8/g9 to the loop 2026-06-05). "Implementing" it would have re-added existing assertions. *Lesson: a ratified decision can carry a stale premise from the audit that surfaced it; verify the premise against the CURRENT code (git blame the exact line) before implementing — the posture's "verify what was done well first" applies even to your own ratified worklist. Re-scope to what's genuinely needed (here: the OCP improvement + the doc-lag, both real), report the stale third.*
2. **The propagation gap is the dominant W6 finding — same as W2/W3/W4b.** The v5/W0.5 SSoTs were clean; the TEMPLATES that implement them lagged (`spec-mapa-funcional` inverted → `01-spec-template` didn't; `02-design-ui` DEAD → 03-arch/06-tickets still cited it; `demo_signoff`/`phase_workflow`/`v4.2` retired → templates kept them). *Lesson reconfirmed across 5 workstreams: when a doctrine is ratified, grep the IMPLEMENTING surface for the OLD token — the SSoT never propagates itself. The fix is almost always "doc moved, implementer stayed."*
3. **A machinery gate can already cover what a stale audit says is missing — and a literal anti-rot list is the anti-pattern.** CHECK 11's frozen `("g1".."g9")` tuple already covered G8/G9, but it would NOT have covered a future G10. The OCP fix (derive the set from the registry + a floor) is the durable answer: anti-rot meta-checks should iterate the registry, never freeze a literal. *Lesson: a frozen-list meta-check is itself the rot it's meant to prevent; derive-from-registry + a floor (for deletion) is the OCP form.*
4. **One-SSoT beats the literal bootstrap ask when they conflict.** The bootstrap said "templates gain `{SLOT}` placeholders now"; option-b said "no `{slot}` rewrite until W5". Reconciled by recording the slot↔token mapping ONCE in the manifest (what W5 reads) rather than duplicating it inline into 26 files — which would have been a second SSoT (the exact anti-pattern the charter forbids) + risked YAML breakage. *Lesson: when an instruction would force a second store of a mapping, the charter's own one-SSoT principle wins — the manifest IS the declaration; "reference the names" ≠ "duplicate the mapping into every file".*
5. **`tier:core` for templates/process-docs holds the law (rules 18→skills 0→agents 1→hooks 5→scripts ~6→templates 6/docs 7).** The portable IP is the artefact SHAPE / doctrine SKELETON; a template that bakes a stack tool or brand enum is `hybrid`. Process-docs are the most core-heavy non-rule surface (they hold doctrine), but still only 7 earn it — the rest carry `engine_prefix`/toolchain/brand tokens. *Cohesion lesson reconfirmed: extract the shape/doctrine, rewrite the project instance per product.*

---

## 8 · Pointers

- `RESEARCH-batch-{T,P1,P2}.md` (siblings) — full per-file tables (tier/proxy/stale/phantom/{SLOTS}/machinery-asserted) + per-finding prose. **Pointer-first: not duplicated above.**
- `docs/process/harness-refactor-charter-2026-06-08.md` §0.5 (option-b proxy) · §3 (seam slots) · §4 (fitness) · §6 (roadmap · W6 done-when) · §7 (B-phase learnings).
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md` §1 (10-state+{G,R,C,D}) · §3 (WT cards) · §5 (one-SSoT) · §6 (conformance) · §7 (cockpit read-schema).
- `docs/process/harness-refactor-w0.5/REQ-TAKING-DETAIL.md` §10 (the 01-spec inversion this implements).
- `docs/process/harness-refactor-w4b/DECISIONS-PENDING.md` — the 3 ratified decisions (header records the ratification).
- `docs/learnings/tooling/2026-06-08-harness-refactor-stub-against-the-gate.md` — validate-after-apply + verify-the-consumer (applied verbatim).
- **Next:** B-phase + W6 done. Structural tail: **W5 (seam `project.config.yaml` + wire · implements D1) → W7 (physical move · implements D2) → W8 (extraction test) → W9 (legacy delete) → W10 (governance)** — each Chris-ratified, NEW conversation anchored to the charter (HLP · NEVER auto-run). Open B-phase tail: W1-Phase2 (Tier-3 eviction) + Tier-2 `paths:` (#16299).

*End W6-OUTPUT.md — machinery 65/0/0 · pointer NEW 0 · 26 templates + 37 process-docs tagged · 01-spec inverted functional-first · 4 dead-refs fixed (02-design-ui ×2 + 5 phantom agentic scripts + mirror-scan) · 6 stale-vocab fixed · Decision 3 implemented (verify-first re-scoped) · 2 archaeology → legacy · 5 process decisions flagged for Chris.*
