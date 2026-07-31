# W1 · Rules — Output (tier manifest + applied changes + learnings)

**Date:** 2026-06-08 · **Session:** harness-refactor W1 (B-phase) · **Owner:** /pm-luana (harness-dedicated, Opus) · **Branch:** `wip/vitalia` (precedent: W0/W0.5 HEAD here) · **Status:** Phase 1 APPLIED + cemented; Phase 2 STAGED (`W1-phase2-execution.md`).

> Charter §6 W1 done-when: *rules tagged core/project/brand · always-on lean · conform to W0.5*. This doc is the W1 deliverable (charter §5 step 7 + §7 tagging convention). Inputs: `harness-rules-audit-2026-06-08.md` (3-tier analysis) + `harness-refactor-w0.5/PROCESS-MODEL.md` §6 conformance checklist + §8 diff.

---

## 0 · Scope decision (ratified Chris)

**Phase 1 + stage Phase 2.** Applied this session = all **path-stable** work (stub fat always-on, W0.5 conformance deltas, strip dead globs, tier manifest), zero enforcement-machinery risk. The coordinated Tier-3 evictions (move 24 domain/phase rule bodies into owning skills' `references/`, repointing `contract-guard.js` + `harness-pointer-baseline.txt`) are STAGED to `W1-phase2-execution.md` (run in `wip/protocol-rules-refactor`, ratified). **Tier-2 `paths:` = gate-blocked** (needs fresh-session `/memory` empirical test for bug #16299; skills are the robust home anyway).

### §0.5 acceptance proxy — option (b) ratified (Chris 2026-06-08)

Charter §0.5 (committed `a7a2d248` mid-session) added the **two co-equal lenses** + the per-session dependency-grep (cheap W8). My initial Phase-1 pass delivered lens-1 (conformance) + budget but treated lens-2 (extractability) as *tagging only* — the proxy then showed **13/22 `core`-tagged rules carried tech/brand tokens** (DoD 10, anti-dup 6, auditor-downstream 5…). Per **option (b)**: proxy = scorecard; `tier:core` ⇒ proxy-clean **else `hybrid`**; `{slot}` rewrite stays W5. Corrected this session:
- **4 files re-tagged `core`→`hybrid`** (structural/multiple tokens, project-half parked → seam W5): `definition-of-done-live-verify`, `anti-duplication`, `auditor-downstream-regression`, `parallel-safety`.
- **9 files cleaned in-place** (trivial token = provenance/single illustrative path → generic, no `{slot}`): story-closure-gate, tdd-mandatory, test-design-doctrine, hotfix-repro-mandatory, anti-duplication-refining, anti-default-flip-audit, auditor-self-fix-policy, claude-md-overlay, pm-skill-chaining.
- **Result: the 18 `core` rules now pass the proxy (0 token hits).** machinery-check 73/0/0 after.

## 1 · Budget

| Milestone | always-on lines (`.claude/rules/*.md`) |
|---|---|
| Pre-W1 | **2012** |
| **Post-Phase-1 (this session)** | **1741** (−271, −13.5%) |
| Projected post-Phase-2 (Tier-3 eviction) | ~450–550 (−73 to −78% total) |

Phase-1 win came from: DoD stub (−214) · anti-duplication table→detail (−24) · auditor-self-fix v4.2 dead-block (−15) · debugging trim + dead globs (−18) · 3× core-stayer frontmatter strip (−12). Net −271 with **0 breakage** (machinery-check 73/0/0; pointer-scan NEW 0).

## 2 · Tier manifest — `tier: core | project | brand` per rule (drives W7 physical move)

**Axis:** `core` = process invariant, carries to any product unchanged (charter CORE / audit GENERIC). `project` = stack/domain-specific, rewrite per product (audit STACK; reads a seam slot). `brand` = market-instance config — **none of the 46 rules are brand-tier** (brand specifics live in `{brand}/CLAUDE.md` overlays + `brand.yaml`; adding a brand = config, OCP). Hybrids tagged `core+project` (a core doctrine half + a stack-specific half to split at W5/W7).

| # | rule | tier | seam slot(s) it should read (W5) | Phase-1 action | W0.5 conformance |
|---|---|---|---|---|---|
| 1 | git-safety | **core** | — | stripped dead globs | ✓ |
| 2 | parallel-safety | **hybrid** | `brands[]` (worktree paths → seam) | stripped dead globs; re-tag core→hybrid | ✓ (WIP-cap lives in story-closure-gate) |
| 3 | story-closure-gate | **core** | — | keep | ✓ (G/R/WIP-cap module-scoped; no per-worktree text) |
| 4 | paradigm-arquitectura | **core** | — | keep | ✓ (3-planos/3-zonas) |
| 5 | anti-orphan-integration | **core** | — | keep | ✓ (CONN) |
| 6 | tdd-mandatory | **core** | — | keep | ✓ |
| 7 | test-design-doctrine | **core** | — | keep | ✓ (verificación REAL) |
| 8 | definition-of-done-live-verify | **hybrid** | `live_verify_infra[]` (+`observability_evidence`) | **STUB 276→~70** (body→rules-detail); re-tag core→hybrid (10 project tokens parked) | ✓ (verification_nature **top-level**; single `chris_verify.signoff` in G; `mutation_gate.py` §2 retained) |
| 9 | hotfix-repro-mandatory | **core** (+project sources) | `live_verify_infra.observability_evidence` | **delta applied** | ✓ (repro = `reproduced_local \| trace_evidence{source,ref}` · D4) |
| 10 | anti-duplication | **hybrid** | `engine_prefix` | **STUB** (engine table→rules-detail) | ✓ (doctrine always-on, fires at write-time #23478) |
| 11 | anti-duplication-refining | **core** | `brands[]` | keep | ✓ |
| 12 | anti-default-flip-audit | **core** | — | keep | ✓ (flag-inventory table reachable) |
| 13 | auditor-self-fix-policy | **core** | — | **STUB** (dead v4.2 block→breadcrumb) | ✓ (v5 Responsable cardinal) |
| 14 | auditor-downstream-regression | **hybrid** | `engine_prefix`/`brands[]` | keep path-stable (`04-r3-ssot.sh` greps it); re-tag core→hybrid | ✓ |
| 15 | architect-autonomous-mode | **core** | — | keep | ✓ |
| 16 | learning-capture | **core** | — | keep | ✓ (CIL L2 routing) |
| 17 | claude-md-overlay | **core** | `brands[]` | keep | ✓ |
| 18 | pm-skill-chaining | **core** | — | keep | ✓ |
| 19 | git-haiku-delegation | **core** | — | keep | ✓ |
| 20 | worktree-dual-strategy | **core** | `brands[]` | keep | ✓ (single-hub default) |
| 21 | step-0-worktree | **core** | `brands[]` | keep (Phase-2 evict; **no `@`-import exists** — audit FP corrected) | ✓ |
| 22 | github-actions-deferred | **core** | `toolchain` | keep | ✓ |
| 23 | tenant-isolation | **project** (doctrine core) | — | stripped dead globs | ✓ (write-time security; never `paths:` #23478) |
| 24 | pii-sanitisation | **project** (doctrine core) | — | keep | ✓ |
| 25 | spanish-text | **project** | `locale` | keep | ✓ (scope acotado a UI/agentic) |
| 26 | master-data | **project** | — | keep (Phase-2: absorbs currency) | ✓ |
| 27 | currency-handling | **project** | — | keep (Phase-2: merge→master-data) | ✓ |
| 28 | backend-ddd | **project** | `toolchain`/`engine_prefix` | keep (Tier-2 candidate) | ✓ |
| 29 | backend-quality | **project** | `toolchain` | keep (Tier-2 candidate) | ✓ |
| 30 | backend-migrations | **project** | `toolchain` | keep (Tier-2 candidate) | ✓ |
| 31 | architectural-fitness | **project** | `toolchain` | keep (Tier-2 candidate; write-time → maybe stay) | ✓ |
| 32 | frontend-fsd | **project** | — | keep (Tier-2 candidate) | ✓ |
| 33 | frontend-quality | **project** | `toolchain` | keep (Tier-2 candidate) | ✓ |
| 34 | frontend-visual-fidelity | **project** (Canon-HARD doctrine core) | `design_system_ref` | keep | ✓ (Design-System-Canon HARD end-to-end present) |
| 35 | form-runtime-array | **project** | `design_system_ref` | keep (Phase-2 evict → brand/offer-expert) | ✓ |
| 36 | e2e-testing | **project** | `toolchain`/`brands[]` | keep (Phase-2 evict; `e2e-preflight.sh`+baseline cite it) | ✓ |
| 37 | debugging | **project** | `toolchain`/`brands[]` | **trim + dead globs** | ✓ (Tier-2 candidate) |
| 38 | brand-docs-schema | **project** (4-ejes model core) | `brands[]` | **delta applied** (Phase-2 evict→pm refs) | ✓ (`outcomes/` purged; `02-design-ui` dead) |
| 39 | offer-catalogs | **project** (domain) | `domain_modules[]` | keep (Phase-2 evict→offer-expert; `contract-guard.js`) | ✓ |
| 40 | analytics-metrics | **project** (domain) | `domain_modules[]` | keep (Phase-2 evict→metrics-expert; `contract-guard.js`) | ✓ |
| 41 | etl-extraction-contract | **project** (domain) | `domain_modules[]` | keep (Phase-2 evict→metrics-expert; cg.js+baseline) | ✓ |
| 42 | copilot-resilience | **project** (domain agentic) | `domain_modules[]` | keep (Phase-2 evict→copilot-expert; cg.js) | ✓ |
| 43 | copilot-observability | **project** (domain agentic) | `domain_modules[]` | keep (Phase-2 MERGE→copilot-resilience) | ✓ |
| 44 | sales-agent-brand-voice | **project** (domain agentic) | `domain_modules[]` | keep (Phase-2 evict→sales-agent-expert) | ✓ |
| 45 | admin-panel | **project** (domain, opt-in) | `domain_modules[]` | keep (Phase-2 evict→backend-expert) | ✓ |
| 46 | data-reliability | **project** (domain) | `domain_modules[]` | keep (Phase-2 evict→metrics-expert; ⚠️ stale Makefile targets = separate story) | ✓ |

**Counts (post §0.5 proxy · option b):** core **18** (all proxy-clean, 0 token hits) · hybrid **4** (definition-of-done, anti-duplication, auditor-downstream-regression, parallel-safety — project-half parked → seam W5) · project **22** · brand **0**. frontend-visual-fidelity/brand-docs carry a core doctrine half but are net-`project` (their tokens are intrinsic stack/layout). The 18 core files pass the §0.5 acceptance proxy.

### `docs/rules-detail/*.md` tier (mirror the owning rule)

`core`: auditor-self-fix-policy, auditor-downstream-regression(+targets), git-safety, github-actions-deferred, hotfix-repro-mandatory, learning-capture, parallel-safety, step-0-worktree, story-closure-gate, anti-duplication-refining, claude-md-overlay, definition-of-done-live-verify(+project facet via seam), anti-duplication(table=project). `project`: brand-docs-schema, spanish-glossary, anti-default-flip-audit. Backups `_AGENTS-original-backup.md`/`_CLAUDE-original-backup.md` = archival (drop at W9). `README.md` = index.

## 3 · Applied changes (path-stable, this session)

**Stubs (body → `docs/rules-detail/`, file path unchanged):**
- `definition-of-done-live-verify.md` 276→~70 lines · new `docs/rules-detail/definition-of-done-live-verify.md` (full body, zero-loss). Cardinal + `dod_evidence` schema + verification_nature top-level + single `chris_verify.signoff` (G) + `scripts/mutation_gate.py` §2 + top-4 anti-patterns + enforcement 1-liner stay always-on.
- `anti-duplication.md` 69→~45 · new `docs/rules-detail/anti-duplication.md` (20-row engine inventory + concrete examples). Grep-before-write doctrine stays always-on (must fire at write-time, #23478).
- `auditor-self-fix-policy.md` dead v4.2 decision-tree → one-line breadcrumb (detail already existed).

**W0.5 conformance deltas (in-place):**
- `hotfix-repro-mandatory.md` — repro now `reproduced_local | trace_evidence{source,ref}` (D4); anti-patterns updated.
- `brand-docs-schema.md` (+ detail) — `outcomes/` purged (4-ejes Release entity); `02-design-ui.md` marked DEAD, `02-design-agentic.md` alive; title R1+R2+R3 → +R4.
- `debugging.md` — trimmed redundant multibrand tail; tier note.

**Cleanup:** stripped dead Cursor `globs:`/`description:` frontmatter from `git-safety`, `parallel-safety`, `tenant-isolation` (Claude Code ignores it; the other 19 globs-carriers are Tier-2/Phase-2 candidates, left for that pass).

**Governance:** `harness-pointer-baseline.txt` shrunk 29→28 (drained the now-fixed DoD `cobertura...` dead ref). `make machinery-check` 73/0/0. `scan_harness_pointers` NEW 0.

## 4 · Learnings (charter §5 step 7 → feed back)

1. **Anti-false-positive earned its keep — the audit's one HIGH-risk claim was wrong.** `step-0-worktree` is documented (in its own frontmatter) as `@`-imported by pm skills, but `grep '@.claude/rules/' .claude/skills/pm-*/SKILL.md` = **0 hits**. The `@`-import doesn't exist. The "HIGH-risk repoint" was a phantom dependency. *Cohesion lesson:* a file claiming a consumer relationship ≠ the consumer having it; verify the consumer side, not the producer's self-description.
2. **Over-stubbing silently broke a machinery check (CHECK 19).** Stubbing DoD dropped the literal `scripts/mutation_gate.py` that `validate_machinery_consistency.py` asserts #37 §2 *hosts*. Caught only by running `make machinery-check` AFTER apply. *Lesson:* a rule's always-on body is sometimes a **load-bearing string for a deterministic gate** — stub against the gate, not just the prose. Validate-after-apply is non-negotiable.
3. **The robust shrink lever is stub-in-place + `rules-detail/`, not `paths:`.** `paths:` is doc-confirmed buggy (#23478 read-not-write; #16299 maybe-global). The whole −271 came from path-stable stubs with zero mechanism risk. `paths:` would have bought nothing reliable here.
4. **`brand` tier is empty for rules — confirms the layer model.** Every market-specific thing is config (overlay/`brand.yaml`), never a rule. This validates charter §1 "adding a brand = adding config (OCP)": the rule layer is `core | project` only.
5. **The pointer-baseline ratchet works as designed.** Moving a dead ref into the (unscanned) `rules-detail/` drained it from the scanned surface → shrink-only `--update-baseline` cleanly removed it. Anti-rot governance survived a refactor without manual baseline surgery.

## 5 · Pointers

- `docs/process/harness-rules-audit-2026-06-08.md` — the 3-tier analysis (input).
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md` §6 — the conformance checklist validated against.
- `docs/process/harness-refactor-charter-2026-06-08.md` — the constitution.
- `W1-phase2-execution.md` — the staged coordinated Tier-3 eviction plan.
