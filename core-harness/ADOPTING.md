# ADOPTING.md — install this dev-process kit in a NEW product (any stack, single- or multi-sistema)

> **Audience:** a team (or a solo operator) starting a NEW product on a DIFFERENT tech stack, who wants the full agentic dev-process — lifecycle, gates, roles, doctrine, safety — without re-inventing it. **You never edit a file inside `core-harness/`.** Everything product-specific goes into ONE file: `project.config.yaml` (the seam), plus your own project-layer rules/skills as you grow. This procedure was proven end-to-end with a fictional adopter (`ledgerline`: a Go 1.23 / SQLite, single-tenant, en-US bookkeeping CLI+API — deliberately unlike the source product on every axis); the source repo keeps that run's record as its W8 extraction-test output.

---

## 0 · What you get

```
                 ┌──────────────────────────────────────────────┐
                 │            core-harness/  (THE KIT)           │
                 │  rules/      21 always-on process invariants  │
                 │  process/    6 doctrine docs (lifecycle, CIL) │
                 │  templates/  5 spec/story skeletons           │
                 │  scripts/    seam loader + 6 git-coordination │
                 │  hooks/      pre-commit checks + SessionStart │
                 │  agents/     generic workers (grep-bot)       │
                 │  skills/     /harness:bootstrap               │
                 │  .claude-plugin/  plugin distribution shape   │
                 └───────────────────┬──────────────────────────┘
                                     │ reads (never the reverse)
                 ┌───────────────────▼──────────────────────────┐
                 │  project.config.yaml  (THE SEAM — you fill)   │
                 └───────────────────┬──────────────────────────┘
                                     │ declares
                 ┌───────────────────▼──────────────────────────┐
                 │  YOUR PRODUCT  (any language, any framework)  │
                 └──────────────────────────────────────────────┘
```

The kit encodes HOW software gets built with agents: the `idea→done` lifecycle (10 macro states + the human-verify and reconcile phases), TDD doctrine, story-closure and anti-duplication gates, git/parallel-session safety, learning capture, the auditor's responsibility model, and the worker-role contracts. It names **zero** technologies and **zero** sistemas — every concrete fact (your linter, your test runner, your market names, your live-verify URL) is read from the seam at runtime.

## 1 · Step-by-step

### Step 1 — drop the kit

```bash
# in your fresh repo (git init done)
cp -r /path/to/core-harness ./core-harness
```

The kit is self-contained (no inward symlinks): a plain `cp -r` is a complete install. If you consume it as a Claude Code plugin instead, add the marketplace: `/plugin marketplace add ./core-harness`.

### Step 2 — create the empty seam + run the doctor

```bash
python3 core-harness/scripts/harness_config.py --doctor
```

If `project.config.yaml` does not exist (or has `__FILL_ME__` slots), the doctor **self-declares what is missing** and exits 3:

```
harness-doctor · project.config.yaml · product=__FILL_ME__
  ✗ 11 slot(s) UNFILLED (__FILL_ME__) — declare these:
      meta.product · sistemas · toolchain · locale · engine_prefix · live_verify_infra
      · design_system_ref · domain_modules · agent_roster · value_stream · wip_caps
EXIT=3
```

This is the contract: **the core tells you what it needs; you never tell the core anything by editing it.**

### Step 3 — fill the slots (worked example: `ledgerline`, Go / single-sistema / en-US)

| Slot | What it declares | `ledgerline` example value |
|---|---|---|
| `meta.product` | product name + 1-line description | `ledgerline` — double-entry bookkeeping CLI+API |
| `sistemas` | your market instances. **Single-sistema = a list with ONE entry** — nothing else changes | `active: [{slug: main}]` · `loop_order: [main]` |
| `toolchain` | lint / format / typecheck / test / migrate commands per stack | the exact commands YOUR repo's own build files declare, quoted verbatim into `lint:` · `format:` · `test:` · `audit:` |
| `locale` | the user-facing language rule the copy gates enforce | `identifier: en-US` (no dialect gate needed) |
| `engine_prefix` | where your SHARED/reusable code lives (the anti-duplication grep target) | `go_module_prefix: github.com/acme/ledgerline/internal/` |
| `live_verify_infra` | how a story is exercised LIVE before `done` (URL/binary, test creds, evidence sources) | local binary smoke + `LEDGERLINE_API_TOKEN` |
| `design_system_ref` | your UI-composition canon (or N/A for non-UI products) | `none` (CLI/API — no web UI) |
| `domain_modules` | the business modules your process talks about | `ledger, accounts, reports, importers` |
| `agent_roster` | the worker roles (builder/auditor split) your stories route to | builder-backend + auditor-backend (no FE roles) |
| `value_stream` | the stages your product map derives zones from | capture → categorize → reconcile → report |
| `wip_caps` | the work-in-progress limits the closure gates enforce | defaults (e.g. `developed_max: 1`) |

