# Harness Rules Audit — Decision Doc (W1)

**Date:** 2026-06-08 · **Owner:** /pm-luana (harness session) · **Status:** classified + mechanism-verified · **NOT yet executed** (pending Chris ratify + one empirical test).

> Scope: the 46 always-on files in `.claude/rules/` (2012 lines / ~18.6k tokens loaded EVERY session). Goal of the parent refactor: a SOLID/clean-code, **portable** harness base — change project tomorrow → swap tech/paths/brand, keep the base. Don't force-abstract genuinely project-specific rules.

---

## 0. Provenance + integrity note

- Mechanism truth (§1) = **independently verified by the main thread** against official Claude Code docs + GitHub issues (citations inline). HIGH confidence.
- Per-rule classification (§3) = produced by a Workflow whose 8 deep cluster-auditors **failed on a schema technicality** (returned `[]`); the synthesis-lead re-derived classifications from rule bodies. Treat actions as **proposed**, refined here by the verified mechanism. Dependency (body-grep) checks still required before executing any MOVE/EVICT (§5 step 0).
- The earlier synthesis recommended bulk `globs:`→`paths:` (22 files). **This doc OVERRIDES that** based on the GitHub-issue findings below — `paths:` is buggy; the robust home for domain rules is Skills.

---

## 1. Verified mechanism truth (Claude Code, June 2026)

Source: https://code.claude.com/docs/en/memory + issues #23478, #16299.

- `.claude/rules/*.md` is **native**. All `.md` discovered recursively. **Rules WITHOUT `paths:` load at launch, always-on, CLAUDE.md priority.** → our 46 files are all always-on (none use `paths:`; 22 carry Cursor `globs:` which Claude Code **ignores**).
- `paths:` (YAML glob list) is the **native conditional-load** field. Path-scoped rules "trigger when Claude **reads** files matching the pattern, not on every tool use."
- Official guidance: *"If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a **skill** or a path-scoped rule."* Skills "only load when invoked or when Claude determines they're relevant."
- `@import` is **CLAUDE.md-only**, loads at launch, **does not reduce context** (and does NOT expand inside SKILL.md). → dedup via `@include` is off the table; use pointer + on-demand Read.
- **BUG #23478 (CLOSED / wontfix):** `paths:` rules load on **Read, not Write**. A rule scoped to backend paths is **absent when Claude CREATES a new backend file** without first reading a matching one. → security/invariant rules that fire at write-new-code time **cannot** be `paths:`-scoped.
- **BUG #16299 (OPEN, v2.0.76, no fix):** `paths:`-scoped rules reportedly **load globally regardless of `paths:`** for some users (regression). → before trusting `paths:` to reduce always-on, run a one-file empirical test in THIS Claude Code version.

**Net:** the only **reliable, doc-blessed** levers are (a) keep the lean always-on core, (b) **stub-in-place** fat always-on rules (path-stable, zero breakage), (c) **move domain/phase knowledge into the owning Skill's `references/`**. `paths:` is a *conditional* nice-to-have, usable only for read-triggered convention rules and only after the test.

---

## 2. Target architecture — 3 tiers

**Tier 1 · Always-on core (no `paths:`)** — true cross-cutting invariants + anything that must fire at write-new-code time. Keep lean (~11–13 files, ~450 lines). This is the portable base.

