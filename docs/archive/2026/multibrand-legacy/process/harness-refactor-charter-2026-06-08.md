# Harness Refactor — Architecture Charter (Constitution)

**Date:** 2026-06-08 · **Author:** architect session (Opus) · **Status:** ratified (3 forks locked by Chris) · **This doc is loaded at Step 1 of every workstream session.**

> **Purpose.** Turn the harness (skills + agents + rules + hooks + commands + process-docs + templates + git-hooks + scripts + cockpit) from an accreted system into a layered architecture whose **CORE is extractable to any new product** and whose project/brand specifics are swappable. Goal stated by Chris: extract the core, drop it in a new repo, have it **detect what's missing** and fill it with project-specific info (vision, tech, design) — `idea→done` works without touching the core.

## 0. Locked decisions (forks, 2026-06-08)

1. **Core home:** `core-harness/` inside this monorepo + a documented extraction procedure (evolvable to a separate repo later).
2. **Scope:** FULL — `.claude/{skills,agents,rules,hooks,commands}` + `docs/{process,rules-detail,specs/templates}` + `scripts/git-hooks` + `scripts/` + `tools/luana-cockpit/`.
3. **Legacy:** superseded files → `legacy/{date}/` per workstream; **deleted only after W8 (extraction test) passes**. Git is the real backup; legacy/ is the cooling window.

---

## 0.5 ★ NORTH-STAR — read this every session, before anything else

**The desired end-state (the whole reason this program exists):** take `core-harness/` + an empty `project.config.yaml`, drop it into a fresh repo, run `/harness-doctor` → it **self-declares the missing slots** → fill them with a *different* product's info (vision/tech/design) → the **`idea→done` cycle runs without editing the CORE**. That is the program DoD (§8) and the only definition of done. **The extraction test (W8) is the north made measurable.**

**The failure mode every session must resist:** *polishing luana's harness* (making it nicer) instead of *separating core from project* (making it extractable). If a workstream ends and its core-tagged files still name a concrete tech/brand (`vitalia`, `ruff`, `Clerk`, `core/luana-core-*`), it **drifted** — it did cleanup, not extraction.

**Two co-equal lenses on every file (a session doing only the first has drifted):**
1. **Process conformance** — implements its work-type correctly (`PROCESS-MODEL.md §6` checklist + §3 WT profile).
2. **Extractability** — tagged `tier: core|project|brand`, and any tech/brand/locale/engine/dev-app reference pushed behind a §3 seam slot.

**Per-session acceptance proxy (the cheap W8, run at playbook step 6, every session):**
```
# over the files this session tagged tier:core
grep -RInE 'vitalia|nicolify|comunify|lupulo|ruff|pytest|mypy|alembic|clerk|next\.js|tailwind|fastapi|sqlalchemy|core/luana-core|\.venv|dev-app|hipaa|phi' <core-tagged-files>
# expected: 0 hits. >0 → the smear isn't pushed to the seam → the session is NOT done.
```

**Resolution (ratified Chris 2026-06-08 · option b):** the proxy is a **per-session scorecard**, not a blanket `{slot}`-rewrite mandate. A B-phase session must leave its `tier:core` set proxy-CLEAN — but a token-carrying file is **re-tagged `hybrid`** (core mechanism + project-half parked), NOT rewritten to `{slot}` notation now. The actual seam wiring (`project.config.yaml` + `{slot}` rewrite) stays **W5**. Trivial tokens (provenance / a single illustrative path) are cleaned to generic in-place; structural/multiple tokens → `hybrid`. Net rule for every B-phase surface: **`tier:core` ⇒ proxy-clean, else `hybrid`/`project`.**

**North-star card (repeat verbatim at the top of every workstream bootstrap AND every WS output):**
> *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens (the rest went to the seam). The goal is an extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*

---

## 1. Conceptual model — 3 layers + the dependency rule

| Layer | What it is | Answers | luana example | Changes when |
|---|---|---|---|---|
| **CORE** | HOW software is built with agents. Tech/domain-agnostic. The reusable IP. | lifecycle, gates, roles, doctrine, safety | idea→done, story-closure-gate, pm/po/architect/dev/auditor roles, TDD/DoD, git/parallel safety, learning-capture | never per-project |
| **PROJECT** | WHICH stack + WHICH domain. One per product. | FastAPI? Django? which business modules? | FastAPI/Next/Clerk/Postgres + `luana-core-*` engine + offer/copilot/analytics | per product |
| **BRAND** | WHICH market instance, sharing the Project's tech. | health? gastronomy? which config? | vitalia / nicolify / comunify (overlays + brand.yaml) | per brand added |