Re-run the doctor until:

```
harness-doctor · project.config.yaml · product=ledgerline
  ✓ all slots filled — ready (idea→done runs without editing the CORE)
EXIT=0
```

### Step 4 — re-expose the kit to Claude Code: `/harness:bootstrap`

Run the bootstrap skill (shipped in `core-harness/skills/harness-bootstrap/`). It wires each surface through its **documented-safe channel** (the "Option-C" mechanism — see `README.md`):

| Surface | Mechanism | Note |
|---|---|---|
| rules | `ln -s core-harness/rules/*.md .claude/rules/` | symlinks are documented-safe for the rules dir; verified to auto-load in a fresh session |
| agents | **copy** into `.claude/agents/` | agent symlinks are undocumented upstream — copy |
| skills | plugin-namespaced, or copy into `.claude/skills/` | |
| hooks | `settings.json` / plugin `hooks.json` point AT `core-harness/hooks/*` | path-referenced, no copy needed |
| templates / process / scripts | symlink-back at the conventional path | read-by-path; the OS resolves |

After bootstrap, open a **fresh session** and confirm the rule bodies appear in the loaded context (the source repo calls this the restart-smoke; it passes by design, but verify once).

### Step 5 — run the cycle

Take your first idea through the lifecycle: refine it into a spec (the `templates/01-spec-template.md` skeleton — functional map + scenario matrix + signatures), architect it, build it test-first, audit it, exercise it LIVE per `live_verify_infra`, merge. Every gate the kit ships (story-closure, TDD, anti-duplication grep-before-write, definition-of-done evidence) reads YOUR values from the seam.

## 2 · What you must NEVER do

- **Never edit a file under `core-harness/`** to make it fit your product. If a core file seems to need your product's name in it, that is a seam gap — add/extend a slot VALUE, or (if you really found a missing slot) open an issue against the kit. The source repo enforces this with a proxy-clean gate (a dependency-grep over the kit = 0 product tokens, run on every commit).
- **Never fork the kit per sistema/market.** A new market instance = one more entry in `sistemas.active`. The whole multisistema machinery degrades gracefully to single-sistema with a 1-entry list.
- **Never bypass the gates** (`--no-verify`, skipping the doctor, declaring "done" on a green test suite without live exercise). The kit's value IS the gates.

## 3 · How you extend (without touching the core)

- **Project-layer rules/skills:** your stack conventions (your framework's patterns, your module boundaries) live in YOUR `.claude/rules/` + `.claude/skills/` as project files, NEXT TO the symlinked core ones. The core never references them; they may reference the core.
- **Domain skills:** one expert skill per business module (`domain_modules`) with a `references/` dir for on-demand depth — keep always-on context lean (the kit's slim-pointer pattern).
- **More sistemas:** append to `sistemas.active` + bootstrap their config. Zero core edits (that is the kit's open-closed rule).
- **Kit upgrades:** pull a newer `core-harness/` (or plugin update). Because you never edited it, the upgrade is a clean replace; your seam + project layer are untouched.

## 4 · Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| doctor exit 3 forever | a slot still `__FILL_ME__` (nested facets count) | the doctor names the exact slot — fill it |
| rules not loading in a fresh session | bootstrap didn't symlink into `.claude/rules/`, or you symlinked a DIRECTORY (link files individually) | re-run `/harness:bootstrap`; verify `ls -l .claude/rules/` |
| seam read returns empty in shell scripts | loader degrades EMPTY + loud warn when python/yaml unavailable — by design, no silent hardcoded fallback | install python3 + pyyaml in the environment running the gates |
| a core gate names a path you don't have | you skipped a slot the gate reads (e.g. `wip_caps`) | doctor again; fill it |

## 5 · Pointers

- `core-harness/README.md` — kit structure, the re-expose mechanism, distribution (plugin/marketplace).
- `core-harness/skills/harness-bootstrap/SKILL.md` — the bootstrap procedure this guide wraps.
- `core-harness/scripts/harness_config.py` — the seam loader + doctor (`--doctor`, `<slot>` reads, `--where` facet filters).
- `core-harness/process/` — the lifecycle + continuous-improvement doctrine your team operates by.
