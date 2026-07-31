# W5 · The seam `project.config.yaml` — Output (W5a: schema design + loader mechanism + wiring plan + ratification ask)

**Date:** 2026-06-09 · **Session:** harness-refactor **W5a** (C-phase · STRUCTURAL · the DIP seam) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` · **Status:** ★ **RATIFIED by Chris 2026-06-09** — schema + mechanism + F1=CENTRALIZED (per-brand facets nest in `project.config.yaml` under `brands[]`, the §4 shape) approved; F2/F3 defaults stand. ZERO edits to live files (Chris chose "W5a sola": design + ratify now; **wire = W5b, fresh session, frozen contract**).

> **North-star card:** *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens (the rest went to the seam). The goal is an extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*
>
> W5 done-when (charter §6): *all tech/brand/locale reads the seam.* **W5a** delivers the SEAM CONTRACT (the `project.config.yaml` schema + the read mechanism) so W5b can wire against a frozen DIP contract. Inputs: `PROCESS-MODEL.md §4` (9 ratified slots + facets) · `DECISIONS-PENDING.md` D1 (`wip_caps`) · charter §0.5/§3/§4 · the 6 B/C-phase tier-manifests (the `{SLOTS}` union = the wiring target) · 2 Opus research siblings.

---

## 0 · Headline

The seam is **one root `project.config.yaml`** (proposed: `project.config.PROPOSED.yaml` in this dir) + **one python loader** `harness_config.py` read by 4 consumer classes. The schema holds the **9 ratified slots + `wip_caps` (D1)**, each with its **luana value actual** (harvested literal, not guessed — `RESEARCH-slot-values.md`). The read mechanism is **verified date-aware against official Claude Code docs** (`RESEARCH-loader-mechanism.md`): no markdown interpolation exists → markdown uses a `{slot}` CONVENTION; bash/python/TS use a real loader. **7 harvest flags** + **3 design forks** surfaced for ratification (§F). Nothing cemented yet.

---

## 1 · The seam mechanism (designed + date-aware verified)

ONE store, ONE python parser, per-class read. (Official docs fetched 2026-06-09 — citations in `RESEARCH-loader-mechanism.md`.)

| Class | Consumer | Read mechanism | Why |
|---|---|---|---|
| **A** | bash + git-hooks | `${WS}/.venv/bin/python -m harness_config <dotted.slot>` | no `yq` installed; the established `.venv/bin/python` idiom; one parser |
| **B** | python scripts | `from harness_config import load` (same module) | scripts already `import yaml`; the helper IS the python path |
| **C** | cockpit (Next 16 TS) | server-only `lib/project-config.ts` (`js-yaml`, typed to an interface, `process.cwd()`) | 2nd parser but SAME store; guard with a cross-runtime schema fixture test |
| **D** | markdown (rules/skills/agents/templates, loaded as CONTEXT) | **CONVENTION** — `{slot}` plain text + "(resolved from `project.config.yaml`)" note → MODEL Reads the yaml on demand | **NO native interpolation exists** for bare rules/CLAUDE.md/agents (official docs: `@import`=inline content not substitution + CLAUDE.md-only; settings `env` not in model context; skill `${...}`=closed set). Optional skill-ONLY native upgrade: `` !`python -m harness_config <slot>` `` — never a hard dependency (`disableSkillShellExecution` kills it). |

**The loader (`harness_config.py`) — built in W5b, designed here:**
- `python -m harness_config <dotted.slot>` → prints value, exit 0. Unfilled/`__FILL_ME__` → stderr + exit 3 (doctor-detectable).
- `python -m harness_config --doctor` → walks the schema, lists unfilled slots (the extraction-test gate, W8).
- `from harness_config import load` → dict for python consumers.
- `yaml.safe_load` (never `load()`), parent-walk to the repo root holding `project.config.yaml`.
- **One module = class-A bash call + class-B python import + class-D skill `!`cmd` upgrade + the W8 doctor.** Single parser, single store, zero drift.

