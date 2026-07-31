# W4b · Scripts + Cockpit — Output (tier manifest + cockpit read-schema/render split + no-paper-rules verdict + process conformance + applied deltas + smoke + handoffs closed + learnings)

**Date:** 2026-06-09 · **Session:** harness-refactor W4b (B-phase · the last B-phase point) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` (precedent: W0/W0.5/W0.5-bis/W1/W2/W3/W4 HEAD here) · **Status:** APPLIED + cemented (path-stable + 3 grep-gated moves).

> **North-star card:** *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens (the rest went to the seam). The goal is an extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*
>
> Charter §6 W4b done-when: *cockpit split + scripts tagged + machinery 73/0/0.* Inputs: `PROCESS-MODEL.md §1,§5,§6,§7` (10-state+{G,R,C,D} vocab · one-SSoT · conformance checklist · cockpit read-schema=core/render=project) + charter §0.5 (option-b proxy) + W4-OUTPUT §5/§6 handoffs (Stop-hook · git gate-scripts · install-drift · contract-guard edge). **Per-file detail is pointer-first in the 3 RESEARCH siblings (`RESEARCH-batch-{A,B,C}.md`) — not duplicated here.**

---

## 0 · Scope + headline result

Scope = `scripts/` (48 top-level .py/.sh + 7 subdirs) + `tools/luana-cockpit/` (Next.js 16 read-schema + render). **Real surface (ls manda):** 3 Opus subagents classified **~57 script files + 2 JSON** (Batch A=12 cap-machinery · B=15+2 portfolio/migrations · C=30 machinery/git/ops/pii/subdirs/warp); I classified the cockpit (read-schema vs render) myself + handled the W4 handoffs.

**Headline:** the script + cockpit surface is mechanically **sound** — **NO critical paper-rules that crash a live gate**, but **the W4-handed Stop hook + 1 CI-mirror validator were silent/under-enforcing dead gates** (now fixed), and the cockpit **read-schema was stale on the v5 spine fields** (now declared). Tier shape mirrors W1→W4: **core RARE** (proxy-EARNED coordination/protection mechanisms only), almost everything `hybrid` (core mechanism + project runner-half → seam), **brand≈0** (OCP — brand is config, not a script). **Validated after every edit (W1 non-negotiable): `make machinery-check` = 73 · 0 · 0 · `scan_harness_pointers.py` = NEW 0 · cockpit `tsc --noEmit` rc=0 + `vitest` 140/140 · every touched script ruff-clean + functional-smoked.**

**Applied (all path-stable except 3 grep-gated legacy moves):** cockpit read-schema v5 fields (type-only) · Stop-hook multibrand conformance (S1-S5) · ci-parity-mirror deferred-aware (kill silent dead-gate) · 2 doc-rot fixes · 1 stale brand-surface row · 3 dead scripts → `legacy/2026-06-09/` · pre-push install-drift re-symlinked.

---

## 1 · Tier manifest (drives W7) — scripts + cockpit split

**Option-b proxy (charter §0.5, ratified Chris):** `tier:core` EARNED only if the dependency-grep (`vitalia|nicolify|comunify|lupulo|ruff|pytest|mypy|alembic|clerk|next|tailwind|fastapi|sqlalchemy|core/luana-core|.venv|dev-app|hipaa|phi`) = **0 hits**. Any token ⇒ `hybrid` (core mechanism + project-half parked → seam W5), not rewritten to `{slot}` now.

### 1a · Scripts — per-batch counts (full per-file table in `RESEARCH-batch-{A,B,C}.md`)

| Batch | Files | core | hybrid | project | brand | dead→legacy |
|---|---|---|---|---|---|---|
| **A** · cap-machinery (HB-51 4-ejes) | 12 | 0 | 8 | 3 | 1 | 0 |
| **B** · portfolio/backlog/system-map/migrations/metrics | 15 (+2 JSON) | 0 | 13 | 2+JSON | 0 | 3 |
| **C** · machinery/git/ops/pii/subdirs/warp | 30 | ~6 ★ | ~14 | ~10 | 0 | 0 |
| **Combined** | **~57 (+2 JSON)** | **~6** | **~35** | **~15** | **1** | **3** |

★ The ~6 proxy-clean `core` (all Batch C) = pure git-coordination / main-protection / session-lifecycle mechanisms: `git/commit-paths.sh` · `git/session-lock.sh` · `git/multi-session-scope-guard.sh` · `git/dod-evidence-gate.sh` · `git/cleanup-wip-branches.sh` · `git/ps1-luana.sh`. The **1 `brand`** = `build_live_reconciliation_matrix.py` (hardcodes `BRAND="vitalia"` + single-brand sweep path — the rare genuine per-brand tool). **Same law as W1→W4** (rules 18 core → skills 0 → agents 1 → hooks 5 → **scripts ~6**): the portable IP is the *coordination/protection/read SKELETON*; every script that shells `ruff`/`pytest`/`docker`/`make dev-{brand}` or loops the brand enum is `hybrid`/`project` by construction. **The #1 W5 lift = the recurring hardcoded brand enum** (`new-session`/`check-sync`/`cleanup-session`/`generate_portfolio.UNIVERSES`/`scan_promotables.BRAND_SLUGS`/`reconcile`/all cockpit+dev-app port maps) → `brands[]` seam lifts most `hybrid`→`core`.

### 1b · Cockpit split (PROCESS-MODEL §7: read-schema = CORE contract · render = PROJECT)

| Layer | Files | tier | note |
|---|---|---|---|
| **READ-SCHEMA contract** | `lib/types.ts` (Story/Capability/SystemMap/Release/ComputedStatus shapes + `StoryType` + `CHRIS_ALLOWED_TRANSITIONS`) | **hybrid** | core read-schema SHAPE + the v5 spine fields (this session) — but proxy=5 (`hipaa_lite_overlay`, `phi`, `vitalia` ADR provenance) ⇒ hybrid (brand fields → `live_verify_infra`/BRAND seam). The portable contract = the generic shape a new product must emit. |
| **FS / lifecycle read primitives** | `lib/{fs-reader,fs-writer,git,sessions,chris-input-parser,md-lifecycle-table,edit-permissions}.ts` | **core-candidate** | proxy-clean generic filesystem-as-DB + lifecycle + transition-permission mechanisms (the portable read kit). |
| **Glob/path builders** | `lib/{story-paths,workspace}.ts` | **hybrid** | the globs the cockpit reads + brand enum → `brands[]`/layout seam (workspace proxy=4, story-paths=6). |
| **RENDER** | all `components/*` + `app/*` (routes + API render) + `lib/{api-client,cap-badges,cap-ledger,drift-helpers,release-resolver,harness-backlog,tech-debt,platform-context,cn}.ts` | **project** | the React render of the read-schema (per §7). Proxy-clean ones (api-client, harness-backlog) are still render-coupled = project (lens-1: not portable IP). |
| **Seam render-data** | `lib/agent-meta.ts` → `agent_roster` · `lib/map-zones.ts` → `value_stream` · `lib/tooltips.ts` → `locale` | **project/brand** | the §4 new seam slots (`agent_roster`/`value_stream`) verbatim. |

> Cockpit NOT inline-tagged file-by-file (churn-avoidance, same decision W4 made for the 22 checks) — this manifest is authoritative for W7. `validate_machinery_consistency.py` CHECK 12 (`ScenariosSection.tsx`) + CHECK 22 (`harness-backlog.ts`) string-assert two render bodies; W4b touched neither (only `types.ts`).

---

## 2 · No-paper-rules verification (deliverable b · PROCESS-MODEL §6.5/§6.6)

`test -e`-verified every cited script/path/rule/make-target across all ~57 scripts (3 subagents + my re-checks). **Mechanically mostly sound** — but **5 real dead-references found** (4 fixed this session, 1 deferred-with-reason):

| # | Dead ref | Where | Verdict / action |
|---|---|---|---|
| 1 ★ | workflow `deploy-prod.yml` + `jobs.quality-gates` (both GONE — CI restructured to `ci.yml`/`cd-prod.yml`) | `validate_ci_parity_mirror.py:54,67` | **FIXED** — was silent `exit 2` masked by `ci-parity.sh`'s advisory wrapper = a **dead gate worse than no gate**. Now **deferred-aware**: missing target → LOUD advisory + `exit 0` (no false dead-gate); repoint at CI reactivation. |
| 2 | missing plan `.claude/plans/ok-lo-apruebo-realiza-cheeky-harbor.md` | `migrate_capability_ledger.py:15` (docstring) | **FIXED** — repointed to `docs/process/capability-protocol.md § cap schema` (real SSoT). Docstring-only; logic never read it. |
| 3 | dead workflow name `deploy-prod.yml` ×5 (comments) | `ci-parity.sh:80,91,93,117,140` | **FIXED** — `deploy-prod.yml` → `ci.yml` (live CI). Comment/step-label only. |
| 4 | per-brand `ci-parity-passed-$BRAND-$SHA` marker (writer) vs no-brand `ci-parity-passed-$SHA` (pre-push reader) → never match | `ci-parity.sh:150` ↔ `scripts/git-hooks/pre-push:34` | **DEFERRED → W5/CI-reactivation** (cross-surface: W4 pre-push + W4b ci-parity; **masked today** — pre-push is ADVISORY via `.ci-parity-deferred` sentinel, so the fast-path marker is moot. Reconciling the marker scheme now is speculative + risks the deferred pre-push). Flagged precisely. |
| 5 | machinery CHECK 11 does **not individually assert** G8/G9 gates (only `run_cap_gates` + `--cap-gates-hard` + G1-G6 repro) | `validate_machinery_consistency.py:321-389` | **DEFERRED → W6/cap-owner** (latent anti-rot gap: deleting G8/G9 wouldn't trip CHECK 11; but G8/G9 have their own negative tests per Batch A §3.5). Out of W4b scripts/cockpit scope — it's the cap-enforcement surface. |

**Consumer wiring verified (not producer self-description, W1 learning):** `settings.json` `Stop` registers `${CLAUDE_PROJECT_DIR}/.venv/bin/python …validate_session_close.py` (correct root venv); Makefile targets (`portfolio`/`infra-matrix`/`system-map-validate`/`new-cap`/`cap-gates`/`cap-doctor`/`migrate-vitalia-schema`/…) all resolve; pre-commit checks source the cap-machinery scripts. **3 dead scripts had 0 live consumers** (grep-gated, §4).

---

## 3 · Process conformance (deliverable c · stale caught/fixed + read-schema v5)

Method = the B-phase propagation-grep (W2/W3/W4): grep the IMPLEMENTING scripts for the OLD token of every ratified-retired concept. **The git-scripts + cap-machinery are CLEAN** (faithful 10-state+{G,R,C,D}, single-hub/triple-branch/M14, 4-ejes; `atomics` consistently a tombstone/inert-data x-check, NOT a live directive — Batch A §3.1, C §3). The stale tokens that DID survive clustered in two places:

### 3a · Cockpit read-schema v5 fields (D6① — the gap was REAL, not cosmetic) — FIXED

`app/api/stories/route.ts:40` spreads `...(fm as Story)` ⇒ **all checkpoint frontmatter keys already flow to consumers at runtime**; the gap was purely the `Story` TS-interface *declaration* (so consumers couldn't read them type-safe). Added to `lib/types.ts` (type-only, zero parser change):

- **v5 spine gate fields**: `chris_verify` (+ `ChrisVerify`/`ChrisSignoff` interfaces: `required`/`signoff{by,date,result,notes,open_items}`/`rounds`), `reconciled`, `dod_live_verified`, `dod_env`, `dod_evidence` (+ `DodEvidenceItem`), `autonomous_mode`, `repro_evidence` (+ `ReproEvidence`, the WT4 canonical key, repro=local OR trace D4).
- **`StoryType`**: added `'bugfix'` (had `'tech'`=technical ✓, was missing WT4 bugfix).
- **`phase`**: relabeled — was `"Legacy outcome/phase (DEPRECATED)"`; it is the **v5 live named-phase** (AWAIT_CHRIS_VERIFY/G/R/C/D under `developed`), NOT legacy. `outcome` left labeled legacy (correct); `phase_workflow` marked `@deprecated` (X6-retired).

> Render badges for these (PROCESS-MODEL §7 "all WTs show v5 gate badges") = a separate ratified-but-unbuilt RENDER feature → deferred (W6 / a product story). W4b closes the **read-schema** gap (the extraction contract), which unblocks any future badge work. Scope-disciplined.

### 3b · Stale-vocab in scripts — caught + fixed/kept

| # | Token | Where | Verdict | Action |
|---|---|---|---|---|
| 1 | `outcomes/` brand surface row + ownership | `generate_portfolio.py:327,340` (brand 1-pager template) | **LIVE STALE** — brand `outcomes/` purged (4-ejes); emitted a dead link in every brand 1-pager | **FIXED** → `Releases | {slug}/docs/product/releases/` (the real 4th axis) + ownership `outcomes`→`releases`. (`:403` luana 1-pager "Roadmap platform: docs/product/outcomes/" = **platform** = NOT stale, left.) |
| 2 | `backend/.venv/bin/python` (single-brand pre-multibrand) | `validate_session_close.py:132` + docstring snippet | **LIVE STALE** — venv at workspace **root**; the freshness sub-check was a **guaranteed no-op** | **FIXED** → root `.venv` (verified: freshness check now actually RUNS — surfaces real BACKLOG drift as WARN). |
| 3 | root single-brand layout (`docs/product/stories`, `docs/product/BACKLOG.yaml`) | `validate_session_close.py` (whole) | **LIVE STALE** — root stories dir doesn't exist; story buckets live per-brand → hook **under-enforced** (advertised multibrand WIP caps it didn't perform) | **FIXED** → glob-discover `*/docs/product/{stories,BACKLOG.yaml}` (no hardcoded enum; per-brand caps, faithful generalization, verified non-spurious: vitalia within caps → exit 0). |
| 4 | dead `outcomes`/epic + `building`/`review` vocab | `validate_session_close.py` docstrings | retired (4-ejes / 10-state canon) | **FIXED** — dropped epic/outcomes language; docstring states → ACTIVE_STATES; added note that the CANONICAL module-scoped WIP cap is the pre-commit story-closure gate. |
| 5 | `atomics` (whole file) | `validate_atomics_implementation.py` | atomics KILLED 2026-05-28; 0 live refs | **MOVED → legacy/** (don't "fix" a dead concept). |

**Not stale (left intact, verified):** all `atomics` in `validate_machinery_consistency.py` / `reconcile_capabilities.py` / `generate_code_to_cap_index.py` = tombstones or inert-data x-checks (Batch A §3.1, C §3); `generate_backlog.py::read_outcomes` (PLATFORM `docs/product/outcomes/` still exists, 16 files — purge is brand-level) + `render_friendly_status.py` outcome handling (platform BACKLOG still has `kind:outcome`) = scope-qualified, NOT stale (W4 precedent); `generate_portfolio.py:403` platform-outcomes; `STATUS_EMOJI["blocked"]` in generate_portfolio = portfolio **brand-status** enum (distinct from the 10 story-states); `litellm-proxy-up.sh` `visionarias_litellm` = intentional back-compat alias.

### 3c · S5 (process decision — flagged, NOT unilaterally changed)

`validate_session_close.py` CAPS are **paradigm-v4 GLOBAL numbers** (developed≤10, etc.), not the **v5 module-scoped** `developed≤1 per code:{module}`. I did **NOT** rewrite the cap algorithm to module-scoped (it would duplicate/diverge from the canonical pre-commit `12-story-closure.sh` gate + change exit-2 BLOCK semantics). Instead: documented the hook as a **coarse per-brand session-close net** + pointed at the canonical gate. **Open process Q for Chris:** should the Stop hook adopt module-scoped v5 caps (duplicating the pre-commit gate), or remain the coarse net? (PROCESS-MODEL doesn't resolve this.)

---

## 4 · Applied changes + smoke evidence (deliverable d)

**9 surfaces touched · all path-stable except 3 grep-gated legacy moves. Zero logic risk to live gates (each smoked).**

- **Cockpit read-schema (1 file):** `lib/types.ts` — v5 fields (type-only). **Smoke: `tsc --noEmit` rc=0 · `vitest run` 140/140.**
- **Stop hook (1 file):** `validate_session_close.py` — S1 venv root, S2/S3 multibrand glob-discovery (WIP-cap + staleness), S4 docstring, S5 coarse-net doc + canonical-gate note. **Smoke: ruff clean · functional run `--repo .` → exit 0 + WARN shows freshness check now LIVE (was no-op) + per-brand read (no spurious block, vitalia within caps).**
- **CI-mirror (1 file):** `validate_ci_parity_mirror.py` — deferred-aware (missing workflow → loud advisory + exit 0, was silent exit-2). **Smoke: ruff clean · run → prints advisory, rc=0 (was rc=2).**
- **Doc-rot (2 files):** `ci-parity.sh` (deploy-prod.yml→ci.yml ×5, comments) + `migrate_capability_ledger.py:15` (missing-plan→capability-protocol.md). **Smoke: `bash -n` OK · py_compile OK.**
- **Stale brand-surface (1 file):** `generate_portfolio.py` outcomes→releases (×2). **Smoke: ruff clean · `--check` runs (rc=1=drift, not crash) · brand template now has Releases row + 0 brand-outcomes links.** (Also auto-fixed 2 PRE-EXISTING ruff errors in the 2 edited py — F541 + I001 — to leave-file-better + unblock the commit's pre-commit ruff gate.)
- **Dead → `legacy/2026-06-09/` (3 git mv, grep-gated):** `validate_atomics_implementation.py` (atomics killed, 0 refs) · `propagate-adr-vitalia-004.py` (one-time, only ADR narrates it) · `test_delta_check.py` (one-time, only archived story). **Grep-gate: 0 live consumers (excl self + /archive/); no pytest collection of `scripts/*.py`.** + `legacy/2026-06-09/README.md` provenance.
- **Consumer-side (install-drift, W4 handoff):** re-ran `make install-hooks` → pre-push was a **stale copy** (8014B jun-1) → now a **symlink to current source** (W1-W4 edits). Both hooks now consistent. **Smoke: `bash -n` installed pre-push OK.** (Note §5.)

**Final validate-after-apply:** `make machinery-check` **73 · 0 · 0** · `scan_harness_pointers.py` **NEW 0** (baseline 28→28; legacy moves had 0 pointer refs) · all touched .py ruff-clean · cockpit tsc rc=0 + vitest 140/140.

---

## 5 · W4 handoffs closed (deliverable d cont.)

| W4 §6 handoff | W4b disposition |
|---|---|
| `Stop` hook `validate_session_close.py` tier + conformance | **DONE** — `tier: hybrid` (Stop-hook contract=core; venv/brand-loop/CAPS/globs → seam). STALE→CONFORMANT (S1-S5 fixed; the freshness no-op + single-brand-tree + dead vocab repaired; S5 cap-semantics flagged for Chris). |
| pre-push install-drift (stale copy 4 days behind source) | **DONE** — re-ran `make install-hooks`; pre-push now a symlink to current source. **Process note for Chris:** the target installs from `$TOP` (current worktree) ⇒ the shared `luana-platform/.git/hooks/` now points to the **vitalia hub** (current content; main lags un-merged W1-W4). Robust long-term answer = merge harness work to main + canonicalize the hook source. Solo-operator + vitalia is a stable canonical hub ⇒ low blast radius; running gate is now current (strictly better than the entry stale-copy). |
| `contract-guard.js` relative-path heuristic edge (latent) | **DEFERRED → W6** — it lives in `.claude/hooks/` (W4 surface, not scripts/cockpit) + is **latent only** (CC passes absolute `file_path` + `CLAUDE_PROJECT_DIR`, so the heuristic branch never fires live — W4-verified). Defensive-hardening, not a live bug. Scope-disciplined defer. |
| `scripts/git/*` gate-scripts | **DONE** — classified (Batch C): `dod-evidence-gate`/`multi-session-scope-guard`/`session-lock`/`commit-paths`/`cleanup-wip-branches`/`ps1-luana` = the ~6 proxy-clean `core`; rest hybrid. W4's `dod-evidence-gate` `demo_signoff→chris_verify` fix verified still in place. No new edits needed (v5-clean). |

---

## 6 · Findings deferred / for downstream WS (honest scope)

- **W5 seam:** the recurring hardcoded **brand enum** (#1 target) + `.venv`/toolchain + ports/dev-app URLs + `engine_prefix` + `agent_roster` (`agent-meta.ts`, `generate_capability_index.VITALIA_AGENTS`, `map_zones.SPECIALIST_AGENTS`) + `value_stream` (`map-zones.ts`) → seam slots. Lifts most `hybrid`→`core`. Plus: ci-parity marker-scheme reconciliation (§2 #4); `validate_session_close` CAPS → `brands[]`-aware + S5 module-scope decision.
- **W6 (docs/templates):** document G8/G9 in `cap-deterministic-enforcement.md` (Batch A §3.5) + verify/extend machinery CHECK 11 to assert G8/G9 (§2 #5); modernize `generate_capability_index` to emit `scenarios` not `atomics` (Batch A §3.2); `contract-guard.js` relative-path hardening; render the v5 gate badges in the cockpit (§3a); optional PostToolUse `additionalContext` migration (W4 §3).
- **W7 physical move:** the ~6 core coordination scripts + the cockpit fs/lifecycle read-primitives → `core-harness/`; the cockpit RENDER + ops shells (docker/cockpit/ci-parity/dev-app/cloudflared/litellm/e2e/release) → `project-profile/`; `build_live_reconciliation_matrix.py` + `migrate_to_release_schema.py` + the 2 migrate JSON → `project-profile/`/`brands/vitalia/`; `extract_baseline_metrics` stale `…-home-chris-AISALESHT` transcript dir → repoint when the transcript path becomes a seam.
- **W9 legacy delete:** the 3 dead scripts in `legacy/2026-06-09/` — delete after W8 extraction test. Also the tracked `scripts/migrate-*-report-2026-05-27.json` (audit history; keep till W9).
- **Fail-OPEN silent-degrade (W4 §2 echo):** `ci-parity.sh`'s silent swallow of the (now deferred-aware) mirror-validator is the same "HARD gate degrades to no-op" pattern; the deferred-CI status masks it today — revisit at CI reactivation.

---

## 7 · Learnings (charter §5 step 7 → feed §7)

1. **The runtime can already carry data the type-contract hides — the read-schema fix was type-only.** The cockpit `Story` interface was missing every v5 spine field, yet `app/api/stories/route.ts` spreads `...(fm as Story)` so the data *already flows* to consumers — the gap was purely the TS declaration. *Lesson: before "wiring up" a missing read-schema field, check whether the producer already passes it through generically (a spread / `**kwargs` / passthrough); the fix may be a pure contract-declaration, not a parser change. The extraction contract (what a new product must EMIT) is the type shape, not the plumbing.*
2. **A "gate" can be dead by drift while looking alive — and a dead gate masked by an advisory caller is worse than no gate.** `validate_ci_parity_mirror.py` returned `exit 2` on every run (its workflow target was renamed away) but its caller swallowed it as advisory; the Stop hook's freshness sub-check was a guaranteed no-op (wrong venv). Both *appeared* to enforce. *Lesson: for every gate, verify it can actually reach its assertion (the target exists, the venv runs) — not just that it's wired. A gate that can't reach its check should fail LOUD/advisory, never silent-pass. (Generalizes W4's two-level consumer check to a "can-it-even-run" third level.)*
3. **"Conform a stale gate" ≠ "rewrite its semantics" — fix what's unambiguously broken, FLAG the genuine process decision.** The Stop hook had clearly-wrong parts (venv no-op, single-brand tree, dead vocab — all fixed) AND a real semantics question (coarse v4 global caps vs canonical v5 module-scoped). I fixed the former and flagged the latter to Chris rather than unilaterally duplicating the canonical pre-commit gate. *Lesson: a B-phase surface session repairs drift; it does NOT relitigate a process-semantics choice the PROCESS-MODEL leaves open — that's a Chris ratification (HLP governance), surfaced as a flag.*
4. **`tier:core` for scripts is as rare as everywhere (rules 18 → skills 0 → agents 1 → hooks 5 → scripts ~6) and earns it only for pure coordination/protection/read mechanisms.** Every script that shells a stack tool or loops the brand enum is `hybrid`/`project`. The portable core across the whole harness is the *skeleton* (orchestration / fail-open+ACK / git-main-protection / session-lock / filesystem-as-DB read primitives / the cockpit read-schema SHAPE), never the runner. *Cohesion lesson: the cockpit cleanly splits read-schema(contract)=portable vs render(executor)=project — the single clearest core/project seam in the whole harness, exactly as PROCESS-MODEL §7 predicted.*
5. **"Purged" stays scope-qualified, three workstreams running (W4 → W4b).** `outcomes/` is dead at BRAND-docs level but alive at PLATFORM (`generate_backlog.read_outcomes` + `render_friendly_status` + `generate_portfolio:403`). I fixed only the brand-surface row (`generate_portfolio:327/340`) and left every platform-outcomes read intact. *Lesson reconfirmed: read the consumer's scope before ripping a token; the ratification headline's scope ≠ the token's blast radius.*

---

## 8 · Pointers

- `RESEARCH-batch-{A,B,C}.md` (siblings) — full per-script tables (purpose/consumer/tier/proxy/paper-rules/stale/conformance/orphan) + per-finding prose w/ file:line + `validate_machinery_consistency.py` body-string dependency map (C §5). **Pointer-first: not duplicated above.**
- `docs/process/harness-refactor-charter-2026-06-08.md` §0.5 (option-b proxy) · §3 (seam slots) · §4 (fitness) · §6 (roadmap · W4b done-when) · §7 (B-phase recurring learnings).
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md` §1 (10-state+{G,R,C,D}) · §5 (one-SSoT, outcomes-purge-scope, demo_signoff→chris_verify) · §6 (conformance) · §7 (cockpit read-schema=core/render=project — D6①).
- `docs/process/harness-refactor-w4/W4-OUTPUT.md` §5/§6 — the handoffs W4b closed (Stop-hook, install-drift, git gate-scripts, contract-guard edge).
- `docs/learnings/tooling/2026-06-08-harness-refactor-stub-against-the-gate.md` — validate-after-apply + verify-the-consumer (applied verbatim).
- **Next:** B-phase TERMINA con W4b. Lo que sigue es ESTRUCTURAL (charter §6 C→E): **W6 (templates) → W5 (seam) → W7 (physical move) → W8 (extraction test) → W9 (legacy delete) → W10 (governance)** — cada uno Chris-ratificado, conversación NUEVA anclada al charter (HLP governance · NUNCA auto-run). Tail B-phase abierto: W1-Phase2 (Tier-3 eviction, `wip/protocol-rules-refactor`) + Tier-2 `paths:` (gate-blocked, #16299).

*End W4b-OUTPUT.md — the W4b deliverable + B-phase close. machinery-check 73/0/0 · pointer NEW 0 · cockpit tsc 0 + vitest 140/140 · ~57 scripts + cockpit tagged · 4 paper-rules fixed + 1 deferred · 5 stale fixed (1 read-schema, 4 scripts) · 3 dead→legacy · 2 W4 handoffs closed · all path-stable + grep-gated.*
