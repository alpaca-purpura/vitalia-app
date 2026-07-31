#!/usr/bin/env python3
"""Generate BACKLOG.yaml + BACKLOG.md from product/process sources (Wave 1).

Single SSoT pipeline replacing manual maintenance of multiple files.
Reads from a base path (= ``repo`` for root/platform, ``repo/{brand}`` for
brand-scoped post multibrand reorg 2026-05-15):

  Sources (new paradigm)
  ----------------------
    {base}/docs/product/ideas-pool.yaml          → ideas + validated entries
    {base}/docs/product/outcomes/*.md            → outcomes (epics)
    {base}/docs/product/stories/{id}/checkpoint.md  → active stories with state (NEW flat layout)
    {base}/docs/product/capabilities/{m}/*.yaml  → capability rollups (R32 reconciled)
    {base}/docs/product/modules/*.md             → module-level metadata

  Sources (legacy — read ONLY for root scope, NEVER per-brand)
  ------------------------------------------------------------
    docs/projects/active/PI-*/checkpoint.md                     → legacy active PIs (PI-12+ paradigm)
    docs/projects/active/PI-*/sprints/*/stories/*/checkpoint.md → legacy active stories
    docs/pm-nico/pis/active/*/PI.md                             → legacy pm-nico PIs (folder removed Wave 2 — read returns []  as guard)

  Outputs
  -------
    {base}/docs/product/BACKLOG.yaml       → SSoT machine-readable (for tooling)
    {base}/docs/product/BACKLOG.md         → human view: roadmap + Mermaid kanban + caps snapshot
    {base}/docs/product/BACKLOG-TLDR.md    → compressed TLDR view

Run:
  python scripts/generate_backlog.py [--check] [--brand SLUG | --all-brands] [--repo PATH]

  --check       : exit 1 if regenerated content differs from on-disk (CI / hook gate)
  --brand SLUG  : scope to {repo}/{brand}/docs/product/ (e.g. --brand vitalia)
  --all-brands  : iterate root + every brand with config/brand.yaml
  --repo P      : repo root, default = script's parent

Origen
======
Process improvement R33 (2026-05-05). Multibrand expansion 2026-05-15 (post
audit aislamiento brand): per-brand backlog generation con base path scoping.
"""

# ruff: noqa: PERF401
# Reason: many small for-append loops are clearer than list.extend in source readers
# where each loop body has multiple branches (state validation, fallback values).

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# ─── Constants ─────────────────────────────────────────────────────────

STATE_ORDER = (
    "idea",
    "refining",
    "refined",
    "ready",
    "developing",
    "developed",
    "reviewing",
    "done",
    "parked",
    "dropped",
)
VALID_STATES = set(STATE_ORDER)
PRE_BUILD_STATUSES = {"planned", "ratified"}

# Legacy state coercion (paradigm v3 → v4, post 2026-05-06 Punto 4).
# Active stories should migrate to v4 vocabulary; this map keeps generator
# robust during transition window. Any state not in v4 enum is coerced.
LEGACY_STATE_MAP = {
    "validated": "refining",  # split: refining (drafts) + refined (ratified)
    "building": "developing",  # split: developing + developed
    "review": "reviewing",  # rename
}

# CAPS — read from the harness seam project.config.yaml (D1 · W5b 2026-06-09). ONE store:
# scripts/validate_session_close.py reads the SAME `wip_caps` slot (the byte-identical dup is
# gone · charter §3 DRY). Downstream key names (refining_max … done_rolling_days) preserved.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_config as _hc  # noqa: E402 — own script dir put on sys.path above

_WIP = _hc.get("wip_caps")
CAPS = {
    **_WIP["coarse_session_net"],  # refining_max … reviewing_max
    "idea_stale_days": _WIP["staleness_days"]["idea_stale"],
    "refining_stale_days": _WIP["staleness_days"]["refining_stale"],
    "refined_stale_days": _WIP["staleness_days"]["refined_stale"],
    "done_rolling_days": _WIP["staleness_days"]["done_rolling"],
}


# ─── Models ───────────────────────────────────────────────────────────


@dataclass
class Item:
    """Generic backlog item — idea / outcome / story (active) / legacy PI."""

    id: str
    kind: str  # idea | outcome | story | legacy-pi
    state: str
    title: str = ""
    one_liner: str = ""
    tags: list[str] = field(default_factory=list)
    last_touched: str | None = None
    created: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapRollup:
    """Capability count snapshot per module."""

    module: str
    live: int = 0
    in_progress: int = 0
    planned: int = 0
    deprecated: int = 0


@dataclass
class Release:
    """Release bucket (F0..F8) — schema v2 cement 2026-05-27.

    Loaded from ``{base}/docs/product/releases/F*.yaml``. Used to group stories
    by release in BACKLOG.md output. Stories without a ``release:`` field (or
    with ``release: null``) bucket under ``(sin release · legacy)``.
    """

    release_id: str  # e.g. "F0"
    name: str  # human-readable title
    status: str  # planned | in-progress | shipped
    order: int  # sort key
    target_date: str | None
    shipped_date: str | None
    stories: list[str] = field(default_factory=list)  # story_id list (declarative)


# ─── Parsing helpers ───────────────────────────────────────────────────