**File location/format (ratified rationale, §F3):** root `project.config.yaml`, YAML (comments + sentinels). Rejected: `pyproject.toml [tool.harness]` (couples polyglot kit to python packaging; TS needs a TOML parser) · `.harness/config.yaml` (a dot-dir hides the one file an adopter must fill).

---

## 2 · The 9 slots + `wip_caps` — shape decisions (the contract Chris ratifies)

Full schema with luana values = `project.config.PROPOSED.yaml`. Shape rationale + the non-obvious calls:

| Slot | Shape decision | DRY / design note |
|---|---|---|
| `brands[]` | `active[]` (slug/vertical/status/ports/dev_app_url/compliance) + `pending_bootstrap[]` + `loop_order` + `cockpit_main_port` | **dev_app_url + ports live HERE ONCE** (not duplicated in `live_verify_infra`). per-brand facets nest under each brand. |
| `toolchain` | `backend.{lint,format,typecheck,test,migrate,audit}` + `frontend.{…}` + shared (`venv_path`, `ci_gate`) | `{brand}`/`{fe_port}` interpolation markers kept literal — the loader/consumer fills them per call. |
| `locale` | identifier + rule(tuteo) + scope[] + magic-comment + agentic-validation | scope acotado (UI + agentic only) encoded — matches the 2026-06-01 narrowing. |
| `engine_prefix` | python_glob + module_prefix + ts_scope + count(**27**) + ts_packages[] | corrected 26→27 (CLAUDE.md stale, §F-flag). |
| `live_verify_infra` | verify MACHINERY only (creds keys/location, clerk mechanism, `observability_evidence.sources`, per_brand arming/test_user/up_cmd) | **dev_app + ports CROSS-REF brands[]** (DRY) — this slot does NOT restate them. |
| `design_system_ref` | canon + adr + ui_kit + tokens + binding + `shell_design_contract` (**per-brand**) | shell-contract is per-brand (not platform), encoded as a per-brand map. |
| `domain_modules[]` | conceptual[] + 3 categories (core_full / engine_brand_extension / engine_brand_config) + `contract_guard_watch[]` | the contract-guard.js RULES array becomes config the hook reads. |
| `agent_roster` | per-brand `[{slug,name,emoji,color,role,subtitle}]` + `common_boxes` | vitalia+nicolify filled (hex from agent-meta.ts); comunify/lupulo = `__FILL_ME__` (no roster in code yet). |
| `value_stream` | `canonical_stages` (cross-brand) + per-brand stage arrays (id/name/order/description/boxIds) | vitalia filled (clinical GTM); others `__FILL_ME__`. |
| `wip_caps` (D1) | `coarse_session_net{*_max}` + `staleness_days{}` + `module_scoped_note` | **D1: the coarse net numbers seamed; the module-scoped ≤1 rule stays in story-closure-gate.md (NOT duplicated here).** Kills the verbatim dup across `validate_session_close.py` + `generate_backlog.py`. |

---

## 3 · W5b wiring plan (the `{SLOTS}` union from the 6 manifests → which files repoint to which slot)

