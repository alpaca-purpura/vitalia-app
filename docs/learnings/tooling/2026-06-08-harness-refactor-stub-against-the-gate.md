# Harness refactor — "stub against the gate" + verify the consumer side

**Date:** 2026-06-08 · **Origin:** harness-refactor W1 (rules) · **Scope:** every B-phase surface refactor (W2 skills · W3 agents · W4 hooks · W6 templates). **Promotable:** candidate (CORE harness governance). **CIL lane:** L2.

## What happened

Two failure modes surfaced while stubbing the always-on rules:

1. **Over-stubbing silently broke a deterministic gate.** Stubbing `definition-of-done-live-verify.md` (276→70) dropped the literal string `scripts/mutation_gate.py`. `scripts/validate_machinery_consistency.py` CHECK 19 asserts that Critical Rule #37 §2 *hosts* that string. The prose still read fine; `make machinery-check` went red. Caught only by running the check **after** apply.

2. **The audit's one HIGH-risk dependency was a phantom.** `step-0-worktree.md` declares (in its own frontmatter) that it is `@`-imported by the pm skills. `grep '@.claude/rules/' .claude/skills/pm-*/SKILL.md` = **0 hits**. The producer's self-description claimed a consumer relationship that does not exist.

## The lesson (durable)

- **A rule/skill/agent body is sometimes a load-bearing string for a machinery check, not just prose.** When you stub or move it, stub *against the gate*: re-run `make machinery-check` (+ `scan_harness_pointers.py`, + the touched hook) **after every apply**. Green prose ≠ green gate. Budget shrink is worthless if it trips an enforcement check.
- **Verify the consumer side of a claimed dependency, never the producer's self-description.** "Consumed by X via @import" written in a file proves nothing — grep X. Anti-false-positive means checking who *actually* reads the file, at the path/slug they read it by.
- **The robust shrink lever is stub-in-place + `docs/rules-detail/`, not `paths:`.** `paths:` is doc-confirmed buggy (#23478 read-not-write, #16299 maybe-global). The entire W1 −271-line win was path-stable stubs with zero mechanism risk.
- **`tier:core` is EARNED (proxy-clean), not assigned by intent.** Tagging a file `core` because it *feels* like process is lens-1 only — that's "polishing, not separating" (charter §0.5). Run the dependency-grep (the cheap W8) over every file you tag `core`; **>0 tech/brand tokens ⇒ re-tag `hybrid`** (per option (b), ratified 2026-06-08), don't leave it `core`. W1's first pass tagged 22 `core`; the proxy found 13 carried tokens → corrected to 18 proxy-clean `core` + 4 `hybrid` + 9 trivial-token cleanups. The `{slot}` rewrite stays W5; the B-phase job is to keep the `core` tag honest, not to wire the seam early.

## How to apply (every workstream session)

After any stub/move/merge of a harness file: `make machinery-check` (0 fallos) + `python3 scripts/scan_harness_pointers.py` (NEW 0) + smoke the specific hook/script that greps the moved file (matrix in `W1-phase2-execution.md` §0). Drain any now-fixed `harness-pointer-baseline.txt` line (shrink-only).

## Refs

- `docs/process/harness-refactor-w1/W1-OUTPUT.md` §4 — the W1 learnings
- `docs/process/harness-refactor-charter-2026-06-08.md` §7 — fed back as a convention
- `scripts/validate_machinery_consistency.py` · `scripts/scan_harness_pointers.py`