**Dependency rule (clean architecture for harnesses):** `BRAND → PROJECT → CORE`. Arrows point **inward**. The CORE never names a concrete tech, brand, locale, or URL. Adding a brand = adding config (OCP). Lifting to a new product = take CORE, write a new PROJECT profile. **"Brand = project with shared tech"** = a Brand is a Project-instance that shares the Project's stack.

**The smear we are removing:** today luana/tech/brand specifics live *inside* process rules/skills → the dependency points outward → violation. Every workstream pushes those specifics out to PROJECT/BRAND and leaves CORE agnostic.

---

## 1.5 Process-first — the development process IS the requirements

The harness exists to **protect the development process**. Therefore the process model is the **requirements layer**; rules/skills/agents/hooks/cockpit are its **implementation**. We define & ratify the process (W0.5) BEFORE conforming the artifacts to it (W1+). Refactoring implementation without ratified requirements = cleanly cementing the wrong process.

**Two processes, both modeled, both visible in the cockpit:**
- **Product-dev process** — how capabilities get built for the project/brands.
- **Harness-improvement process** — how the dev-OS improves itself (HLP + CIL). The harness self-hosts this use-case (dogfood).

**Work-type taxonomy (the use-cases the process must handle):**

| # | Work type | Actors/skills | Cockpit view | Maturity (to validate in W0.5) |
|---|---|---|---|---|
| WT1 | UI/functional capability (new/extend/modify) | po-ux→architect→dev→auditor→pm | /board · /functionality | mature |
| WT2 | Service capability (no UI) | po→… | /board | mature |
| WT3 | Agentic (conversational flow / AI action) | po+ux-agentico→… | /board · agents | mature |
| WT4 | Bugfix/hotfix (technical or UI) | bugfix story type, repro-first | /board | mature (ADR-011) |
| WT5 | **Technical capability** (observability/security/perf/infra) | TBD | Infra zone (user_visible:false) | **UNDER-DEFINED — gap to close** |
| WT6 | Promotion (brand→engine lift) | pm-luana modo core | TBD | mature; needs core/project placement |
| WT7 | Harness improvement (dev-OS CI) | HLP, /harness-issue, /harnesses-improvement, CIL | /harness | mature; needs unified cockpit view |

