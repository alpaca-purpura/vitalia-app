# W1 · Phase 2 — Coordinated Tier-3 eviction (STAGED)

**Status: ✅ EXECUTED 2026-06-09 (W9/W10 closure session, on `wip/vitalia` — Chris delegated the program closure; the dedicated-worktree provision was superseded by the single-hub harness-dedicated session).** Result:

- **Groups A-D (12 domain rules → owning-skill references + 7-9-line pointer stubs, path-stable):** analytics-metrics · etl-extraction-contract · data-reliability (→ metrics-expert) | copilot-resilience · copilot-observability (→ copilot-expert; the §1 merge was SKIPPED — both references already exist split, merging = churn) | sales-agent-brand-voice (→ sales-agent-expert) | admin-panel · master-data · currency-handling (→ backend-expert; currency→master-data merge SKIPPED, same reason) | offer-catalogs (→ offer-expert) | form-runtime-array (→ brand-expert; ⚠️ pre-existing mirror with offer-expert copy flagged to harness-backlog) | e2e-testing (→ playwright-expert `references/e2e-rule-summary.md`, new file) | debugging (→ `docs/rules-detail/debugging.md`, new file) | brand-docs-schema (R1-R4 one-liners kept; detail already at `docs/rules-detail/`).
- **Group E (Tier-2 `paths:` per §3 verdict):** frontend-quality · frontend-fsd · backend-quality converted (dead `globs:` frontmatter replaced — empirically confirmed ignored: those rules loaded always-on WITH `globs:` present). **Live-verified on the real converted rule:** fresh-session `DEFAULT=NO` + `POSTREAD=YES` after reading `vitalia/frontend/src/lib/` file.
- **KEPT always-on (justified):** tenant-isolation · pii-sanitisation · backend-ddd · architectural-fitness · spanish-text (write-time safety, #23478) · frontend-visual-fidelity (canon binding HARD — gates po-ux who never reads `frontend/src`) · definition-of-done-live-verify (#37 hybrid) · backend-migrations (write-time new files — **candidate** for Tier-2 if migration-authoring always reads `alembic/versions` first; deferred conservative).
- **Budget:** always-on 1726 → **1310** lines (−24% total; project-side real files 836 → 420, −50%). The original ~450-550 target is **unreachable without slimming the 21-rule CORE corpus (890 lines)** — that is a separate decision (the plugin slim-manifest path: SessionStart injects only 3 hard rules ≤9.5k, the rest via `/harness:bootstrap`), NOT a Phase-2 scope. Recorded honestly.
- **Consumers:** contract-guard.js msgs cite rule PATHS only (stubs keep paths) → zero repoint. Pointer baseline drained 28→25 (shrink-only: e2e workflows ref + 2 architect-references `core/config.py` refs gone). machinery 65/0/0 + pointers NEW-0 after every group.

**Original plan below (historical):** · **Where:** dedicated `wip/protocol-rules-refactor` worktree (cross-cutting `.claude/**` + `docs/**` + `scripts/**`) with `SCOPE_GATE_SKIP=1`, per HLP guardrail + audit §5. **Never mid-feature.** **Owner:** harness session (Opus). Input: `harness-rules-audit-2026-06-08.md` §3/§5 + `W1-OUTPUT.md` tier manifest.

> Phase 1 (path-stable) is done + cemented on `wip/vitalia`. Phase 2 = the **non-path-stable** moves: relocate domain + phase rule **bodies** into their owning skill's `references/`, leaving a thin pointer (or deleting the rule when a skill + a hook already cover it). These touch enforcement machinery → each move is **dependency-grep-gated** and repoints its consumers in the SAME commit. Goal: lean always-on core ≈ 450–550 lines.

## 0 · Dependency gate matrix (verified by grep, 2026-06-08)

Before ANY move/delete, the consumer that greps the rule by path/slug MUST be repointed in the same commit:

| Rule (to evict) | Consumer to repoint (same commit) | Mechanism |
|---|---|---|
| offer-catalogs | `.claude/hooks/contract-guard.js` (slug string ×4) | advisory reminder path |
| analytics-metrics | `contract-guard.js` (slug ×2) | advisory |
| etl-extraction-contract | `contract-guard.js` (slug) **+ `harness-pointer-baseline.txt`** (`:: docs/etl/extraction-contract.md`) | advisory + anti-rot |
| copilot-resilience | `contract-guard.js` (slug) — **MERGE copilot-observability IN first** | advisory |
| auditor-downstream-regression | **DO NOT MOVE** — `scripts/git-hooks/checks/04-r3-ssot.sh` reads `SSoT_TABLE=.claude/rules/auditor-downstream-regression.md`; keep path-stable (already slim) | hard freshness gate |
| e2e-testing | `scripts/e2e-preflight.sh` (comment SSoT) + `harness-pointer-baseline.txt` (`:: .github/workflows/e2e-tests.yml`) | comment + anti-rot |
| step-0-worktree | **audit FP corrected:** no `@`-import in pm skills (grep = 0). Prose refs in `worktree-protocol`/`harnesses-improvement` skills — update pointers, no `@` repoint needed | prose only |
| backend-migrations | `harness-pointer-baseline.txt` (`:: docs/domains/migrations.md`) — stays if rule keeps the (dead) pointer | anti-rot |

**Rule:** after every move, run `python3 scripts/scan_harness_pointers.py` (NEW must = 0) + `make machinery-check` (0 fallos) + `node .claude/hooks/contract-guard.js`-touched-path smoke. Shrink `harness-pointer-baseline.txt` for any drained ref.

## 1 · Tier-3 DOMAIN evictions (→ owning skill `references/`)

Per file: (a) grep-gate consumers (§0), (b) `git mv` body to `references/<rule>.md` (or merge), (c) leave thin pointer rule OR delete if skill 1st-turn-loads it + `contract-guard.js` covers, (d) repoint consumers, (e) validate.

| rule | owning skill | move/merge | note |
|---|---|---|---|
| offer-catalogs | offer-expert / offer-type-preset-expert | body→references | skill loads it 1st-turn already |
| analytics-metrics | metrics-expert | body→references | contract-guard repoint |
| etl-extraction-contract | metrics-expert | body→references | cg + baseline repoint |
| copilot-observability | copilot-expert | **MERGE → copilot-resilience** first | one agentic-obs SSoT |
| copilot-resilience | copilot-expert | body→references (absorbs obs) | cg repoint |
| sales-agent-brand-voice | sales-agent-expert | body→references | ux-agentico loads it |
| data-reliability | metrics-expert | body→references | ⚠️ stale Makefile targets = separate story (don't fix here) |
| admin-panel | backend-expert | body→references | opt-in feature |
| master-data | backend-expert | body→references (**absorbs currency**) | merge currency in |
| currency-handling | backend-expert | **MERGE → master-data** | — |
| form-runtime-array | brand-expert / offer-expert | body→references | FE form convention |
| e2e-testing | playwright-expert (already SSoT) | body→references | preflight+baseline cite path |

## 2 · Tier-3 PHASE evictions (→ owning skill `references/`)

Most are already slim stubs whose bodies live in skill `references/`; finish the move + trim the always-on stub to a 1-line pointer where the skill is the true SSoT.

| rule | owning skill | risk |
|---|---|---|
| brand-docs-schema | pm-{brand} references | med (outcomes purge already applied Phase 1) |
| anti-default-flip-audit | dev-team/auditor refs | keep flag-inventory table reachable |
| anti-duplication-refining | pm/po/architect refs | low |
| test-design-doctrine | dev-team refs (body there) | low |
| architect-autonomous-mode | architect refs (body there) | low |
| git-haiku-delegation | commit-push refs (body there) | low |
| worktree-dual-strategy | worktree-protocol refs (body there) | low |
| pm-skill-chaining | pm skills (body replicated) | low |
| github-actions-deferred | keep always-on OR Tier-2 | low |
| step-0-worktree | pm/* references | **LAST** — repoint the 3 prose refs; verify no `@`-import re-introduced |

**KEEP always-on (do NOT evict):** the 22 core process rules in `W1-OUTPUT.md` §2 + the write-time-safety stack rules (tenant-isolation, pii-sanitisation, anti-duplication doctrine, backend-ddd, architectural-fitness) — these must fire at write-new-code time (#23478) and cannot be `paths:`-scoped nor skill-deferred.

## 3 · Tier-2 `paths:` — ✅ GATE RESOLVED (empirical test 2026-06-09 · W9/W10 session)

**★ VERDICT: `paths:` WORKS as conditional-load in this CC version — #16299 does NOT manifest. Tier-2 is UNBLOCKED.**

Empirical method (headless `claude -p` fresh sessions = real session-start rule loading; A/B controlled):
1. **Negative half:** throwaway rule with `paths: [vitalia/frontend/src/never-touched-canary-dir/**]` + canary string → fresh session probe (Sonnet, quoted-evidence forensic) = `CANARY=NO` while always-on control (`# TDD Obligatorio`) = `YES`.
2. **Untracked confound ruled out:** second throwaway WITHOUT `paths:` (equally untracked) → `NOPATHS=YES` (loaded + quoted verbatim) while canary stayed `NO` → the no-load is attributable to `paths:`, not git-tracking.
3. **Positive half:** fresh session instructed to `Read` a file matching the glob → `POSTREAD-CANARY=YES` (rule injected after the read) → conditional-load is real, not a black hole.

**Standing caveat (#23478 wontfix, unchanged):** trigger = READ of a matching file, NOT write/creation of a new file → only convention-only rules whose value arrives when *reading existing code* qualify; write-time-safety rules stay always-on.

If the test passes, candidates (convention-only, read-trigger acceptable, NOT write-time-safety): `frontend-quality`, `frontend-fsd`, `frontend-visual-fidelity`, `backend-quality`, `backend-migrations`, `debugging`, `offer-catalogs` (if not skill-evicted). `backend-ddd`/`architectural-fitness` matter at write-new-code → keep always-on or skill-ref instead.

## 4 · Validation gate (per move + at end)

```bash
WS=$(git rev-parse --show-toplevel); cd "$WS"
python3 scripts/scan_harness_pointers.py            # NEW must = 0
make machinery-check                                 # 0 fallos
wc -l .claude/rules/*.md | tail -1                   # budget → ~450-550
# contract-guard smoke: edit a touched domain path, confirm reminder still resolves
```

## 5 · Done-when (Phase 2)

- always-on core ≈ 450–550 lines · all domain/phase bodies in skill `references/` · `contract-guard.js` + `harness-pointer-baseline.txt` repointed · `04-r3-ssot.sh` still green (auditor-downstream path-stable) · machinery-check 0 fallos · pointer-scan NEW 0 · merges done (copilot-obs→resilience, currency→master-data) · superseded whole-files (if any rule deleted) → `legacy/2026-06-08/`.
