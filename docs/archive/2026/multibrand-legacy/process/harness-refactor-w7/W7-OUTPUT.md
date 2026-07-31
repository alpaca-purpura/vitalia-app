# W7 · Core/Project/Brand physical move — Output (GATE-ZERO resolved + reshape escalation + move manifest + D2 spec + R-OBS/R-CI + execution playbook)

**Date:** 2026-06-09 · **Session:** harness-refactor **W7** (C-phase · STRUCTURAL · the physical move) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` · **Status:** ⛔ **GATE-ZERO HIT escalation condition (d) — the physical move is BLOCKED on a Chris ratification of the extraction-load mechanism.** This session resolved the gate-zero research (2 independent Opus passes, date-aware official docs), produced the complete move manifest + D2 spec + R-OBS/R-CI assessment + the post-ratification execution playbook. **ZERO live-harness edits** (machinery stays **65/0/0**, pointer **28/NEW-0**) — the move is mechanism-dependent, so nothing was moved.

> **North-star card:** *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens. The goal is an extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*
>
> W7 done-when (charter §6): *`core-harness/` with `grep`-tech = 0.* **Inputs:** charter §0.5/§2/§3/§4/§6 (the target tree + seam + fitness) · the 6 B/C-phase tier-manifests (`W{1,2,3,4,4b,6}-OUTPUT.md` — authoritative for WHAT each file is) · `W5-OUTPUT § W5b` (the seam is LIVE) · `DECISIONS-PENDING.md D2` (install-hooks determinism — W7 implements) · `PROCESS-MODEL.md §7` (R-OBS cockpit contract).

---

## 0 · Why this session STOPPED at the gate (the autonomy grant, honored)

The bootstrap grant reserves **one** decision for Chris even in autonomous mode (§autonomía (d)):

> *"el blocker de mecanismo de carga de W7 — si resulta que mover archivos fuera de `.claude/` rompe el auto-load → eso RESHAPEA el modelo de extracción = decisión de Chris."*

The gate-zero research (below, 2 independent passes) proves the trigger is met: **a naive physical move of `rules/` + `agents/` out of `.claude/` BREAKS Claude Code's always-on load / discovery.** The charter §2 literal ("move files to repo-root `core-harness/`, same load") does **not** survive as-written. The extraction model must be reshaped. Per the grant, the reshape choice is **escalated to Chris** with a fully-worked recommendation (§2). Everything that does NOT require that decision was prepared this session (the manifest, the D2 spec, the playbook). The move itself, D2's hook-source path, and W8 are all **downstream of the mechanism choice** → not executed.

This is the bootstrap's prescribed pattern: *"Si W7 es demasiado / hay un fork de mecanismo de carga → dejá un CHECKPOINT VERDE, documentá, parás. NUNCA dejes la maquinaria roja."* Machinery is green; nothing is half-moved.

---

## 1 · GATE-ZERO — does moving harness files out of `.claude/` break auto-load? (2 independent Opus passes, date-aware 2026-06-09)

**Method:** Opus research subagent fetched live official docs (`code.claude.com/docs/en/*` — note the `docs.claude.com → code.claude.com` 301 migration) + GitHub issues/CHANGELOG; an **adversarial** second Opus pass attacked the two load-bearing claims and corrected the first. Full citations: `GATE-ZERO-RESEARCH.md` + `GATE-ZERO-ADVERSARIAL.md` (this dir). **No model memory trusted.**

### Per-surface verdict (the matrix)

| Surface | Loads from | Move OUT of `.claude/` breaks load? | Symlink-back into `.claude/`? | Other channel? |
|---|---|---|---|---|
| **Rules** (`.claude/rules/*.md`, whole-dir always-on, **recursive into subdirs**) | `.claude/rules/` ONLY | **YES — hard gate** (no external-dir setting; no plugin rules channel) | ✅ **DOCUMENTED-SAFE** — memory doc: *".claude/rules/ supports symlinks… resolved and loaded normally, circular symlinks handled gracefully"* (dir **and** single-file) | none (plugin CLAUDE.md explicitly NOT loaded) |
| **Agents** (`.claude/agents/*.md`, recursive) | `.claude/agents/` ONLY (+ `~/.claude/`) | **YES** (excluded from `--add-dir`/`additionalDirectories`) | ⚠️ **UNDOCUMENTED** — docs silent; needs a session-restart empirical test | plugin `agents/` dir (copy-on-install) |
| **Skills** (`.claude/skills/{n}/SKILL.md`, parent+nested) | walk-up `.claude/skills/` + nested + `--add-dir` + plugin | PARTIALLY (recoverable) | ⚠️ **UNDOCUMENTED + open bugs** (#14836 `/skills` discovery doesn't follow symlinks though execution does; #36659 `.claude`-as-symlink) — *though luana's own `clerk-*`/`sentry-*` intra-repo skill symlinks DO load in this session* → works-here-but-flaky/version-dependent | `--add-dir` (launch-flag), plugin `skills/` |
| **Hooks** (`settings.json` → script path) | path reference | **NO** — script lives anywhere; only the path string moves | n/a (path-referenced) | `${CLAUDE_PROJECT_DIR}/core-harness/hooks/…` |

### The 3 corrections the adversarial pass made (verify > memory paid off)

1. **Rules symlink is DOCUMENTED-SAFE** (pass-1 had it "undocumented"). The memory doc explicitly blesses `ln -s … .claude/rules/foo.md`. This is the ONE always-on channel that is symlink-safe by spec.
2. **Plugin CANNOT ship always-on rules** (confirmed, kill-shot): *"A CLAUDE.md file at the plugin root is not loaded as project context. Plugins contribute context through skills, agents, and hooks."* The plugin manifest has no `rules` field. (Asterisk: a plugin `SessionStart`/`UserPromptSubmit` hook can *simulate* injection, non-declarative.)
3. **Skills/agents symlink is fragile** — undocumented + open bugs. luana's clerk/sentry skill symlinks happen to load *here*, but that's not a guarantee to build the program on across CC upgrades or in an unknown adopter repo.

### The decisive de-risk (changes the cost calculus)

**Both copy AND symlink keep `.claude/rules/foo.md` PATH-STABLE** — the file resolves at the same path either way. Verified: `validate_machinery_consistency.py` hardcodes **29 distinct `.claude/` paths** (rules/agents/skills) it `test -e` / `Read`s. Under EITHER doc-safe mechanism those 29 paths stay valid (a symlink resolves transparently; a copy is a real file there). **⇒ The bootstrap's feared "~40 validator paths to rewrite" largely evaporates.** The validator keeps reading `.claude/rules/definition-of-done-live-verify.md` and gets the content regardless of where the SSoT physically lives. (Only checks that assert a `core-harness/`-specific path — none today — would need touching.) This is the single biggest W7 de-risk and it holds for any reshape that keeps `.claude/` as the discovery surface.

---

## 2 · ★ THE FORK FOR CHRIS — the extraction-load mechanism (one decision, then W7 executes mechanically)

> **★ RATIFIED by Chris 2026-06-09 = Option C (per-surface doc-safe) + plugin-shape NOW.** After a clarification round on the plugin/marketplace distribution model (`PLUGIN-DISTRIBUTION-RESEARCH.md`), Chris's goal was reframed: the portable IP is **the PROCESS** (tech-agnostic core), NOT the multibrand machinery — multibrand is already a seam slot (`brands.active=[one]` = single-brand, zero core change, OCP). The ratified direction: **in-repo load = Option C** (rules→symlink doc-safe · agents/skills→copy [or symlink if the empirical test passes] · hooks→direct) **+ give `core-harness/` plugin-shape now** (a `marketplace.json` + a "harness" plugin shipping skills/agents/hooks/commands + a **SessionStart hook that injects the slim always-on rule core ≤10k as `additionalContext`** + a **`/harness:bootstrap`** skill that copies the full `.claude/rules/` corpus + writes a `project.config.yaml` stub + runs `/harness-doctor`). `core-harness/` stays **in-monorepo** (charter §0 fork1 honored); graduate to a separate private git-repo marketplace via `git subtree split` when the 1st other-tech project is ported (cross-account = private repo + collaborator/org, or public — auth is git creds, NOT the Claude account). The always-on-rules gap is worked by the SessionStart-injector (slim core, travels in the plugin) + the bootstrap-copy (full corpus, native auto-load). Execution playbook = §9.

`core-harness/` is the extractable kit (SSoT). The question is **how its core files re-expose to Claude Code's `.claude/` discovery** so the LIVE luana harness keeps loading AND a fresh adopter repo can bootstrap. Four options, each doc-grounded:

| Opt | Mechanism | rules | agents | skills | hooks | drift / freshness | dev edit | adopter bootstrap | robustness |
|---|---|---|---|---|---|---|---|---|---|
| **A · Copy-sync** | `core-harness/` = SSoT; `make harness-install` COPIES core files into `.claude/`; hooks point direct | copy | copy | copy | direct | **needs freshness gate** (like BACKLOG auto-gen) | edit `core-harness/` → re-sync | `make harness-install` | ✅ **all doc-safe**, survives CC upgrades |
| **B · Symlink-shim** | `.claude/{rules,skills,agents}/*` = symlinks → `core-harness/` | ✅ doc-safe | ⚠️ undoc | ⚠️ undoc+buggy | direct | **none** (one physical file) | live (edit core-harness/, instant) | bootstrap creates symlinks | ⚠️ agents/skills fragile/version-dependent |
| **C · Per-surface doc-safe (HYBRID · recommended)** | rules → **symlink** (doc-safe); agents+skills+templates → **copy-sync** (freshness-gated); hooks → **direct**; process-docs → live in core-harness/, read by path | symlink | copy | copy | direct | freshness gate on the COPIED set only | rules live; agents/skills via re-sync | one `make harness-install` does both | ✅ each surface uses its doc-blessed channel |
| **D · Plugin** | `core-harness/` packaged as a CC plugin (in-repo marketplace `./core-harness`) | ✗ (rules still need A/B) | plugin | plugin | plugin | copy-on-install cache | `/plugin update`+reload | `/plugin install` | best "true drop-in"; **rules unsolved** + most moving parts |

**My recommendation: Option C (per-surface doc-safe), defaulting to A's uniformity if you prefer one mechanism.** Rationale from the constitution (§4):
- **DIP / robustness for a foundational mechanism:** use each surface's *doc-blessed* channel (rules-symlink is doc-guaranteed; agents/skills-copy is doc-guaranteed) rather than betting the whole program on an undocumented+buggy symlink behavior for agents/skills.
- **Path-stability (§1 de-risk):** C keeps every `.claude/…` path valid → the 29 validator paths + all cockpit/script consumers are unaffected (low blast radius).
- **OCP / extraction:** `core-harness/` is the SSoT kit; `make harness-install` is the one bootstrap step (rules-symlink + agents/skills-copy + hook-path-merge). The adopter drops `core-harness/`, fills `project.config.yaml`, runs `make harness-install` + `/harness-doctor`.
- **Cohesion vs the drift cost:** C's freshness gate covers ONLY the copied set (agents 1 file + ~few core skills-skeleton + templates); rules have zero drift (symlinked). Smaller drift surface than full copy-sync (A).

**The one open unknown either way (B/C/D for agents/skills):** an **empirical session-restart test** — symlink one agent into `.claude/agents/` (and one skill into `.claude/skills/`) from `core-harness/`, restart, confirm `/agents` + the skill registry list them. luana's clerk/sentry skill-symlinks loading *here* is encouraging but not conclusive (open bug #14836). If the agents/skills symlink test PASSES cleanly → C can symlink those too (collapsing toward B, zero drift). If it FAILS → C's copy-for-agents/skills is the safe fallback (and is what's recommended regardless). **This test needs a fresh session → it is the natural first step of the W7 execution session, post-ratification.**

**REJECTED:** under-`.claude/` nesting (`.claude/core-harness/` not on any discovery path — inert). `permissions.additionalDirectories` for rules/agents/skills (file-access only, #43267). `--add-dir` for agents (silent miss).

---

## 3 · The move manifest (consolidated from the 6 tier-manifests — the WHAT, ready for execution)

**Principle:** only **proxy-clean `core`-tagged** files move into `core-harness/` (the kit must `grep`-tech = 0). **Hybrid + project + brand files STAY** physically in `.claude/`, `scripts/`, `docs/`, `tools/` — they ARE luana's project/brand layer (in the §2 tree they're conceptually `project-profile/`, but for luana-the-reference-product they live in place; an ADOPTER writes their own project layer). Tier source = the W-OUTPUT manifests (authoritative; in-file `tier:` markers are sparse by the manifest-authoritative decision — re-derive from the manifests at execution, do NOT trust a global in-file grep).

| → `core-harness/` target | Files (count) | Source manifest | Move mechanism (per §2 Option C) |
|---|---|---|---|
| `core-harness/rules/` + `rules-detail/` | **21 core rules** (W1's 18 + W5b-lifted `anti-duplication`·`parallel-safety`·`auditor-downstream-regression`) + their core `rules-detail/` mirrors | W1-OUTPUT §2 + W5b.c | **symlink** back into `.claude/rules/` (doc-safe) |
| `core-harness/agents/` | **1 core**: `grep-bot.md` | W3-OUTPUT §1 | copy (or symlink if the empirical test passes) into `.claude/agents/` |
| `core-harness/skills/` | **0 today** — the portable IP = a *generic role skeleton* per spine skill, which **does not exist as files yet** (W2/W3 finding). Creating it = a W8 "lift kit" task, NOT a W7 move. | W2-OUTPUT §1,§6 | n/a this WS (W8 authors the skeletons) |
| `core-harness/hooks/` | **core checks** `07-checkpoint-enum` · `11-worktree` · `17-checkpoint-dupkeys` (proxy-clean) | W4-OUTPUT §1 | ⚠️ **coupling care:** these are SOURCED by the **hybrid** `pre-commit` dispatcher — moving the check bodies while the dispatcher stays project means the dispatcher's source paths must repoint. Treat as a coordinated sub-move (grep-gate). |
| `core-harness/scripts/` | **~6 core git scripts** `git/{commit-paths,session-lock,multi-session-scope-guard,dod-evidence-gate,cleanup-wip-branches,ps1-luana}.sh` + **`harness_config.py`** (the seam loader, core) | W4b-OUTPUT §1a + W5b.a | path-referenced → repoint callers (Makefile, hooks, settings.json) |
| `core-harness/templates/` | **6 core** templates (`00-chris-input`, `00-research`, `00-story`, `01-spec` body, `story-ui.yaml`, +1 placeholder) | W6-OUTPUT §1a | read-by-path → repoint the (few) consumers |
| `core-harness/process/` | **7 core P1 docs** (`cockpit-permissions`, `continuous-improvement`, `harness-lifecycle`, `tech-debt`, `ticket-states`, `spec-mapa-funcional`, `INDEX`) + the kit doctrine (`charter`, `PROCESS-MODEL`, `REQ-TAKING-DETAIL`) | W6-OUTPUT §1b | read-by-path → repoint refs |
| **stays at repo ROOT** | `project.config.yaml` (THE SEAM, per charter §2) | W5b.a | unchanged |
| **STAYS in place (project/hybrid/brand)** | 22 project rules · ~24 hybrid + ~24 project skills · 11 hybrid agents · pre-commit/pre-push + 19 hybrid checks · ~35 hybrid + ~15 project scripts · 18 hybrid + 4 dead templates · 17 hybrid P2 process-docs · cockpit (project tool) | all 6 manifests | no move (luana's project layer) |

**Cockpit (R-OBS):** `tools/luana-cockpit/` is a **PROJECT tool** that reads `.md`/`.yaml` by path + the read-schema TYPES (`lib/types.ts`). The move keeps every path it reads **stable** (§1) → the cockpit is **unaffected**, keeps seeing both processes. The cockpit's "core read-primitives" (`lib/{fs-reader,fs-writer,git,sessions,…}.ts`, W4b-tagged core-candidate) **stay with the cockpit** — moving them adds cross-dir import coupling for no extraction win (a new product's portable contract is the read-schema *type shape*, which it re-emits; the `.ts` impl is project). **Decision (within structural authority): cockpit + its lib stay put in W7;** the portable cockpit contract is the TYPES, extracted as documentation in W8, not a file move. (If Chris wants the read-primitives physically in `core-harness/`, that's a small add — flagged, not assumed.)

**Architect instruction-docs (W2/W3 deferred to W7):** `architect-{be,fe,agentic}` are `disable-model-invocation` instruction-docs mis-housed as skills, read by-path by `architect-orchestrator`, **machinery-asserted** (validator L54-55/193-195 + baseline L13-14 + 3 templates). At execution: move `.claude/skills/architect-{be,fe,agentic}/SKILL.md` → `architect/references/{be,fe,agentic}.md`, repoint the validator paths + baseline + templates **in the same commit, behind a dependency-grep gate** (W3-OUTPUT §3 evidence). These are **hybrid** (stay project-side), so this is a project-layer tidy, not a core move.

---

## 4 · D2 — `make install-hooks` determinism + canonical source (charter §6 says W7 implements; spec'd here, executed post-ratification)

**The bug (W4b §5 + DECISIONS-PENDING D2):** `make install-hooks` symlinks `.git/hooks/{pre-commit,pre-push}` from **`$TOP`** = whatever worktree ran it → **last-writer-wins / non-deterministic** across the shared common-git-dir. W4b re-ran it from the vitalia hub (fixing a stale 4-day-old pre-push *copy*), so the shared hooks now point into `luana-vitalia/scripts/git-hooks/` — a temporary, worktree-coupled stopgap.

**The fix (ratified D2 · DIP: a shared resource depends on a STABLE source):**
1. Make `install-hooks` source-**deterministic** — resolve from a stable canonical path, not `$TOP`. Post-move the canonical source is **`core-harness/hooks/`** (the kit); pre-move it is the PRINCIPAL (`main`) worktree's `scripts/git-hooks/`. Use `$(git rev-parse --git-common-dir)`-relative resolution to the main worktree, NOT the invoking worktree.
2. **Cadence:** hook edits land on `wip/*` → merge to `main` → `main`/`core-harness` is the canonical running gate. "main lags" is a merge step, not a coupling to dodge.
3. **Stopgap (accepted until the W-series merges to main):** the vitalia-hub pointer stays — low blast radius (solo-operator, stable canonical hub, carries the current harness work). Resolve at the program→main merge.

**Why execute post-ratification, not now:** the canonical SOURCE path is the mechanism decision (§2) — under Option C the hooks point at `core-harness/hooks/` directly (no symlink), under a no-move world they'd point at `scripts/git-hooks/`. Implementing the determinism fix against a path that the mechanism choice changes = touching `install-hooks` twice. The fix is a ~5-line Makefile edit, mechanical once the source home is fixed. (The pure determinism principle — drop `$TOP` for a common-dir-relative resolve — is mechanism-independent and can be done first IF Chris wants it decoupled; flagged.)

---

## 5 · R-OBS + R-CI (the two transversal invariants — assessed, intact)

- **R-OBS (cockpit sees everything, both processes):** the move is **path-stable** for every file the cockpit reads (§1, §3) → the board/functionality/agents/map/harness views are **unaffected**. No live cockpit edit this session → tsc/vitest/live-render unchanged (last green: W6 `65/0/0` + W4b cockpit `tsc 0 / vitest 140/140`). At execution: re-run `tsc --noEmit` + `vitest` + levantar el cockpit only IF a cockpit file is touched (the recommendation is it is NOT). **Invariant holds.**
- **R-CI (the harness self-improvement loop):** HLP (`/harness-issue` → `harness-backlog.md`) + CIL 4 lanes (L1/L2/L3/L4) + `/harnesses-improvement` + the deep-sweep are process-docs (core P1) + skills (hybrid) + the backlog file. The move (copy-sync/symlink) **preserves their load + their paths** → the loop is intact. W10 cements it. **This session routes its own learnings to their CIL lanes (§7), not a 5th store.** **Invariant holds.**

---

## 6 · What this session did vs what is GATED

**DONE (green checkpoint):**
- ✅ Gate-zero research resolved (2 independent Opus passes, date-aware, official docs) — `GATE-ZERO-RESEARCH.md` + `GATE-ZERO-ADVERSARIAL.md`.
- ✅ The reshape fork framed with 4 doc-grounded options + a constitution-reasoned recommendation (Option C) — §2.
- ✅ The complete move manifest consolidated from the 6 tier-manifests — §3.
- ✅ D2 spec'd (determinism + canonical source + cadence) — §4.
- ✅ R-OBS + R-CI assessed (intact; the move is path-stable) — §5.
- ✅ The §1 de-risk discovered (29 validator paths stay valid under any `.claude/`-preserving mechanism).
- ✅ ZERO live-harness edits → machinery **65/0/0**, pointer **28/NEW-0** unchanged.

**GATED on Chris's §2 mechanism ratification (the W7 execution session, fresh, anchored to the charter):**
1. The agents/skills **symlink empirical test** (session-restart) — FIRST step, decides C-symlink-vs-C-copy for those surfaces.
2. The physical move per §3, **per-group behind a dependency-grep gate + validate-after-every-group** (machinery 65/0/0 + pointer 28 + smoke), order by risk: scripts/loader → templates/process-docs → agents → (architect-instruction-docs rehoming) → rules → hooks (last; re-register settings.json + re-symlink/`harness-install`).
3. D2 implemented with the now-fixed canonical source home.
4. `make harness-install` authored (the bootstrap step the mechanism implies).
5. The POST-move §0.5 dependency-grep over `core-harness/` (expected 0 tech tokens) = the cheap W8.
6. → **W8**: `/harness-doctor` already exists (`harness_config.py --doctor` exit-3 + `__FILL_ME__` list); the extraction test drops `core-harness/` + an all-`__FILL_ME__` config into a temp repo + a fictional product.

---

## 7 · Learnings (charter §5 step 7 → CIL routing)

1. **(L2 · learnings) The charter's own §2 carried an unverified mechanism assumption.** "Move files to repo-root `core-harness/`" silently assumed Claude Code would still load them — it does NOT for rules/agents. The program's foundational tree was drawn before the load mechanism was date-aware verified. *Lesson: a target-architecture diagram is a hypothesis about the platform until its load/discovery mechanism is verified against current official docs; verify the platform contract before committing the move that depends on it. (This is the §7 "verify > memory" convention applied to the program's OWN charter, not just to a rule body.)*
2. **(L2) The adversarial second pass corrected the first on a load-bearing claim** (rules-symlink: "undocumented" → "documented-safe"). A single research pass would have over-rejected the cleanest mechanism. *Lesson: for a foundational/irreversible-ish mechanism decision, a single Opus research pass is insufficient — an adversarial second pass (default-to-refute) is worth its cost; it flipped the recommendation surface.*
3. **(L2) Path-stability is the W7 super-power.** Because both copy and symlink keep `.claude/foo` resolving, the ~40-validator-path repoint the bootstrap feared is mostly a non-event. *Lesson: when a refactor can preserve the consumer-visible path (symlink/copy at the old location), the blast radius collapses to the SOURCE side; design the move to keep the discovery path stable.*
4. **(L1 · harness-backlog candidate) The "core skill/agent skeleton" is a CREATE task, not a MOVE task.** W2/W3 found 0 portable skill files + 1 portable agent; the real core IP (generic role contracts) must be *authored* (W8 lift kit), which means `core-harness/skills/` ships ~empty after W7. *Lesson: a "move by tag" workstream silently assumes the core files EXIST; when the portable layer is a not-yet-written abstraction, the move can't produce it — flag the gap to the lift-kit WS rather than mis-scoping it into W7.* → route to HB as a W8 scope note.

---

## 9 · Execution playbook (the ratified Option-C + plugin-shape — mechanical for the move session)

**Mechanism per surface (the "how each file re-exposes to `.claude/`"):**
- **rules** → `git mv .claude/rules/X.md core-harness/rules/X.md` + `ln -s <relpath> .claude/rules/X.md` (symlink-back · **DOC-SAFE** for CC always-on load). Path-stable → the validator's 29 `.claude/` paths + all consumers stay valid.
- **agents** (grep-bot) → COPY to `core-harness/agents/` while leaving `.claude/agents/grep-bot.md` real (safe default); the empirical session-restart test (`/agents` lists a symlinked agent) decides whether to collapse to symlink (zero-drift). Drift on the 1 copied file = freshness-gated.
- **read-by-path** (scripts incl `harness_config.py` + 6 core git-scripts · 6 templates · 7 core process-docs) → `git mv` to `core-harness/{scripts,templates,process}/` + `ln -s` back at the OLD path (OS resolves symlinks for Read/import/source → path-stable, zero consumer repoint). **harness_config.py is commit-time-wired (13 consumers + hooks) → verify the symlink resolves + run the loader smoke + the pre-commit dispatcher dry BEFORE committing that group.**
- **hooks** (core checks 07/11/17) → coupling care: the **hybrid** `pre-commit` dispatcher SOURCEs them → symlink-back at the old `scripts/git-hooks/checks/` path (source line stays valid) OR repoint the dispatcher; symlink-back is lower-risk.
- **project.config.yaml** → stays at repo ROOT (the seam, charter §2).
- **everything hybrid/project/brand** → STAYS in place (luana's project layer).

**Order (risk-ascending · validate-after-EACH-group: `make machinery-check` 65/0/0 + `scan_harness_pointers.py` NEW 0 + smoke + commit green BEFORE next group):**
1. **Group 1 — process-docs + templates** (pure read-by-path, no commit-time hook involvement, lowest blast radius). Verify CHECK 9/25/27 read through the symlinks.
2. **Group 2 — core scripts + `harness_config.py` + core git-scripts** (commit-time-wired → run loader smoke + pre-commit dispatcher dry before commit).
3. **Group 3 — core hooks/checks** (re-source/symlink; smoke the dispatcher).
4. **Group 4 — agents** (copy grep-bot; restart-test optional-collapse-to-symlink).
5. **Group 5 — RULES** (symlink-back; **DOC-SAFE but unobservable mid-session → requires a session-restart smoke: `/memory` lists the symlinked rules + the rule bodies still inject always-on**). Do this group, then **STOP for a restart-verify** before declaring it green.
6. **D2** — `make install-hooks` source-deterministic (drop `$TOP` → `$(git rev-parse --git-common-dir)`-relative to the canonical worktree; post-move canonical source = `core-harness/hooks/`) + cadence note.
7. **architect-{be,fe,agentic}** instruction-doc rehoming (W2/W3 deferred) → `architect/references/` + repoint validator L54-55/193-195 + baseline L13-14 + 3 templates, same commit, grep-gated.

**Plugin-shape (the lift-kit · additive, NOT wired into luana's live settings.json — inert until `/plugin marketplace add`):**
- `core-harness/.claude-plugin/marketplace.json` — the catalog (one "harness" plugin entry; omit `version` → commit-SHA = version → every push is an update).
- `core-harness/.claude-plugin/plugin.json` — components: `skills/`, `agents/`, `hooks/`, `commands/`.
- `core-harness/hooks/session-start-rules.sh` (or `hooks.json` entry) — emits the **slim always-on rule core (≤10k chars)** as `additionalContext` on `SessionStart`. The slim core = the cardinal stanzas of the proxy-clean core rules (the always-on invariants that must fire regardless of invocation).
- `core-harness/skills/harness-bootstrap/SKILL.md` — `/harness:bootstrap`: copies the full `core-harness/rules/*` into the adopter's `.claude/rules/`, writes a `project.config.yaml` stub (all `__FILL_ME__`), runs `python harness_config.py --doctor`, prints the unfilled slots.

**POST-move gate (the cheap W8):** the §0.5 dependency-grep over every file physically in `core-harness/` → expected **0 tech/brand tokens**. Then **W8**: drop `core-harness/` + an all-`__FILL_ME__` `project.config.yaml` into a `/tmp` repo + a fictional product → `python harness_config.py --doctor` lists every slot → fill with the fictional product → confirm idea→done resolves without editing CORE.

**Empirical session-restart smoke (Group 4/5 precondition):** symlink one agent into `.claude/agents/` + confirm a fresh session's `/agents` lists it; confirm `/memory` lists the symlinked rules + they inject. luana's `clerk-*`/`sentry-*` skill-symlinks loading is encouraging (skills follow symlinks here) but agents/skills symlink is undocumented (#14836) → the restart-smoke is the gate before trusting symlink for those surfaces.

---

## 8 · Pointers

- `GATE-ZERO-RESEARCH.md` · `GATE-ZERO-ADVERSARIAL.md` (this dir) — the date-aware official-doc citations (the evidence behind §1/§2).
- `PLUGIN-DISTRIBUTION-RESEARCH.md` (this dir) — the marketplace/plugin distribution model (hosting · public-vs-private · cross-account git-auth · install/update · the always-on-rules workaround ranking) behind the §2 ratified plugin-shape.
- `docs/process/harness-refactor-charter-2026-06-08.md` §0.5/§2/§3/§4/§6 — north-star + target tree + seam + fitness + roadmap (W7 marker updated this session).
- The 6 tier-manifests `harness-refactor-w{1,2,3,4,4b,6}/W*-OUTPUT.md` — authoritative for the per-file tier (the §3 manifest source).
- `harness-refactor-w5/W5-OUTPUT.md § W5b` — the LIVE seam (loader + `--doctor` = the W8 gate).
- `harness-refactor-w4b/DECISIONS-PENDING.md` D2 — the install-hooks determinism the §4 spec implements.
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md §7` — the R-OBS cockpit read-schema=core/render=project contract.

*End W7-OUTPUT.md (gate-zero phase) — the move is BLOCKED on the §2 mechanism ratification (escalation condition d). Machinery 65/0/0 · pointer 28/NEW-0 · zero live edits · green checkpoint. The W7 execution session begins with the §2 choice + the agents-symlink empirical test.*
