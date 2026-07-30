# W4 · Hooks + pre-commit checks — Output (tier manifest + no-paper-rules verdict + process conformance + applied deltas + smoke evidence + learnings)

**Date:** 2026-06-09 · **Session:** harness-refactor W4 (B-phase) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` (precedent: W0/W0.5/W0.5-bis/W1/W2/W3 HEAD here) · **Status:** APPLIED + cemented (path-stable).

> **North-star card:** *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens (the rest went to the seam). The goal is an extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*
>
> Charter §6 W4 done-when: *hooks + checks tagged + conformant + split genérico-vs-project + machinery 73/0/0.* Inputs: `PROCESS-MODEL.md §2,§3,§5,§6` (spine gates · WT profiles · conformance checklist · no-paper-rules) + charter §0.5 (option-b proxy) + W1/W3 precedent (validate-after-apply, propagation-grep, proxy-earned core). Full per-check research: **`RESEARCH-checks.md`** (sibling, pointer-first — not duplicated here).

---

## 0 · Scope + headline result

Scope = `.claude/hooks/` + `scripts/git-hooks/`. **Real surface (the `ls` manda, not the charter's "4 hooks + 18 checks"):**
- **4 Claude-Code event hooks** in `.claude/hooks/` (+ a 5th `Stop` hook → `scripts/validate_session_close.py`, registered in `settings.json` but living OUTSIDE `.claude/hooks/` — out of scope, noted).
- **pre-commit dispatcher** + **pre-push** + **22 sourced checks** (`02…18` incl. sub-letters `05b/c/d/e`, `15.5`). Charter said "18 checks" → real = **22**.

All work this session is **PATH-STABLE**: 5 comment/text-only conformance fixes (zero logic touched) + 6 inline tier tags (comments). Zero file moves, zero mechanism risk. **Validated after edits (W1 non-negotiable): `make machinery-check` = 73 checks · 0 fallos · 0 advisory · `scan_harness_pointers.py` = NEW 0 · full dispatcher chain sources clean (rc=0) · each touched hook smoke-tested functionally.**

**Headline:** the enforcement surface is mechanically **sound** — NO critical paper-rules (every executed script/rule/make-target resolves on disk). Conformance work was the same W2/W3 failure mode (stale tokens the ratified SSoT didn't propagate): `outcomes/` brand-advice (purged 4-ejes), `cross_check_1/atomics` (killed 2026-05-28), `blocked` extra state (not in 10-state canon), `demo_signoff` (retired → `chris_verify.signoff`), + 1 doc-rot pointer. External docs (date-aware) confirm our `hookSpecificOutput.additionalContext` emitters are **current, not stale**. Tier shape mirrors W3: almost everything `hybrid` (core enforcement skeleton + project runner-half parked → seam), only **5 proxy-clean `core`** files, **0 brand**.

---

## 1 · Tier manifest — `tier: core | project | brand | hybrid` (drives W7)

**Option-b proxy (charter §0.5, ratified Chris):** `tier:core` is EARNED only if the dependency-grep (`vitalia|nicolify|…|ruff|pytest|alembic|clerk|next|tailwind|fastapi|sqlalchemy|core/luana-core|.venv|dev-app|hipaa|phi`) returns **0 hits**. Any token ⇒ `hybrid` (core mechanism + project-half parked → seam W5), not rewritten to `{slot}` now. I ran the proxy MYSELF over every `core`-candidate (the cheap W8); the subagent's per-check pass is corroborated + corrected (07 → core, see note).

### Top-level hook surfaces (inline-tagged in-file this session)

| File | event / role | tier | core half (portable) | project half → seam slot |
|---|---|---|---|---|
| `.claude/hooks/auto-chain-detect.sh` | UserPromptSubmit | **hybrid** | prompt-intent → `additionalContext` chaining mechanism (PM→secondary skill) | brand enum + secondary-skill names → `brands[]` |
| `.claude/hooks/learning-detect.sh` | UserPromptSubmit | **hybrid** | learning-capture trigger → `additionalContext` mechanism + doctrine (CIL L2) | Spanish trigger phrases → `locale` |
| `.claude/hooks/claude-md-overlay-check.sh` | SessionStart | **hybrid** | overlay-walk advisory mechanism (missing/over-cap) | brand enum + 165-line cap + luana worktree paths → `brands[]` |
| `.claude/hooks/contract-guard.js` | PostToolUse (Write\|Edit\|MultiEdit) | **hybrid** | PostToolUse SSoT-guard dispatch (edit → regen/test reminder) | RULES array (engine/brand paths + ruff/pytest/vitest) → `domain_modules[]`/`engine_prefix`/`toolchain` |
| `scripts/git-hooks/pre-commit` | git dispatcher | **hybrid** | orchestration skeleton (branch GATE_LEVEL · fail-open preamble · explicit-order sourcing · staged-file collection) | check-list composition + `sales_agent`/`.venv` exclusions → `brands[]`/`toolchain` |
| `scripts/git-hooks/pre-push` | git push-to-main gate | **hybrid** | push-gate machinery (ci-parity marker · bidirectional/cap-gate sourcing · fail-open+ACK) | brand enums + `CAP_GATES_HARD_BRANDS` + PHI + `.venv` → `brands[]`/`toolchain` |

### 22 sourced checks (tier recorded here — manifest is authoritative for W7; not inline-tagged to avoid churning 22 working enforcement files)

| # | check | tier | seam slot(s) | ACK / escape |
|---|---|---|---|---|
| 02 | voseo | **hybrid** | `locale` (+ `sales_agent` voice-exception paths) | magic `# voseo-allowed` |
| 03 | ruff | **project** | `toolchain` (ruff/`.venv`) + brand paths | fail-OPEN (no ACK) |
| 04 | r3-ssot | **hybrid** | `engine_prefix`/`brands[]` | magic `# downstream-regression-na:` |
| 05 | r32-cap-story | **hybrid** | `.venv` (wraps `reconcile_capabilities.py`) | fail-OPEN |
| 05b | cap-advisory | **hybrid** | `brands[]` + `.venv` | env `CAP_ADVISORY_SKIP=1` |
| 05c | code-cap-index | **hybrid** | `brands[]` + stack ext + `.venv` | env `CODE_INDEX_SKIP=1` |
| 05d | bidirectional | **hybrid** | `brands[]` + `.venv` | env `BIDIRECTIONAL_SKIP=1` |
| 05e | cap-gates | **hybrid** | `brands[]` (`CAP_GATES_HARD_BRANDS` maturity allowlist) | env `CAP_GATES_SKIP=1` |
| 06 | backlog | **hybrid** | `brands[]` + `.venv` | fail-OPEN |
| 07 | checkpoint-enum | **core** ★ | — (enforces the **core 10-state vocab**; generic story-glob; **proxy-clean**) | magic `<!-- state-enum-na: -->` |
| 08 | pii-seed | **hybrid** | `.venv` + eval-fixture path | fail-OPEN |
| 09 | pii-goldens | **hybrid** | `.venv` + `sales_agent` goldens path | fail-OPEN |
| 10 | infra-matrix | **hybrid** | `config/brand.yaml` + `.venv` | fail-OPEN |
| 11 | worktree | **core** | — (pure git main-protection; **proxy-clean**) | env `LUANA_ALLOW_MAIN_COMMIT=1` |
| 12 | story-closure | **hybrid** | `brands[]` | env `STORY_CLOSURE_GATE_SKIP=1` |
| 13 | scope-branch | **hybrid** | `brands[]` + `engine_prefix` | env `SCOPE_GATE_SKIP=1` |
| 14 | brand-docs-schema | **hybrid** | `brands[]` | env `BRAND_DOCS_SCHEMA_SKIP=1` |
| 15 | cap-ledger | **hybrid** | `brands[]` + `.venv` | magic `# cap-ledger-skip:` / env `CAP_LEDGER_SKIP=1` |
| 15.5 | system-map | **hybrid** | `.venv` (+ vitalia-named ADR in help text) | env `SYSTEM_MAP_SKIP=1` |
| 16 | chris-input | **hybrid** | `brands[]` | magic `# chris-input-skip:` / env `CHRIS_INPUT_SKIP=1` |
| 17 | checkpoint-dupkeys | **core** | — (pure YAML-frontmatter integrity; **proxy-clean**) | env `CHECKPOINT_DUPKEY_SKIP=1` |
| 18 | machinery | **hybrid** | `.venv` (wraps `validate_machinery_consistency.py`) | env `MACHINERY_CHECK_SKIP=1` |

