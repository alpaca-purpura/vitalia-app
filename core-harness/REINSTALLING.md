# REINSTALLING.md — re-install the kit FROM SCRATCH in an existing engagement

> **Audience:** the operator / delivery team re-birthing the harnesses of an EXISTING
> install so they come back **measurable** (plugin + embedded telemetry, kit ≥ v0.5.0).
> Runs INSIDE the engagement repo (data-plane) — nothing here touches the factory.
> Companion docs: `ADOPTING.md` (fresh install) · `telemetry/README.md` (the sensor).

## What survives, what re-births

| Survives (the OBJECT — client property) | Re-births (the CLASS — kit snapshot) |
|---|---|
| `project.config.yaml` — the seam, signed values | `core-harness/` wholesale (read-only for the client BY DESIGN → wholesale replace is safe) |
| specs · stories · docs · code of the product | `.claude/` re-exposure of core rules/agents/skills |
| PROJECT-layer rules/skills (the client's fill-in) | hook wiring (now via the plugin's `hooks.json`, telemetry included) |
| git history | plugin registration (marketplace + install) |

## Procedure (day-0 of the re-birth)

**0 · Preconditions.** Clean tree, everything committed and pushed. One dedicated session.

**1 · Backflow audit (governance — NEVER skip).** Diff the install's `core-harness/`
against the kit tag it was pinned to. Any local delta is a hot-fix that MUST flow
upstream to the factory (backflow) or be consciously discarded — a reinstall must never
silently bury an unbackflowed fix. Zero deltas expected if the governance held.

**2 · Retire the old exposure.** Remove `.claude/rules/*` symlinks that point into
`core-harness/`, agents/skills that were COPIED from the core (project-layer ones stay),
and any `settings.json` hook entries that reference old core paths. **Consult
[`CHANGELOG.md`](./CHANGELOG.md) (travels in the kit):** its RENAMES tables list every
renamed/moved/removed piece between your pinned tag and the new version, each with a
one-line migration — apply them so project-layer pointers don't dangle.

**3 · Drop the new kit.** Replace `core-harness/` wholesale with the new version
(`installer/new-project.sh` from the factory, or `cp -r` of the pinned tag). Verify
`core-harness/VERSION` shows the expected `KIT_VERSION`.

**4 · Install the plugin — FROM the private marketplace (KIT-06).** In Claude Code,
inside the repo:
```
claude plugin marketplace add alpacapurpura/prenter-marketplace
/plugin install harness@prenter-marketplace
```
Access rides your ambient git credentials — the account's client code is a read-only
token/deploy-key on the marketplace repo (export `GITHUB_TOKEN` for background
auto-updates). `harness` = STABLE channel · `harness-beta` = beta; ONE channel per
machine (switching = uninstall + install). Skills/agents/hooks activate — including the
telemetry hooks (Stop · SubagentStop · SessionEnd → `telemetry/emit.py`). Update later =
a semver bump published to your channel, then `claude plugin marketplace update
prenter-marketplace` + `/plugin update harness` (explicit semver — no silent updates).
Air-gapped fallback (no marketplace reachable — I-31): the local index that travels in
the kit still works: `/plugin marketplace add ./core-harness` + `/plugin install
harness@prenter-harness`.

**5 · `/harness:bootstrap`.** Re-exposes the rules corpus, runs the DETECTION SWEEP
(proposes seam values with provenance — slots already signed are NOT overwritten), and
the doctor certifies (`exit 0` = every slot declared).

**6 · Telemetry smoke — the harness is born measurable.** After the first Stop of the
session: `~/.prenter/telemetry/<project>/trazas.jsonl` gains a span (nodo = skill or
`conversacion`, tokens/cost/manifest/latency/hash). With egress configured on the
machine (`~/.config/prenter/observatorio.yaml` — NEVER in the repo), the trace appears
in the operator backend; without config, local sink only (expected default). Verify
NOTHING sensitive left: the sink has no `prompt`/`output` fields, only `output_hash`.

**7 · Operational sanity.** Fresh session: core rules load always-on · one kit skill
responds · gates fire on a dummy commit · run one small story through the cycle.

## Rollback

The reinstall is one commit in the engagement repo: `git revert` + `/plugin uninstall
harness@prenter-harness` restores the previous state. The seam and all client property
were never touched.
