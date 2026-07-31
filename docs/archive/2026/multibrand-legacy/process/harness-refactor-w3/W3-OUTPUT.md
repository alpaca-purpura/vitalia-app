# W3 · Agents — Output (tier manifest + anti-telephone contract verification + rehoming decision + applied deltas + learnings)

**Date:** 2026-06-09 · **Session:** harness-refactor W3 (B-phase) · **Owner:** harness-dedicated, Opus · **Branch:** `wip/vitalia` (precedent: W0/W0.5/W0.5-bis/W1/W2 HEAD here) · **Status:** APPLIED + cemented (path-stable).

> **North-star card:** *This session succeeds only if (1) it implements its work-type per `PROCESS-MODEL.md`, AND (2) every file it tags `core` names ZERO tech/brand tokens (the rest went to the seam). The goal is an extractable `core-harness/`, not a nicer luana harness. Measured by the dependency-grep (§4) — the cheap W8.*
>
> Charter §6 W3 done-when: *11 agents tagged + anti-telephone contract verified + split genérico-vs-stack + machinery 73/0/0.* Inputs: `PROCESS-MODEL.md §2,§3,§5,§6` (spine + WT profiles + conformance checklist) + `CLAUDE.md § Anti-telephone-game` (the contract) + W1/W2 precedent (option-b proxy, validate-after-apply).

---

## 0 · Scope + headline result

Scope = `.claude/agents/` — **12 real files** (the charter's 11 + `grep-bot.md`, surfaced by `ls`; the real list manda). All work this session is **PATH-STABLE** (in-place stale-ref fixes + v5 conformance delta + WT3 bar addition); zero file moves, zero enforcement-machinery risk. The `architect-{be,fe,agentic}` instruction-doc rehoming (W2's deferred item) = **decided B (defer to W7)**, evidence §3.

**Validated after every apply** (W1 non-negotiable): `make machinery-check` = **73 checks · 0 fallos · 0 advisory** · `scan_harness_pointers.py` = **NEW 0**, at every checkpoint. Anti-telephone contract = **12/12 present, intact post-edit**.

**Headline:** the surface was already in good contract/model shape (12/12 anti-telephone, model-routing fully conformant). Three real W0.5-conformance deltas fixed: (1) **`02-design-ui.md` DEAD** but cited as a live build/audit input in 7 places → repointed to `01-spec § Wireframes` + `mockups/`; (2) **auditor-agentic frozen at self-fix v4.2** while auditor-backend/frontend already carry v5 Auditor-Responsable → brought to v5 parity **with the agentic caveat** (Carril R mechanical-only; behavior → Carril C); (3) **no-fake-`if`s bar (WT3)** absent from builder-agentic + auditor-agentic → added. Zero `core`-false-positives: 11 hybrid + **1 core** (grep-bot, the only genuinely-portable agent).

---

## 1 · Tier manifest — `tier: core | project | brand | hybrid` per agent (drives W7)

**Key insight (option-b proxy, charter §0.5):** agents are **PROJECT instances of generic worker roles**. Every spine agent names brands, toolchain, dev-app, Clerk, LangGraph, `core/luana-core-*`, trace-tables on nearly every screen → per option-b a token-carrying file is **`hybrid`, never proxy-clean `core`**. The genuinely-portable IP = the *role contract* (anti-telephone return shape · gate-output.json consumer pattern · self-fix carril doctrine · pre-flight-reader pattern), which the W7 generic skeleton extracts; the luana agent body is the project instance written against it. This mirrors W2's finding for skills.

**The one exception:** `grep-bot` — a one-shot lookup worker with no luana coupling. Its 2 proxy hits are generic build-artifact skip-dirs (`.venv`/`.next` in an exclusion list any project has), not project smear → tagged **`core`** (a new product inherits it unchanged).

### Tier table