The wire (W5b) is **path-stable, behind a dependency-grep gate, validate-after-every-edit (machinery 65/0/0 + smoke)**. Highest-yield first = **`brands[]`** (the recurring enum/loop — the #1 lift named by every manifest). Per-slot consumer set (union of the manifests' `{SLOTS}` columns):

| Slot | Consumers to repoint (W5b) | Mechanism |
|---|---|---|
| **`brands[]`** ★#1 | scripts: `git/{new-session,check-sync,cleanup-session}.sh`, `scan_promotables.BRAND_SLUGS`, `generate_portfolio.UNIVERSES`, `reconcile_capabilities`, cockpit `workspace.ts`/`story-paths.ts` port maps · hooks: checks 05b/05c/05d/05e/06/12/13/14/16 + loops 08/09 + pre-push + `auto-chain-detect.sh` + `claude-md-overlay-check.sh` · rules (markdown {slot}): parallel-safety, anti-duplication-refining, claude-md-overlay, worktree-dual-strategy, step-0-worktree, auditor-downstream-regression, e2e-testing, debugging, brand-docs-schema | A (bash), B (py), C (TS), D (md convention) |
| **`toolchain`** | hooks: 03-ruff + all `.venv` wrappers (05/05b-e/06/08/09/10/15/15.5/18) + pre-commit/push · rules(md): backend-{ddd,quality,migrations}, architectural-fitness, frontend-quality, e2e-testing, debugging, github-actions-deferred · scripts shelling ruff/pytest/docker | A, B, D |
| **`engine_prefix`** | rules(md): anti-duplication, auditor-downstream-regression, backend-ddd · hooks: 04-r3-ssot, 13-scope-branch, `contract-guard.js` | A, D |
| **`locale`** | hooks: 02-voseo, `learning-detect.sh` (trigger phrases) · rule(md): spanish-text · cockpit `tooltips.ts` | A, C, D |
| **`live_verify_infra`** | rules(md): definition-of-done-live-verify (#37 body), hotfix-repro-mandatory · cockpit `types.ts` (hipaa/phi fields) | A, C, D |
| **`design_system_ref`** | rules(md): frontend-visual-fidelity, form-runtime-array | D |
| **`domain_modules[]`** | rules(md): offer-catalogs, analytics-metrics, etl-extraction-contract, copilot-resilience, copilot-observability, sales-agent-brand-voice, admin-panel, data-reliability · hook: `contract-guard.js` RULES array | A (hook), D |
| **`agent_roster`** | cockpit: `agent-meta.ts`, `map-zones.SPECIALIST_AGENTS`, `generate_capability_index.VITALIA_AGENTS`, `MapView` VITALIA_ROLES | C, B |
| **`value_stream`** | cockpit: `map-zones.ts` VALUE_STREAM_STAGES | C |
| **`wip_caps`** (D1) | `validate_session_close.py:73`, `generate_backlog.py:84` (both read the slot) | B |

**Two consumer classes, different wire cost:** **(A/B/C) executable** = real loader calls, smoke-testable, the genuine fresh-repo extraction blockers (~30-40 call-sites, mechanical). **(D) markdown** = `{slot}` notation rewrite across the hybrid rules/skills/agents/templates (the volume mass; validated by the dependency-grep, each edit preserving machinery-asserted strings). W5b should likely sub-split A/B/C (executable) from D (markdown) given the volume — flag for the W5b kickoff.

**Machinery guardrail (do NOT break):** CHECK 9/11/14/19/25/27 + 13-18 + 22-24 string-assert specific bodies (named in the manifests). Any slot-rewrite touching an asserted body → validate BEFORE.

---

## 4 · POST-wire dependency-grep target (the cheap W8 — W5b deliverable, recorded here)

After W5b wires, the §0.5 proxy runs over every file tagged `tier:core`: expected **0 tech/brand tokens**. The hybrids that became proxy-clean after their token went to the seam → **re-tag `core`** (the levantamiento W5 produces). Predicted lift (from the manifests): the `brands[]` seam alone lifts most of the `hybrid` hooks/scripts/rules to `core`. W5a does not run this (nothing wired yet); W5b owns it.

---

## 5 · DRY / one-SSoT wins this design produces

1. **`wip_caps` D1 dedup** — `CAPS` is byte-identical in `validate_session_close.py` + `generate_backlog.py` (both comment "must match"). The seam makes it ONE store → the dup the charter forbids dies.
2. **`dev_app_url` + ports — ONE home** (`brands[]`); `live_verify_infra` cross-refs, never restates. (The harvest found dev_app scattered across rule #37 body + the cockpit + scripts.)
3. **The loader is one module** serving bash + python + skill-native + the W8 doctor — not a generated `.env` second store (rejected: drift).
4. **`contract_guard_watch`** moves the hardcoded RULES array out of `contract-guard.js` into config — a new product declares its SSoT-guard targets without editing the CORE hook.

---

## F · FLAGS for Chris — ratify / decide (the genuine forks)

**Design forks (architecture — your call):**
- **F1 · per-brand facets: centralize vs delegate.** This draft centralizes per-brand facets (roster/value_stream/dev_app/ports/compliance) INSIDE `project.config.yaml` under `brands[]` — matching the PROCESS-MODEL §4 ratified slot list (those slots ARE project.config slots). **Alternative (cleaner OCP):** delegate per-brand facets to `{brand}/config/brand.yaml` (the BRAND layer that already exists), `project.config.yaml` holds only the `brands[]` enum + project-level slots + a pointer. Trade: centralized = one file the doctor sees fully (simpler extraction) · delegated = "adding a brand = drop a brand.yaml, never touch project.config" (purer Brand→Project→Core). **★ RATIFIED 2026-06-09 = CENTRALIZED (§4 shape).**
- **F2 · `agent_roster`/`value_stream` granularity.** These are cockpit-render data (per `map-zones.ts`/`agent-meta.ts`). Encode them fully in the seam (this draft) so the cockpit reads config and is extractable — OR leave them cockpit-owned and seam only a pointer? Default = full (makes the cockpit extractable, the §7 read-schema goal).
- **F3 · file name/location** — `project.config.yaml` at root. Confirm (vs `.harness/config.yaml`). Default = root (best for the drop-in-then-doctor extraction story).

**Harvest flags (data accuracy — I encoded as-found; confirm or correct):**
1. **`engine_prefix` = 27 packages**, not 26 (CLAUDE.md header is STALE). Encoded 27. Downstream: a CLAUDE.md fix (separate, W9/governance).
2. **`dev_app_url` is NOT a uniform `{brand}lat.com`** — vitalia=vitalialat.com, nicolify=nicolify.com, comunify=comunifyagents.com, lupulo=lupulo.com. Encoded per-brand literals.
3. **6 pending-bootstrap brands have NO ports** — encoded slug+vertical only; ports allocated at bootstrap.
4. **`agent_roster` comunify/lupulo = `__FILL_ME__`** (no roster in cockpit code yet) + **Sara** (nicolify, ADR-nicolify-002) not yet in `agent-meta.ts` (TODO note). The SHAPE supports them; the data fill is pending their cockpit rosters.
5. **`wip_caps` 3-SSoT divergence** (scripts developed=10/reviewing=2 · CLAUDE.md table=1/1 · story-closure module-scoped=≤1): **D1 already resolved this** — the seam holds the COARSE net (10/2), the module-scoped ≤1 stays in story-closure-gate.md. NOT a new decision. (Minor doc-consistency: CLAUDE.md's v4 table line still says "developed≤1" loosely — a W9 doc-cleanup, not the seam.)
6. **`shell_design_contract` is per-brand**, not platform-level. Encoded per-brand.
7. **`toolchain.backend.typecheck` (mypy --strict)** comes from the DoD technical-gates detail, not AGENTS.md Quick Commands. Encoded; confirm it belongs in the seam.

---

## 6 · Learnings (charter §5 step 7 → feed §7) — W5a partial

1. **The seam SHAPE is mostly DRY-driven, not slot-driven.** The 9 ratified slots are the skeleton; the real design work was deduplication — `dev_app`/ports have ONE home (`brands[]`), `wip_caps` collapses 2 verbatim copies (D1), the loader is one module for 4 consumers. *Lesson: a DIP seam's value is as much the dedup it forces as the abstraction it names.*
2. **Markdown has no config seam — the convention IS the mechanism (date-aware confirmed, not assumed).** The instinct to "make rules read project.config.yaml like code does" is impossible natively (verified official docs). The honest seam for class D is a `{slot}` convention the MODEL resolves — which means the dependency-grep (not a loader) is what proves class-D conformance. *Lesson: verify the mechanism before designing against it; half the "wiring" (markdown) is notation + a grep, not a loader call.*
3. **Two consumer classes ⇒ W5b should sub-split.** Executable (A/B/C, smoke-testable, the real extraction blockers) vs markdown (D, volume, grep-validated). Conflating them in one wire session risks a long unfocused pass. *Recorded for the W5b kickoff.*

---

## 7 · Ratification ask (what closes W5a)

Chris ratifies: (a) the **schema shape** (`project.config.PROPOSED.yaml` — the 9 slots + `wip_caps`), (b) the **read mechanism** (root yaml + `harness_config.py` loader + class-D `{slot}` convention), (c) the **3 design forks** (F1 centralize-vs-delegate · F2 roster/value-stream granularity · F3 file location), (d) the **harvest flags** (confirm encode-as-found). On ratification → W5b (fresh session): move to root, build `harness_config.py` + doctor, wire the `{SLOTS}` union behind the grep-gate, run the POST-wire proxy, re-tag the lifted hybrids `core`. Then update charter §6 + memory.

---

## 8 · Pointers

- `project.config.PROPOSED.yaml` (this dir) — ★ the proposed schema (the ratification artifact).
- `RESEARCH-slot-values.md` (this dir) — the literal luana values per slot + 7 flags.
- `RESEARCH-loader-mechanism.md` (this dir) — the date-aware read-mechanism verification (official Claude Code doc citations).
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md §4` — the 9 ratified slots + facets.
- `docs/process/harness-refactor-w4b/DECISIONS-PENDING.md` — D1 (`wip_caps` → W5).
- `docs/process/harness-refactor-charter-2026-06-08.md` §0.5/§3/§4/§6 — north-star + seam + fitness + roadmap.
- The 6 tier-manifests (`W{1,2,3,4,4b,6}-OUTPUT.md`) — the `{SLOTS}` union = the W5b wiring target.

---

# W5b · WIRE the seam (executed 2026-06-09)

**Session:** harness-refactor **W5b** (C-phase · STRUCTURAL · wire) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` · **Chris chose:** ONE session (exec + markdown). **Validate-after-every-edit held throughout: machinery 65/0/0 + pointers 28/NEW-0 + per-file smoke.**

> **North-star card:** *succeeds only if (1) implements its work-type, AND (2) every file it tags `core` names ZERO tech/brand tokens. Goal = extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*

## W5b.a · The loader + doctor (PASO 0 — precondition of all wiring) ✅

- **`project.config.yaml` promoted to repo ROOT** (`git mv` from `docs/process/harness-refactor-w5/project.config.PROPOSED.yaml`; header updated to "LIVE"; tombstone `project.config.MOVED-TO-ROOT.md` left so the W5a trail resolves — **ONE live store**).
- **`scripts/harness_config.py` built TDD** (RED test first → GREEN): `safe_load` (never `load()`), parent-walk from `__file__` to the repo root holding the config, `python harness_config.py <dotted.slot> [pluck_key]` (scalar→stdout · list→newline-joined · list-of-dicts+pluck→plucked · dict→JSON), `--doctor` (walks the tree, lists every `__FILL_ME__`, exit 3), `from harness_config import load, get`. Exit codes pinned: 0 ok · 2 no-config · 3 unfilled · 4 not-found.
- **Cockpit `lib/project-config.ts` built** (server-only, `yaml` pkg — already a cockpit dep, NOT a new js-yaml dependency; typed `ProjectConfig` interface; `getProjectConfig()`/`getAgentRoster()`/`getValueStream()`/`getActiveBrandSlugs()`; module cache). **Cross-runtime fixture test** (`__tests__/project-config.test.ts`) asserts TS parses the SAME store with the SAME values the python test asserts (`engine_prefix.python_package_count==27`, the 4 active slugs, vitalia roster hex, unfilled→null) — the single-store parity guard (RESEARCH Q3).
- **Smoke evidence:** every slot read returns the literal (`engine_prefix.python_glob`→`core/luana-core-*`; `brands.loop_order`→10; `brands.active slug`→4; `toolchain.backend.lint`→the ruff cmd; `wip_caps.coarse_session_net.developed_max`→10); `agent_roster.comunify`→exit 3 + `__FILL_ME__`; `--doctor`→lists the 5 luana pending slots, exit 3. Loader test 11/11 · cockpit test 6/6 · ruff+tsc clean.

## W5b.b · Wiring manifest — what repointed to which slot, by class

| File | Slot | Class | Mechanism |
|---|---|---|---|
| `scripts/validate_session_close.py` | `wip_caps` (D1) | B | `from harness_config import get` → `CAPS`/`CHECKPOINT_STALE_DAYS`/`ACTIVE_STATES` |
| `scripts/generate_backlog.py` | `wip_caps` (D1) | B | same store; downstream key names (`*_max`/`*_stale_days`) preserved |
| `scripts/scan_promotables.py` | `brands.active` | B | `BRAND_SLUGS = get("brands.active", pluck="slug")` |
| `scripts/mutation_gate.py` | `brands.active` | B | `_BRANDS = tuple(get("brands.active", pluck="slug"))` |
| `scripts/git/check-sync.sh` | `brands.loop_order` | A | `$(python harness_config.py brands.loop_order)` + loud-degrade |
| `scripts/git/regenerate-manifest.sh` | `brands.loop_order` | A | same |
| `scripts/git/cleanup-session.sh` | `brands.loop_order` | A | same (loop over the read) |
| `scripts/git-hooks/checks/12-story-closure.sh` | `brands.loop_order` | A | same (REPO_ROOT inherited) |
| `.claude/hooks/claude-md-overlay-check.sh` | `brands.loop_order` | A | same (repo-root via `BASH_SOURCE`) |
| `scripts/git-hooks/pre-push` | `brands.active` | A | `brands.active slug` (venv guaranteed by enclosing `if`) |
| `.claude/rules/anti-duplication.md` | `engine_prefix`/`brands` | D | `{slot}` notation; exec snippet → prose-pointer to rules-detail |
| `.claude/rules/parallel-safety.md` | `engine_prefix` | D | `{engine_prefix.python_glob}` notation |
| `.claude/rules/auditor-downstream-regression.md` | `engine_prefix`/`brands` | D | `{slot}` notation; bash block → prose-pointer |

**Degrade design (class A/bash):** ZERO hardcoded fallback list (a fallback would leave brand tokens → defeats core). On a missing seam read → **empty + LOUD warn** (the config ships with the kit; a fresh/unconfigured repo also has no brand dirs to sweep). Never silent-pass.

**`{slot}` mechanism (class D):** prose references → `{slot}` notation the model resolves from `project.config.yaml`; **executable snippets** → either a `harness_config.py` subshell (token-free + runnable) OR prose-pointer to the stack-specific verbatim in `docs/rules-detail/` (the project half). NO bash `{slot}` interpolation invented (it doesn't exist — RESEARCH confirmed).

## W5b.c · POST-wire dependency-grep (the cheap W8) + hybrids→core LEVANTADOS ✅

- **All 13 core-tagged rules proxy-CLEAN (0 tech/brand tokens).** Verified with the §0.5/§4 grep.
- **3 hybrids LIFTED hybrid→core** (the visible "extraction, not cleanup" deliverable): `anti-duplication.md`, `parallel-safety.md`, `auditor-downstream-regression.md` — each re-tagged `tier: core (W5b)` in its header after its engine/brand tokens went to `{slot}` (exec detail pushed to `docs/rules-detail/`).
- **D1 `wip_caps` = ONE store:** the byte-identical `CAPS` dup across `validate_session_close.py` + `generate_backlog.py` is GONE — both read the seam. (charter §3 DRY win realized.)

## W5b.d · DEFERRED with flags (honest ROI — not Frankenstein)

| Target | Why deferred | What it needs |
|---|---|---|
| `generate_portfolio.py` `UNIVERSES` | **project-tier** (renders luana's portfolio narrative — won't become core); carries `cliente`/`diferenciacion`/`kind` fields **NOT in the ratified seam** (richer than `brands[]`). Wiring = DRY-only on a project file + risk to PORTFOLIO gen. | **Chris fork:** enrich the seam `brands[]` with portfolio-narrative fields (schema change) OR keep `UNIVERSES` as the project-tier portfolio source. |
| `.claude/hooks/contract-guard.js` | node has **no YAML parser** (would need `execSync`→python on every Write/Edit); the seam `domain_modules.contract_guard_watch` holds `{name,regen}` but **NOT** the regex paths + message strings the hook actually uses; brand mentions are advisory comment/msg text. | **Chris fork:** enrich the seam with the contract-guard regex/message array (schema change) + a node read mechanism. |
| `CAP_GATES_HARD_BRANDS="vitalia comunify"` (`pre-push` + `05e-cap-gates.sh`) | a **policy SUBSET** (which brands have HARD cap-gates) — NOT derivable from any ratified slot (not `active`, not a compliance derive). | **Chris fork:** a new `cap_gates_hard_brands` slot (schema addition beyond the ratified 9+D1) — flagged, not decided unilaterally. |
| `definition-of-done-live-verify.md` brand-URL examples | stays **hybrid by construction** (`mutation_gate.py` is REQUIRED in its body by machinery CHECK 19; tool names tsc/mypy/ruff/eslint + `dod-evidence-gate.sh` + the vitalia ADR ref remain). Cleaning the illustrative `dev-app.vitalialat.com`/`dr.demo@` examples is **cosmetic** (not measured — it's not a core file) + risks CHECK 16/19/25/27. | nothing — correctly tagged hybrid; examples are illustrative. |
| argparse help-strings (`generate_capability_index`/`extract_changelog`/`reconcile`/`generate_backlog` `--brand` help text) | non-functional help text "(e.g. vitalia, nicolify…)" — not a functional enum. | trivial genericize (W9 cosmetic), not load-bearing. |

## W5b.e · Learnings → charter §7

1. **The bootstrap paradox of `.venv` in a CORE rule's exec snippet:** a snippet that READS the seam needs the toolchain venv, whose path IS a seam slot (`toolchain.venv_path`). You can't `{slot}` it in runnable bash. Resolution that keeps the rule `core`: **the exec snippet moves to `docs/rules-detail/` (the project half); the stub keeps doctrine + `{slot}` prose + a pointer.** A CORE rule is doctrine + `{slot}`, not copy-paste bash (the runnable verbatim is project-tier). This is the same stub↔detail split W1 used for size, now used for extractability.
2. **`{slot}` is for PROSE; executable code wires differently.** Class-D markdown splits in two: prose the model resolves (`{slot}` notation) vs runnable snippets (→ `harness_config` subshell OR pushed to rules-detail). Conflating them (writing `{slot}` inside a bash block) yields non-runnable rules. The honest class-D conformance is the dependency-GREP, not a loader call.
3. **The seam captures what consumers NEED, not everything a richer dup holds.** `generate_portfolio.UNIVERSES` + `contract-guard.js` RULES carry fields (narrative / regex+message) the ratified `brands[]`/`domain_modules` slots don't — wiring them fully needs a schema decision, not a mechanical repoint. Flag-don't-invent kept the ratified contract frozen (learning #7 honored).
4. **No-hardcoded-fallback is the price of `core`.** A bash degrade-to-hardcoded-list would keep brand tokens → the file can't be `core`. Degrade-to-empty + LOUD warn keeps it token-free AND non-silent. The config IS part of the kit (its absence is a setup error, surfaced loudly).
5. **Most hybrids STAY hybrid; few lift.** Of the 4 markdown targets, only 2-3 reached `core`; DoD + (the engine-regex half of) auditor-downstream are inherently project (mutation_gate.py / `sed 's#core/luana-core-…'`). The levantamiento is real but selective — the proxy-EARNED law (W1→W4) holds at W5: core is rare; the worker/example body is project-bound.

## W5b.f · What W5 leaves for downstream

- **W7** (physical move) inherits: `harness_config.py` + `project.config.yaml` + `lib/project-config.ts` move to `core-harness/` paths; the wired consumers are PATH-STABLE (no move done in W5b). Implements D2 (canonical hook source).
- **W8** (extraction test): `python harness_config.py --doctor` IS the gate — already returns exit 3 + names unfilled slots. The fresh-repo test drops core-harness/ + an all-`__FILL_ME__` config → doctor lists every slot.
- **Open seam-schema forks for Chris** (3, above): portfolio-narrative fields · contract-guard regex/message array · `cap_gates_hard_brands` policy slot. Each is a schema addition beyond the ratified 9+D1 — surfaced, not decided.

## W5b.g · The 3 seam-schema forks — RESOLVED (2026-06-09, Chris delegated to criterion: max maintainability + extensibility)

Chris delegated the 3 flagged forks. Resolutions, each reasoned from the constitution (DIP · OCP · cohesion · dependency rule Brand→Project→Core):

**Fork 1 — `generate_portfolio.UNIVERSES` → WIRED (structural/narrative split).** The brand ENUM + `slug`/`vertical`/`status`/`kind` now DERIVE from the seam `brands[]` (`_build_universes()` reads `harness_config.get("brands")`) — the enum had two homes, now ONE (DRY). The portfolio NARRATIVE (`cliente`/`diferenciacion`) stays as a local `_PORTFOLIO_NARRATIVE` map — **single-consumer presentation content, cohesive with its only renderer, NOT bloating the shared seam** (the seam holds CORE-consumed slots; portfolio prose isn't one). Adding a brand = config in `project.config.yaml` (structural auto-flows) + one narrative entry. generate_portfolio stays project-tier (correct — it renders luana's portfolio). Verified: UNIVERSES builds 11 rows, shape byte-identical to the old literal except 3 benign deltas (luana 26→27 pkgs · lupulo/saasora vertical = the seam's richer wording, now the SSoT). Render exit 0; portfolio files are gitignored autogen (were already stale pre-edit).

**Fork 2 — `contract-guard.js` → NOT wired (tag clarified; RULES stay project-inline).** Maintainability > forced DIP: node has no built-in YAML parser → seaming would mean `execSync`→python on EVERY Write/Edit (latency + a hard python dep on a JS hook) OR a second store; and the RULES' shape (per-rule regex + multi-line message) is richer than the ratified `domain_modules.contract_guard_watch` ({name,regen}) slot. The portable IP is the **dispatch kernel** (regex-match → reminder); the RULES are PROJECT config that lives in this PROJECT hook (a new product ships its own `contract-guard.js` RULES). Header tier-note updated to document this + the "lift the kernel only when a 2nd product needs it (YAGNI)" stance. Mechanism verified intact (reminder on watched engine path / silent on non-match).

**Fork 3 — `cap_gates_hard_brands` → WIRED as a per-brand F1 facet.** Added `cap_gate: hard|advisory` to each `brands.active[]` entry (vitalia/comunify=hard, nicolify/lupulo=advisory) — **consistent with the ratified F1 (centralized per-brand facets), NOT a new top-level slot.** The loader gained a general `--where field=value` filter (`get(..., where=("cap_gate","hard"))` + CLI `--where cap_gate=hard`) — a reusable facet-filter, the right extensibility investment in the seam reader. `05e-cap-gates.sh` (BOTH its var AND its path pre-filter regex, built from the HARD set) + `pre-push` now derive the HARD set from the seam. OCP+DRY: a brand's gate policy = config co-located with the brand, the 2-site dup gone. Verified: HARD set→`vitalia comunify`, regex matches vitalia / excludes nicolify, CHECK 11 (`cap-gates-hard` wired) stays green, loader tests 13/13, cockpit fixture 6/6.

**Net:** 2 forks WIRED (generate_portfolio · cap_gate), 1 deliberately NOT (contract-guard — maintainability call). Seam additions: `brands.active[].cap_gate` facet (F1-consistent) + loader `--where` filter. ZERO new top-level slots (the ratified 9+D1 contract held; cap_gate is a facet, not a slot). machinery 65/0/0 throughout.

*End W5b — loader + doctor + 15 consumers wired (12 executable + 3 markdown) · 3 hybrids→core · D1 dedup · 2 of 3 forks wired (1 maintainability-deferred) · all core-tagged rules proxy-clean · machinery 65/0/0 throughout. The seam is LIVE.*
