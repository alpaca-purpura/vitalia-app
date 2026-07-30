#!/usr/bin/env python3
"""
migrate_capability_ledger.py — Phase 3.4 capability ledger migration (one-shot, idempotent).

Migrates {brand}/docs/product/capabilities/{module}/{cap}.yaml to schema v2:
  - Adds frontmatter fields: created_in_story, created_date, last_modified,
    parent_cap, derives_capabilities[]
  - Converts atomics: flat list[str] → list[{label, added_in_story, added_date}].
    If atomics absent, adds atomics: [] + WARN.
  - Initializes change_log[] (1 entry seeded with story_introduced data).
  - For caps with extends_capability — parent cap gains derives_capabilities[child].
  - Idempotent: presence of `change_log:` field marks file as already migrated.

Refs:
  - docs/process/capability-protocol.md § cap schema (the ledger v2 model this migrates to)

Usage:
  python3 scripts/migrate_capability_ledger.py vitalia [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# YAML frontmatter / pure-yaml helpers
# ---------------------------------------------------------------------------


def parse_cap_file(path: Path) -> tuple[dict[str, Any], list[str], list[str], bool]:
    """
    Parse a capability YAML.

    Returns: (parsed_dict, frontmatter_lines, body_lines, is_markdown_style).
      - markdown_style=True  → file wrapped in --- ... --- with markdown body below.
      - markdown_style=False → pure YAML file (no body).

    frontmatter_lines does NOT include surrounding --- markers.
    """
    raw = path.read_text(encoding="utf-8")
    raw_lines = raw.splitlines(keepends=False)

    if raw_lines and raw_lines[0].strip().startswith("---"):
        # markdown frontmatter style
        end_idx = None
        for i in range(1, len(raw_lines)):
            if raw_lines[i].strip() == "---":
                end_idx = i
                break
        if end_idx is None:
            return {}, raw_lines[1:], [], True
        fm_lines = raw_lines[1:end_idx]
        body_lines = raw_lines[end_idx + 1 :]
        try:
            parsed = yaml.safe_load("\n".join(fm_lines)) or {}
        except yaml.YAMLError:
            parsed = {}
        return parsed if isinstance(parsed, dict) else {}, fm_lines, body_lines, True

    # Pure YAML
    try:
        parsed = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}, raw_lines, [], False


def write_cap_file(
    path: Path,
    fm_lines: list[str],
    body_lines: list[str],
    is_markdown_style: bool,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    if is_markdown_style:
        parts = ["---"] + fm_lines + ["---"] + body_lines
    else:
        parts = list(fm_lines)
    content = "\n".join(parts)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Frontmatter upsert + atomics conversion
# ---------------------------------------------------------------------------


def top_level_keys(fm_lines: list[str]) -> set[str]:
    keys = set()
    for line in fm_lines:
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:", line)
        if m:
            keys.add(m.group(1))
    return keys


def append_v2_fields(
    fm_lines: list[str],
    new_fields: list[tuple[str, str, str]],
) -> tuple[list[str], list[str]]:
    """
    Append (key, value, comment) tuples to frontmatter (skip duplicates).

    Returns (new_fm_lines, added_keys).
    """
    existing = top_level_keys(fm_lines)
    additions: list[str] = []
    added_keys: list[str] = []
    for key, value, comment in new_fields:
        if key in existing:
            continue
        comment_part = f"   # {comment}" if comment else ""
        additions.append(f"{key}: {value}{comment_part}")
        added_keys.append(key)

    if not additions:
        return fm_lines, []

    result = list(fm_lines)
    while result and result[-1].strip() == "":
        result.pop()
    result.append("")
    result.append("# Capability ledger v2 (cement 2026-05-27)")
    result.extend(additions)
    return result, added_keys


def convert_atomics_to_v2(
    fm_lines: list[str],
    parsed: dict[str, Any],
    story_introduced: str,
    date_introduced: str,
) -> tuple[list[str], bool, str | None]:
    """
    Convert atomics field if present as flat list[str].
    If absent, append atomics: [] + return warning.

    Returns (new_fm_lines, was_converted, warning).
    """
    atomics_value = parsed.get("atomics")
    if atomics_value is None:
        # Absent — append atomics: [] + WARN
        result, _ = append_v2_fields(
            fm_lines,
            [("atomics", "[]", "v2 cement · empty initial · Chris populate manually")],
        )
        return result, False, "atomics field missing · initialized to [] · Chris ratify"

    # Already a list — check if already v2 (list of dicts) or v1 (list of strings)
    if isinstance(atomics_value, list):
        if not atomics_value:
            return fm_lines, False, None  # already empty list, no action
        if all(isinstance(item, dict) for item in atomics_value):
            return fm_lines, False, None  # already v2 format
        if all(isinstance(item, str) for item in atomics_value):
            # Convert v1 → v2
            return _convert_atomics_inplace(
                fm_lines, atomics_value, story_introduced, date_introduced
            )

    return fm_lines, False, f"atomics has unexpected shape ({type(atomics_value).__name__})"


def _convert_atomics_inplace(
    fm_lines: list[str],
    flat_atomics: list[str],
    story: str,
    date: str,
) -> tuple[list[str], bool, str | None]:
    """Find atomics: block in fm_lines and rewrite it to v2 shape."""
    new_lines: list[str] = []
    i = 0
    converted = False
    while i < len(fm_lines):
        line = fm_lines[i]
        m = re.match(r"^atomics\s*:\s*(.*)$", line)
        if m and not converted:
            # Replace this line + consume any subsequent indented "- " lines belonging to atomics
            new_lines.append("atomics:   # v2 cement 2026-05-27 — converted from flat list")
            for label in flat_atomics:
                # quote the label safely
                safe_label = label.replace('"', '\\"')
                new_lines.append(f'  - label: "{safe_label}"')
                new_lines.append(f"    added_in_story: {story}")
                new_lines.append(f"    added_date: {date}")
            # Skip following lines that were part of the original atomics list
            j = i + 1
            while j < len(fm_lines):
                nxt = fm_lines[j]
                if re.match(r"^\s+-\s", nxt) or nxt.strip() == "":
                    j += 1
                    # stop if hits next top-level key
                    if j < len(fm_lines) and re.match(r"^[a-zA-Z_]", fm_lines[j]):
                        break
                else:
                    break
            i = j
            converted = True
            continue
        new_lines.append(line)
        i += 1

    if converted:
        return new_lines, True, None
    return fm_lines, False, None


def append_change_log(
    fm_lines: list[str],
    parsed: dict[str, Any],
    story: str,
    date: str,
    atomics_labels: list[str],
) -> list[str]:
    """Append a seed change_log entry to frontmatter."""
    if "change_log" in top_level_keys(fm_lines):
        return fm_lines  # already present

    result = list(fm_lines)
    while result and result[-1].strip() == "":
        result.pop()
    result.append("")
    result.append("# Capability change log v2 (cement 2026-05-27)")
    result.append("change_log:")
    result.append(f"  - story_id: {story}")
    result.append(f"    date: {date}")
    result.append("    type: new")
    result.append('    summary: "Implementación inicial · migración legacy a schema v2"')
    if atomics_labels:
        labels_yaml = ", ".join(f'"{lbl}"' for lbl in atomics_labels)
        result.append(f"    atomics_added: [{labels_yaml}]")
    else:
        result.append("    atomics_added: []")
    result.append("    atomics_modified: []")
    result.append("    merge_sha: null")
    result.append("    status: done")
    return result


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------


@dataclass
class CapMigrationReport:
    brand: str
    dry_run: bool
    timestamp: str
    caps_migrated: list[str] = field(default_factory=list)
    caps_skipped_already_migrated: list[str] = field(default_factory=list)
    atomics_converted: list[str] = field(default_factory=list)
    derives_back_populated: list[dict[str, str]] = field(default_factory=list)
    orphan_parents: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def list_caps(brand_root: Path) -> list[Path]:
    caps_dir = brand_root / "docs" / "product" / "capabilities"
    if not caps_dir.exists():
        return []
    return sorted(caps_dir.rglob("*.yaml"))


def slug_for_cap(parsed: dict[str, Any], path: Path) -> str:
    return parsed.get("slug") or path.stem


def migrate_one_cap(
    path: Path,
    dry_run: bool,
    report: CapMigrationReport,
) -> tuple[dict[str, Any], list[str], list[str], bool]:
    """
    Migrate one cap file.

    Returns (parsed_dict_post_migration, fm_lines, body_lines, is_markdown_style).
    """
    parsed, fm_lines, body_lines, mdstyle = parse_cap_file(path)
    cap_slug = slug_for_cap(parsed, path)

    # Idempotency check
    if "change_log" in parsed:
        report.caps_skipped_already_migrated.append(cap_slug)
        return parsed, fm_lines, body_lines, mdstyle

    story_intro = parsed.get("story_introduced") or "unknown-legacy"
    date_intro = parsed.get("date_introduced") or "2026-05-15"
    if isinstance(date_intro, datetime):
        date_intro = date_intro.strftime("%Y-%m-%d")
    date_intro = str(date_intro)

    date_updated = parsed.get("date_updated") or date_intro
    if isinstance(date_updated, datetime):
        date_updated = date_updated.strftime("%Y-%m-%d")
    date_updated = str(date_updated)

    parent_cap = parsed.get("extends_capability")

    # 1. Append v2 frontmatter fields
    v2_fields = [
        ("created_in_story", str(story_intro), "v2 cement · mirror of story_introduced"),
        ("created_date", date_intro, "v2 cement · mirror of date_introduced"),
        ("last_modified", date_updated, "v2 cement · mirror of date_updated or date_introduced"),
        (
            "parent_cap",
            str(parent_cap) if parent_cap else "null",
            "v2 cement · mirror of extends_capability",
        ),
        ("derives_capabilities", "[]", "v2 cement · initial empty list"),
    ]
    fm_lines, added = append_v2_fields(fm_lines, v2_fields)

    # 2. Convert atomics (or seed empty)
    fm_lines, atomics_converted, atomics_warn = convert_atomics_to_v2(
        fm_lines, parsed, str(story_intro), date_intro
    )
    if atomics_converted:
        report.atomics_converted.append(cap_slug)
    if atomics_warn:
        report.warnings.append({"cap_slug": cap_slug, "issue": atomics_warn})

    # 3. Append change_log[] seed entry
    flat_atomics = parsed.get("atomics") if isinstance(parsed.get("atomics"), list) else []
    atomics_labels = [a for a in flat_atomics if isinstance(a, str)]
    fm_lines = append_change_log(fm_lines, parsed, str(story_intro), date_intro, atomics_labels)

    # 4. Persist
    write_cap_file(path, fm_lines, body_lines, mdstyle, dry_run)
    report.caps_migrated.append(cap_slug)

    # Re-parse to return updated parsed dict for downstream derives back-fill
    try:
        if mdstyle:
            new_parsed = yaml.safe_load("\n".join(fm_lines)) or {}
        else:
            new_parsed = yaml.safe_load("\n".join(fm_lines)) or {}
        if not isinstance(new_parsed, dict):
            new_parsed = parsed
    except yaml.YAMLError:
        new_parsed = parsed
    return new_parsed, fm_lines, body_lines, mdstyle


def back_populate_derives(
    caps_with_parent: list[tuple[Path, str, str, bool, list[str], list[str]]],
    cap_path_by_slug: dict[str, Path],
    cap_id_to_slug: dict[str, str],
    dry_run: bool,
    report: CapMigrationReport,
) -> None:
    """
    For each cap with parent_cap set, append child to parent's derives_capabilities[].

    caps_with_parent: list of tuples
      (parent_id_or_slug, child_slug, child_path_str, mdstyle, fm_lines_unused, body_unused)
    """
    for parent_ref, child_slug, _, _, _, _ in caps_with_parent:
        # parent_ref may be a capability_id (e.g. vitalia-brand-studio-medical-sections)
        # try slug match first, then id match
        parent_path = cap_path_by_slug.get(parent_ref)
        if not parent_path:
            # try id mapping
            slug_via_id = cap_id_to_slug.get(parent_ref)
            if slug_via_id:
                parent_path = cap_path_by_slug.get(slug_via_id)

        if not parent_path or not parent_path.exists():
            report.orphan_parents.append(
                {"child_slug": child_slug, "parent_ref": parent_ref, "issue": "parent cap not found"}
            )
            continue

        parsed, fm_lines, body_lines, mdstyle = parse_cap_file(parent_path)
        # Read current derives list
        derives = parsed.get("derives_capabilities")
        if not isinstance(derives, list):
            derives = []
        if child_slug in derives:
            continue

        # Rewrite the derives_capabilities line in fm_lines
        new_fm: list[str] = []
        updated = False
        for line in fm_lines:
            if re.match(r"^derives_capabilities\s*:", line):
                # Single-line list rewrite
                existing = derives + [child_slug]
                quoted = ", ".join(existing)
                new_fm.append(f"derives_capabilities: [{quoted}]   # v2 cement · back-populated")
                updated = True
            else:
                new_fm.append(line)

        if not updated:
            # No derives field present (perhaps not yet migrated) — append
            new_fm = list(fm_lines)
            while new_fm and new_fm[-1].strip() == "":
                new_fm.pop()
            new_fm.append("")
            new_fm.append("# Capability derives v2 back-populated (cement 2026-05-27)")
            new_fm.append(f"derives_capabilities: [{child_slug}]")

        write_cap_file(parent_path, new_fm, body_lines, mdstyle, dry_run)
        report.derives_back_populated.append(
            {"parent": parent_ref, "child": child_slug}
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate capability ledger to schema v2 (Phase 3.4)."
    )
    parser.add_argument("brand_positional", nargs="?", default=None)
    parser.add_argument(
        "--brand",
        dest="brand_flag",
        default=None,
        help="Brand slug (also accepted as first positional arg). Default: vitalia.",
    )
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()
    args.brand = args.brand_positional or args.brand_flag or "vitalia"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("migrate-cap-ledger")

    try:
        ws_root = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            ).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        ws_root = Path.cwd()

    brand_root = ws_root / args.brand
    if not brand_root.exists():
        log.error("Brand root not found: %s", brand_root)
        return 1

    now = datetime.now()
    report = CapMigrationReport(
        brand=args.brand,
        dry_run=args.dry_run,
        timestamp=now.isoformat(),
    )

    log.info(
        "Cap ledger migration · brand=%s dry_run=%s ws=%s",
        args.brand,
        args.dry_run,
        ws_root,
    )

    caps = list_caps(brand_root)
    log.info("Found %d cap YAMLs", len(caps))

    # 1. First pass: migrate each cap, collect parent_cap references
    cap_path_by_slug: dict[str, Path] = {}
    cap_id_to_slug: dict[str, str] = {}
    parent_refs: list[tuple[Path, str, str, bool, list[str], list[str]]] = []

    for cap_path in caps:
        try:
            parsed_pre, _, _, _ = parse_cap_file(cap_path)
        except Exception as exc:
            report.warnings.append(
                {"cap_slug": cap_path.stem, "issue": f"parse failed: {exc}"}
            )
            continue
        slug = slug_for_cap(parsed_pre, cap_path)
        cap_path_by_slug[slug] = cap_path
        cap_id = parsed_pre.get("capability_id")
        if cap_id:
            cap_id_to_slug[str(cap_id)] = slug

    for cap_path in caps:
        try:
            parsed_post, fm_lines, body_lines, mdstyle = migrate_one_cap(
                cap_path, args.dry_run, report
            )
        except Exception as exc:
            report.warnings.append(
                {"cap_slug": cap_path.stem, "issue": f"migration failed: {exc}"}
            )
            continue

        parent_cap = parsed_post.get("parent_cap") or parsed_post.get("extends_capability")
        if parent_cap and parent_cap != "null":
            slug = slug_for_cap(parsed_post, cap_path)
            parent_refs.append(
                (cap_path, str(parent_cap), slug, mdstyle, fm_lines, body_lines)
            )

    # 2. Back-populate derives_capabilities in parent caps
    # parent_refs is (path, parent_ref, child_slug, ...)
    back_populate_input: list[tuple[Path, str, str, bool, list[str], list[str]]] = [
        (parent_ref, child_slug, str(child_path), mdstyle, fm, body)
        for (child_path, parent_ref, child_slug, mdstyle, fm, body) in parent_refs
    ]
    back_populate_derives(
        back_populate_input, cap_path_by_slug, cap_id_to_slug, args.dry_run, report
    )

    # 3. Write report
    report_path = ws_root / "scripts" / f"migrate-capability-ledger-report-{now.strftime('%Y-%m-%d')}.json"
    report_data = {
        "brand": report.brand,
        "dry_run": report.dry_run,
        "timestamp": report.timestamp,
        "caps_total": len(caps),
        "caps_migrated": report.caps_migrated,
        "caps_skipped_already_migrated": report.caps_skipped_already_migrated,
        "atomics_converted": report.atomics_converted,
        "derives_back_populated": report.derives_back_populated,
        "orphan_parents": report.orphan_parents,
        "warnings": report.warnings,
    }
    if not args.dry_run:
        report_path.write_text(
            json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print("=" * 72)
    print(f"Capability ledger migration · brand={report.brand} dry_run={report.dry_run}")
    print("=" * 72)
    print(f"Total caps                 : {len(caps)}")
    print(f"Migrated                   : {len(report.caps_migrated)}")
    print(f"Already v2 (skipped)       : {len(report.caps_skipped_already_migrated)}")
    print(f"Atomics flat→v2 conversions: {len(report.atomics_converted)}")
    print(f"Derives back-populated     : {len(report.derives_back_populated)}")
    print(f"Orphan parents             : {len(report.orphan_parents)}")
    print(f"Warnings                   : {len(report.warnings)}")
    if report.warnings and len(report.warnings) <= 20:
        for w in report.warnings:
            print(f"  WARN · {w.get('cap_slug', '?')} · {w['issue']}")
    elif report.warnings:
        print(f"  (showing first 5 of {len(report.warnings)})")
        for w in report.warnings[:5]:
            print(f"  WARN · {w.get('cap_slug', '?')} · {w['issue']}")
    if report.orphan_parents:
        for o in report.orphan_parents[:10]:
            print(f"  ORPHAN · child={o['child_slug']} parent_ref={o['parent_ref']}")
    print("=" * 72)
    if not args.dry_run:
        print(f"Report JSON: {report_path}")
    else:
        print("DRY RUN — no filesystem mutations performed.")
    return 0


# ---------------------------------------------------------------------------
# Inline tests
# ---------------------------------------------------------------------------


def _run_tests() -> None:
    # append_v2_fields idempotent
    fm = ["capability_id: x", "module: brand"]
    new, added = append_v2_fields(fm, [("parent_cap", "null", "test")])
    assert "parent_cap" in added
    new2, added2 = append_v2_fields(new, [("parent_cap", "null", "test")])
    assert added2 == []
    # change_log idempotent
    new3 = append_change_log(new, {}, "story-x", "2026-05-27", ["a", "b"])
    assert any("change_log:" in line for line in new3)
    new4 = append_change_log(new3, {}, "story-x", "2026-05-27", ["a"])
    # second call should not duplicate
    count = sum(1 for line in new4 if line == "change_log:")
    assert count == 1, f"change_log idempotency broken count={count}"
    # atomics conversion (flat list)
    fm_with_atomics = [
        "slug: lisa-marca",
        "atomics:",
        "  - Vista calendario",
        "  - Drag-to-reschedule",
        "module: brand",
    ]
    parsed = {"atomics": ["Vista calendario", "Drag-to-reschedule"]}
    new_fm, conv, warn = convert_atomics_to_v2(fm_with_atomics, parsed, "story-x", "2026-05-27")
    assert conv is True
    assert any("- label:" in line for line in new_fm)
    # absent atomics → warning
    parsed2 = {"slug": "test"}
    new_fm2, conv2, warn2 = convert_atomics_to_v2(["slug: test"], parsed2, "story-x", "2026-05-27")
    assert warn2 is not None
    print("✓ Inline tests passed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        _run_tests()
        sys.exit(0)
    sys.exit(main())
