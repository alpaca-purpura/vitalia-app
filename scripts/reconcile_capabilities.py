#!/usr/bin/env python3
"""Reconcile capability YAML status fields from story YAML status (R32).

Capability files at ``{base}/docs/product/capabilities/{module}/{cap}.yaml`` declare
``status``, ``stories_live``, ``stories_planned``, ``stories_total`` in their
frontmatter. These MUST be a deterministic function of the referenced
``story_ids`` (each pointing at ``{base}/docs/product/stories/{module}/{story_id}.yaml``).

Where ``{base}`` is either:
  * ``{repo_root}/`` (legacy single-brand or platform-wide capabilities) — default
  * ``{repo_root}/{brand}/`` (brand-scoped capabilities post multibrand reorg 2026-05-15)
  * ``{repo_root}/{brand}/`` iterated for all brands (when ``--all-brands``)

Without enforcement, ``/pm-{brand}`` updates the capability manually at merge time
and drift is invisible — readers (auditors, eval runners, dashboards) get stale
overview data.

This script reads every capability YAML, looks up each referenced story,
recomputes the four derived fields, and either:

  * ``--check``     → exits 1 if any drift; prints details. Used by pre-commit hook.
  * (default)       → rewrites drifted capability files in place using regex on
                      the frontmatter (preserves comments / key order / blank lines).

Scope flags (mutually exclusive):
  * (default)       → root ``docs/product/`` (legacy / platform cross-brand)
  * ``--brand X``   → ``X/docs/product/`` only (e.g. ``--brand vitalia``)
  * ``--all-brands``→ iterate every dir with ``{brand}/config/brand.yaml`` + root

Run via ``python scripts/reconcile_capabilities.py [--check] [--require-capabilities-exist]
[--validate-ledger] [--strict] [--brand SLUG | --all-brands] [--repo PATH]``.

Coverage gate (``--require-capabilities-exist``)
================================================
Verifies that brands with ``status: shipped`` in their checkpoint frontmatter
have at least 1 capability YAML mapped. Detects the failure mode where a brand
ships features but never updates the SSoT funcional (capabilities/ empty).

Combine with ``--brand SLUG`` or ``--all-brands`` to scope which brands are
checked. Exit 1 on any gap. No auto-fix — gaps require manual inventory by the
brand's ``/pm-{brand}`` skill.

Origen
======
Process improvement R32 (2026-05-05). Multibrand expansion 2026-05-15 (post
audit aislamiento brand). Replaces manual ``/pm-{brand}`` recalc step in
SDD merge phase with deterministic gate.

Coverage gate added 2026-05-16 via proposal ``2026-05-16-capability-inventory-
enforcement`` (origen vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md).

Atomics killed 2026-05-28 (``docs/process/lifecycle.md``). The unit of behavior
is now ``scenario`` (Gherkin), not atomic. The ``--validate-atomics`` flag was
removed; ``atomics[]``/``atomics_added`` fields in cap YAML are inert historical
data left untouched.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_STORY_STATUS = {"planned", "ratified", "in-progress", "live", "deprecated"}
# `ratified` = spec approved by Chris, not yet built — bucketed with `planned`
# for capability rollup (capability isn't shipping until at least 1 story `live`).
PRE_BUILD_STATUSES = {"planned", "ratified"}


@dataclass
class CapDrift:
    """Drift record for a single capability YAML."""

    path: Path
    diffs: dict[str, tuple[object, object]]  # field → (actual, expected)
    missing_stories: list[str]


@dataclass
class CapCoverageGap:
    """Coverage gap for a brand with status=shipped but missing capability YAMLs.

    Raised by ``--require-capabilities-exist``. Detects the failure mode behind
    proposal ``2026-05-16-capability-inventory-enforcement``: brand mergea outcomes
    sin actualizar SSoT funcional (capabilities/ stays empty).
    """

    brand: str
    checkpoint_path: Path
    caps_dir: Path
    yaml_count: int  # excluding README.md / non-YAML files


@dataclass
class CapLedgerError:
    """Ledger-validation error (schema v2 cement 2026-05-27).

    Raised by ``--validate-ledger`` when a capability YAML's ``change_log``,
    ``atomics``, or ``parent_cap`` / ``derives_capabilities`` cross-references
    are inconsistent.

    Categories
    ----------
    * ``missing_story_checkpoint`` — change_log entry references story_id that
      lacks both an active and an archived checkpoint.md
    * ``atomic_story_mismatch`` — atomics[].added_in_story not found in any
      change_log[].story_id
    * ``parent_cap_missing`` — parent_cap declared but file does not exist
    * ``parent_cap_inverse_missing`` — parent cap file exists but does NOT list
      this capability in its derives_capabilities[]
    """

    cap_path: Path
    category: str
    detail: str


@dataclass
class CapLedgerWarning:
    """Ledger-validation WARNING (advisory by default, error under --strict).

    Categories
    ----------
    * ``live_without_scenarios`` — cap is ``status: live``/``beta`` but declares
      0 ``scenarios[]`` → not verifiable. WARN (no e2e coverage anchor).
    * ``live_created_in_story_unresolved`` — a ``live``/``beta`` cap whose
      ``created_in_story`` does not resolve to a checkpoint.md. Loud WARN
      (a shipped cap MUST trace to a real story). NOTE: ``planned`` caps with
      unresolved ``created_in_story`` are EXPECTED (forward-declared) and are
      NOT warned.
    """

    cap_path: Path
    category: str
    detail: str


class FrontmatterError(ValueError):
    """Raised when a YAML file has malformed or missing frontmatter."""


def load_frontmatter(path: Path) -> dict:
    r"""Parse YAML frontmatter.

    Three layouts supported:
      * Markdown-style: ``---\n<yaml>\n---\n<body>`` (capabilities, modules)
      * Pure YAML with leading marker: ``---\n<yaml>`` (stories — no body, no closer)
      * Comment block + frontmatter: ``# ...\n---\n<yaml>`` (some service stories
        prefix the YAML with header comments documenting eval policy / owners).
    """
    text = path.read_text(encoding="utf-8")

    # Skip leading comment-only lines and blank lines until reaching '---'
    lines = text.splitlines(keepends=True)
    cursor = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped in {"", "\n"}:
            cursor += len(line)
            continue
        break

    body = text[cursor:]
    if not body.startswith("---"):
        raise FrontmatterError(str(path))

    after = body[3:].lstrip("\n")
    yaml_text = after.split("\n---", 1)[0]

    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise FrontmatterError(str(path))
    return data


def derive_status(stories_status: list[str]) -> str:
    """Pure function: capability status from list of story statuses.

    Bucketing:
      * empty / no live → ``planned``
      * all deprecated → ``deprecated``
      * all live (non-deprecated) → ``live``
      * all pre-build (planned/ratified) → ``planned``
      * mixed → ``in-progress``
    """
    if not stories_status:
        return "planned"
    non_deprecated = [s for s in stories_status if s != "deprecated"]
    if not non_deprecated:
        return "deprecated"
    if all(s == "live" for s in non_deprecated):
        return "live"
    if all(s in PRE_BUILD_STATUSES for s in non_deprecated):
        return "planned"
    return "in-progress"


def replace_frontmatter_field(text: str, key: str, value: object) -> str:
    """Replace ``key: <whatever>`` in frontmatter, preserving rest of file.

    Only substitutes the first occurrence (frontmatter) to avoid touching
    body content that might mention the same key in prose.
    """
    pattern = rf"^({re.escape(key)}:)[^\n]*$"
    replacement = f"{key}: {value}"
    return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE)


def check_capability_coverage(repo: Path, brand: str) -> CapCoverageGap | None:
    """Verify shipped brand has at least 1 capability YAML.

    Reads ``{repo}/{brand}/docs/product/checkpoint.md`` frontmatter for
    ``status:`` field. If ``status: shipped``, counts ``*.yaml`` files under
    ``{repo}/{brand}/docs/product/capabilities/`` (recursive). Returns a gap if
    zero YAMLs found.

    Excluded statuses (no gap raised):
      * ``placeholder`` — brand bootstrapped but no real features yet
      * ``pending`` — brand not yet bootstrapped (saasora, inmoflow, etc.)
      * missing checkpoint — treated as placeholder (defensive)

    Origen: proposal ``2026-05-16-capability-inventory-enforcement``
    (vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md).
    """
    checkpoint = repo / brand / "docs" / "product" / "checkpoint.md"
    caps_dir = repo / brand / "docs" / "product" / "capabilities"

    if not checkpoint.exists():
        return None

    try:
        meta = load_frontmatter(checkpoint)
    except (FrontmatterError, yaml.YAMLError):
        return None

    if meta.get("status") != "shipped":
        return None

    if not caps_dir.exists():
        return CapCoverageGap(brand=brand, checkpoint_path=checkpoint, caps_dir=caps_dir, yaml_count=0)

    yaml_count = sum(1 for _ in caps_dir.rglob("*.yaml"))

    if yaml_count == 0:
        return CapCoverageGap(brand=brand, checkpoint_path=checkpoint, caps_dir=caps_dir, yaml_count=0)

    return None


def _story_checkpoint_exists(repo: Path, brand: str, story_id: str) -> bool:
    """Return True if a checkpoint.md exists for the story (active or archived).

    Searches:
      * ``{repo}/{brand}/docs/product/stories/{story_id}/checkpoint.md`` (active)
      * ``{repo}/{brand}/docs/archive/{year}/stories/{story_id}/checkpoint.md`` (archived)

    Archive scan iterates every ``{year}`` directory present (forward-compat with
    multi-year archive growth).
    """
    active = repo / brand / "docs" / "product" / "stories" / story_id / "checkpoint.md"
    if active.exists():
        return True
    archive_root = repo / brand / "docs" / "archive"
    if archive_root.exists():
        for year_dir in archive_root.iterdir():
            if not year_dir.is_dir():
                continue
            archived = year_dir / "stories" / story_id / "checkpoint.md"
            if archived.exists():
                return True
    return False


def _resolve_parent_cap(caps_dir: Path, parent_cap: str) -> Path | None:
    """Resolve parent_cap reference to a YAML path under caps_dir.

    parent_cap may be either:
      * Full capability_id (e.g. ``vitalia-booking-widget-embed``) — resolved by
        scanning caps_dir for matching ``capability_id`` frontmatter field
      * Module/slug form (e.g. ``booking/booking-widget-embed``) — resolved
        directly as a path under caps_dir
    """
    candidate = caps_dir / f"{parent_cap}.yaml"
    if candidate.exists():
        return candidate
    for cap_file in caps_dir.rglob("*.yaml"):
        try:
            data = load_frontmatter(cap_file)
        except (FrontmatterError, yaml.YAMLError):
            continue
        if data.get("capability_id") == parent_cap or data.get("slug") == parent_cap:
            return cap_file
    return None


def validate_ledger(repo: Path, brand: str | None) -> list[CapLedgerError]:
    """Validate cap ledger schema v2 cement 2026-05-27.

    Three validations per capability YAML that has ``change_log:`` field:

    1. Each ``change_log[].story_id`` references a story whose checkpoint.md
       exists (active or archived). Missing → ``missing_story_checkpoint``.
    2. Each ``atomics[].added_in_story`` matches a ``change_log[].story_id``.
       Mismatch → ``atomic_story_mismatch``.
    3. If ``parent_cap`` is not null, the parent capability exists AND lists
       the current capability in its ``derives_capabilities[]``. Missing/
       inconsistent → ``parent_cap_missing`` or ``parent_cap_inverse_missing``.

    Returns list of errors (empty list = OK).
    """
    base = repo / brand if brand else repo
    caps_dir = base / "docs" / "product" / "capabilities"
    if not caps_dir.exists():
        return []
    if not brand:
        # Ledger schema v2 is brand-scoped — root scope has no story checkpoints
        # to cross-reference against. Skip gracefully.
        return []

    errors: list[CapLedgerError] = []

    for cap_file in sorted(caps_dir.rglob("*.yaml")):
        try:
            cap = load_frontmatter(cap_file)
        except (FrontmatterError, yaml.YAMLError) as exc:
            sys.stderr.write(f"SKIP {cap_file}: {exc}\n")
            continue

        change_log = cap.get("change_log")
        # Skip caps without change_log (pre-v2 schema, not yet migrated)
        if not change_log or not isinstance(change_log, list):
            continue

        cap_id = cap.get("capability_id") or cap.get("slug") or cap_file.stem

        # Validation 1: change_log[].story_id → checkpoint exists
        change_log_story_ids: list[str] = []
        for idx, entry in enumerate(change_log):
            if not isinstance(entry, dict):
                continue
            story_id = entry.get("story_id")
            if not story_id:
                continue
            change_log_story_ids.append(story_id)
            if not _story_checkpoint_exists(repo, brand, story_id):
                errors.append(
                    CapLedgerError(
                        cap_path=cap_file,
                        category="missing_story_checkpoint",
                        detail=(
                            f"change_log[{idx}].story_id={story_id!r} has no checkpoint.md "
                            f"at {brand}/docs/product/stories/{story_id}/checkpoint.md "
                            f"nor at {brand}/docs/archive/*/stories/{story_id}/checkpoint.md"
                        ),
                    )
                )

        # Validation 2: atomics[].added_in_story → must match a change_log story_id
        atomics = cap.get("atomics") or []
        if isinstance(atomics, list):
            for idx, atomic in enumerate(atomics):
                if not isinstance(atomic, dict):
                    continue
                added_in = atomic.get("added_in_story")
                if not added_in:
                    continue
                if added_in not in change_log_story_ids:
                    label = atomic.get("label") or atomic.get("id") or f"atomic[{idx}]"
                    errors.append(
                        CapLedgerError(
                            cap_path=cap_file,
                            category="atomic_story_mismatch",
                            detail=(
                                f"atomic {label!r} (atomics[{idx}].added_in_story={added_in!r}) "
                                f"not found in any change_log[].story_id "
                                f"(declared: {change_log_story_ids})"
                            ),
                        )
                    )

        # Validation 3: parent_cap consistency
        parent_cap = cap.get("parent_cap")
        if parent_cap:  # not None, not empty string
            parent_path = _resolve_parent_cap(caps_dir, parent_cap)
            if parent_path is None:
                errors.append(
                    CapLedgerError(
                        cap_path=cap_file,
                        category="parent_cap_missing",
                        detail=(
                            f"parent_cap={parent_cap!r} declared but no capability YAML "
                            f"with that capability_id/slug exists under {caps_dir.relative_to(repo)}"
                        ),
                    )
                )
            else:
                try:
                    parent_data = load_frontmatter(parent_path)
                except (FrontmatterError, yaml.YAMLError):
                    parent_data = {}
                derives = parent_data.get("derives_capabilities") or []
                if cap_id not in derives:
                    errors.append(
                        CapLedgerError(
                            cap_path=cap_file,
                            category="parent_cap_inverse_missing",
                            detail=(
                                f"parent_cap={parent_cap!r} resolved to {parent_path.relative_to(repo)} "
                                f"but its derives_capabilities[] does NOT list {cap_id!r} "
                                f"(found: {derives})"
                            ),
                        )
                    )

    return errors


# Statuses that imply the capability is shipped/usable and therefore should be
# verifiable + traceable to a real story.
_LIVE_STATUSES = frozenset({"live", "beta"})


def validate_live_evidence(repo: Path, brand: str | None) -> list[CapLedgerWarning]:
    """Validate live⟹evidence invariants. Returns WARNINGS (advisory by default).

    Two checks per capability YAML:

    1. ``status: live``/``beta`` but 0 ``scenarios[]`` → ``live_without_scenarios``
       (cap live sin scenarios = no verificable).
    2. ``status: live``/``beta`` whose ``created_in_story`` does NOT resolve to a
       checkpoint.md → ``live_created_in_story_unresolved`` (loud — shipped cap
       must trace to a real story). ``planned`` caps with unresolved
       ``created_in_story`` are EXPECTED (forward-declared) and skipped silently.

    These are WARNINGS — they do not fail the build unless ``--strict`` is set.
    """
    base = repo / brand if brand else repo
    caps_dir = base / "docs" / "product" / "capabilities"
    if not caps_dir.exists() or not brand:
        # Brand-scoped: root scope has no story checkpoints to resolve against.
        return []

    warnings: list[CapLedgerWarning] = []

    for cap_file in sorted(caps_dir.rglob("*.yaml")):
        try:
            cap = load_frontmatter(cap_file)
        except (FrontmatterError, yaml.YAMLError) as exc:
            sys.stderr.write(f"SKIP {cap_file}: {exc}\n")
            continue

        status = str(cap.get("status") or "").strip().lower()
        cap_id = cap.get("capability_id") or cap.get("slug") or cap_file.stem

        # Check 1: live/beta cap with 0 scenarios → not verifiable
        if status in _LIVE_STATUSES:
            scenarios = cap.get("scenarios")
            n_scenarios = len(scenarios) if isinstance(scenarios, list) else 0
            if n_scenarios == 0:
                warnings.append(
                    CapLedgerWarning(
                        cap_path=cap_file,
                        category="live_without_scenarios",
                        detail=(
                            f"cap {cap_id!r} is status={status!r} but declares 0 scenarios "
                            f"(cap live sin scenarios = no verificable). Add scenarios[] with "
                            f"e2e_test anchors so the live claim can be verified."
                        ),
                    )
                )

        # Check 2: created_in_story resolution. planned → expected (skip).
        #          live/beta → loud WARN if unresolved.
        created_in_story = cap.get("created_in_story")
        if created_in_story and status in _LIVE_STATUSES:
            if not _story_checkpoint_exists(repo, brand, created_in_story):
                warnings.append(
                    CapLedgerWarning(
                        cap_path=cap_file,
                        category="live_created_in_story_unresolved",
                        detail=(
                            f"cap {cap_id!r} is status={status!r} but created_in_story="
                            f"{created_in_story!r} has no checkpoint.md at "
                            f"{brand}/docs/product/stories/{created_in_story}/ nor "
                            f"{brand}/docs/archive/*/stories/{created_in_story}/ "
                            f"(a shipped cap must trace to a real story)."
                        ),
                    )
                )

    return warnings


def discover_brands(repo: Path) -> list[str]:
    """Return sorted list of brand slugs (dirs containing ``config/brand.yaml``).

    Post multibrand reorg 2026-05-15: each brand vertical lives under
    ``{repo}/{brand}/`` with its own ``config/brand.yaml`` marker. Used by
    ``--all-brands`` to iterate all active verticals.
    """
    brands: list[str] = []
    for cfg in sorted(repo.glob("*/config/brand.yaml")):
        brand = cfg.parent.parent.name
        brands.append(brand)
    return brands


def reconcile(repo: Path, *, check_only: bool, brand: str | None = None) -> tuple[int, list[CapDrift]]:
    """Walk capabilities for a given scope, detect drift, optionally rewrite.

    Scope resolution:
      * ``brand=None`` → root ``{repo}/docs/product/`` (legacy / platform cross-brand)
      * ``brand="vitalia"`` → ``{repo}/vitalia/docs/product/``

    Returns (exit_code, drifts).
    """
    base = repo / brand if brand else repo
    caps_dir = base / "docs" / "product" / "capabilities"
    stories_dir = base / "docs" / "product" / "stories"

    if not caps_dir.exists():
        # Empty scope (no capabilities yet for this brand, or root post-multibrand
        # reorg where capabilities migrated to {brand}/) is NOT an error — just skip.
        return 0, []

    drifts: list[CapDrift] = []

    for cap_file in sorted(caps_dir.rglob("*.yaml")):
        try:
            cap = load_frontmatter(cap_file)
        except (FrontmatterError, yaml.YAMLError) as exc:
            sys.stderr.write(f"SKIP {cap_file}: {exc}\n")
            continue

        module = cap.get("module")
        story_ids = cap.get("story_ids") or []
        if not module or not story_ids:
            continue

        stories_status: list[str] = []
        missing: list[str] = []
        for sid in story_ids:
            sfile = stories_dir / module / f"{sid}.yaml"
            if not sfile.exists():
                missing.append(sid)
                continue
            try:
                story = load_frontmatter(sfile)
            except (FrontmatterError, yaml.YAMLError):
                missing.append(sid)
                continue
            status = story.get("status", "planned")
            if status not in VALID_STORY_STATUS:
                status = "planned"
            stories_status.append(status)

        expected = {
            "status": derive_status(stories_status),
            "stories_live": sum(1 for s in stories_status if s == "live"),
            "stories_planned": sum(1 for s in stories_status if s in PRE_BUILD_STATUSES),
            "stories_total": len(stories_status),
        }
        actual = {k: cap.get(k) for k in expected}

        diffs = {k: (actual[k], expected[k]) for k in expected if actual[k] != expected[k]}
        if not diffs and not missing:
            continue

        drifts.append(CapDrift(path=cap_file, diffs=diffs, missing_stories=missing))

        if not check_only and diffs:
            text = cap_file.read_text(encoding="utf-8")
            for key, val in expected.items():
                text = replace_frontmatter_field(text, key, val)
            cap_file.write_text(text, encoding="utf-8")

    return 0, drifts


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 on drift without modifying files (CI / pre-commit gate).",
    )
    parser.add_argument(
        "--require-capabilities-exist",
        action="store_true",
        help="Verify shipped brands have at least 1 capability YAML. "
        "Exit 1 if any brand with checkpoint status=shipped has empty capabilities/. "
        "Origen: proposal 2026-05-16-capability-inventory-enforcement.",
    )
    parser.add_argument(
        "--validate-ledger",
        action="store_true",
        help="Validate capability ledger schema v2 (cement 2026-05-27): "
        "change_log[].story_id has checkpoint.md (active or archive); "
        "atomics[].added_in_story matches a change_log[].story_id; "
        "parent_cap (if non-null) exists and lists current cap in derives_capabilities[]. "
        "Exit 1 on any error. Combine with --brand or --all-brands.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Reserved for future use (promote advisory warnings to errors).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repo root containing docs/product/ (and brand verticals). Defaults to script's parent.",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--brand",
        type=str,
        default=None,
        help="Brand slug to scope reconciliation (vitalia). "
        "Reads {repo}/{brand}/docs/product/. Default: root docs/product/ (legacy/platform).",
    )
    scope.add_argument(
        "--all-brands",
        action="store_true",
        help="Iterate root + every brand vertical (dirs with config/brand.yaml). "
        "Aggregates drifts across all scopes.",
    )
    args = parser.parse_args()

    # Build list of (label, brand_arg) tuples to process
    scopes: list[tuple[str, str | None]] = []
    if args.all_brands:
        scopes.append(("root (platform)", None))
        for b in discover_brands(args.repo):
            scopes.append((b, b))
    elif args.brand:
        scopes.append((args.brand, args.brand))
    else:
        scopes.append(("root (platform)", None))

    all_drifts: list[tuple[str, CapDrift]] = []
    for label, brand_arg in scopes:
        err, drifts = reconcile(args.repo, check_only=args.check, brand=brand_arg)
        if err:
            return err
        for d in drifts:
            all_drifts.append((label, d))

    # Coverage check: shipped brands must have ≥1 capability YAML.
    # Only triggered when flag is explicitly passed (opt-in, backward-compatible).
    coverage_gaps: list[CapCoverageGap] = []
    if args.require_capabilities_exist:
        # Brand-scoped: only check the requested brand(s); never the root scope.
        brands_to_check: list[str] = []
        if args.all_brands:
            brands_to_check = discover_brands(args.repo)
        elif args.brand:
            brands_to_check = [args.brand]
        # else: --require-capabilities-exist without --brand/--all-brands → no-op
        # (root scope has no brand checkpoint; user must scope explicitly).
        for b in brands_to_check:
            gap = check_capability_coverage(args.repo, b)
            if gap is not None:
                coverage_gaps.append(gap)

    # Ledger validation (schema v2 cement 2026-05-27).
    # Opt-in via --validate-ledger. Brand-scoped (root scope skipped — no story checkpoints).
    ledger_errors: list[tuple[str, CapLedgerError]] = []
    if args.validate_ledger:
        for label, brand_arg in scopes:
            if brand_arg is None:
                continue  # root scope has no brand-scoped stories
            for e in validate_ledger(args.repo, brand_arg):
                ledger_errors.append((label, e))

    # live⟹evidence advisory checks (WARN by default; error only under --strict).
    # Runs alongside --validate-ledger and --check so the pre-commit gate surfaces
    # them without silently skipping. Brand-scoped (root has no story checkpoints).
    ledger_warnings: list[tuple[str, CapLedgerWarning]] = []
    if args.validate_ledger or args.check:
        for label, brand_arg in scopes:
            if brand_arg is None:
                continue
            for w in validate_live_evidence(args.repo, brand_arg):
                ledger_warnings.append((label, w))

    # Under --strict, live⟹evidence warnings are promoted to blocking errors.
    strict_promotes_warnings = bool(args.strict and ledger_warnings)

    def _print_warnings() -> None:
        if not ledger_warnings:
            return
        label_word = "ERROR" if strict_promotes_warnings else "WARN"
        print(f"\nLIVE⟹EVIDENCE {label_word}S in {len(ledger_warnings)} cap(s):")  # noqa: T201
        for label, w in ledger_warnings:
            rel = w.cap_path.relative_to(args.repo)
            print(f"\n  [{label}] {rel}")  # noqa: T201
            print(f"    category: {w.category}")  # noqa: T201
            print(f"    detail:   {w.detail}")  # noqa: T201
        if strict_promotes_warnings:
            print("\n--strict: live⟹evidence warnings promoted to blocking errors.")  # noqa: T201
        else:
            print("\n(advisory — non-blocking. Run with --strict to make these errors.)")  # noqa: T201

    if not all_drifts and not coverage_gaps and not ledger_errors:
        scope_desc = ", ".join(label for label, _ in scopes)
        print(f"OK — all capabilities consistent with stories. Scope: {scope_desc}.")  # noqa: T201
        if args.require_capabilities_exist:
            checked = ", ".join(b for b in (
                discover_brands(args.repo) if args.all_brands
                else ([args.brand] if args.brand else [])
            )) or "(none — pass --brand or --all-brands to enable)"
            print(f"Capability coverage check: PASS. Brands checked: {checked}.")  # noqa: T201
        if args.validate_ledger:
            ledger_scopes = ", ".join(label for label, b in scopes if b is not None) or "(none — pass --brand or --all-brands)"
            print(f"Capability ledger check: PASS. Scopes: {ledger_scopes}.")  # noqa: T201
        _print_warnings()
        return 1 if strict_promotes_warnings else 0

    if all_drifts:
        print(f"DRIFT detected in {len(all_drifts)} capability file(s):")  # noqa: T201
        for label, d in all_drifts:
            rel = d.path.relative_to(args.repo)
            print(f"\n  [{label}] {rel}")  # noqa: T201
            for key, (actual, expected) in d.diffs.items():
                print(f"    {key}: actual={actual!r} → expected={expected!r}")  # noqa: T201
            if d.missing_stories:
                print(f"    missing story files: {d.missing_stories}")  # noqa: T201

    if coverage_gaps:
        print(f"\nCAPABILITY COVERAGE GAP in {len(coverage_gaps)} brand(s):")  # noqa: T201
        for gap in coverage_gaps:
            print(f"\n  [{gap.brand}] status=shipped but {gap.caps_dir.relative_to(args.repo)} contains 0 capability YAMLs")  # noqa: T201
            print(f"    checkpoint: {gap.checkpoint_path.relative_to(args.repo)}")  # noqa: T201
            print(f"    fix: poblar capabilities/{{module}}/{{cap}}.yaml leyendo código vivo + rules + archive")  # noqa: T201
            print(f"    ref: docs/promotion-protocol/proposals/2026-05-16-capability-inventory-enforcement.md")  # noqa: T201

    if ledger_errors:
        print(f"\nCAPABILITY LEDGER ERRORS in {len(ledger_errors)} entry/entries:")  # noqa: T201
        for label, e in ledger_errors:
            rel = e.cap_path.relative_to(args.repo)
            print(f"\n  [{label}] {rel}")  # noqa: T201
            print(f"    category: {e.category}")  # noqa: T201
            print(f"    detail:   {e.detail}")  # noqa: T201
        print("\nLedger schema v2 cement: 2026-05-27. Fix by editing change_log/parent_cap/derives_capabilities in cap YAML.")  # noqa: T201

    _print_warnings()

    has_blocking_errors = bool(coverage_gaps or ledger_errors or strict_promotes_warnings)
    if args.check or has_blocking_errors:
        # Coverage gaps + ledger errors are always blocking
        # (no auto-fix possible — manual edit required).
        if all_drifts and args.check:
            print("\nRun without --check to fix drifts in place. Coverage gaps + ledger errors require manual edits.")  # noqa: T201
        elif coverage_gaps and not ledger_errors:
            print("\nCoverage gaps require manual capability YAML authoring (no auto-fix).")  # noqa: T201
        elif ledger_errors and not coverage_gaps:
            print("\nLedger errors require manual edits to capability YAML frontmatter.")  # noqa: T201
        return 1

    if not all_drifts:
        return 0

    print(f"\nFixed {len(all_drifts)} file(s).")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