★ **07 correction vs RESEARCH-checks.md:** the subagent tagged 07 `project` ("brand-checkpoint layout"). I re-grepped: **0 proxy hits**; its only inputs are the canonical **10-state list** (core vocab, `lifecycle.md`) + a generic `*/docs/product/stories/*/checkpoint.md` glob. Proxy-clean + enforces core doctrine ⇒ **core** (per option-b, proxy-clean files CAN be core). My `blocked`-removal edit (§3) makes it *more* aligned to the core enum.

**Counts:** **core 5** (07, 11, 17 in checks + none of the 6 top-level — every top-level hook carries a brand-enum/path) · **hybrid 23** (4 hooks + pre-commit + pre-push + 18 checks) · **project 1** (03-ruff) · **brand 0**. Matches the W3 prediction (kickoff): *the ruff/pytest/brand-loop runners = project/hybrid; the enforcement SKELETON (orchestration, fail-open+ACK, baseline-ratchet, pathspec-guard) = the portable core.* The single biggest extractability blocker is the **verbatim hardcoded 10-brand enum** (in 05b/05c/05d/05e/12/13/14/16 + loops in 08/09/12 + pre-push) → a `brands[]` seam (W5) lifts most `hybrid`→`core`. `brand` tier empty (same as W1/W3 — brand specifics are config, never a hook · OCP).

