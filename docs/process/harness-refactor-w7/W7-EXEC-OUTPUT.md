# W7-EXEC · The physical move EXECUTED (Option C + plugin-shape) — Output

**Date:** 2026-06-09 · **Session:** harness-refactor **W7-execution** (C-phase · STRUCTURAL · the move) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` · **Status:** ✅ **MOVE EXECUTED + W8 extraction-test PASSING.** Machinery **65/0/0**, pointers **28/NEW-0** held through every group. Mechanism = the Chris-ratified **Option C** (per-surface doc-safe) + plugin-shape (`W7-OUTPUT.md §2`). One residual: the rules always-on **restart-smoke** is PENDING (a fresh session — doc-safe by spec, see §6).

> **North-star card:** *Succeeds only if (1) it implements its work-type, AND (2) every core-tagged file names ZERO tech/brand tokens. Goal = extractable `core-harness/`, not a nicer luana harness.* **MET:** the POST-move dependency-grep over `core-harness/` = **2 hits, both grep-bot's generic build-artifact skip-dirs** (`.venv`/`.next` in exclusion lists — W3-blessed functional exception); zero project smear. W8 then proved a *different* product runs the cycle without editing the core (§7).

---

## 1 · What moved (per-group, risk-ascending, validate-after-each → commit green)

Every group: dependency-grep gate (proxy-clean only) → `git mv` to `core-harness/` → `ln -sr` symlink-back at the OLD path (read-by-path / doc-safe) → smoke → `machinery 65/0/0` + `pointers NEW 0` → commit (pre-commit hook = live smoke) → push. Repo never half-moved-roto.

| Grp | Surface | Files → `core-harness/` | Mechanism | Commit |
|---|---|---|---|---|
| 1 | process-docs (6) + templates (5) | `process/{cockpit-permissions,continuous-improvement,harness-lifecycle,tech-debt,ticket-states,spec-mapa-funcional}` · `templates/{00-chris-input,00-research,00-story,01-spec,story-ui.yaml}` | symlink-back (read-by-path) | `62edb18d` |
| 2 | seam loader + 6 git-scripts | `scripts/harness_config.py` · `scripts/git/{commit-paths,session-lock,multi-session-scope-guard,dod-evidence-gate,cleanup-wip-branches,ps1-luana}.sh` | symlink-back; loader/import/dispatcher smoked | `7fe0eea0` |
| 3 | 3 core pre-commit checks | `hooks/checks/{07-checkpoint-enum,11-worktree,17-checkpoint-dupkeys}.sh` | symlink-back (dispatcher `source`s them) | `979484e3` |
| 4 | 1 core agent | `agents/grep-bot.md` | **COPY** (agents-symlink undocumented #14836; live `.claude/agents/` stays real) | `caf8a360` |
| 5 | 21 core rules | `rules/*` (18 W1-core + 3 W5b-lifted: anti-duplication, parallel-safety, auditor-downstream-regression) | symlink-back into `.claude/rules/` (**DOC-SAFE** always-on) | `0913d409` |
| — | D2 + plugin finalize + proxy-clean | `Makefile` (D2) · `hooks/always-on-core.manifest` (curated) · README/bootstrap genericized | — | `3b82ea9b` |

**Proxy-cleaned in-place (option-b trivial-token path · illustrative tokens in docstrings/messages/comments/self-docs):** 01-spec `FastAPI/Zod`→generic · harness_config docstring `dev-app`→`live-env` · dod-evidence-gate message `dev-app`→`entorno live` · ps1 `vitalia`-example→`{brand}` · paradigm `PHI`→`datos sensibles/regulados` · README/bootstrap "NOT-here" list + `dev-app`→`live-env`.

## 2 · Refs rewritten — almost none (path-stability is the W7 super-power)

The §1-de-risk held perfectly: **both symlink and copy keep the OLD path resolving** → the machinery validator's **29 hardcoded `.claude/` paths**, the cockpit's by-path reads, the 13 `harness_config.py` consumers, the pre-commit dispatcher's `source "${CHECKS_DIR}/NN.sh"`, and every `${REPO_ROOT}/scripts/git/X.sh` call all resolve transparently. **Zero consumer repoint was needed.** `machinery 65/0/0` confirmed the validator reads every moved file through its symlink and still finds every load-bearing string (CHECK 9/25/27 read `01-spec` via symlink; the 21 rule bodies read via `.claude/rules/` symlinks).

**The one verified mechanism subtlety (Group 2):** `harness_config.py::find_config` does `Path(__file__).resolve()` (follows the symlink to the real path) + a **full parent-walk to repo root**. From EITHER the symlink path (`scripts/`) or the real path (`core-harness/scripts/`) the walk reaches the repo-root `project.config.yaml`. Smoked from both paths (exit 0) + the 13-test suite + a `--where` facet query.

## 3 · D2 — `make install-hooks` determinism (implemented, NOT re-run)

`install-hooks` now resolves the shared `.git/hooks` source from the **canonical MAIN worktree** (`dirname "$(git rev-parse --git-common-dir)"`), NOT `$TOP` (the invoking worktree → last-writer-wins). DIP: a shared resource depends on a stable source. **Not re-run this session** — the vitalia-hub stopgap stays until the W-series merges to `main` (cadence: `main` IS the canonical running gate; "main lags" is a merge step). Dry-resolved correctly to `/home/chalreme/Proyectos/luana-platform` (whose `scripts/git-hooks/pre-commit` exists). `make -n install-hooks` syntax ✓.

## 4 · Plugin-shape finalized

- `hooks/always-on-core.manifest` **curated** = the 3 hard always-on CONSTRAINTS that fit the ≤9.5k SessionStart cap without mid-rule truncation: `anti-duplication` (grep-before-write) + `git-safety` + `tdd-mandatory` (8267 chars). Injector smoke: valid `additionalContext` JSON, **8090 chars**, all 3 present, no truncation. The full 21-rule corpus loads via `/harness:bootstrap`.
- `.claude-plugin/{marketplace,plugin}.json` component dirs are populated by the move: `skills/harness-bootstrap` · `agents/grep-bot` · `hooks/{hooks.json,session-start-rules.sh}`. (`commands/` absent — no core commands; optional.) Inert until `/plugin marketplace add ./core-harness`.

## 5 · ★ Findings that CORRECT the move manifest (W7-OUTPUT §3)

1. **The 14 rules-detail mirrors are tier:PROJECT, NOT core — they did NOT move.** The dependency-grep showed every candidate detail carries 6–45 tech/brand tokens: they ARE the stack-specific half that was *stubbed OUT* of the slim always-on rule (engine inventory, brand bash, dev-app creds, …). The portable IP is the **slim always-on rule**; the detail is the project elaboration. The kit ships 21 slim rules; an adopter writes their own `docs/rules-detail/`. (W7-OUTPUT §3 had said "21 core rules + their core rules-detail mirrors" — empirically only the slim rules are core.)
2. **The kit-doctrine docs (charter / PROCESS-MODEL / REQ-TAKING-DETAIL) are tier:HYBRID program-record, NOT shipped core.** charter=13 / PROCESS-MODEL=15 proxy hits — they're token-heavy (the luana refactor diary). Shipping them would break the measured DoD AND give an adopter luana's refactor history. They STAY in `docs/process/harness-refactor-*`; the kit README points to them. (Only `core-harness/process/` proxy-clean P1 doctrine moved.)
3. **INDEX.md stays project** (1 `ruff` token — it indexes luana's specific rule-detail set, a project navigation artifact).

## 6 · Restart-smoke — PENDING (the one residual · doc-safe by spec)

The rules group is **symlink-back into `.claude/rules/`**, which is **DOCUMENTED-SAFE** for always-on load (the CC memory doc: `.claude/rules/` resolves symlinks, recursive, circular-safe). The machinery validator confirms the 21 rules are READABLE through the symlinks (it reads them + finds all load-bearing strings). The one thing un-observable mid-session is the **always-on auto-injection in a FRESH session**. Per the playbook this needs a session restart.

**Action for Chris (fresh session):** confirm `/memory` (or the rule auto-load) lists the symlinked rules + their bodies inject always-on. Doc-safe → expected pass; this is belt-and-suspenders. **IF it fails → it reopens the Option-C mechanism (escalation condition d)** — but `.claude/skills/` symlinks (clerk/sentry) already load in-session, and `.claude/rules/` symlink is doc-blessed, so the risk is low.

## 7 · W8 — extraction test PASSING (the program DoD made measurable) → `W8-OUTPUT.md`

In a clean `/tmp` git repo, `cp -r core-harness/` (50 self-contained real files, 0 inner symlinks) + an all-`__FILL_ME__` `project.config.yaml`: `harness_config.py --doctor` → **exit 3**, self-declared all **11 unfilled slots**. Filled with a **fictional product** (`ledgerline` — Go/SQLite single-tenant bookkeeping CLI, en-US, no web UI — deliberately ≠ luana) → `--doctor` **exit 0** ("idea→done runs without editing the CORE"). Slot reads returned ledgerline values (`go vet ./...`, `en-US`, `github.com/acme/ledgerline/internal/`, single brand `main`), the `--where cap_gate` facet resolved. The copied core = **0 luana** in rules/templates/process/scripts/hooks (only grep-bot's 2 blessed). Full detail in `W8-OUTPUT.md`.

## 8 · R-OBS + R-CI (transversal invariants — intact)

- **R-OBS (cockpit sees everything):** the move was **path-stable** for every `.md`/`.yaml` the cockpit reads → board/functionality/agents/map/harness unaffected. **No cockpit file touched** → no tsc/vitest needed (last green: W6/W4b). Invariant holds.
- **R-CI (self-improvement loop):** the CIL process-docs (`continuous-improvement`, `harness-lifecycle`, `tech-debt`) moved to `core-harness/process/` + symlinked back → load preserved; `harness-backlog.md` (project data) untouched. This session routes its learnings to the CIL lanes (§10), not a 5th store. Invariant holds.

## 9 · W7-tail (deferred, documented — like W1-Phase2)

- **architect-`{be,fe,agentic}` instruction-doc rehoming** → `architect/references/`. **Deferred.** These are **tier:HYBRID** (project-side, NOT a core move) and the repoint touches **machinery-asserted** validator paths (L54-55/193-195 + baseline L13-14 + 3 templates). It does NOT advance the extraction DoD (the core is already grep-clean). Grouped with the B-phase tail for a focused pass to avoid risking the machinery-asserted gate under an extraction-focused session. Evidence: W3-OUTPUT §3.
- **W1-Phase2** (Tier-3 rule eviction, `wip/protocol-rules-refactor`) + **Tier-2 `paths:`** (#16299 empirical test) — unchanged B-phase tail.

## 10 · Learnings → CIL lanes

1. **(L2) `git mv` of a working-tree-EDITED file stages the rename of the ORIGINAL blob — the edit stays UNSTAGED at the new path.** Group-1's 01-spec FastAPI-clean was deferred out of its commit (on-disk stayed correct via the symlink; only the git blob was stale). *Lesson: when you edit-THEN-`git mv`, you must `git add <newpath>` to capture the content edit; verify the STAGED blob (`git show :path`), not just the working tree.* (Caught by re-grepping the staged content.)
2. **(L2) `Path(__file__).resolve()` + full-parent-walk is what makes a relocated-via-symlink loader portable.** Because `resolve()` follows the symlink to the real dir and the walk climbs to repo root, the config is found from either path AND inside the right worktree. *Lesson: a read-by-path module that walks for a root marker survives a symlink relocation iff it resolves `__file__` and walks to the marker (not a fixed `../`).* The single biggest Group-2 de-risk.
3. **(L2) "Move by tag" silently assumes the tagged files are PROXY-CLEAN at the leaf.** The rules-detail mirrors were tagged "core" by parent, but each carries the stack-specific half — they're project. *Lesson: re-run the dependency-grep per-file at execution (don't trust the manifest's parent-level tag); the proxy is the arbiter of what physically moves.* → corrects W7-OUTPUT §3.
4. **(L1 · HB candidate) The kit's OWN self-docs (README/bootstrap) carried illustrative tech tokens** ("NOT here: FastAPI/.../vitalia"). Genericizing them ("your stack's framework/auth/linter") is both proxy-clean AND clearer for an adopter on a different stack. *Lesson: a kit's self-documentation should describe the SEAM generically, never by the source product's stack — the negative example IS a token.*

## 11 · Pointers
- `W7-OUTPUT.md` §2 (ratified mechanism) · §3 (move manifest, corrected by §5 here) · §9 (execution playbook).
- `W8-OUTPUT.md` (this dir) — the extraction-test detail.
- `core-harness/README.md` — the populated kit + re-expose mechanism + bootstrap procedure.
- `docs/process/harness-refactor-charter-2026-06-08.md` §6 — roadmap (W7 ✅ / W8 ✅ markers updated).

*End W7-EXEC-OUTPUT.md — the move is EXECUTED, green, extraction-test PASSING. Restart-smoke (rules always-on) PENDING a fresh session. W9 (legacy delete) = Chris gate, NOT autonomous.*
