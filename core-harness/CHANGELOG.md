# CHANGELOG — core-harness (the kit)

> **Travels IN the kit (KIT-08).** One section per version: what changed, plus a
> **RENAMES table** (renamed / moved / removed pieces) with a ONE-LINE migration each.
> `REINSTALLING.md` **step 2** consumes this file when retiring an install's old
> exposure — apply every migration between your pinned tag and the new version so
> project-layer pointers don't dangle. Wording here is stack-neutral by design (the
> factory's proxy-clean gate scans this file too).

## 0.5.2 — 2026-07-02

Beta-channel catch (the channel doing its job): the 0.5.1 isolated smoke — first real
consumer of the beta channel — revealed that in print-mode (`claude -p`) the Stop hook
can fire BEFORE the assistant lines are flushed to the transcript; turn-detection v2
then emitted an EMPTY span (0 tokens, no cost). **0.5.1 was never promoted to stable.**

- **Telemetry: Stop now HOLDS a trailing turn that has no assistant usage yet**, and
  SessionEnd closes it complete (`telemetry/emit.py`). The factory gate reproduces the
  race (truncated-transcript fixture). No schema change — **no migration**.

### Renames in 0.5.2

| Old | New | Migration (1 line) |
|---|---|---|
| — | — | No files renamed/moved/removed in this release. |

## 0.5.1 — 2026-07-02

Hot-fix train — the first update published through the private marketplace channel
(KIT-06): three findings from a real reinstall, fixed in the CLASS, propagated by bump.

- **Telemetry: headless runs are now visible (KIT-07).** Turn-detection v2 in
  `telemetry/emit.py`: print-mode (`claude -p`) prompts carry no `origin` and previously
  emitted 0 spans; they now open turns. Local-command wrappers, meta lines and sidechain
  (subagent) prompts still do NOT open turns. No schema change — **no migration**.
- **CLASS content de-stacked (KIT-09).** The detection-sweep examples in
  `skills/harness-bootstrap/SKILL.md` and every stack-named mention across
  `rules/`·`templates/`·`ADOPTING.md` were rewritten agnostic: the client repo's own
  files and the seam (`project.config.yaml`) are the ONLY sources of tool names (I-52).
  The factory now enforces this with a proxy-clean gate. Prose-only — **migration: only
  if your project layer greps rule text for tool names (machinery checks): re-baseline
  those checks against the new wording.** Two wording details worth knowing:
  - `rules/architect-autonomous-mode.md` now references the visual-scope section of your
    project-layer `autonomous-mode.md` DESCRIPTIVELY (no stack-named heading to match);
    the `04-validators.yaml` block key is unchanged.
  - `rules/hotfix-repro-mandatory.md` example values for `trace_evidence.source` are now
    infra-neutral (`runtime-logs | apm-alert | …`); existing hot-fix docs keep working —
    the real sources come from the seam (`live_verify_infra.observability_evidence`).
- **This CHANGELOG (KIT-08).** Introduced, referenced from `REINSTALLING.md` step 2.

### Renames in 0.5.1

| Old | New | Migration (1 line) |
|---|---|---|
| — | — | No files renamed/moved/removed in this release. |

## 0.5.0 and earlier — retroactive table

These shipped without migration notes (the finding that motivated KIT-08). If your
install was pinned to a tag **before v0.5.0**, apply all of them.

| Old | New | Landed | Migration (1 line) |
|---|---|---|---|
| `scripts/git/ps1-luana.sh` | `scripts/git/ps1-harness.sh` | v0.5.0 | Re-point any local PS1 symlink / shell-rc include to the new filename. |
| project-layer skill dir `_pm-brand-template/` | `_pm-sistema-template/` | v0.5.0 (I-52) | Rename the project-layer skill dir — kit rules (`pm-skill-chaining.md`) point at the `sistema` name. |
| project-layer rule `.claude/rules/brand-docs-schema.md` | `sistema-docs-schema.md` | v0.5.0 (I-52) | Rename the project-layer rule file — `story-closure-gate.md` points at the `sistema` name. |
| project-layer skills `pm-{brand}/` | `pm-{sistema}/` | v0.5.0 (I-52) | Rename each PM skill dir to the `{sistema-slug}` pattern (vocabulary: `brand` → `sistema` everywhere). |