| Agent | model | tier | core half (portable role) | project/brand half → seam slot |
|---|---|---|---|---|
| `architect-orchestrator` | opus | **hybrid** | full-stack ready-package role · CONN/anti-orphan · WT5 contract-spec | FastAPI/SQLA/FSD/LangGraph · `engine_prefix` · brands · canon (`design_system_ref`) · toolchain |
| `builder-backend` | sonnet | **hybrid** | DDD-inside-out builder role · TDD · anti-telephone · defers verdict | FastAPI/SQLA/alembic (`toolchain`) · brands · `engine_prefix` |
| `builder-frontend` | sonnet | **hybrid** | build-from-design role · live-verify gate · CONN | Next/React/Shadcn/Tailwind/Clerk/FSD · brands · `design_system_ref` · dev-app (`live_verify_infra`) |
| `builder-agentic` | opus | **hybrid** | agentic-builder role · engine-boundary discipline · newest-Opus (R23/D3) · no-fake-`if`s | LangGraph/deepagents/Qdrant/Anthropic-cache · trace-tables · EP catalog · brands |
| `auditor-backend` | opus | **hybrid** | review role · self-fix v5 (Carril R) · gate-output consumer · reconciled/live-verify | toolchain gates · brands · `engine_prefix` · domain sub-auditors |
| `auditor-frontend` | opus | **hybrid** | review role · self-fix v5 (Carril R) · gate-output consumer | tsc/eslint/vitest · FSD · canon · brands |
| `auditor-agentic` | opus | **hybrid** | review role · self-fix v5 **§ Caveat AGENTIC** · engine-boundary · no-fake-`if`s | LangGraph/Qdrant/trace/goldens · `domain_modules[]` · brands |
| `gate-runner` | haiku | **hybrid** | deterministic gate-runner · **gate-output.json contract** · "no overall verdict" rule | brand test shortcuts (`test-{brand}`) · toolchain · `code-health.sh` |
| `context-builder` | haiku | **hybrid** | pre-flight reader · CONTEXT-BRIEF schema · anti-telephone · spawns validator | brand-scan paths · `engine_prefix` · story-folder layout · framework-docs map |
| `context-validator` | haiku | **hybrid** | adversarial validator role · duplicate-scan + spot-check mechanism | brand enum · `engine_prefix` · domain synonym maps (clerk/qdrant/alembic) |
| `grep-bot` | haiku | **core** | one-shot lookup worker · inline-result anti-telephone variant · auto-escalate | — (2 hits = generic build-artifact skip-dirs, not luana smear) |

**Counts:** **core 1** (grep-bot, proxy-clean) · **hybrid 11** (spine/worker agents, project-half parked → seam W5/W7) · project 0 · brand 0. Matches the predicted shape (nearly all hybrid; zero false-core). The `brand` tier is empty for agents — same as rules (W1): brand specifics are config, never an agent (OCP).

### Model-routing conformance (PROCESS-MODEL §5 D3 + cost-routing) — all ✓

`architect-orchestrator` + 3 auditors + `builder-agentic` = **opus** (agentic/strategic + newest-Opus D3 + R23) · `builder-backend`/`builder-frontend` = **sonnet** (non-agentic BE/FE) · `gate-runner`/`context-builder`/`context-validator`/`grep-bot` = **haiku** (cheap readers/workers). **No hardcoded model id** (`claude-opus-4-8`) anywhere — the `model: opus` frontmatter is the seam-clean form (PROJECT slot = "Opus 4.8 today").

---

## 2 · Anti-telephone contract verification (deliverable b)

CLAUDE.md § Anti-telephone-game: *every subagent MUST return ONE final line `<verdict> -> <path-to-artifact>`; NEVER inline >500 tokens of artifact body.*