class FrontmatterError(ValueError):
    """Raised when a Markdown/YAML file has malformed frontmatter."""


def load_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter (handles Markdown-style ---/yaml/---/body, pure YAML, comment-prefix)."""
    text = path.read_text(encoding="utf-8")

    # Skip leading comment-only lines / blank lines
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


def days_since(date_str: str | None) -> int | None:
    """Days between today and an ISO date / datetime string. None if unparseable."""
    if not date_str:
        return None
    s = str(date_str).split("+", maxsplit=1)[0].rstrip("Z")
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ", "%Y-%m"):
        try:
            d = datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            today = datetime.now(timezone.utc)
            return (today - d).days
        except ValueError:
            continue
    return None


# ─── Source readers ────────────────────────────────────────────────────


def read_ideas_pool(repo: Path) -> list[Item]:
    """Read docs/product/ideas-pool.yaml → list of Items (state in {idea,validated,parked,dropped})."""
    path = repo / "docs" / "product" / "ideas-pool.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: list[Item] = []
    for entry in data.get("ideas") or []:
        state = entry.get("state", "idea")
        # Coerce legacy v3 → v4
        state = LEGACY_STATE_MAP.get(state, state)
        if state not in VALID_STATES:
            state = "idea"
        out.append(
            Item(
                id=entry["id"],
                kind="idea",
                state=state,
                title=entry.get("one_liner", entry["id"]),
                one_liner=entry.get("one_liner", ""),
                tags=entry.get("tags") or [],
                created=entry.get("created"),
                last_touched=entry.get("last_touched") or entry.get("created"),
                extra={
                    "promoted_to_outcome": entry.get("promoted_to_outcome"),
                    "ost": entry.get("ost"),
                },
            )
        )
    return out


def read_outcomes(repo: Path) -> list[Item]:
    """Read docs/product/outcomes/*.md → list of outcome Items."""
    outcomes_dir = repo / "docs" / "product" / "outcomes"
    if not outcomes_dir.exists():
        return []
    out: list[Item] = []
    for f in sorted(outcomes_dir.glob("*.md")):
        if f.name == ".gitkeep":
            continue
        try:
            fm = load_frontmatter(f)
        except (FrontmatterError, yaml.YAMLError):
            continue
        outcome_state = fm.get("state", "refining")
        outcome_state = LEGACY_STATE_MAP.get(outcome_state, outcome_state)
        if outcome_state not in VALID_STATES:
            outcome_state = "refining"
        out.append(
            Item(
                id=fm.get("id", f.stem),
                kind="outcome",
                state=outcome_state,
                title=fm.get("title", fm.get("id", f.stem)),
                tags=fm.get("tags") or [],
                created=fm.get("created"),
                last_touched=fm.get("last_modified") or fm.get("created"),
                extra={
                    "story_ids": fm.get("story_ids") or [],
                    "why_now": fm.get("why_now"),
                    "why_next": fm.get("why_next"),
                    "target_end": fm.get("target_end"),
                    "priority": fm.get("priority", 3),
                    "success_metrics": fm.get("success_metrics") or [],
                },
            )
        )
    return out


def read_active_stories_new(repo: Path) -> list[Item]:
    """Read docs/product/stories/{id}/checkpoint.md (NEW flat layout) → active stories."""
    stories_dir = repo / "docs" / "product" / "stories"
    if not stories_dir.exists():
        return []
    out: list[Item] = []
    for d in sorted(stories_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        # Skip module subdirs (legacy single-file-per-story layout)
        # New layout: each child is a story folder containing files (01-spec.md, etc.)
        # Legacy layout: each child is a module folder containing yaml files
        children = list(d.iterdir())
        if not any(f.suffix == ".md" or f.name == "checkpoint.md" for f in children):
            continue
        cp = d / "checkpoint.md"
        if not cp.exists():
            continue
        try:
            fm = load_frontmatter(cp)
        except (FrontmatterError, yaml.YAMLError):
            continue
        story_state = fm.get("state", "ready")
        story_state = LEGACY_STATE_MAP.get(story_state, story_state)
        if story_state not in VALID_STATES:
            story_state = "refining"
        # legacy_exempt:true → tag with legacy:* so cap counter excludes it
        story_tags = list(fm.get("tags") or [])
        if fm.get("legacy_exempt") and not any(t.startswith("legacy:") for t in story_tags):
            migrated_from = fm.get("migrated_from", "")
            tag_suffix = "exempt"
            if "PI-" in migrated_from:
                # Extract PI-N from migrated_from path
                import re as _re

                m = _re.search(r"PI-\d+", migrated_from)
                if m:
                    tag_suffix = m.group(0).lower()
            story_tags.append(f"legacy:{tag_suffix}")
        # v4 schema uses story_id; v3 used id; fallback to folder name
        story_id = fm.get("story_id") or fm.get("id") or d.name
        out.append(
            Item(
                id=story_id,
                kind="story",
                state=story_state,
                title=story_id,
                tags=story_tags,
                last_touched=fm.get("last_modified"),
                extra={
                    "outcome": fm.get("outcome"),
                    "release": fm.get("release"),  # v2 cement 2026-05-27 (None for legacy)
                    "phase": fm.get("phase"),
                    "next_action": fm.get("next_action"),
                    "blocked_by": fm.get("blocked_by"),
                    "priority_override": fm.get("priority_override"),
                    "audit_iterations": fm.get("audit_iterations", 0),
                },
            )
        )
    return out


def read_releases(base: Path) -> list[Release]:
    """Read ``{base}/docs/product/releases/F*.yaml`` → sorted list of Releases.

    Schema v2 cement 2026-05-27. Returns empty list if releases dir missing
    (backward compatible with brands not yet migrated). Sort order:
    ``order`` field ascending, then ``release_id`` lexicographic as tiebreaker.
    """
    releases_dir = base / "docs" / "product" / "releases"
    if not releases_dir.exists():
        return []
    out: list[Release] = []
    for f in sorted(releases_dir.glob("F*.yaml")):
        try:
            fm = load_frontmatter(f)
        except (FrontmatterError, yaml.YAMLError):
            continue
        out.append(
            Release(
                release_id=fm.get("release_id", f.stem),
                name=fm.get("name", f.stem),
                status=fm.get("status", "planned"),
                order=int(fm.get("order", 999)),
                target_date=fm.get("target_date"),
                shipped_date=fm.get("shipped_date"),
                stories=list(fm.get("stories") or []),
            )
        )
    out.sort(key=lambda r: (r.order, r.release_id))
    return out


def read_legacy_active_stories(repo: Path) -> list[Item]:
    """Read docs/projects/active/PI-*/sprints/*/stories/*/checkpoint.md (transition period)."""
    base = repo / "docs" / "projects" / "active"
    if not base.exists():
        return []
    out: list[Item] = []
    for cp in sorted(base.glob("PI-*/sprints/*/stories/*/checkpoint.md")):
        try:
            fm = load_frontmatter(cp)
        except (FrontmatterError, yaml.YAMLError):
            continue
        # Map legacy phase to macro state
        phase = fm.get("phase", "PM_DRAFT")
        legacy_status = fm.get("status", "pending")
        state = _map_legacy_phase_to_state(phase, legacy_status)
        # Derive PI from path: docs/projects/active/PI-12-.../sprints/S1-.../stories/{id}/checkpoint.md
        parts = cp.relative_to(repo).parts
        pi_dir = parts[2] if len(parts) > 2 else "unknown"
        out.append(
            Item(
                id=fm.get("id", cp.parent.name),
                kind="story",
                state=state,
                title=fm.get("id", cp.parent.name),
                tags=[f"legacy:{pi_dir}"],
                last_touched=fm.get("last_modified"),
                extra={
                    "phase": phase,
                    "next_action": fm.get("next_action"),
                    "blocked_by": fm.get("blocked_reason"),
                    "outcome": pi_dir,
                    "audit_iterations": fm.get("audit_iterations", 0),
                    "legacy_layout": True,
                },
            )
        )
    return out


def read_legacy_pm_nico_pis(repo: Path) -> list[Item]:
    """Read docs/pm-nico/pis/active/PI-*/PI.md (legacy paradigm — closes there, NOT migrating in Wave 1)."""
    base = repo / "docs" / "pm-nico" / "pis" / "active"
    if not base.exists():
        return []
    out: list[Item] = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        pi_md = d / "PI.md"
        if not pi_md.exists():
            continue
        # Legacy PI.md format varies — try to extract title from first heading
        text = pi_md.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else d.name
        # Look for state hints in body (rough heuristic — pm-nico uses prose, not frontmatter consistently)
        state = "refining"  # default for legacy active (v4 vocabulary)
        if re.search(r"(?i)\bDONE\b|shipped|cierra|closed", text[:1500]):
            state = "done"
        elif re.search(r"(?i)\bin-progress\b|active\b|S\d+\s+in-progress", text[:1500]):
            state = "developing"
        out.append(
            Item(
                id=d.name,
                kind="legacy-pi",
                state=state,
                title=title,
                tags=["legacy:pm-nico"],
                last_touched=None,
                extra={"path": str(pi_md.relative_to(repo))},
            )
        )
    return out


def _map_legacy_phase_to_state(phase: str, status: str) -> str:  # noqa: PLR0911
    """Map legacy phase strings (PM_DRAFT/PO_SPEC/ARCH_DONE/BUILD_T*/AUDIT_*/DONE) to v4 macro state.

    Order matters: prefix-qualified phases (ARCH_DONE = arch phase done) checked BEFORE
    bare DONE (= entire story done). AUDIT_*_APPROVED → reviewing (Conv 3 in progress).

    Post v4 (Punto 4 2026-05-06): emits 10-state vocabulary directly. Legacy
    artifacts still keyed by old phase strings — this mapper is the bridge.
    """
    if status == "blocked":
        return "parked"
    p = phase.upper()
    # Check phase-prefix-qualified first (most specific)
    if "AUDIT" in p:
        return "reviewing"
    if "BUILD" in p:
        return "developing"
    if "ARCH" in p:
        return "ready"
    if "UX" in p or "DESIGN" in p:
        return "refining"
    if "PO_SPEC" in p or "PM_DRAFT" in p:
        return "refining"
    # Bare DONE / MERGED only matches if no other prefix consumed (whole-story done)
    if p in {"DONE", "MERGED"} or "MERGED_TO" in p:
        return "done"
    return "refining"


def read_capability_rollup(repo: Path) -> list[CapRollup]:
    """Aggregate capability statuses per module (R32 reconciled)."""
    caps_dir = repo / "docs" / "product" / "capabilities"
    if not caps_dir.exists():
        return []
    by_module: dict[str, CapRollup] = {}
    for f in sorted(caps_dir.rglob("*.yaml")):
        try:
            fm = load_frontmatter(f)
        except (FrontmatterError, yaml.YAMLError):
            continue
        module = fm.get("module", f.parent.name)
        rollup = by_module.setdefault(module, CapRollup(module=module))
        status = fm.get("status", "planned")
        if status == "live":
            rollup.live += 1
        elif status == "in-progress":
            rollup.in_progress += 1
        elif status == "deprecated":
            rollup.deprecated += 1
        else:
            rollup.planned += 1
    return sorted(by_module.values(), key=lambda r: r.module)


# ─── Aggregation ──────────────────────────────────────────────────────


def discover_brands(repo: Path) -> list[str]:
    """Return sorted list of brand slugs (dirs with ``config/brand.yaml``).

    Post multibrand reorg 2026-05-15: each brand vertical lives under
    ``{repo}/{brand}/`` with its own ``config/brand.yaml`` marker.
    """
    brands: list[str] = []
    for cfg in sorted(repo.glob("*/config/brand.yaml")):
        brands.append(cfg.parent.parent.name)
    return brands


def aggregate(repo: Path, *, brand: str | None = None) -> dict[str, Any]:
    """Walk all sources for a given scope, return unified backlog dict.

    Scope resolution:
      * ``brand=None``      → root ``{repo}/docs/product/`` (legacy + platform cross-brand)
      * ``brand="vitalia"`` → ``{repo}/vitalia/docs/product/`` (skips legacy readers)
    """
    base = repo / brand if brand else repo

    ideas = read_ideas_pool(base)
    outcomes = read_outcomes(base)
    stories_new = read_active_stories_new(base)
    caps = read_capability_rollup(base)
    releases = read_releases(base)

    # Legacy readers only make sense in root scope (single-brand pre-reorg state).
    # Per-brand scopes never had docs/projects/ or docs/pm-nico/.
    if brand is None:
        stories_legacy = read_legacy_active_stories(repo)
        pis_legacy = read_legacy_pm_nico_pis(repo)
    else:
        stories_legacy = []
        pis_legacy = []

    items = ideas + outcomes + stories_new + stories_legacy + pis_legacy

    # Bucket by state — preserve canonical order for deterministic output
    buckets: dict[str, list[Item]] = {s: [] for s in STATE_ORDER}
    for it in items:
        if it.state in buckets:
            buckets[it.state].append(it)

    # Stale flags
    stale_ideas = []
    for it in buckets["idea"]:
        d = days_since(it.last_touched)
        if d is not None and d > CAPS["idea_stale_days"]:
            stale_ideas.append(it.id)
    stale_refining = []
    for it in buckets["refining"]:
        d = days_since(it.last_touched)
        if d is not None and d > CAPS["refining_stale_days"]:
            stale_refining.append(it.id)
    stale_refined = []
    for it in buckets["refined"]:
        d = days_since(it.last_touched)
        if d is not None and d > CAPS["refined_stale_days"]:
            stale_refined.append(it.id)

    # Cap warnings — only stories + ideas count vs WIP cap.
    # Outcomes (epics) span multiple stories and shouldn't consume WIP slots.
    # Legacy stories tagged `legacy:*` exempt (pre-paradigma v4 forward-only enforcement).
    def _cap_eligible(items_: list[Item]) -> list[Item]:
        """Filter for cap counting: kind=story (not outcome/legacy-pi) AND no legacy:* tag."""
        return [
            i
            for i in items_
            if i.kind == "story" and not any(t.startswith("legacy:") for t in i.tags)
        ]

    warnings: list[str] = []
    if len(_cap_eligible(buckets["refining"])) > CAPS["refining_max"]:
        warnings.append(
            f"refining cap exceeded ({len(_cap_eligible(buckets['refining']))} > {CAPS['refining_max']}, excl. legacy+outcomes)"
        )
    if len(_cap_eligible(buckets["refined"])) > CAPS["refined_max"]:
        warnings.append(
            f"refined cap exceeded ({len(_cap_eligible(buckets['refined']))} > {CAPS['refined_max']}, excl. legacy+outcomes)"
        )
    if len(_cap_eligible(buckets["ready"])) > CAPS["ready_max"]:
        warnings.append(
            f"ready cap exceeded ({len(_cap_eligible(buckets['ready']))} > {CAPS['ready_max']}, excl. legacy+outcomes)"
        )
    if len(_cap_eligible(buckets["developing"])) > CAPS["developing_max"]:
        warnings.append(
            f"developing cap exceeded ({len(_cap_eligible(buckets['developing']))} > {CAPS['developing_max']}, excl. legacy+outcomes)"
        )
    if len(_cap_eligible(buckets["developed"])) > CAPS["developed_max"]:
        warnings.append(
            f"developed cap exceeded ({len(_cap_eligible(buckets['developed']))} > {CAPS['developed_max']}, excl. legacy+outcomes)"
        )
    if len(_cap_eligible(buckets["reviewing"])) > CAPS["reviewing_max"]:
        warnings.append(
            f"reviewing cap exceeded ({len(_cap_eligible(buckets['reviewing']))} > {CAPS['reviewing_max']}, excl. legacy+outcomes)"
        )
    if stale_ideas:
        warnings.append(f"{len(stale_ideas)} stale ideas (>{CAPS['idea_stale_days']}d untouched)")
    if stale_refining:
        warnings.append(f"{len(stale_refining)} stale refining (>{CAPS['refining_stale_days']}d untouched)")
    if stale_refined:
        warnings.append(f"{len(stale_refined)} stale refined (>{CAPS['refined_stale_days']}d untouched)")

    # Release-grouping bucket (schema v2 cement 2026-05-27).
    # Maps release_id → list of story items. Stories without release/null land
    # in "(sin release · legacy)" bucket for backward compat.
    by_release: dict[str, list[Item]] = {r.release_id: [] for r in releases}
    by_release["(sin release · legacy)"] = []
    for it in stories_new:
        rel = it.extra.get("release")
        if rel and rel in by_release:
            by_release[rel].append(it)
        else:
            by_release["(sin release · legacy)"].append(it)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "brand": brand or "platform",
        "caps": CAPS,
        "warnings": warnings,
        "stale_ideas": stale_ideas,
        "stale_refining": stale_refining,
        "stale_refined": stale_refined,
        "buckets": {state: [_item_to_dict(it) for it in items_] for state, items_ in buckets.items()},
        "capabilities": [
            {
                "module": c.module,
                "live": c.live,
                "in_progress": c.in_progress,
                "planned": c.planned,
                "deprecated": c.deprecated,
                "total": c.live + c.in_progress + c.planned + c.deprecated,
            }
            for c in caps
        ],
        # Release schema v2 metadata + grouping. Empty list / empty dict if brand
        # not yet migrated to release schema (backward compat with legacy outcomes).
        "releases": [
            {
                "release_id": r.release_id,
                "name": r.name,
                "status": r.status,
                "order": r.order,
                "target_date": r.target_date,
                "shipped_date": r.shipped_date,
                "declared_stories": r.stories,
            }
            for r in releases
        ],
        "stories_by_release": {
            rel_id: [_item_to_dict(it) for it in items_]
            for rel_id, items_ in by_release.items()
        },
    }


def _item_to_dict(it: Item) -> dict[str, Any]:
    """Item → JSON-friendly dict (for YAML dump)."""
    return {
        "id": it.id,
        "kind": it.kind,
        "state": it.state,
        "title": it.title,
        "tags": it.tags,
        "last_touched": it.last_touched,
        "extra": it.extra,
    }


# ─── Renderers ────────────────────────────────────────────────────────


def render_yaml(backlog: dict[str, Any]) -> str:
    """Pretty YAML dump."""
    header = (
        "# docs/product/BACKLOG.yaml — auto-generated SSoT machine-readable\n"
        "# DO NOT EDIT MANUALLY — modify source artifacts instead.\n"
        "# Regenerate: python scripts/generate_backlog.py\n"
        f"# Generated at: {backlog['generated_at']}\n"
        "\n"
    )
    return header + yaml.safe_dump(backlog, sort_keys=False, allow_unicode=True, width=120)


def render_md(backlog: dict[str, Any]) -> str:  # noqa: PLR0915, C901, PLR0912
    """Human-readable Markdown — Roadmap section + Mermaid kanban + caps snapshot.

    Doc renderer with many branches per section — complexity is intrinsic.
    """
    lines: list[str] = []
    gen = backlog["generated_at"]
    warnings = backlog["warnings"]
    buckets = backlog["buckets"]

    brand_label = backlog.get("brand", "platform")
    lines.append(f"# {brand_label.capitalize()} Backlog (auto-generated)")
    lines.append("")
    lines.append(f"> Generated at: `{gen}`")
    lines.append("> DO NOT EDIT MANUALLY — modify source artifacts.")
    lines.append("> Regenerate: `python scripts/generate_backlog.py`")
    lines.append("")

    if warnings:
        lines.append("## ⚠️ Warnings")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # ─── Roadmap view (v4 — 10 estados) ───────────────────────────────
    lines.append("## 📊 Roadmap view (filtered + curated)")
    lines.append("")
    lines.append(f"### 💡 Ideas ({len(buckets['idea'])})")
    if buckets["idea"]:
        for it in buckets["idea"][:15]:
            kind = f" `[{it['kind']}]`"
            lines.append(f"- {it['id']}{kind}")
        if len(buckets["idea"]) > 15:
            lines.append(f"- _... +{len(buckets['idea']) - 15} more_")
    else:
        lines.append("- _(none)_")
    lines.append("")

    refining_eligible = sum(
        1 for it in buckets["refining"] if it["kind"] == "story" and not any(t.startswith("legacy:") for t in it.get("tags", []))
    )
    lines.append(
        f"### 🔬 Refining ({len(buckets['refining'])} total · {refining_eligible} cap-eligible / cap {CAPS['refining_max']})"
    )
    if buckets["refining"]:
        for it in buckets["refining"]:
            outcome = it["extra"].get("outcome")
            phase = it["extra"].get("phase", "")
            tag = f" — outcome `{outcome}`" if outcome else ""
            phase_str = f" [{phase}]" if phase else ""
            lines.append(f"- **{it['id']}**{tag}{phase_str}")
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append(f"### ✅ Refined — listo para arquitectos ({len(buckets['refined'])} / cap {CAPS['refined_max']})")
    if buckets["refined"]:
        for it in buckets["refined"]:
            outcome = it["extra"].get("outcome")
            tag = f" — outcome `{outcome}`" if outcome else ""
            lines.append(f"- **{it['id']}**{tag}")
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append(f"### 📦 Ready for development ({len(buckets['ready'])} / cap {CAPS['ready_max']})")
    if buckets["ready"]:
        for it in buckets["ready"]:
            outcome = it["extra"].get("outcome")
            tag = f" — outcome `{outcome}`" if outcome else ""
            lines.append(f"- **{it['id']}**{tag}")
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append(f"### 🔨 Developing ({len(buckets['developing'])} / cap {CAPS['developing_max']})")
    if buckets["developing"]:
        for it in buckets["developing"]:
            outcome = it["extra"].get("outcome")
            phase = it["extra"].get("phase", "")
            tag = f" — outcome `{outcome}`" if outcome else ""
            phase_str = f" [{phase}]" if phase else ""
            lines.append(f"- **{it['id']}**{tag}{phase_str}")
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append(
        f"### 🧪 Developed — esperando QA ({len(buckets['developed'])} / cap {CAPS['developed_max']})"
    )
    if buckets["developed"]:
        for it in buckets["developed"]:
            outcome = it["extra"].get("outcome")
            tag = f" — outcome `{outcome}`" if outcome else ""
            lines.append(f"- **{it['id']}**{tag}")
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append(f"### 🔍 Reviewing ({len(buckets['reviewing'])} / cap {CAPS['reviewing_max']})")
    if buckets["reviewing"]:
        for it in buckets["reviewing"]:
            lines.append(f"- {it['id']}")
    else:
        lines.append("- _(none in review)_")
    lines.append("")

    # ─── Done rolling 90d ────────────────────────────────────────────
    done_recent = []
    for it in buckets["done"]:
        d = days_since(it["last_touched"])
        if d is not None and d <= CAPS["done_rolling_days"]:
            done_recent.append(it)
    lines.append(f"### Recently shipped (last {CAPS['done_rolling_days']}d, {len(done_recent)} items)")
    if done_recent:
        for it in done_recent[:10]:
            lines.append(f"- {it['id']} — {it['last_touched']}")
        if len(done_recent) > 10:
            lines.append(f"- _... +{len(done_recent) - 10} more_")
    else:
        lines.append("- _(none recent)_")
    lines.append("")

    lines.append(f"### Parked ({len(buckets['parked'])}) · Dropped ({len(buckets['dropped'])})")
    for it in buckets["parked"]:
        lines.append(f"- 🅿 {it['id']}")
    for it in buckets["dropped"]:
        lines.append(f"- ❌ ~~{it['id']}~~")
    lines.append("")

    # ─── Stories grouped by release (schema v2 cement 2026-05-27) ────
    releases_meta = backlog.get("releases") or []
    by_release_dict = backlog.get("stories_by_release") or {}
    if releases_meta or by_release_dict.get("(sin release · legacy)"):
        lines.append("---")
        lines.append("")
        lines.append("## 🚀 Stories by release (schema v2)")
        lines.append("")
        # Sorted release buckets first (F0..F8 in declared order)
        for r in releases_meta:
            rel_id = r["release_id"]
            stories_in_rel = by_release_dict.get(rel_id, [])
            status_badge = {
                "shipped": "✅ shipped",
                "in-progress": "🔨 in-progress",
                "planned": "📋 planned",
            }.get(r.get("status", "planned"), r.get("status", "planned"))
            date_str = r.get("shipped_date") or r.get("target_date") or "—"
            lines.append(f"### {rel_id} · {r.get('name', rel_id)}")
            lines.append(f"> status: **{status_badge}** · date: `{date_str}` · stories: **{len(stories_in_rel)}**")
            lines.append("")
            if stories_in_rel:
                for it in stories_in_rel:
                    state = it.get("state", "?")
                    phase = (it.get("extra") or {}).get("phase", "")
                    phase_str = f" [{phase}]" if phase else ""
                    lines.append(f"- `{state}` **{it['id']}**{phase_str}")
            else:
                lines.append("- _(no stories yet)_")
            lines.append("")
        # Legacy bucket — stories without release: field (or release: null)
        legacy_stories = by_release_dict.get("(sin release · legacy)") or []
        if legacy_stories:
            lines.append("### (sin release · legacy)")
            lines.append(
                f"> stories sin campo `release:` (pre-schema-v2). Migrar a release "
                f"appropriado via `scripts/migrate_to_release_schema.py`. **{len(legacy_stories)}** items."
            )
            lines.append("")
            for it in legacy_stories:
                state = it.get("state", "?")
                outcome = (it.get("extra") or {}).get("outcome")
                outcome_str = f" — outcome `{outcome}`" if outcome else ""
                lines.append(f"- `{state}` **{it['id']}**{outcome_str}")
            lines.append("")

    # ─── Mermaid kanban ──────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 🔄 Operational view (Mermaid kanban)")
    lines.append("")
    lines.append("```mermaid")
    lines.append("kanban")
    _emit_mermaid_column(lines, "💡 Ideas", buckets["idea"], cap_label=None)
    _emit_mermaid_column(lines, "🔬 Refining", buckets["refining"], cap_label=f"cap {CAPS['refining_max']}", show_cap_eligible=True)
    _emit_mermaid_column(lines, "✅ Refined", buckets["refined"], cap_label=f"cap {CAPS['refined_max']}", show_cap_eligible=True)
    _emit_mermaid_column(lines, "📦 Ready", buckets["ready"], cap_label=f"cap {CAPS['ready_max']}", show_cap_eligible=True)
    _emit_mermaid_column(lines, "🔨 Developing", buckets["developing"], cap_label=f"cap {CAPS['developing_max']}", show_cap_eligible=True)
    _emit_mermaid_column(lines, "🧪 Developed", buckets["developed"], cap_label=f"cap {CAPS['developed_max']}", show_cap_eligible=True)
    _emit_mermaid_column(lines, "🔍 Reviewing", buckets["reviewing"], cap_label=f"cap {CAPS['reviewing_max']}", show_cap_eligible=True)
    _emit_mermaid_column(lines, "✅ Done", done_recent, cap_label=f"{CAPS['done_rolling_days']}d rolling")
    _emit_mermaid_column(lines, "🅿 Parked", buckets["parked"], cap_label=None)
    lines.append("```")
    lines.append("")

    # ─── Capabilities snapshot ────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 📈 Capabilities snapshot")
    lines.append("")
    lines.append("| module | live | in-progress | planned | deprecated | total |")
    lines.append("|---|---|---|---|---|---|")
    for c in backlog["capabilities"]:
        lines.append(
            f"| {c['module']} | {c['live']} | {c['in_progress']} | {c['planned']} | {c['deprecated']} | {c['total']} |"
        )
    totals = {
        "live": sum(c["live"] for c in backlog["capabilities"]),
        "in_progress": sum(c["in_progress"] for c in backlog["capabilities"]),
        "planned": sum(c["planned"] for c in backlog["capabilities"]),
        "deprecated": sum(c["deprecated"] for c in backlog["capabilities"]),
        "total": sum(c["total"] for c in backlog["capabilities"]),
    }
    lines.append(
        f"| **TOTAL** | **{totals['live']}** | **{totals['in_progress']}** | "
        f"**{totals['planned']}** | **{totals['deprecated']}** | **{totals['total']}** |"
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def _cap_eligible_count(items: list[dict[str, Any]]) -> int:
    """Items que cuentan vs WIP cap: kind=story sin tag legacy:* (outcomes excluidos)."""
    return sum(
        1
        for it in items
        if it.get("kind") == "story" and not any(t.startswith("legacy:") for t in it.get("tags", []))
    )


def _emit_mermaid_column(
    lines: list[str],
    title: str,
    items: list[dict[str, Any]],
    cap_label: str | None,
    show_cap_eligible: bool = False,
) -> None:
    """Emit one Mermaid kanban column with up to 10 items + count.

    Si `show_cap_eligible=True`, el header muestra "{cap_eligible}/{total} cap-eligible"
    en vez del total bruto — alineado con la lógica WIP cap (outcomes excluidos).
    """
    if show_cap_eligible and cap_label:
        eligible = _cap_eligible_count(items)
        total = len(items)
        if eligible != total:
            label = f"{title} ({eligible} cap-eligible of {total} / {cap_label})"
        else:
            label = f"{title} ({eligible} / {cap_label})"
    else:
        label = f"{title} ({len(items)}"
        if cap_label:
            label += f" / {cap_label}"
        label += ")"
    lines.append(f"  {label}")
    for it in items[:10]:
        # Mermaid kanban node syntax: id[Title]
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", it["id"])[:30]
        title_short = it["id"][:40].replace("[", "(").replace("]", ")")
        lines.append(f"    {safe_id}[{title_short}]")
    if len(items) > 10:
        lines.append(f"    overflow-{title}[+{len(items) - 10} more]")


# ─── CLI ──────────────────────────────────────────────────────────────


def render_tldr(backlog: dict[str, Any]) -> str:
    """Render dense 5-15 line snapshot for /pm bootstrap (G1).

    Token-cheap alternative to full BACKLOG.md (~150 lines). Skills and
    bootstrap reads consume this instead of full file.
    """
    lines: list[str] = []
    lines.append("# Backlog TLDR (auto-generated)")
    lines.append(f"> Generated at: `{backlog['generated_at']}`")
    lines.append("> Source: scripts/generate_backlog.py — full view: BACKLOG.md")
    lines.append("")

    buckets = backlog["buckets"]
    caps = backlog["caps"]

    def _eligible_count(state: str) -> int:
        return sum(
            1
            for it in buckets.get(state, [])
            if it.get("kind") == "story" and not any(t.startswith("legacy:") for t in it.get("tags", []))
        )

    def _slugs(state: str, n: int = 3) -> str:
        items = buckets.get(state, [])
        if not items:
            return "_(none)_"
        names = [it.get("id", "?") for it in items[:n]]
        more = f" +{len(items) - n}" if len(items) > n else ""
        return ", ".join(names) + more

    rows = [
        ("idea", "Ideas", None),
        ("refining", "Refining", "refining_max"),
        ("refined", "Refined", "refined_max"),
        ("ready", "Ready", "ready_max"),
        ("developing", "Developing", "developing_max"),
        ("developed", "Developed", "developed_max"),
        ("reviewing", "Reviewing", "reviewing_max"),
    ]
    for state, label, cap_key in rows:
        total = len(buckets.get(state, []))
        eligible = _eligible_count(state) if cap_key else total
        cap = caps.get(cap_key) if cap_key else None
        cap_str = f" / cap {cap}" if cap is not None else ""
        warn = " ⚠️" if cap is not None and eligible > cap else ""
        lines.append(f"- **{label}** ({eligible}{cap_str}{warn}): {_slugs(state)}")

    if backlog.get("warnings"):
        lines.append("")
        lines.append(f"⚠ Warnings ({len(backlog['warnings'])}): {'; '.join(backlog['warnings'][:3])}")

    lines.append("")
    lines.append("Detail: read `docs/product/BACKLOG.md` (kanban + roadmap) or `docs/product/stories/{id}/checkpoint.md`.")
    return "\n".join(lines) + "\n"


def _normalize(text: str) -> str:
    """Strip volatile generated_at timestamp for drift comparison."""
    text = re.sub(r"generated_at: '[^']*'", "generated_at: '<NORMALIZED>'", text)
    text = re.sub(r"# Generated at: [^\n]*", "# Generated at: <NORMALIZED>", text)
    text = re.sub(r"> Generated at: `[^`]*`", "> Generated at: `<NORMALIZED>`", text)
    return text


def _process_scope(repo: Path, brand: str | None, *, check_only: bool) -> tuple[bool, list[str]]:
    """Generate (or check) BACKLOG for one scope. Returns (drift, warnings)."""
    base = repo / brand if brand else repo
    base_docs = base / "docs" / "product"

    # Skip if scope has no docs/product/ (brand bootstrapped but not yet documented)
    if not base_docs.exists():
        return False, []

    backlog = aggregate(repo, brand=brand)
    new_yaml = render_yaml(backlog)
    new_md = render_md(backlog)
    new_tldr = render_tldr(backlog)

    yaml_path = base_docs / "BACKLOG.yaml"
    md_path = base_docs / "BACKLOG.md"
    tldr_path = base_docs / "BACKLOG-TLDR.md"

    drift = False
    for path, content in [(yaml_path, new_yaml), (md_path, new_md), (tldr_path, new_tldr)]:
        on_disk = path.read_text(encoding="utf-8") if path.exists() else ""
        if _normalize(on_disk) != _normalize(content):
            drift = True
            if check_only:
                scope_label = brand if brand else "root"
                print(f"DRIFT [{scope_label}]: {path.relative_to(repo)}")  # noqa: T201

    if not check_only and drift:
        yaml_path.write_text(new_yaml, encoding="utf-8")
        md_path.write_text(new_md, encoding="utf-8")
        tldr_path.write_text(new_tldr, encoding="utf-8")
        scope_label = brand if brand else "root"
        print(  # noqa: T201
            f"Wrote [{scope_label}] {yaml_path.relative_to(repo)} + "
            f"{md_path.relative_to(repo)} + {tldr_path.relative_to(repo)}"
        )

    return drift, backlog.get("warnings", [])


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 on diff vs on-disk (CI/hook gate).")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repo root. Default: script's parent.",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--brand",
        type=str,
        default=None,
        help="Brand slug to scope generation (vitalia). "
        "Reads {repo}/{brand}/docs/product/. Default: root docs/product/ (legacy/platform).",
    )
    scope.add_argument(
        "--all-brands",
        action="store_true",
        help="Iterate root + every brand vertical (dirs with config/brand.yaml). "
        "Regenerates each scope's BACKLOG.{yaml,md,TLDR.md} independently.",
    )
    args = parser.parse_args()

    # Build list of scopes to process
    scopes: list[str | None] = []
    if args.all_brands:
        scopes.append(None)  # root
        scopes.extend(discover_brands(args.repo))
    elif args.brand:
        scopes.append(args.brand)
    else:
        scopes.append(None)

    any_drift = False
    all_warnings: list[tuple[str, str]] = []
    for brand_arg in scopes:
        drift, warnings = _process_scope(args.repo, brand_arg, check_only=args.check)
        any_drift = any_drift or drift
        scope_label = brand_arg if brand_arg else "root"
        for w in warnings:
            all_warnings.append((scope_label, w))

    if args.check:
        if any_drift:
            print("\nRun without --check to regenerate.")  # noqa: T201
            return 1
        scope_desc = ", ".join(b if b else "root" for b in scopes)
        print(f"OK — BACKLOG.{{yaml,md,TLDR.md}} fresh. Scope: {scope_desc}.")  # noqa: T201
        return 0

    if all_warnings:
        print(f"WARNINGS ({len(all_warnings)}):")  # noqa: T201
        for scope_label, w in all_warnings:
            print(f"  - [{scope_label}] {w}")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