**Tier 2 · `paths:`-scoped (conditional, read-triggered)** — ONLY low-risk *convention* rules where the read-trigger is acceptable and the write-gap (#23478) doesn't matter (you're editing/reading existing code, not relying on it for new-file safety). Apply ONLY after the #16299 empirical test passes. Candidates: `debugging`, `backend-quality`, `frontend-quality`, `frontend-fsd`, `frontend-visual-fidelity`, `architectural-fitness`, `backend-migrations`, `offer-catalogs`/domain (if not skill-evicted).

**Tier 3 · Skill `references/` (the robust home for domain + multi-step phase knowledge)** — domain rules (offer, copilot, analytics, sales-agent, admin, etl, data-reliability, master-data/currency, form-runtime) and PM/auditor/dev-team *phase* procedures. These already have owning skills; move the body to `references/`, leave a thin pointer (or delete the rule if skill + `contract-guard.js` already cover it).

---

## 3. Per-rule classification (corrected by mechanism)

`port`: GENERIC (carries to any project) · STACK (rewrite per project) · HYBRID. `tier`: target tier. Action corrected from raw synthesis per §1.

### Tier 1 — STAY ALWAYS-ON (keep; stub if fat, path-stable)
| file | lines | port | action | note |
|---|---|---|---|---|
| git-safety.md | 47 | GENERIC | KEEP (strip dead `globs`) | every commit |
| parallel-safety.md | 72 | GENERIC | KEEP | multi-session, every turn |
| tenant-isolation.md | 17 | STACK | KEEP (never paths — #23478) | security, fires on write |
| pii-sanitisation.md | 42 | STACK | KEEP (never paths — #23478) | security, fires on write |
| spanish-text.md | 36 | STACK | KEEP | UI/agentic output guard |
| paradigm-arquitectura.md | 68 | GENERIC | KEEP | north-star decision tree |
| story-closure-gate.md | 71 | GENERIC | KEEP (trim ok) | lifecycle spine |
| anti-orphan-integration.md | 29 | GENERIC | KEEP | CONN, all outputs |
| anti-duplication.md | 69 | HYBRID | **STUB** (cardinal stays; engine-inventory table → detail) | grep-before-write doctrine always-on; table stack-specific |
| learning-capture.md | 37 | GENERIC | KEEP | trigger any turn |
| claude-md-overlay.md | 33 | GENERIC | KEEP | meta |
| tdd-mandatory.md | 32 | GENERIC | KEEP (6-line invariant stub; body→dev-team ref) | invariant must stay visible |

### Tier 1 — STUB-IN-PLACE (fat always-on; biggest wins, zero breakage)
| file | lines | action | saved | risk |
|---|---|---|---|---|
| **definition-of-done-live-verify.md** | 276 | **STUB** (keep path; body→`docs/rules-detail/`; ~30-line cardinal+`dod_evidence` schema stays) | **~245** | path-stable; literal refs resolve (file stays) |
| auditor-self-fix-policy.md | 82 | **STUB** (delete dead v4.2 block; keep v5 cardinal; detail exists) | ~60 | low |
| debugging.md | 59 | STUB or Tier-2 paths (post-test) | ~35 | low |

### Tier 3 — EVICT TO OWNING SKILL `references/` (domain/application, brand-varying)
Robust per docs. Each = move body + update skill pointer + update `contract-guard.js` advisory path (verified: contract-guard.js references offer-catalogs/analytics/etl/copilot by path).
| file | lines | owning skill | note |
|---|---|---|---|
| offer-catalogs.md | 31 | offer-expert / offer-type-preset-expert | skill loads it 1st-turn today |
| analytics-metrics.md | 32 | metrics-expert | contract-guard ref |
| etl-extraction-contract.md | 27 | metrics-expert | contract-guard ref |
| copilot-resilience.md | 25 | copilot-expert | contract-guard ref; MERGE observability in |
| copilot-observability.md | 25 | copilot-expert | MERGE → copilot-resilience |
| sales-agent-brand-voice.md | 19 | sales-agent-expert | ux-agentico loads it |
| data-reliability.md | 24 | metrics-expert | ⚠️ Makefile targets stale (separate fix) |
| admin-panel.md | 29 | backend-expert | opt-in feature |
| master-data.md | 16 | backend-expert | absorbs currency |
| currency-handling.md | 18 | backend-expert | MERGE → master-data |
| form-runtime-array.md | 16 | brand-expert / offer-expert | FE form convention |
| e2e-testing.md | 52 | playwright-expert (already SSoT) | ⚠️ `e2e-preflight.sh` cites path |

### Tier 3 — EVICT TO SKILL `references/` (PM/auditor/dev-team PHASE procedures)
Already mostly slim stubs whose bodies live in skill references; finish the move + trim.
| file | lines | owning skill | risk |
|---|---|---|---|
| step-0-worktree.md | 80 | pm/* references | **HIGH — `@`-imported by pm skills; repoint in same commit** |
| brand-docs-schema.md | 44 | pm-{brand} references | med |
| auditor-downstream-regression.md | 45 | auditor references | **DO NOT silently move — `04-r3-ssot.sh` greps its BODY table; keep table reachable** |
| anti-default-flip-audit.md | 40 | dev-team/auditor refs | keep flag-inventory table |
| hotfix-repro-mandatory.md | 30 | dev-team/po refs | low |
| anti-duplication-refining.md | 33 | pm/po/architect refs | low |
| test-design-doctrine.md | 31 | dev-team refs (body already there) | low |
| architect-autonomous-mode.md | 27 | architect refs (body there) | low |
| git-haiku-delegation.md | 26 | commit-push refs (body there) | low |
| worktree-dual-strategy.md | 27 | worktree-protocol refs (body there) | low |
| pm-skill-chaining.md | 29 | pm skills (body replicated) | low |
| github-actions-deferred.md | 34 | (Tier-2 paths or keep) | low |

### Tier 2 — `paths:` candidates (ONLY post #16299 test; never for write-time-safety rules)
`backend-ddd, backend-quality, frontend-fsd, frontend-quality, frontend-visual-fidelity, architectural-fitness, backend-migrations, debugging`. ⚠️ `backend-ddd`/`architectural-fitness` also matter at write-new-code → if write-safety is wanted, keep always-on or skill-ref instead. Decide per rule after test.

---

## 4. Budget

- Now: **2012 lines always-on**.
- After Tier-1 stubs (DoD + auditor-self-fix + anti-dup table) ≈ **−350** with zero breakage.
- After Tier-3 eviction (domain + phase) ≈ **−600 more** (coordinated edits).
- Projected lean always-on core ≈ **450–550 lines (−73 to −78%)**.

---

## 5. Execution order (safe-first)

0. **Empirical test:** convert ONE low-risk rule to `paths:` (YAML list), open a NEW session, run `/memory`, confirm it does NOT load when no matching file is touched. Resolves #16299 for our version. (Chris or `InstructionsLoaded` hook.) → decides whether Tier 2 is viable at all.
1. **Tier-1 stub-in-place** (path-stable, zero breakage): `definition-of-done-live-verify` (biggest win), `auditor-self-fix-policy` (delete dead v4.2), `anti-duplication` (table→detail). Detail bodies → `docs/rules-detail/`. **Safe to do now.**
2. **Tier-3 domain eviction** (coordinated): per rule — `git mv` body to skill `references/`, update skill 1st-turn pointer, update `contract-guard.js` path string. Dependency-grep gate per file first. Merges: copilot-observability→copilot-resilience, currency→master-data.
3. **Tier-3 phase eviction:** the already-slim ones first (low risk); `step-0-worktree` LAST with the `@`-import repoint in the same commit (HIGH). `auditor-downstream-regression` stays reachable for `04-r3-ssot.sh`.
4. **Tier-2 `paths:`** only if step 0 passed, only for the convention subset.
5. Clean dead `globs:` frontmatter from any rule that stays always-on.

**Guardrail (HLP):** harness refactor in a dedicated session; coordinated steps in `wip/protocol-rules-refactor` with `SCOPE_GATE_SKIP=1`, ratified. Steps 1 is safe anytime.

---

## 6. Portability manifest (Chris's original goal)

**GENERIC_PROCESS (copy to any project ~unchanged):** git-safety, parallel-safety, worktree-dual-strategy, step-0-worktree, git-haiku-delegation, story-closure-gate, anti-orphan-integration, paradigm-arquitectura, pm-skill-chaining, learning-capture, claude-md-overlay, github-actions-deferred, tdd-mandatory, test-design-doctrine, definition-of-done-live-verify (stub), hotfix-repro-mandatory, anti-default-flip-audit, auditor-self-fix-policy, auditor-downstream-regression, architect-autonomous-mode, anti-duplication-refining, anti-duplication (doctrine half).

**STACK_SPECIFIC (rewrite per project — expected, don't force-abstract):** tenant-isolation, pii-sanitisation, master-data(+currency), backend-ddd, backend-quality, backend-migrations, architectural-fitness, frontend-fsd, frontend-quality, frontend-visual-fidelity, form-runtime-array, e2e-testing, debugging, spanish-text (locale), brand-docs-schema (docs layout), + all domain rules (offer/analytics/etl/copilot/sales-agent/admin/data-reliability).

**Lift checklist:** (1) copy GENERIC dir as-is; (2) split engine-inventory table out of anti-duplication into STACK; (3) regenerate STACK rules for the new stack; (4) the GENERIC `paths:` (mostly `.github/**`, `**/tests/**`) port verbatim.

---

## 7. Open items

1. **#16299 empirical test** (gates Tier 2). Until passed, treat `paths:` as unproven in our version.
2. The 8 deep cluster-auditors should be **re-run without schema** (text return) if we want auditor-ratified vigencia + per-rule grep-dependency before the Tier-3 moves. Cheaper alternative: a single deterministic dependency-grep pass over the Tier-3 file list.
3. `data-reliability.md` Makefile targets are stale (single-brand legacy) — separate story, not this refactor.