| Agent | contract block | verdict | note |
|---|---|---|---|
| architect-orchestrator | `## Return format (anti-telephone-game)` L12 + `<verdict> -> <path>` + `NEVER inline >500 tokens` | ✅ | standard |
| builder-{backend,frontend,agentic} | idem | ✅ | standard |
| auditor-{backend,frontend,agentic} | idem | ✅ | standard |
| gate-runner | idem + `Caller reads gate-output.json on demand` | ✅ | standard (artifact = gate-output.json) |
| context-builder | idem + R24/R28 post-condition proof (paste literal bash) | ✅ | strongest enforcement |
| context-validator | idem | ✅ | standard |
| grep-bot | `<verdict> -> <short-result>` + `Keep result < 200 tokens` + paginate/escalate >10 | ✅ | **inline-result variant** — correct for a lookup worker (no artifact path; small result returned inline under a hard token cap). Conformant in spirit (one final line + token ceiling). |

**Result: 12/12 conformant, intact after all edits.** No agent inline-dumps artifact bodies. No edit was needed to the contract itself; verified present + correct.

---

## 3 · Rehoming decision — `architect-{be,fe,agentic}`: **B (defer physical move to W7)** (deliverable c)

W2 deferred this to W3. **Decision: B — leave path-stable + tagged `hybrid`, move at W7 behind a dependency-grep gate.** Evidence (the anti-false-positive grep, verify-the-consumer-side per the W1 learning):

