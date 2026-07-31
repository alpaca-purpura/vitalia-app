# W8 · Extraction test — Output (the program DoD, made measurable + PASSING)

**Date:** 2026-06-09 · **Session:** harness-refactor **W8** (D-phase · the extraction test) · run inline after W7-execution · **Owner:** harness-dedicated, Opus · **Status:** ✅ **PASSING.** The program DoD (charter §8) is demonstrated: drop `core-harness/` + an empty `project.config.yaml` into a fresh repo → `--doctor` self-declares the missing slots → fill with a *different* product → the cycle resolves **without editing the CORE**.

> Charter §8 DoD (verbatim): *"Take `core-harness/` + an empty `project.config.yaml`, drop into a fresh repo, run `/harness-doctor` → it lists the missing slots → fill them with a different product's info (vision, tech, design) → the `idea→done` cycle runs without editing the CORE."*

---

## 1 · Setup (the fresh-repo drop)

```
/tmp/harness-extract-test/         # git init -q (clean, OUTSIDE the luana workspace)
└── core-harness/                  # cp -r — 50 self-contained REAL files, 0 inner symlinks
```

`core-harness/` is **self-contained**: the 50 files (21 rules · 6 process-docs · 5 templates · 6 git-scripts + `harness_config.py` · 3 checks + 2 plugin hooks + manifest · 1 agent · 1 bootstrap skill · README · 2 plugin manifests) are all REAL files — the symlinks live at luana's `.claude/`/`docs/`/`scripts/` and point INTO the kit, never the reverse → `cp -r` yields a complete, portable kit.

## 2 · The fictional product — `ledgerline` (deliberately ≠ luana)

A single-tenant double-entry bookkeeping **CLI+API**, chosen to break every luana assumption:

| Axis | luana | ledgerline (the adopter) |
|---|---|---|
| Language | Python 3.12 (FastAPI) | **Go 1.23** |
| Toolchain | ruff / pytest / mypy / alembic | **go vet / gofmt / go test / govulncheck** |
| Brands | 4 active + 6 pending (multibrand) | **single product (`brands.active: [main]`)** |
| Locale | es-LATAM-neutro (voseo gate) | **en-US** |
| Engine | `core/luana-core-*` (27 pkgs) | `github.com/acme/ledgerline/internal/` (4 pkgs) |
| UI / design-system | Next/Tailwind/`@luana/ui-kit` | **N/A — CLI/API, no web UI** |
| Live-verify | cloudflared dev-app + Clerk | local binary smoke + `LEDGERLINE_API_TOKEN` |

## 3 · The run (4 stages, all green)

**Stage 1 — gap detection (empty config):** `project.config.yaml` with 10 top-level slots = `__FILL_ME__` →
```
$ python3 core-harness/scripts/harness_config.py --doctor
harness-doctor · project.config.yaml · product=__FILL_ME__
  ✗ 11 slot(s) UNFILLED (__FILL_ME__) — declare these:
      meta.product · brands · toolchain · locale · engine_prefix · live_verify_infra
      · design_system_ref · domain_modules · agent_roster · value_stream · wip_caps
EXIT=3
```
The loader — running from the **copied kit** in `/tmp` with zero luana present — parent-walked (`__file__.resolve()`) to the temp's config and **self-declared every missing slot**. This IS "detect what's missing."

**Stage 2 — fill with ledgerline → ready:**
```
$ python3 core-harness/scripts/harness_config.py --doctor
harness-doctor · project.config.yaml · product=ledgerline
  ✓ all slots filled — ready (idea→done runs without editing the CORE)
EXIT=0
```

**Stage 3 — the CORE reads the seam (ledgerline values, never luana):**
| slot the core queries | returned |
|---|---|
| `engine_prefix.go_module_prefix` | `github.com/acme/ledgerline/internal/` |
| `brands.loop_order` | `main` |
| `brands.active` (pluck `slug`) | `main` |
| `toolchain.backend.lint` | `go vet ./...` |
| `locale.identifier` | `en-US` |
| `wip_caps.coarse_session_net.developed_max` | `10` |
| `brands.active --where cap_gate=advisory` (pluck `slug`) | `main` (the facet-filter consumer pattern resolves) |

**Stage 4 — zero-luana in the copied CORE:** dependency-grep over the copied kit →
`rules/ 0 · templates/ 0 · process/ 0 · scripts/ 0 · hooks/ 0 · agents+skills 2` (the 2 = grep-bot's generic `.venv`/`.next` skip-dirs, W3-blessed). **No core file names luana → no core file needs editing to adopt.**

## 4 · Verdict — DoD MET, with honest scope notes

**MET:** the loader is repo-portable (parent-walk works from `/tmp`), the doctor self-declares gaps + clears on fill, the core reads the seam (not luana), and the core carries zero project tokens. An adopter on a foreign stack fills 10 slots and the process artifacts (rules/templates/process/scripts) apply byte-identical.

**Honest scope of what "idea→done runs" was tested (charter is explicit the test is the slot-resolution + no-core-edit, not a literal feature build):**
- ✅ **Verified mechanically:** slot-gap detection, slot resolution, the `--where` facet, zero-core-edit (grep), kit self-containment, the bootstrap-skill procedure references only `core-harness/` + `project.config.yaml`.
- ⚠️ **NOT exercised (would need a real adopter codebase + a live Claude Code session in that repo):** an actual `po-ux→architect→dev→auditor→pm` cycle producing real ledgerline code; the plugin install (`/plugin marketplace add`) + the SessionStart slim-rule injection in the adopter session; `/harness:bootstrap` actually creating `.claude/rules/` symlinks in the adopter. These are **session-runtime** behaviors (the same class as the W7 rules restart-smoke) — verified by spec + the in-session smokes (injector emits valid 8090-char JSON; the clerk/sentry skill-symlinks already load), not by a second live repo this session.

## 5 · What the test found in the CORE that still named luana → NOTHING functional

The grep over the copied kit found **only**: (a) grep-bot's 2 generic build-artifact skip-dirs (functional, not smear), and — before the W7 finalize-commit cleaned them — (b) 2 illustrative tokens in the kit's own self-docs (README "NOT-here" list; bootstrap `dev-app` slot-category prose), now genericized. **No functional luana dependency in any core file.** The bare word "luana" survives only as legitimate PUBLISHER provenance (`marketplace.json` `name: luana-harness`; README's "today it lives in-monorepo (luana), `git subtree split` graduates it") — an adopter forking renames the marketplace; neither is in the dependency-grep pattern nor a runtime dependency.

## 6 · Cleanup
The `/tmp/harness-extract-test/` repo is a throwaway (outside the workspace, not committed). It can be `rm -rf`'d; re-creatable from `core-harness/` + the ledgerline config in §2 any time.

## 7 · Pointers
- `W7-EXEC-OUTPUT.md` (sibling dir) — the move that produced the kit this test consumed.
- `core-harness/scripts/harness_config.py --doctor` — the gate (exit-3 on `__FILL_ME__`).
- `core-harness/skills/harness-bootstrap/SKILL.md` — the `/harness:bootstrap` procedure an adopter runs after the drop.
- charter §8 — the program DoD this test discharges.

*End W8-OUTPUT.md — extraction test PASSING. The remaining program steps are W9 (legacy delete · **Chris gate, NOT autonomous**) + W10 (anti-rot governance · own session).*
