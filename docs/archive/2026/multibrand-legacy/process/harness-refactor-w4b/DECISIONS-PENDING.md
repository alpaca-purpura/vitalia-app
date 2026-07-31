# W4b · Pending process decisions (surfaced 2026-06-09 · ratify in the next session)

> **★ RATIFIED by Chris · 2026-06-09 (start of W6 session).** All 3 recommendations CONFIRMED as written.
> - **D1 (Stop-hook caps):** keep COARSE per-brand net; do NOT duplicate the module-scoped rule; seam the cap NUMBERS → **W5** (`wip_caps` slot). Implement at W5.
> - **D2 (shared git-hook source):** canonicalize on `main` + fix `install-hooks` `$TOP`→stable path; hub-pointer = accepted TEMPORARY stopgap until the W-series merges → **W7 + governance**. Implement at W7.
> - **D3 (machinery CHECK 11 G8/G9):** iterate the gate REGISTRY (OCP, not a frozen literal) + document G8/G9 in `cap-deterministic-enforcement.md` → **W6 (THIS session — IMPLEMENT now)**.
>
> Routing stands as the table in § Routing summary below.

**Origin:** harness-refactor W4b found 3 questions the `PROCESS-MODEL.md` does NOT resolve. Per HLP governance I did NOT unilaterally change semantics — I fixed only unambiguous drift and FLAGGED these. Each carries my recommendation reasoned from **SOLID + maintainability + scalability** (the charter §4 constitution). **Ratify (confirm/adjust) at the start of the next structural session; route each to its WS.**

> **Posture (verbatim from Chris):** verify what was done WELL first — do NOT assume everything is broken and rebuild a lower-quality version, and do NOT patch-on-top into a Frankenstein. Each fix is root-cause + best-possible, with research room.

---

## Decision 1 — Stop-hook WIP caps: coarse v4-global vs canonical v5 module-scoped · routes to **W5**

**Context.** `scripts/validate_session_close.py` (the `Stop` hook) enforces WIP caps at session close. W4b fixed it to read per-brand (was a single-brand no-op), but its CAP numbers are still the **paradigm-v4 GLOBAL** set (`refining≤3 … developed≤10 … reviewing≤2`). The **canonical v5 WIP cap is module-scoped** (`developed≤1 per code:{module}`, `story-closure-gate.md` WIP-cap v2), enforced by the **pre-commit `12-story-closure.sh`** gate.

**Question.** Should the Stop hook adopt module-scoped v5 (replicating the per-commit gate), or stay a coarse net?

