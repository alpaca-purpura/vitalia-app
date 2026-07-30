# W2 · Skills — Output (tier manifest + applied changes + REQ-TAKING conformance + learnings)

**Date:** 2026-06-08 · **Session:** harness-refactor W2 (B-phase) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` (precedent: W0/W0.5/W1 HEAD here) · **Status:** APPLIED + cemented (path-stable).

> **North-star card:** *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens (the rest went to the seam). The goal is an extractable `core-harness/`, not a nicer luana harness.*
>
> Charter §6 W2 done-when: *no dup/drift · process-vs-domain split · refinement conforms to W0.5-bis · machinery-check green · proxy-clean core tags.* Inputs: `PROCESS-MODEL.md §3,§6` + `REQ-TAKING-DETAIL.md §10` (the gate) + `spec-mapa-funcional.md` + W1 precedent (option-b proxy).

---

## 0 · Scope + headline result

Scope = `.claude/skills/` (49 real dirs + 15 vendored plugin symlinks `clerk-*`/`sentry-*` = out of extraction). **All work this session is PATH-STABLE** (stub-in-place / depopulate / dedup-by-pointer / additive sections); zero file moves, zero enforcement-machinery risk. The instruction-doc mis-housing (`architect-be/fe/agentic`) + any physical move = deferred to W7 (coordinated, machinery-asserted — see §5).

**Validated after every apply** (W1 non-negotiable): `make machinery-check` = **73 checks · 0 fallos · 0 advisory** · `scan_harness_pointers.py` = **NEW 0**, at every checkpoint.

**Headline:** the 5 refinement surfaces (po-ux/po/ux-agentico/architect/pm-{brand}) now **conform to W0.5-bis** (functional-first inversion · 1-question protocol · CTO-to-CEO technical lane · observability-first bugfix · intake-handshake). Dedup removed **~280 lines** (chris-input block, 10 skills → 1 SSoT pointer). Depopulated **6 phantom PMs** (~1,200 lines of rotting body → 30-line stubs). Marker decision **ratified with Chris** (`> 🗨️ CHRIS:` blockquote).

---

## 1 · Tier manifest — `tier: core | project | brand | hybrid` per skill (drives W7)

**Key insight (option-b proxy, charter §0.5):** skills are **far more project-smeared than rules**. The CORE process doctrine already lives in process-docs (`PROCESS-MODEL`, `REQ-TAKING-DETAIL`, `lifecycle`, `story-closure-gate`); the spine skills are the **PROJECT instances** of that doctrine (they name brands, toolchain, dev-app, Clerk, canon, `core/luana-core-*` on nearly every screen). Per option-b, **a skill carrying project tokens is `hybrid`, never proxy-clean `core`**. Proxy evidence: po-ux 37 token-lines · architect 50 · po 23 · ux-agentico 10 — **none proxy-clean**. So the skill layer has **zero `core`-tagged files**; the genuinely-portable half is the doctrine in process-docs (W6) + the generic role skeleton to extract at W7. This is the honest separation: *a new product writes new skill instances against the same process-docs.*

### Spine / process skills — **hybrid** (core role-skeleton + project instance; seam at W5/W7)

| Skill | core half (portable) | project/brand half → seam slot |
|---|---|---|
| `po-ux` | refinement role · functional-first · 1-q protocol · cardinal stance · signatures | brands enum · Shadcn/Tailwind · `@luana/ui-kit`/canon (`design_system_ref`) · dev-app (`live_verify_infra`) · español (`locale`) |
| `po` | service-contract role · observability-first bugfix doctrine · 1-q protocol | toolchain (`pytest`/`.venv`) · `core/luana-core-*` (`engine_prefix`) · obs sources (`live_verify_infra.observability_evidence`) |
| `ux-agentico` | agentic-architecture-expert hat · no-fake-`if`s bar · improve-not-destroy | LangGraph/deepagents/Anthropic-cache/Qdrant · roster (`agent_roster`) · `domain_modules[]` |
| `architect` | ready-package role · WT5 CTO-to-CEO technical lane · CONN/anti-orphan | toolchain · `engine_prefix` · brands · canon · cap-locator (`resolve_cap.py`) |
| `dev-team` | autonomous-build role · TDD · G-pause · DoD live-verify | toolchain · brands · dev-app · agentic Opus routing |
| `auditor` | review role · self-fix v5 · reconciled precondition · gherkin Phase D | toolchain · brands · `engine_prefix` · domain sub-auditors |
| `pm-luana` | portfolio + **promotion (WT6 lift)** + core-engineering role | `engine_prefix` · EP catalog · brands enum |
| `pm-vitalia · pm-nicolify · pm-comunify · pm-lupulo` | brand-PM role · 10-state spine · G/R · intake-handshake · Fase F.3 | brand paths/`brand.yaml`/dev-app/compliance (vitalia HIPAA-lite = **brand**) |
| `_pm-brand-template` | the LSP source-of-truth for the PM body | luana paths in the scaffold |
| `pm` | alias pointer → pm-luana | luana naming |
| `architect-be · architect-fe · architect-agentic` | the 03-arch section-contract (what each surface must contain) | FastAPI/SQLAlchemy · FSD/Shadcn · LangGraph/cache — **mis-housed as skills** (instruction-docs loaded by-path; W7 → `architect/references/`) |
| `harness-issue · harnesses-improvement` | **WT7 HLP+CIL** mechanism (any product inherits) | HB paths · cockpit `/harness` · luana CIL lanes |
| `commit-push · handoff · worktree-protocol · pase-produccion` | git/parallel/handoff patterns (core doctrine) | triple-branch paths · brands · `make ci-parity` |

### Domain skills — **project** (stack/vertical-specific; rewrite per product)

`backend-expert` · `frontend-expert` · `brand-expert` · `offer-expert` · `offer-type-preset-expert` · `copilot-expert` · `sales-agent-expert` · `metrics-expert` · `brand-offer-auditor` · `content-hunter` · `data-storyteller` · `manychat-expert` · `playwright-expert` · `chrome-devtools-verify` · `ai-docs` · `tessl-context` (vendored tooling — staleness candidate, see §5). Seam: `domain_modules[]` / `toolchain` / `design_system_ref`.

### Brand skills — **brand** (market-instance UI SSoT)

`vitalia-design-system` · `nicolify-design-system` — instances of the `{brand}-design-system` class. Seam: `design_system_ref` + `agent_roster`. Adding a brand-DS = config (OCP), never edits another brand.

### Pre-bootstrap placeholders — **project** (depopulated this session)

`pm-saasora · pm-inmoflow · pm-retailly · pm-fixia · pm-guestly · pm-fitflow` — 30-line stubs pointing at `_pm-brand-template`; bodies materialize at bootstrap.

### Tombstones — **project** (deprecated redirects; drop at W9)

`ux-disruptivo · ux-flow-architect → /po-ux` · `git-manager → /commit-push`. Already `disable-model-invocation: true` + `user-invocable: false`. Harmless redirects; leave for discoverability until W9.

### Vendored plugins — **out of extraction** (symlinks, not tagged for move)

`clerk` + 11 `clerk-*` · 3 `sentry-*` — external plugin installs (symlinks into plugin cache). A new product installs its own. Not part of `core-harness/`.

**Counts:** hybrid **~24** (spine/process, project-half parked → seam W5/W7) · project **~24** (domain 16 + 6 phantom + 3 tombstone − overlaps) · brand **2** · vendored-out **15**. **core (proxy-clean) = 0** — the portable doctrine lives in process-docs, not in the skill bodies (this is the correct separation, not a gap).

---

## 2 · Applied changes (path-stable)

### A · Refinement conformance to W0.5-bis (the heart)

- **`po-ux`** — (1) added **Postura cardinal** (never-stenographer · contradict-on-value · improve-not-reinvent · refinement-is-phase-#1). (2) **Replaced** the old "batched 3-5 questions" section with the ratified **Interrogatorio: 1-question-at-a-time / reflect-first / no-cave / human-bullets / role-obligatory / internet-refs** (the old pattern directly *contradicted* W0.5-bis). (3) **Inverted** the 6-step flow to **functional-first / mockup-after** (killed "mockup borrador en RONDA 1"); mockup now born AFTER firma-1 functional; **Gherkin GENERATED at firma-2**, not hand-authored. (4) Locked the **`> 🗨️ CHRIS:`** comment-marker + live-doc + chris-input-from-creation. (5) anti-patterns + § Wireframes + § Gherkin notes updated.
- **`po`** — Postura cardinal + sombrero-por-tipo table + the 1-question Interrogatorio (removed batched section); **bugfix Step 2.5 rewritten repro-local-first → observability-first** (read ALL logs/observability to root cause; invariant *error without observability = bad design = a finding*); schema aligned to canonical **`repro_evidence`** (`reproduced_local | trace_evidence{source,ref}`, D4) — was stale `hotfix_metadata`. One human-language signature.
- **`ux-agentico`** — Postura cardinal **agentic-architecture-expert** (not chatbot) + **no-fake-`if`s quality bar** (HARD, inherited by architect/auditor) + improve-not-destroy + one human-language behavior signature; anti-patterns cement the bar.
- **`architect`** — added the **WT5 `technical-story` lane**: `/architect` IS the refiner (skips po/po-ux/ux-agentico), **CTO-to-CEO** hat (research SOTA + propose + Chris decides), **contract-spec not Gherkin** (contract/consumers/invariant/verification-by-effect), verification = técnica, WT5-builds-vs-WT6-lifts boundary, reduced ready-package. Purely additive (machinery-asserted strings untouched).
- **`pm-vitalia/nicolify/comunify/lupulo` + `_pm-brand-template`** — added the **Intake-handshake** (identical block, LSP): the story is BORN from a system-designer conversation (zona/caja + extends-or-new + what-exists + push; prior-art **in the intake**; all asks → `chris-input.md` from creation). The `"idea {x}"` command row upgraded from mechanical file-creation → run-the-handshake-first. Template carries the verbatim block so future bootstraps inherit it.

### B · Dedup (pointer + sync) — low-coupling win

The **chris-input append protocol** block (~33 verbose lines: verdict-labels table + format + anti-patterns) was **re-stated verbatim in 10 skills**. Replaced each with a **3-line pointer to the SSoT** `docs/process/chris-input-protocol.md §5` (which holds §4 labels + §5 verbatim). Files: po-ux · po · ux-agentico · architect · auditor · dev-team · pm-luana · pm-vitalia · pm-nicolify · _pm-brand-template. **−280 lines**, one SSoT per concern (charter high-cohesion). Mechanically safe (no hook/gate greps the block; machinery 73/0/0 after).

### C · Depopulate phantom PMs — kill the rot surface

The 6 unbootstrapped brands (`saasora/inmoflow/retailly/fixia/guestly/fitflow` · 0 stories each, scaffold only) carried **187-258-line fully-populated `pm-{brand}` bodies** — duplicate Step-0/Auto-chain/Fase-F.3/capability-inventory/chris-input that rots without use (LSP drift × 6). **Depopulated to 30-line pre-bootstrap stubs** (frontmatter preserved → `/pm-{brand}` stays discoverable + `disable-model-invocation: true`; body → "scaffold via `_pm-brand-template`"). Not machinery-asserted → safe.

---

## 3 · How each refinement skill implements REQ-TAKING-DETAIL §10 (the gate)

| §10 requirement | po-ux | po | ux-agentico | architect (WT5) | pm-{brand} |
|---|:--:|:--:|:--:|:--:|:--:|
| Cardinal stance (never-stenographer · contradict-on-value · improve-not-reinvent) | ✅ | ✅ | ✅ | ✅ (CTO) | ✅ (intake) |
| Hat per input type | PO/PM user-advocate | PO contract / bugfix-obs | agentic-arch expert | **CTO-to-CEO** | system-designer |
| 1-question / reflect-first / no-cave / human-bullets | ✅ (replaced batched) | ✅ (replaced batched) | ✅ (refs po protocol) | ✅ (refs po) | — (intake convo) |
| Role-obligatory + internet-references-always | ✅ | ✅ | ✅ | ✅ (SOTA) | n/a |
| Functional-first, mockup-after (inversion) | ✅ | n/a (no UI) | n/a | n/a | n/a |
| Human-bullets NOT Gherkin · Gherkin GENERATED at firma-2 | ✅ | ✅ (mapa) | branch-tree | contract-spec (no Gherkin) | n/a |
| Live-doc + **`> 🗨️ CHRIS:`** marker + reconcile-to-clean | ✅ | (via spec doc) | (via design doc) | (contract-spec) | n/a |
| chris-input ledger (every ask, **from creation**) | ✅ | ✅ | ✅ | ✅ | ✅ **(intake-handshake)** |
| Signatures (UI 2-internal→1-final · no-UI 1 human-language · G separate) | ✅ 2→1 | ✅ 1 | ✅ 1 | ✅ 1 | (G separate) |
| Scope critical-path-first · zero-loss · never-re-ask | ✅ | ✅ | ✅ | ✅ | (intake placement) |
| Observability-first bugfix (error-without-obs = bad design) | →po | ✅ | n/a | n/a | n/a |
| no-fake-`if`s bar (handed to architect/auditor) | n/a | n/a | ✅ | (inherits) | n/a |

---

## 4 · Marker decision — RATIFIED with Chris (deliverable d)

REQ-TAKING-DETAIL §5 left the comment-marker open. **Chris ratified (2026-06-08): `> 🗨️ CHRIS:` blockquote.** Cemented in po-ux (live-doc section + example) and the SSoT `spec-mapa-funcional.md` already references it. The refiner greps `> 🗨️ CHRIS:` to find + reconcile Chris's notes into a clean doc; every note also lands in `chris-input.md`.

---

## 5 · Findings deferred / for downstream WS (honest scope)

- **`architect-be/fe/agentic` mis-housed as skills (→ W7).** They are `disable-model-invocation` **instruction-docs loaded by PATH** by `architect-orchestrator`, AND **machinery-asserted** (`validate_machinery_consistency.py` lines 54-55/192-195). Correct home = `architect/references/{be,fe,agentic}.md`. Moving them is a **coordinated change** (touches `.claude/agents/` = W3 scope + the validator) → **deferred to W7** behind a dependency-grep gate. Left path-stable + tagged hybrid.
- **PM LSP drift — the validator IS the sync-check (no body-extraction possible).** `validate_machinery_consistency.py` CHECK 16/17 **require** `chris_verify.signoff` + `reconcile`/`reconciled` strings to live **inside each** of the 4 active `pm-{brand}` files. So the spine-gate sections **cannot** be pointer-extracted (the machinery intentionally mandates per-PM duplication = the LSP fitness test, implemented). The intake-handshake was added as the **identical block** across all 4 + template to keep LSP honest. **Recommendation (W4/machinery):** add a CHECK that diffs the intake-handshake block template↔instances (extend CHECK 17's pattern) so it can't drift silently.
- **`tessl-context` staleness candidate.** PII rule notes Tessl tiles were referenced but the canonical tile didn't exist; verify Tessl is still installed before W9, else tombstone.
- **chris-input dedup is complete for the 10 carriers** (pm-comunify/pm-lupulo never had the block). If a future skill is added, it must use the pointer, not re-paste the block.

---

## 6 · Learnings (charter §5 step 7 → feed back to §7)

1. **The skill layer is ~zero proxy-clean `core` — and that's correct, not a gap.** Unlike rules (18 core), skills are project instances of doctrine that already lives in process-docs. The extraction story for skills = "ship a generic role skeleton + write the project instance against the process-docs," not "make the luana skill agnostic." Tagging all spine skills `hybrid` (not aspirationally `core`) is the honest application of option-b. *Cohesion lesson: doctrine belongs in one process-doc SSoT; the skill is its project-bound executor.*
2. **A skill carried a protocol that CONTRADICTED its own ratified SSoT.** po-ux still enforced "batched 3-5 questions" while `spec-mapa-funcional.md` had already inverted to functional-first/1-question (W0.5-bis). The SSoT doc moved; the skill didn't. *Lesson: when a process is ratified in a doc, grep the implementing skills for the OLD pattern — the doc update doesn't propagate itself.*
3. **The machinery validator is the de-facto LSP sync mechanism.** CHECK 16/17 mandate per-PM duplication of spine strings — which both *blocks* clean body-extraction AND *is* the "sync-check template↔instances" fitness test the charter asks for. The right move isn't to fight it (extract + break the gate) but to **extend it** to cover new shared blocks (intake-handshake). *Lesson: where a gate mandates duplication, the dedup lever is a new gate-check, not a pointer.*
4. **Dedup-by-pointer is safe only after confirming the SSoT is complete + the block isn't a load-bearing gate string.** Verified `chris-input-protocol.md §4+§5` holds the full schema and no hook greps the verbose block before replacing 10 copies. Validate-after-apply held (73/0/0). *Reinforces the W1 "stub against the gate" learning.*
5. **Depopulation > deletion for phantom placeholders.** The 6 phantom PMs keep their frontmatter (discoverability + `disable-model-invocation`) while shedding the rotting body → the registry stays intact, the LSP drift surface drops from 11 instances to 5 (4 active + template).

---

## 7 · Pointers

- `docs/process/harness-refactor-w0.5/REQ-TAKING-DETAIL.md` §10 — the gate this session implements.
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md` §3,§6 — WT cards + conformance checklist.
- `docs/process/spec-mapa-funcional.md` — the UI functional-first SSoT (po-ux mirrors it).
- `docs/process/harness-refactor-charter-2026-06-08.md` §0.5,§4 — north-star + fitness tests.
- `docs/process/harness-refactor-w1/W1-OUTPUT.md` — option-b proxy precedent.
- **Next:** W3 (agents — incl. the `architect-be/fe/agentic` rehoming) ‖ W4/W4b (hooks/scripts/cockpit) ‖ W6 (templates — `01-spec` functional-first per REQ-TAKING §10).

*End W2-OUTPUT.md — the W2 deliverable. machinery-check 73/0/0 · pointer-scan NEW 0.*