---

## 2 · No-paper-rules verification (deliverable b · PROCESS-MODEL §6.5/§6.6)

**Every gate the hooks claim has a REAL mechanism.** I (+ subagent) `test -e`-verified every cited script/rule/make-target across all 22 checks + pre-push + the 2 preamble gates + the 4 event hooks:

- **All 11 executed Python scripts exist** (`reconcile_capabilities`, `resolve_cap`, `generate_code_to_cap_index`, `validate_code_cap_bidirectional`, `generate_backlog`, `generate_portfolio`, `generate_infra_matrix`, `validate_system_map`, `scan_seed_pii`, `scan_goldens_pii`, `validate_machinery_consistency`) + `_pii_scan_lib.py`, `ci-parity.sh`, `validate_session_close.py`.
- **All preamble gates exist** (`scripts/git/multi-session-scope-guard.sh`, `scripts/git/dod-evidence-gate.sh`) + `scripts/mutation_gate.py` (CHECK-19 load-bearing) + `scripts/learning/capture.sh` (cited by learning-detect as "don't use without ratification") + `scripts/git/new-session.sh`.
- **All cited rules/docs/make-targets resolve.** Sentinel `.ci-parity-deferred` present (pre-push currently ADVISORY for the Docker mirror).
- **Consumer wiring verified (not the producer's self-description, per W1 learning):** `settings.json` registers all 4 hooks at the correct events (UserPromptSubmit ×2, SessionStart, PostToolUse `Write|Edit|MultiEdit`) + Stop. `make install-hooks` symlinks pre-commit + pre-push. Installed hooks live in the **shared** `luana-platform/.git/hooks/` (worktree-común).

**ONE non-critical paper-rule — FIXED:** `05b-cap-advisory.sh` block-message cited SSoT `_cap-verification-decisions.md § F` → **no such file exists anywhere**. Repointed to `docs/process/cap-deterministic-enforcement.md` (the HB-51 cement SSoT). Mechanism-path was never affected (help-text only); now points devs at a real doc.

**Resilience note (design, not a paper-rule — flagged for W4b/W10):** ~9 checks (03/04/05/06/08/09/10/15.5/18) + the HARD cap-gates (05d/05e/pre-push) are **fail-OPEN** when `.venv`/script is absent — intentional (don't hard-block on tooling absence) but means a HARD gate **silently degrades to a no-op** if its script is ever deleted, with no warning. Candidate hardening: a "script-missing ⇒ loud warn" path for the HARD-tier checks. Out of W4 conformance/tier scope; logged.

---

## 3 · Process conformance per hook (deliverable c · stale patterns caught/fixed)

Method (same as W3 caught `02-design-ui`/`v4.2`): grep the IMPLEMENTING hooks for the OLD token of every ratified-retired concept. Found **5 real stale tokens** (subagent's 3 in checks + 2 I found myself in the preamble gate). CLEAN of `02-design-ui`, `phase_workflow`, A-F letter-phases, per-worktree WIP-cap (v5 vocab honored by absence — the dod/chris_verify/reconciled gates live in dedicated scripts, not this dispatcher).

| # | Stale token | Where | Ratified truth | Fix applied (path-stable) |
|---|---|---|---|---|
| 1 | `cross_check_1 (atomics→headers)` as a **live** check | `05d-bidirectional.sh` L16, L58 | atomics killed 2026-05-28; validator now has only `cross_check_3` (scenario→e2e_test, HARD) + `cross_check_4` (access↔PHI, advisory) — verified in `validate_code_cap_bidirectional.py` (no `cross_check_1/2` defined) | relabeled advisory text to the live checks; HARD line now names only `cross_check_3` |
| 2 | `outcomes/` as **brand** epic destination | `14-brand-docs-schema.sh` L19, L43, L54 | brand docs purged `outcomes/` (4-ejes: Release→Story→Cap→Scenario); product/ sub-dirs = stories/capabilities/modules/**releases** | swapped the 3 brand-advice spots `outcomes/{slug}.md` → `releases/{FN}.yaml` |
| 3 | `blocked` extra checkpoint state | `07-checkpoint-enum.sh` L32 | canonical macro-states = exactly **10** (no `blocked`); **0 live usage** (grep `^state: blocked` = 0) | removed `\|blocked` from the enum regex (smoke: `blocked` now rejected, valid states pass) |
| 4 | `demo_signoff` (retired token) | `scripts/git/dod-evidence-gate.sh` L14 (comment) | v5 consolidated `demo_signoff` → single **`chris_verify.signoff`** (G phase) | comment token → `chris_verify.signoff` (gate mechanism already v5-correct: enforces `dod_live_verified`+`dod_evidence` on transition to developed\|done) |
| 5 | `_cap-verification-decisions.md` (missing doc) | `05b-cap-advisory.sh` L145 | the cap-format SSoT is `cap-deterministic-enforcement.md` (HB-51) | repointed (also §2) |

**Not stale (left intact, verified):** `pre-push` L106 + `15-cap-ledger.sh` L14/15/96 reference `atomics` correctly as a **retired/historical tombstone** ("killed 2026-05-28 … removido") — these are the *right* way to mark a dead concept (W3 precedent: keep tombstones, fix live directives). `contract-guard.js` L159 `per-worktree` = worktree-clone path handling, not the WIP-cap pattern. `06-backlog.sh` `outcomes/` trigger = **NOT stale**: `generate_backlog.py::read_outcomes` (L228) STILL reads the **platform** `docs/product/outcomes/` (the purge is brand-level only) → leaving the platform trigger is correct; touching it would break a live regen trigger.

**v5-gate scripts (preamble, sourced by my pre-commit — kickoff named them):** `dod-evidence-gate.sh` (fixed #4) + `multi-session-scope-guard.sh` (read, HB-31 cement 2026-06-04, v5-clean, no stale vocab) both reflect the ratified process. These live in `scripts/git/` (W4b territory) but were verified here because the pre-commit preamble invokes them; only the trivial comment-token (#4) was fixed in-place.

**External-docs conformance (date-aware 2026-06-09, official Claude Code hooks docs):** our `{"hookSpecificOutput":{"hookEventName":...,"additionalContext":...}}` emitters for UserPromptSubmit + SessionStart are **CURRENT, not deprecated**. `settings.json` shape correct (`matcher` is ignored by UserPromptSubmit — harmless empty string present; SessionStart matcher optional). `CLAUDE_PROJECT_DIR` still injected. **One advisory (NOT applied):** for PostToolUse the docs now *prefer* `hookSpecificOutput.additionalContext` on exit-0 over `stderr+exit0` (which `contract-guard.js` uses); stderr **still works** (not stale) → documented as an optional SOTA migration, not perturbing a working ADVISORY hook for marginal gain.

---

## 4 · Applied changes + smoke evidence (deliverable d)

**11 files modified — all comment/text-only (conformance) or comment-insert (tier tags). Zero logic lines changed.**

- **Conformance (5 files):** `05d-bidirectional.sh` (atomics→cross_check_3/4) · `14-brand-docs-schema.sh` (outcomes→releases ×3) · `07-checkpoint-enum.sh` (drop `blocked`) · `05b-cap-advisory.sh` (doc-rot repoint) · `scripts/git/dod-evidence-gate.sh` (demo_signoff→chris_verify.signoff).
- **Tier tags (6 files):** 4 `.claude/hooks/*` + `pre-commit` + `pre-push` (inline `# tier:` header comment).

**Smoke evidence (per touched surface):**
- `bash -n` / `node --check` parse: **all 11 files OK** (+ pre-commit dispatcher OK).
- `07` regex behavioral: `developed`/`reviewing` → PASS · `blocked` → **REJECTED** (conforms to 10-state). ✓
- Full **pre-commit dispatcher chain** (empty staging, `PRECOMMIT_VERBOSE=1`): all 22 checks source in order, **rc=0**. ✓
- Event-hook functional smoke (live behavior intact post comment-edit): `auto-chain-detect` → emits `additionalContext` JSON on trigger / 0 bytes on no-trigger ✓ · `learning-detect` → JSON on "aprendamos de esto" ✓ · `claude-md-overlay-check` → SessionStart advisory JSON on this worktree's cwd ✓ · `contract-guard` → reminder on real path (absolute + `CLAUDE_PROJECT_DIR`) / silent on non-match ✓.
- Stale-token recheck on touched files: **0 remaining**.
- Final: `make machinery-check` **73 · 0 · 0** · `scan_harness_pointers.py` **NEW 0**.

**LOW finding (pre-existing, NOT introduced — logged, not fixed):** `contract-guard.js` path-normalization: a **repo-relative** `file_path` that itself contains `luana-core-*` (e.g. `core/luana-core-copilot/...`) gets over-stripped by the `/luana-[a-z0-9-]+/` worktree-root heuristic → reminder misfires. **Latent only:** in real operation Claude Code passes an **absolute** `file_path` + injects `CLAUDE_PROJECT_DIR` (confirmed via external docs), so the first normalization branch handles it and the heuristic is never reached (verified: absolute + `CLAUDE_PROJECT_DIR` → reminder fires correctly). Candidate W4b/W6 hardening.

---

## 5 · Consumer-side drift flagged (not W4-content — install/governance)

- **Installed `pre-push` is a STALE regular-file copy**, not a symlink: `luana-platform/.git/hooks/pre-push` (8014 B, jun-1) ≠ source `scripts/git-hooks/pre-push` (10817 B, jun-5). The `make install-hooks` target uses `ln -sf` (would be a symlink); the live file is an older copy → the *running* pre-push lags the source by ~4 days of edits. **Fix = re-run `make install-hooks`** (touches the shared main `.git/hooks/` — deliberately NOT done from this brand worktree mid-session). `pre-commit` IS a correct symlink. Logged for Chris / W4b. *(Smoke was run against THIS worktree's source files directly — not via `git commit`, which would run the main worktree's installed copy.)*

---

## 6 · Findings deferred / for downstream WS (honest scope)

- **Seam wiring (`{slot}` rewrite) = W5.** Every hybrid hook/check's project-half (brand enum / `.venv` / `engine_prefix` / toolchain / locale / PHI) is parked + tagged, ready for `project.config.yaml`. The recurring hardcoded 10-brand enum is the #1 W5 target.
- **W7 generic-skeleton extraction** = the portable enforcement IP (dispatcher orchestration · fail-open+ACK pattern · baseline-ratchet · pathspec-guard · PostToolUse SSoT-guard dispatch · `additionalContext` chaining mechanism). A new product writes new check instances against the same skeleton — same story as skills (W2) / agents (W3).
- **Fail-OPEN silent-degrade hardening** for HARD-tier checks (§2) → W4b or W10 governance.
- **`contract-guard.js` relative-path heuristic edge** (§4) → W4b/W6.
- **pre-push install drift** (§5) → re-run `make install-hooks` (Chris / W4b).
- **PostToolUse `additionalContext` migration** for contract-guard (§3, optional SOTA) → W6 or skip.
- **`Stop` hook** (`validate_session_close.py`) registered in settings.json but lives outside `.claude/hooks/` → its tier/conformance belongs to **W4b (scripts)**.

---

## 7 · Learnings (charter §5 step 7 → feed §7)

1. **The enforcement surface was mechanically sound — the work was stale-token propagation, exactly like W2/W3.** Zero critical paper-rules; every script resolved. The 5 fixes were all "the SSoT was ratified (atomics killed, outcomes purged, demo_signoff→chris_verify, 10-state canon), and the hook kept the OLD token." *Lesson reinforced for every B-phase surface: when a doctrine is ratified, grep the IMPLEMENTING enforcement (hooks/checks) for the OLD token — the SSoT does not propagate itself. The propagation-grep is the highest-yield conformance tool, three workstreams running.*
2. **"Purged" is scope-qualified — verify WHICH layer purged it before deleting a live trigger.** `outcomes/` was purged from *brand* docs (4-ejes) but the *platform* `generate_backlog.py::read_outcomes` still reads `docs/product/outcomes/`. The naive fix (rip `outcomes/` everywhere) would have broken a live backlog-regen trigger. *Lesson: a "retired" concept can be retired at one layer and live at another — read the consumer (`generate_backlog.py`) before removing its trigger, don't trust the ratification headline's scope.*
3. **A comment-only edit to a live event-hook still needs a FUNCTIONAL smoke, not just `bash -n`.** Tier tags are pure comments, but these hooks emit JSON parsed by Claude Code — a botched heredoc/quote could silently kill the emit. Smoking each (`echo JSON | hook` → assert emit/silence) is what proved the tag was inert. It also surfaced the pre-existing `contract-guard` relative-path edge that a parse-only check would never reveal. *Lesson: green parse ≠ green behavior for an I/O hook; exercise the real stdin→stdout contract.*
4. **`tier:core` for hooks is as rare as for agents — 5/28, all proxy-EARNED.** Rules had 18 core, skills 0, agents 1, hooks 5. The pattern holds: the portable core is the *enforcement skeleton* (orchestration / fail-open+ACK / git-main-protection / YAML-integrity / 10-state-enum), not the *runner* that shells `ruff`/`pytest` against brand paths. Every check that runs a stack tool or loops the brand enum is hybrid-by-construction. *Cohesion lesson: a check is a project-bound executor of a core gate-contract; extract the contract (the skeleton + the seam), rewrite the runner per product.*
5. **Verify the installed artifact, not just the source — they can diverge.** `make install-hooks` *intends* symlinks, but the live `pre-push` was a stale copy 4 days behind source. The source can be perfectly refactored while the *running* gate is an old file. *Lesson: a hook session's consumer-side check is two-level — (a) is it registered (settings.json / install target)? AND (b) is the installed thing actually current (symlink vs stale copy)? Smoke the source directly, but flag the install drift.*

---

## 8 · Pointers

- `RESEARCH-checks.md` (sibling) — full per-check table (what/GATE/cited-artifacts/stale/tokens/tier/ACK) + paper-rule audit + stale findings. **Pointer-first: not duplicated above.**
- `docs/process/harness-refactor-charter-2026-06-08.md` §0.5,§3,§4,§6 — north-star + seam slots + fitness tests + roadmap.
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md` §2 (spine gates) · §5 (D-X2/D-X3/D-X4 retirements: outcomes/demo_signoff/02-design-ui) · §6 (conformance checklist — no-paper-rules, one-SSoT).
- `docs/learnings/tooling/2026-06-08-harness-refactor-stub-against-the-gate.md` — validate-after-apply + verify-the-consumer (applied verbatim).
- `docs/process/harness-refactor-w1/W1-OUTPUT.md` · `…w3/W3-OUTPUT.md` — B-phase precedent (option-b proxy, propagation-grep, validate-after-apply).
- **Next (B-phase parallel):** W4b (scripts + cockpit — owns the `scripts/git/*` gate scripts, `Stop` hook, install-drift) → then W6 (templates) → W5 (seam) → W7 (physical move). **W5/W6/W7/W8 are STRUCTURAL — Chris-ratified, new conversation each (HLP governance).**

*End W4-OUTPUT.md — the W4 deliverable. machinery-check 73/0/0 · pointer-scan NEW 0 · dispatcher rc=0 · 5 conformance fixes + 6 tier tags · 11 files, all path-stable.*