**SOLID / maintainability / scalability.**
- **DRY + one-SSoT-per-concern (the very thing W4b's drift violated):** the module-scoped rule already has ONE home (the pre-commit gate + `story-closure-gate.md`). Re-implementing it in the Stop hook = a **second SSoT of the same rule** → exactly the drift that just bit us (the Stop hook silently fell behind to v4). **Reject duplication.**
- **SRP (different responsibilities, different trigger points):** the pre-commit gate's job = *block a commit* that breaks module WIP (precise, per-module, commit-time). The Stop hook's job = *catch session-close hygiene* (uncommitted, stale, GROSS over-accumulation). A coarse per-brand "you've piled up 8 refining stories" net is a **distinct, complementary** responsibility at a different altitude — not a duplicate of the precise gate.
- **DIP:** if we DO want the Stop hook to surface precise module violations, it should **delegate to the canonical script** (shell/import the same check the pre-commit uses), never re-implement the algorithm.

**Recommendation (do this):** **Keep the Stop hook COARSE; do NOT re-implement module-scoping.** (a) Document the SRP split (coarse close-time net ≠ canonical commit-time gate — W4b already added this note). (b) In **W5**, lift the cap NUMBERS to a seam slot (`wip_caps` under the project config) so a new product tunes them without editing the CORE. (c) IF a precise close-time signal is later wanted, have the Stop hook **shell the canonical gate** (one implementation, two call sites) — do not fork the rule. **Net: one SSoT for the WIP rule; the coarse net is a legitimate separate concern; seam the numbers.**

---

## Decision 2 — Canonical shared git-hook source: `main` vs the active hub · routes to **W7 + governance**

**Context.** `.git/hooks/` is SHARED across all worktrees (common git dir). `make install-hooks` symlinks from `$TOP` (= whatever worktree you run it in). W4b re-ran it from the vitalia hub (fixing a stale pre-push *copy*), so the shared hooks now symlink into `luana-vitalia/scripts/git-hooks/`. `main` lags (the W1-W4b harness work is on `wip/vitalia`, un-merged).

**Question.** Should the shared hooks point to (a) `main` (PRINCIPAL — stable, never removed, but content lags until the harness work merges), or (b) the active hub worktree (current content, but coupled to that worktree's existence/branch)?

**SOLID / maintainability / scalability.**
- **DIP + stable-abstraction:** a SHARED resource must depend on a **stable** source, not a volatile one. `main`/PRINCIPAL never disappears; a brand hub can be removed or switch branches. Pointing the shared gate at a volatile worktree = depending on a concretion that can vanish → fragile (breaks every worktree's git ops if vitalia is removed).
- **The real smell is `install-hooks` itself:** it sources from `$TOP` → the hook source is **non-deterministic / last-writer-wins** across worktrees. That's the defect to fix, not "which worktree won this time."
- **The tension (currency vs stability)** is a **merge-cadence** symptom, not an architecture choice: harness work SHOULD reach `main` to be live for everyone. "main lags" ⇒ merge it, don't couple the gate to a hub to dodge the merge.

**Recommendation (do this):** **Canonicalize on `main` + make `install-hooks` source-deterministic.** (a) Fix the `install-hooks` target to symlink from a STABLE canonical path (the PRINCIPAL worktree's `scripts/git-hooks/`, or a `$GIT_COMMON_DIR`-relative path), NOT `$TOP`. (b) Establish the cadence: hook edits land on `wip/*` → merge to `main` → `main` is the canonical running gate. (c) **Stopgap until the W-series merges to main (ACCEPTED for now):** the hooks pointing at the vitalia hub is fine — solo-operator + vitalia is a stable canonical hub + it carries the current harness work. Treat it as TEMPORARY, resolved when the refactor merges. **Net: shared gate depends on a stable abstraction; fix the source-non-determinism; the lag is a merge step, not a coupling.** (Interacts with W7 physical-move + the eventual program→main merge.)

---

## Decision 3 — machinery CHECK 11 does not assert G8/G9 cap-gates · routes to **W6**

**Context.** `scripts/validate_machinery_consistency.py` CHECK 11 (anti-rot) asserts the cap-gate dispatcher (`run_cap_gates`) + `--cap-gates-hard` + a G1-G6 repro, but does NOT individually assert that **G8/G9** (`user_visible_has_description` / `user_visible_has_scenario`, added later per HB-52/56) are defined. Deleting G8/G9 would NOT trip the anti-rot gate (latent paper-rule). They have their own negative tests, so it's latent, not live-broken. Also: `cap-deterministic-enforcement.md` documents only G1-G7 (G8/G9 doc-lag).

**Question.** How to close the latent anti-rot gap without re-introducing brittleness?

**SOLID / maintainability / scalability.**
- **OCP (the scalable fix):** CHECK 11 hardcodes the gate set `{G1..G6}`. The anti-rot meta-check should **iterate the gate REGISTRY** (the validator's `GATE_IDS` / `run_cap_gates` registration), not a frozen literal — so adding **G10** later is covered automatically (extend by adding a gate; the meta-check picks it up; no edit to CHECK 11). A frozen list is the anti-pattern that produced this gap.
- **One-SSoT:** document G8/G9 in `cap-deterministic-enforcement.md` (close the doc-lag, Batch A §3.5) so the doc and the code agree on the gate inventory.

**Recommendation (do this in W6):** (a) Refactor CHECK 11 to derive the asserted gate set from the validator's gate registry (OCP — future gates auto-covered), keeping the G1+G2 repro test. (b) Add G8/G9 to `cap-deterministic-enforcement.md`. **Low-risk, high-value: closes the latent gap permanently + future-proofs the anti-rot meta-check.** This is cap-enforcement machinery (W6 docs/process surface), not W4b scripts/cockpit — correctly deferred.

---

## Routing summary

| # | Decision | My recommendation (1-liner) | WS |
|---|---|---|---|
| 1 | Stop-hook WIP caps | Keep coarse (distinct SRP); do NOT duplicate the rule; seam the numbers; delegate if precision wanted | **W5** |
| 2 | Shared git-hook source | Canonicalize on `main` + fix `install-hooks` `$TOP`→stable path; hub-pointer is a temporary stopgap until the W-series merges | **W7 + governance** |
| 3 | machinery CHECK 11 G8/G9 | Iterate the gate registry (OCP), not a frozen list; document G8/G9 | **W6** |

**Common thread (the constitution):** every recommendation favors **one SSoT + a stable abstraction + extend-don't-edit (OCP)** over duplication / coupling / frozen lists. None requires rebuilding a working surface; each is a root-cause refinement of something already mostly-right.