Each WT, in W0.5, gets: lifecycle states · actors · gates · artifacts · **cockpit view** · **core-vs-project split** (generic skeleton = CORE; luana instances = PROJECT). The pieces exist today but are scattered across ~8 docs (`lifecycle.md`, `capability-protocol.md`, `paradigm-arquitectura.md`, `promotion-protocol/`, `harness-lifecycle.md`, DoD #37, `story-closure-gate.md`) and were never consolidated into one operator-walked model. W0.5 consolidates + closes WT5 + unifies cockpit visibility.

## 2. Target end-state

```
repo/
├── core-harness/              ← CORE · 100% agnostic · the extractable kit
│   ├── rules/                 ← process invariants only (lean always-on)
│   ├── skills/                ← pm/po/architect/dev-team/auditor (generic)
│   ├── agents/                ← builder/auditor/gate-runner (generic contracts)
│   ├── hooks/                 ← generic enforcement
│   ├── templates/             ← spec/arch/validators/tickets (with {SLOTS})
│   └── process/               ← doctrine (lifecycle, gates, playbooks)
│
├── project.config.yaml        ← THE SEAM (DIP): the slots the CORE reads
│
├── project-profile/           ← PROJECT · all luana/tech/domain
│   ├── rules/                 ← stack-specific (backend-ddd, frontend-fsd…)
│   ├── skills/                ← domain (offer/copilot/analytics/sales-agent…)
│   └── brands/{vitalia,…}/    ← BRAND · overlays + config + verticals
│
├── tools/luana-cockpit/       ← PROJECT tooling (renders the CORE read-schema)
└── legacy/{date}/             ← superseded files, deleted after W8
```

**Extractability mechanism — the `bootstrap-doctor`:** a skill+script. Drop `core-harness/` in an empty repo → run `/harness-doctor` → it reports exactly which seam slots are unfilled ("declare: toolchain, brands, locale, engine_prefix, live_verify_infra, design_system, domain_modules"). The CORE **self-declares its required inputs** via the seam. That is "detect what's missing and fill it."

---

## 3. The seam — `project.config.yaml` slots (the DIP contract)

The CORE is written against these abstract slots; the PROJECT fills them. Defining them is W5; every surface wires to them.

| Slot | Replaces (today smeared in ~15 files) |
|---|---|
| `toolchain.{lint,format,typecheck,test,migrate}` per stack | `ruff`, `pytest`, `mypy`, `npx tsc/eslint/vitest`, `alembic`, `.venv/bin/` literals |
| `brands[]` (enum) | `for B in nicolify vitalia comunify lupulo` hardcoded loops |
| `locale` | the `voseo`/Spanish-neutro gate as a hard step |
| `engine_prefix` | `core/luana-core-*` path literals in process logic |
| `live_verify_infra[]` (per brand: dev-app URL, test user, ports) | vitalia URLs/creds/ports in rule #37 normative body |
| `design_system_ref` | the `design-system-canon.md` binding |
| `domain_modules[]` | offer/copilot/analytics/… as process assumptions |

---

## 4. Constitution — SOLID / clean-arch adapted to harnesses

Every session scores its surface against this. Each principle has a *smell* and a *fitness test*.

| Principle | In the harness | Smell | Fitness test |
|---|---|---|---|
| **SRP** | 1 skill/rule/agent = 1 responsibility | a process change touches 8 files | "how many files does this change touch?" → 1 |
| **OCP** | add brand/project = add profile, never edit CORE | a brand bootstrap edits the engine | bootstrap = `cp` + config only |
| **LSP** | every `pm-{brand}` is a faithful instance of the template | template-vs-instance drift | sync-check template↔instances |
| **ISP** | an agent loads only what its task needs | 43k tokens always-on by default | always-on rules ≤ ~500 lines |
| **DIP** | process depends on the seam (slots), not FastAPI/vitalia | tech hardcoded in process logic | `grep` tech-tokens in `core-harness/` = 0 |
| **High cohesion** | one concern, one home | 3 rules re-state "what is verified" | 1 SSoT per concern |
| **Low coupling** | a rule stands without 9 siblings | a hub cited by 9 rules | cross-refs per file ≤ ~2 |
| **Dependency rule** | Brand→Project→Core, never reverse | CORE names a brand/tech | `grep` brand/tech in `core-harness/` = 0 |

---

## 5. The session playbook (the consistent logic every workstream follows)

Each roadmap point = **one Opus session, own context**, always these 7 steps:

1. **Load the constitution** (this charter + the principles).
2. **Research internal** (read the real surface) **+ external** (Claude Code docs, `date`-aware June-2026; never trust model memory for SOTA).
3. **Classify/design** each file against the principles + the Core/Project/Brand layer (tag every file `tier: core | project | brand`).
4. **Verify anti-false-positive** (dependency greps in hooks/scripts/skills; empirical test when a mechanism is uncertain — e.g. the `paths:` test).
5. **Apply** (path-stable changes first; coordinated changes behind a dependency-grep gate).
6. **Validate** (surface still works; gates green; `bootstrap-doctor` doesn't regress).
7. **Capture learnings** (cohesion/coupling/SOLID notes) → feed back into this charter.

All sub-work uses **Opus** subagents. A session leaves its surface **cemented**, not half-done.

### Kickoff template (paste to start any workstream session)

```
Sesión harness · W{n} · {surface}.
1. Cargá docs/process/harness-refactor-charter-2026-06-08.md (constitución + playbook).
2. Corré el playbook de 7 pasos para W{n} sobre: {scope paths del WS}.
3. Subagentes Opus para research interno+externo y verificación anti-falso-positivo.
4. Entregá: tabla `tier: core|project|brand` por archivo + cambios aplicados (path-stable primero) + learnings.
5. No editar fuera del scope de W{n}. Superseded → legacy/2026-06-08/. Harness session dedicada (no mid-feature).
```

---

## 6. Roadmap (5 phases, all points)

> **★ Progress (2026-06-09):** **DONE** = W0 · W0.5 · W0.5-bis · W1 (Phase-1) · W2 · W3 · W4 · W4b (B-phase COMPLETE) · **W6 + W5a + W5b (seam WIRED) DONE.** **W7 GATE-ZERO DONE + RATIFIED + lift-kit SCAFFOLD built (2026-06-09):** the physical-move's load mechanism was date-aware verified (2 independent Opus passes) — a naive move of `rules/`+`agents/` OUT of `.claude/` **breaks Claude Code's always-on load** (rules: no external-dir/no-plugin-rules-channel; agents: excluded from `--add-dir`). This hit escalation condition (d). **Chris RATIFIED `W7-OUTPUT.md §2` = Option C (per-surface doc-safe) + plugin-shape NOW** (reframe: the portable IP is the PROCESS, not the multibrand machinery — multibrand is already a seam slot `brands.active=[one]`). Key facts: rules-symlink is DOCUMENTED-SAFE; agents/skills-symlink UNDOCUMENTED+buggy (needs a session-restart empirical test); **both copy & symlink keep `.claude/…` paths stable → the validator's 29 hardcoded paths are unaffected** (big de-risk). **Built this session (additive, inert, machinery 65/0/0):** `core-harness/` scaffold + README (the Option-C re-expose mechanism + extraction procedure) + the plugin-shape lift-kit (`marketplace.json` + `plugin.json` + SessionStart-rules-injector hook ≤10k + `/harness:bootstrap` skill) + the §9 execution playbook + the move-manifest + D2 spec + R-OBS/R-CI assessment + `PLUGIN-DISTRIBUTION-RESEARCH.md` (cross-account/private-marketplace model). **The physical file-move + the restart-smoke (rules/agents CC-discovery) = a focused continuation** (read-by-path groups safe+observable; rules/agents need the restart). **NEXT = W7-execution (the move · focused) → W8 (extraction test) → W9 (legacy delete) → W10 (governance)** — each is STRUCTURAL, **Chris-ratified, ONE session each, new conversation anchored to this charter** (HLP governance · NEVER auto-run a structural WS). Outputs per WS: `docs/process/harness-refactor-w{n}/W{n}-OUTPUT.md` (+ research siblings). Open B-phase tail: W1-Phase2 (Tier-3 eviction, `wip/protocol-rules-refactor`) + Tier-2 `paths:` (gate-blocked, needs #16299 empirical test). **★ 3 W4b-pending decisions RATIFIED 2026-06-09 (`DECISIONS-PENDING.md` header):** D1 (Stop-hook caps → keep coarse, seam numbers → **W5**) · D2 (shared hook source → canonicalize on `main` + fix `install-hooks` → **W7**) · D3 (CHECK 11 G8/G9 → **W6 implemented**). **W6 cemented:** 26 templates + 37 process-docs tagged (templates 6 core/18 hybrid/4 dead-tombstone · process-docs P1 7 core/11 hybrid · P2 0 core/17 hybrid); **`01-spec-template` inverted functional-first** (§ Pantallas + § Mockup-FINAL-before-Gherkin + comment-marker + GENERADO-at-firma-2, preserving CHECK 9/25/27); 4 dead-refs fixed (02-design-ui ×2 → `01-spec § Wireframes`; 5 phantom agentic-eval scripts + mirror-scan → real `pytest tests/agentic_evals/`); 6 stale-vocab fixed (demo_signoff→chris_verify ×4, phase_workflow/A-F demote, v4.2→v5 ×2, lifecycle WIP-cap module-scoped, story-closure-gate v5 banner, INDEX +5 rows, pm-redesign SUPERSEDED banner); **Decision 3 verify-first re-scoped** (premise stale — CHECK 11 already asserted G8/G9 since `c77793f3`; implemented OCP registry-derivation + doc G8/G9, NOT the non-problem); 2 served-purpose handoffs → `legacy/2026-06-09/` (grep-gated); {SLOTS} = manifest-authoritative (one-SSoT, no inline churn); 5 process decisions flagged for Chris. machinery 65/0/0 (73→65 = D3 OCP fewer-stronger checks). **★ W5a cemented (2026-06-09):** the seam SCHEMA ratified by Chris — `project.config.PROPOSED.yaml` (9 slots + `wip_caps`/D1, luana literals harvested) + the read mechanism date-aware verified vs official Claude Code docs (bash/python `harness_config.py` loader · cockpit `js-yaml` · markdown `{slot}` CONVENTION — NO native interp for rules/CLAUDE.md/agents; optional skill-only `` !`cmd` `` upgrade). **F1 = CENTRALIZED** (per-brand facets nest under `brands[]`, §4 shape) · F2/F3 defaults (root yaml, full roster/value_stream in seam). DRY wins: `wip_caps` D1 kills the 2-script verbatim dup · `dev_app`/ports one-home in `brands[]`. 7 harvest flags recorded (engine=27 not 26; dev_app non-uniform per-brand; comunify/lupulo rosters `__FILL_ME__`; etc.). W5b (fresh session) builds the loader + doctor + wires the `{SLOTS}` union behind the grep-gate + re-tags lifted hybrids `core`. **ZERO live-harness edits in W5a** (design-only · 65/0/0 holds). SSoT: `harness-refactor-w5/W5-OUTPUT.md`. Commit `f47a9e20`. **★ W5b WIRED (2026-06-09):** loader `scripts/harness_config.py` (TDD · `<slot>`/`--doctor`/`load` · `safe_load` · parent-walk · exit-3 on `__FILL_ME__`) + cockpit `lib/project-config.ts` (server-only · `yaml` pkg — NOT js-yaml · cross-runtime fixture parity test) + `project.config.yaml` moved to repo ROOT. **13 consumers wired:** 10 executable (D1 `wip_caps` dedup validate_session_close+generate_backlog · `brands.active`/`brands.loop_order` into scan_promotables/mutation_gate/pre-push + check-sync/regenerate-manifest/cleanup-session/12-story-closure/claude-md-overlay) + 3 markdown `{slot}` (anti-duplication/parallel-safety/auditor-downstream **LIFTED hybrid→core**). **All 13 core-tagged rules proxy-CLEAN** (the cheap W8 · 0 tokens). Bash degrade = empty+LOUD-warn (no hardcoded fallback → keeps `core`). **3 seam-schema forks RESOLVED (Chris delegated to criterion · §W5b.g):** generate_portfolio.UNIVERSES **WIRED** (structural enum from seam · narrative cohesive-local) · `cap_gate: hard|advisory` **WIRED as a per-brand F1 facet** (+ loader `--where` filter · 05e+pre-push derive the HARD set) · contract-guard.js **NOT wired** (maintainability call — node has no yaml parser + RULES shape richer than the slot; the dispatch kernel is the portable IP, RULES stay project-inline). ZERO new top-level slots (ratified 9+D1 held; cap_gate is a facet). Still hybrid-by-construction: DoD brand-URL examples (`mutation_gate.py` asserted CHECK 19). machinery 65/0/0 throughout. SSoT: `harness-refactor-w5/W5-OUTPUT.md` § W5b. **★ W7-EXECUTION DONE + W8 extraction-test PASSING (2026-06-09):** the physical move was executed per the ratified Option-C + plugin-shape (6 commits `62edb18d`→`3b82ea9b`, machinery 65/0/0 + pointer 28/NEW-0 through every group). Moved into `core-harness/`: 21 core rules (symlink-back into `.claude/rules/`, DOC-SAFE) · 6 process-docs + 5 templates · `harness_config.py` + 6 core git-scripts · 3 pre-commit checks (07/11/17) · grep-bot (copy) · plugin-shape (manifest curated, injector smoke 8090-char JSON). **Path-stability held perfectly — ZERO consumer repoint** (the 29 validator paths + 13 loader consumers + dispatcher all resolve through symlinks). **POST-move dependency-grep over `core-harness/` = 2 hits, both grep-bot generic build-artifact skip-dirs → measured DoD MET.** D2 (install-hooks canonical-source) implemented (not re-run; vitalia-hub stopgap until program→main merge). **W8 proved it:** drop kit + empty config into `/tmp` → `--doctor` exit-3 self-declares 11 slots → fill with a fictional Go/single-tenant/en-US product (`ledgerline`) → exit-0, core reads the seam (never luana), zero core edit. **2 manifest corrections:** the 14 rules-detail mirrors are tier:PROJECT (6–45 tokens each = the stubbed-out stack half — they STAY); charter/PROCESS-MODEL/REQ-TAKING-DETAIL are hybrid program-record (NOT shipped core). **Residual:** rules always-on **restart-smoke PENDING** (a fresh session — doc-safe by spec). **W7-tail deferred:** architect-`{be,fe,agentic}` rehoming (hybrid, machinery-asserted, orthogonal to extraction). SSoT: `harness-refactor-w7/W7-EXEC-OUTPUT.md` + `harness-refactor-w8/W8-OUTPUT.md`. **★ PROGRAMA COMPLETO (2026-06-09, sesión de cierre Chris-delegada): W9 ✅** (legacy borrado post-W8 grep-gated + reconcile + **restart-smoke PASS** — las 21 rules symlinkeadas cargaron always-on con cuerpo completo en sesión fresca → Option-C confirmado end-to-end) **+ W10 ✅** (anti-rot: **CHECK 29** proxy-clean core-harness en cada commit = el cheap-W8 mecánico + **CHECK 30** LSP sync template↔instancias PM — cazó drift real día-1: pm-comunify/lupulo sin Auto-chain — + HLP/CIL verificado + cadencia merge→main D2; machinery 65→**67**/0/0 by-design) **+ colas pagadas:** W7-tail architect-{be,fe,agentic} rehomed a `architect/references/` · **Tier-2 `paths:` gate RESUELTO empírico** (#16299 ausente: DEFAULT=NO + POSTREAD=YES, A/B headless `claude -p`; `globs:` confirmado muerto) · **W1-Phase2 EJECUTADA** (12 domain rules → owning-skill references + 3 Tier-2 conversions; always-on 1726→**1310**, project-side −50%). Deliverables: `harness-architecture-guide.md` (Chris deep-dive) + `core-harness/ADOPTING.md` (adopción single-brand/otra-tech). SSoT cierre: `harness-refactor-w9/W9-OUTPUT.md` + `harness-refactor-w10/W10-OUTPUT.md` + `docs/learnings/tooling/2026-06-09-harness-refactor-program-close.md`. El merge `wip/vitalia`→`main` (gate canónico + D2 efecto) = **decisión de Chris**.

| Phase | WS | Session (1 each, Opus) | Scope paths | Done when | Depends on |
|---|---|---|---|---|---|
| **A · Constitution** | W0 | this charter | — | charter persisted + forks locked | — |
| **A.5 · Process Model** | W0.5 | **Process model (operator-POV)** — AS-IS map (Opus subagents) + TO-BE ratified WITH Chris: per work-type WT1-7 → lifecycle/actors/gates/artifacts/cockpit-view/core-vs-project. Closes WT5 (technical caps), unifies cockpit visibility. | the ~8 process docs + cockpit + entry skills | Process Model SSoT ratified by Chris; WT5 defined; every WT mapped to a cockpit view | W0 |
| **A.6 · Req-detail** | W0.5-bis | **Refine-detail de la toma de requerimientos** (added 2026-06-08, Chris) — W0.5 ratified the refinement *skeleton* but not the *detail* of HOW requirements are taken per input type. An **open-ended interview** (Chris↔Claude, abiertas + repreguntas, NO execution) over: raw intake · pre-spec interrogation · how it differs per type (UI/service/agentic/bugfix/technical) · scope-cut · artifacts+signatures · design-system-canon compose · current pains. **Gates W2 (skills) + W6 (templates)** — those implement refinement, so the requirement must close first (avoids re-work; W1 already done is unaffected). | `PROCESS-MODEL.md §3` (WT1-5 cards) + `spec-mapa-funcional.md` (+ entry skills read-only) | **✅ CLOSED 2026-06-08** — Chris ratified the per-type requirement-taking detail; §3 §3.0 + WT1-5 cards + spec-mapa-funcional updated; CORE-vs-Luana tagged. SSoT: `harness-refactor-w0.5/REQ-TAKING-DETAIL.md` | W0.5 |
| **B · Surface audits** | W1 | **Rules** (3-tier; analysis in `harness-rules-audit-2026-06-08.md`). Surfaces now also validated for **conformance to the ratified process model**. | `.claude/rules/`, `docs/rules-detail/` | rules tagged core/project/brand; always-on lean; conform to W0.5 | W0.5 |
| | W2 | **Skills** (dedup via pointer+sync; fix template drift; depopulate phantom PMs; taxonomy) | `.claude/skills/` | no dup/drift; process vs domain split | W0 |
| | W3 | **Agents** (SRP + anti-telephone contract; generic vs stack) | `.claude/agents/` | 11 agents tagged + contract verified | W0 |
| | W4 | **Hooks + pre-commit checks** (enforcement: generic vs project) | `.claude/hooks/`, `scripts/git-hooks/` | 4 hooks + 18 checks tagged | W0 |
| | W4b | **Scripts + Cockpit** (cockpit read-schema=core contract, render=project tool; classify `scripts/`) | `scripts/`, `tools/luana-cockpit/` | cockpit split; scripts tagged | W0 |
| | W6 | **Process-docs + Templates** (consolidate archaeology; add {SLOTS} to templates) | `docs/process/`, `docs/specs/templates/` | docs/templates tagged; generic vs luana | W1-W4b |
| **C · Structural split** | W5 | **The seam `project.config.yaml`** — split: **W5a ✅ schema design + ratify (2026-06-09)** · **W5b ✅ wired (2026-06-09)** — loader `harness_config.py` + cockpit `project-config.ts` + 13 consumers (10 exec + 3 markdown) + 3 hybrids→core + D1 dedup; 3 schema-forks flagged | `project.config.yaml` at root + loader + repoint | all tech/brand/locale reads the seam (core rules proxy-clean) | W1-W4b |
| | W7 | ✅ **Core/Project/Brand physical move DONE** (Option-C symlink/copy; 6 commits `62edb18d`→`3b82ea9b`) | repo-wide reorg | ✅ `core-harness/` grep-tech = 0 (only grep-bot generic skip-dirs); restart-smoke PENDING | W5, W6 |
| **D · Extractability** | W8 | ✅ **Bootstrap-doctor + extraction test PASSING** (`ledgerline` fictional product in `/tmp`) | doctor + temp repo | ✅ doctor detects gaps; fill→resolve without editing CORE | W7 |
| **E · Cleanup + governance** | W9 | ✅ **Legacy cleanup DONE** (program legacy/ deleted post-W8 grep-gated; restart-smoke PASS; indexes reconciled) | `legacy/`, MEMORY.md, indexes | ✅ zero orphan/stale in live surfaces | W8 |
| | W10 | ✅ **Anti-rot governance DONE** (CHECK 29 proxy-clean + CHECK 30 template↔instance sync, negative-tested; HLP/CIL intact; merge cadence) + **final learnings → CIL L2** | governance rules + this charter | ✅ mechanisms prevent re-Frankenstein | W9 |

**Critical path:** W0 → **W0.5 (process model — gates everything)** → **W0.5-bis ✅ (req-detail — gates W2/W6 · `REQ-TAKING-DETAIL.md`)** → (W1✅‖W2‖W3‖W4‖W4b) → W6 → W5 → W7 → W8 → W9 → W10. The B-phase surfaces can run in **parallel sessions** because the charter + the ratified process model (W0.5) make them consistent without coordination. **W0.5 is the requirements gate: no surface refactor starts until the process it implements is ratified.** **W0.5-bis specifically gates W2 (refinement skills) + W6 (spec templates): the requirement-taking detail must be ratified before those surfaces implement it.** (W1 rules already done — unaffected; W1-Phase2 + W3/W4/W4b don't depend on W0.5-bis.)

---

## 7. Cross-WS conventions

- **Tagging:** every file gets a `tier: core | project | brand` decision (recorded in the WS output table). This drives the W7 physical move.
- **Path-stable first:** prefer changes that keep a file's path (stub-in-place) over moves; do moves behind a dependency-grep gate.
- **Anti-false-positive is mandatory:** before any move/delete/merge, grep `scripts/ .claude/hooks/ Makefile .claude/skills/*/SKILL.md` for the filename AND a distinctive body string. Chris is paranoid about false positives — earn each claim. **Verify the consumer side, never the producer's self-description** (W1: `step-0-worktree` *claimed* an `@`-import that grep proved doesn't exist). **The consumer check is two-level (W4):** (a) is it registered (`settings.json` / `make install-hooks` / `.git/hooks` symlink)? AND (b) is the INSTALLED artifact actually current? — `make install-hooks` *intends* symlinks, but a live `.git/hooks/pre-push` was a stale **copy** 4 days behind source. The source can be perfectly refactored while the *running* gate is an old file. Smoke the source directly; flag install drift.
- **Validate-after-apply:** a rule/skill/agent body can be a **load-bearing string for a deterministic gate** (`validate_machinery_consistency.py`), not just prose. After any stub/move, run `make machinery-check` (0 fallos) + `scan_harness_pointers.py` (NEW 0) + smoke the touched hook — **green prose ≠ green gate** (W1: stubbing #37 dropped `scripts/mutation_gate.py` → CHECK 19 red). Learning: `docs/learnings/tooling/2026-06-08-harness-refactor-stub-against-the-gate.md`.
- **B-phase recurring learnings (W1→W4, durable — apply every surface session):** (1) **Propagation-grep is the highest-yield conformance tool** — when a doctrine is ratified, grep the IMPLEMENTING surface (rule/skill/agent/hook/check) for the OLD token; the SSoT never propagates itself (W2 `02-design-ui`/`v4.2`; W3 same; W4 `atomics`/`outcomes`/`demo_signoff`/`blocked`). The fix is almost always "doc moved, implementer stayed." (2) **`tier:core` is proxy-EARNED, not intent-assigned** (§0.5 option-b) — core is RARE (rules 18 → skills 0 → agents 1 → hooks 5); the portable IP is the *contract/skeleton*, the worker body is project-bound (rewrite per product). (3) **"Purged" is scope-qualified** — verify WHICH layer retired a concept before deleting a live trigger (W4: `outcomes/` purged at *brand* level but still read at *platform* level by `generate_backlog.py` — the naive global rip would have broken a live regen trigger). (4) **A comment-only edit to an I/O artifact still needs a FUNCTIONAL smoke**, not just `bash -n`/parse — exercise the real stdin→stdout/gate contract. (5, W4b) **A gate dead-by-drift + masked by an advisory caller is worse than no gate** — verify a gate can actually REACH its assertion (target exists, venv runs), not just that it's wired; a gate that can't run must fail LOUD/advisory, never silent-pass (`validate_ci_parity_mirror` silent exit-2 on a renamed workflow; Stop-hook freshness no-op'd on `backend/.venv`). (6, W4b) **A missing read-schema field is often type-only** when the producer passes data generically (cockpit `...(fm as Story)` spread) — fix the contract declaration, not the plumbing; the extraction contract is the type SHAPE. (7, W4b) **Conform a stale gate ≠ rewrite its semantics** — fix unambiguous drift; FLAG the open process decision (Stop-hook coarse-v4-global-caps vs canonical-v5-module-scoped) to Chris rather than unilaterally duplicating the canonical gate.
- **Dogfood:** the charter and its outputs obey their own principles (lean, pointer-first, one SSoT per concern).
- **Verification > model memory:** for any Claude Code mechanism claim, fetch official docs (`date`-aware). Confirmed June-2026 facts: `.claude/rules/` whole-dir always-on; `paths:` native conditional (read-trigger, **not** write — issue #23478 wontfix; #16299 open: may load globally — empirical test required); `globs:` ignored; `@import` CLAUDE.md-only, doesn't reduce context.

---

## 8. Program Definition of Done (success = the extraction test)

Take `core-harness/` + an empty `project.config.yaml`, drop into a fresh repo, run `/harness-doctor` → it lists the missing slots → fill them with a *different* product's info (vision, tech, design) → the `idea→done` cycle runs **without editing the CORE**. When that passes (W8), and `legacy/` is cleared (W9), and anti-rot governance is in place (W10) — the program is done.

---

## 9. Inputs / prior artifacts

- `docs/process/harness-rules-audit-2026-06-08.md` — W1 analysis (rules 3-tier classification, mechanism truth, bug findings). Feeds W1.
- `docs/process/harness-lifecycle.md` (HLP) — "never edit harness mid-feature" + the apply-pipeline. Governs how each session commits.
- `docs/process/harness-backlog.md` — the CIL L1 lane; harness issues land here.
