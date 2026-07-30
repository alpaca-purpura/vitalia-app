"""Architecture fitness: TS type mirrors match Python dataclass fields.

V-F-ts-1. Verifies 3 mirrored types (EP-6 SidebarRouteDef, EP-10 LandingTemplateDef,
EP-18 WizardStepDef) have field-by-field parity between:
  - Python: luana_core_extension_sdk.models (dataclasses.fields())
  - TypeScript: core/@luana/extension-sdk/src/models.ts (AST parse interface fields)

Conversion: Python snake_case ↔ TS camelCase.

A field missing in either direction is a V-F-ts-1 violation.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

ROOT = Path(__file__).parents[3]
TS_MODELS = ROOT / "core" / "@luana" / "extension-sdk" / "src" / "models.ts"

from luana_core_extension_sdk.models import (  # noqa: E402
    LandingTemplateDef,
    SidebarRouteDef,
    WizardStepDef,
)

_MIRROR_TYPES: list[tuple[str, type]] = [
    ("SidebarRouteDef", SidebarRouteDef),
    ("LandingTemplateDef", LandingTemplateDef),
    ("WizardStepDef", WizardStepDef),
]


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase (Python → TS)."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _parse_ts_interface_fields(ts_source: str, interface_name: str) -> set[str]:
    """Parse field names from a TS interface block (camelCase).

    Uses line-by-line depth tracking to handle TS comments that contain
    `{brand_slug}` style template literals — a naive `[^}]` regex would
    stop at the first `}` inside a comment.

    Handles:
    - `fieldName: type;` (required)
    - `fieldName?: type;` (optional)
    Returns set of camelCase field names.
    """
    lines = ts_source.splitlines()
    in_interface = False
    depth = 0
    fields: set[str] = set()

    for line in lines:
        if not in_interface:
            # Match `interface Name {` or `export interface Name {`
            if re.search(
                rf"(?:export\s+)?interface\s+{re.escape(interface_name)}\s*\{{",
                line,
            ):
                in_interface = True
                depth = line.count("{") - line.count("}")
        else:
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                # End of interface block
                break
            # Match field: `  fieldName:` or `  fieldName?:`
            match = re.match(r"\s+(\w+)\??:", line)
            if match:
                fields.add(match.group(1))

    return fields


def test_ts_models_file_exists() -> None:
    """V-F-ts-1: TS models.ts file must exist."""
    assert TS_MODELS.exists(), (
        f"TS models file not found at {TS_MODELS}.\n"
        "Story 8 T-8 must create core/@luana/extension-sdk/src/models.ts "
        "with 3 mirrored interfaces (SidebarRouteDef, LandingTemplateDef, WizardStepDef)."
    )


def test_ts_mirrors_match_python_fields() -> None:
    """V-F-ts-1: TS interface fields match Python dataclass fields (snake→camel conversion)."""
    ts_source = TS_MODELS.read_text(encoding="utf-8")
    violations: list[str] = []

    for ts_name, py_cls in _MIRROR_TYPES:
        # Python fields → expected camelCase TS names
        py_fields = {f.name for f in dataclasses.fields(py_cls)}
        expected_ts_fields = {_snake_to_camel(f) for f in py_fields}

        # TS fields parsed from interface
        actual_ts_fields = _parse_ts_interface_fields(ts_source, ts_name)

        if not actual_ts_fields:
            violations.append(
                f"  {ts_name}: interface not found in TS models.ts\n    Expected fields: {sorted(expected_ts_fields)}"
            )
            continue

        missing_in_ts = expected_ts_fields - actual_ts_fields
        extra_in_ts = actual_ts_fields - expected_ts_fields

        if missing_in_ts:
            violations.append(
                f"  {ts_name}: Python fields missing in TS:\n"
                + "\n".join(
                    f"    Python: {py_field!r} → TS expected: {_snake_to_camel(py_field)!r}"
                    for py_field in sorted(py_fields)
                    if _snake_to_camel(py_field) in missing_in_ts
                )
            )

        if extra_in_ts:
            violations.append(
                f"  {ts_name}: TS fields without Python counterpart:\n"
                + "\n".join(f"    {f!r}" for f in sorted(extra_in_ts))
            )

    assert not violations, (
        "V-F-ts-1: TS type mirrors diverge from Python dataclasses.\n"
        "Fix: update core/@luana/extension-sdk/src/models.ts to match Python fields.\n\n"
        "Violations:\n" + "\n".join(violations)
    )