1. **They are `disable-model-invocation: true` instruction-docs (skills, not agents).** Frontmatter of all three: *"NO es agent type spawnable … `architect-orchestrator` lo LEE por path."* The `/architect-be` slash forms scattered in prose are **not live invocations** (disable-model-invocation), just documentation.
2. **No live by-path `Read` consumer exists.** `grep 'architect-(be|fe|agentic)/SKILL.md|skills/architect-(be|fe|agentic)' .claude/ scripts/` over executable consumers = **only prose** (`/architect` SKILL.md L109-111 describes "carga contextualmente"; `architect-orchestrator.md` doesn't even name them). The coupling is documented, not wired.
3. **The move sprawls outside W3 scope.** It touches: `.claude/skills/architect-{be,fe,agentic}/` (W2, done) → `architect/references/`; `scripts/validate_machinery_consistency.py` L54-55 (`PREMULTIBRAND_SCAN_FILES`) + L193-195 (`MACHINERY_SKILL_DIRS`); `scripts/machinery/harness-pointer-baseline.txt` L13-14; templates `03-arch-template.md` / `02-design-ui-template.md` / `02-design-agentic-template.md` (**W6**). **None of these is `.claude/agents/`** (the W3 scope). Moving them is a multi-WS coordinated change — textbook W7.
4. **The mis-housing is cosmetic; the real bug is separate + already guarded.** The substantive defect (architect-be/agentic grep dead `backend/src/shared` / `backend/src/core/` paths, per the 2026-05-28 agentic-machinery-audit) is exactly what `PREMULTIBRAND_SCAN_FILES` (validator L52-55) exists to catch — already machinery-asserted. Re-homing the file doesn't fix that; it's orthogonal.

**Net:** W7 owns the physical move (it's the Core/Project/Brand reorg workstream). At W7, repoint [validator L54-55,193-195 + baseline L13-14 + the 3 templates] **behind a dependency-grep gate**, validate-after each repoint. Left this session: path-stable, `hybrid` (per W2 tag).

---

## 4 · Applied changes (path-stable, this session)

### Delta 1 · `02-design-ui.md` DEAD → `01-spec § Wireframes` + `mockups/` (D-X2 conformance)

`02-design-ui.md` is **DEAD** (PROCESS-MODEL §3 WT1 + §8 diff: "live (8 refs) → DEAD; canon + spec-wireframes"). It was still cited as a **live build/audit input** in 7 places, telling builders/auditors to read a retired artifact. Confirmed **NOT machinery-asserted** (`grep 02-design-ui scripts/ Makefile` = empty). Repointed:
- `context-builder.md:169` — input-read list → keep `02-design-agentic.md` (alive, agentic-only); note `02-design-ui.md` retired.
- `builder-frontend.md` — desc L3 · role L33 · input-read L69 · technical_design L196 (4 refs) → `01-spec § Wireframes` + `mockups/`.
- `auditor-frontend.md` — input-read L68 · mockup-adherence checklist L437 (2 refs) → idem.

Remaining 3 `02-design-ui` strings in agents are **deliberate "RETIRED" tombstone notes** (tell the reader it's dead), not stale directives.

### Delta 2 · auditor-agentic self-fix v4.2 → v5 Auditor-Responsable (with AGENTIC caveat) — the W2-pattern contradiction

auditor-backend/frontend already carried the **v5 Auditor-Responsable** section (Carril R fix-and-own); **auditor-agentic was frozen at v4.2** (description + L33 + rule #1, zero v5/reconciled/Carril-R) — the SSoT (`auditor-self-fix-policy.md`) moved to v5, the implementer didn't propagate (W2 learning #2). Brought to v5 parity **with the rule's `§ Caveat AGENTIC`**: for agentic surfaces Carril R is **mechanical-only** (non-deterministic eval gates → a self-fix would overfit the golden); any **behavior** finding (prompt slots/goldens/state-machine/tool-logic/voice) is stake-asymmetric → **Carril C** (CHANGES_REQUESTED → builder-agentic), engine/security → escalate Chris. Added: a new `## Auditor Responsable v5 (cement 2026-06-03 · AGENTIC caveat)` section (parallel placement to BE/FE, after `</verdict_math>`) + the **auto-hardening reflex** (`## Upstream deficiency` finding + auto-HB capture, same as BE/FE v5) + version-label fixes in description/L33/rule#1. `grep v4.2 auditor-agentic.md` = **0** after.

### Delta 3 · no-fake-`if`s bar (WT3) → builder-agentic + auditor-agentic

PROCESS-MODEL §3 WT3: agentic quality bar = **no fake `if`s** — "inherited by architect/auditor". Was absent from both agentic agents (grep = 0). Added, additive, **without disturbing verdict_math structure**:
- `builder-agentic` `<forbidden>`: hardcoded keyword branches (`if "precio" in msg`) faking reasoning instead of tool/LLM routing + state-machine edges.
- `auditor-agentic` Cat 2 (Tool registration & contracts): a bar bullet + a FAIL condition for keyword-`if` faking where a tool/LLM/state edge belongs.

---

## 5 · Conformance verified (lens-1) — no edit needed

- **builder-agentic** strongly conformant: engine `core/luana-core-{copilot,sales-agent}/` OFF-LIMITS + `/pm-luana` lift gate (L35-51), Opus by R23/D3 (L26), date-aware research (L58), DDD inside-out. ✓
- **gate-runner** conformant: produces `gate-output.json`, does NOT decide overall PR verdict (that's the auditor); auditors consume the JSON, never parse raw logs (59 `gate-output` hits across agents). ✓
- **context-builder/validator** conformant: Haiku cheap readers, no architecture reasoning, anti-telephone + R24/R28 enforcement, brand-scoped scans (no cross-brand pollution). ✓
- **auditor-backend/frontend** conformant: v5 Carril R sections present; live-verify in Carril R; gate-output preflight. ✓

---

## 6 · Findings deferred / for downstream WS (honest scope)

- **`architect-{be,fe,agentic}` physical move → W7** (decision §3; coordinated across W2-skills/W6-templates/validator/baseline, behind a dependency-grep gate).
- **auditor-agentic category-count drift (cosmetic, not W3-conformance).** The file says "14 categories" (role L35) / "15 categories" (output L398) but actually defines Cat 1-16. Pre-existing miscount, not a stale-SSoT contradiction → left for a content-cleanup pass (or the deeper agentic-machinery audit that owns category structure). Flagged, not fixed (scope discipline).
- **Seam wiring (`{slot}` rewrite) = W5.** Every hybrid agent's project-half (toolchain/brands/`engine_prefix`/dev-app/canon/trace-tables/EP) is parked, tagged, ready for the W5 `project.config.yaml` seam — not rewritten now (option-b).
- **The W7 generic-skeleton extraction** (the portable role contract per agent type) is the actual "core" deliverable for the agent layer — same story as skills (W2): a new product writes new agent instances against the same contracts.

---

## 7 · Learnings (charter §5 step 7 → feed back to §7)

1. **The agent layer was already in good contract shape — the deltas were stale-SSoT propagation, not contract holes.** 12/12 anti-telephone + fully-conformant model routing were already there. The real work was the same W2 failure mode: a ratified SSoT (DoD #37 killing `02-design-ui`; self-fix v5) moved, and the implementing agents didn't propagate. *Lesson reinforced: when a doctrine is ratified, grep the IMPLEMENTING agents for the OLD token — the SSoT doesn't propagate itself. `02-design-ui` (7 stale) + `v4.2` (auditor-agentic) were both "doc moved, agent stayed."*
2. **Sub-agent fan-out by self-fix CARRIL must respect the surface's gate determinism.** auditor-backend/frontend got "fix-and-own" (deterministic gates → a fix is verifiable by re-running the gate). auditor-agentic must NOT inherit that verbatim — its gates (eval goldens, pass^k) are non-deterministic, so "fix-and-own" degenerates into golden-overfitting. The v5 doctrine already encodes this (`§ Caveat AGENTIC`); the agent just hadn't absorbed it. *Lesson: a cross-cutting policy (v5) applied to a sibling set is NOT uniform — the agentic sibling needs the narrowing, and the narrowing is what keeps the policy honest.*
3. **`tier:core` for agents is even rarer than for rules/skills — exactly one (grep-bot).** Rules had 18 core; skills had 0; agents have 1. The pattern holds: the more an artifact is a *worker doing luana's specific job*, the more project-smeared it is. The portable IP is the *contract/role*, which lives one level up (the W7 generic skeleton / the process-docs), not in the worker body. *Cohesion lesson: the agent body is a project-bound executor of a core contract; extract the contract, rewrite the body per product.*
4. **A proxy hit isn't a smear if it's a generic build-artifact name.** grep-bot matched `.venv`/`.next` — but only as exclusion-dir defaults any project carries. The dependency-grep is a *signal*, not a verdict; reading the 2 lines in context (vs. counting them) is what earned grep-bot its `core` tag. *Lesson: run the proxy, but read the hits — generic tooling artifacts (`.venv`, `node_modules`, `.next`, `coverage`) are not project tokens.*
5. **Anti-telephone has a legitimate variant for non-artifact workers.** grep-bot returns its small result inline under a hard 200-token cap instead of writing a file + returning a path — and that's *correct* for a lookup worker (writing a file for "3 matches" would be silly). The contract's intent (one final line + don't dump the body) is honored two ways: artifact-path (writers) vs. capped-inline-result (lookups). *Lesson: the contract is the intent (bounded final line, no body-dump), not one literal shape.*

---

## 8 · Pointers

- `docs/process/harness-refactor-charter-2026-06-08.md` §0.5,§4 — north-star + fitness tests (option-b proxy).
- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md` §2 (spine gates) · §3 (WT profiles — WT3 no-fake-`if`s, WT5 self-fix) · §5 (D3 newest-Opus) · §6 (conformance checklist).
- `CLAUDE.md § Anti-telephone-game` — the contract verified §2.
- `.claude/rules/auditor-self-fix-policy.md` § Auditor Responsable v5 + § Caveat AGENTIC — the SSoT Delta 2 propagates.
- `docs/process/harness-refactor-w1/W1-OUTPUT.md` · `harness-refactor-w2/W2-OUTPUT.md` — B-phase precedent (option-b proxy, validate-after-apply, the propagation-grep pattern).
- `docs/learnings/tooling/2026-06-08-harness-refactor-stub-against-the-gate.md` — validate-after-apply + verify-the-consumer.
- **Next (B-phase parallel):** W4 (hooks + pre-commit) ‖ W4b (scripts + cockpit) → then W6 (templates — incl. the `architect-{be,fe,agentic}` rehoming at W7) → W5 (seam) → W7 (physical move).

*End W3-OUTPUT.md — the W3 deliverable. machinery-check 73/0/0 · pointer-scan NEW 0 · anti-telephone 12/12.*
