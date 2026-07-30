"""Architecture fitness: copilot registry public API contracts are FROZEN.

Per 03-arch.md §7.3 + D-T1 cement. Story 6 lift moment establishes the
public API surface of 5 copilot registries:

- ToolRegistry (functional API: ROUTE_TOOL_MAP, ALWAYS_AVAILABLE_GROUPS,
  TOOL_GROUPS, get_tools_for_route, get_tools_for_context, get_all_tools,
  ToolNameCollisionError, ToolGroupMeta)
- WorkflowRegistry (functional API: collect_workflows, WorkflowRegistryError)
- ModuleRegistry (functional API: get_module_registry, ModuleDescriptor,
  reset_module_registry_cache)
- ExtractorRegistry (functional API: ExtractionDomainConfig, supported_domains,
  get_extraction_config, ResponseValueKind)
- SuggestionRegistry (functional API: get_default_engine, register_provider)

Golden snapshot: ``_snapshots/copilot_registry_v1.json``. Mismatch FAIL with
diff. Bump (schema_version increment) requires architect ratification —
Story 8 EP-1..EP-5 SDK introduction is the next allowed bump occasion.

V-AG-3 validator.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

SNAPSHOT_PATH = Path(__file__).parent / "_snapshots" / "copilot_registry_v1.json"


def _public_names(mod: Any) -> list[str]:
    return sorted([n for n in dir(mod) if not n.startswith("_")])


def _signature_str(fn: Any) -> str | None:
    try:
        return str(inspect.signature(fn))
    except (TypeError, ValueError):
        return None


def _class_info(cls: type) -> dict[str, Any]:
    info: dict[str, Any] = {
        "name": cls.__name__,
        "bases": [b.__name__ for b in cls.__bases__],
    }
    if is_dataclass(cls):
        info["dataclass_fields"] = sorted([f.name for f in fields(cls)])
    info["methods"] = sorted([m for m in dir(cls) if not m.startswith("_")])
    return info


def _is_own_attr(attr: Any, mod: Any) -> bool:
    """True if attr is defined in mod (not imported from elsewhere)."""
    try:
        return getattr(attr, "__module__", None) == mod.__name__
    except Exception:
        return False


def _module_snapshot(mod: Any) -> dict[str, Any]:
    """Snapshot mod's OWN public surface (exclude imported callables/classes).

    Top-level constants (no __module__) are captured by type-name only —
    deterministic across runs.
    """
    names = _public_names(mod)
    own_public_names: list[str] = []
    functions: dict[str, str | None] = {}
    classes: dict[str, Any] = {}
    constants: dict[str, str] = {}

    for name in names:
        attr = getattr(mod, name)
        if inspect.isclass(attr):
            if _is_own_attr(attr, mod):
                classes[name] = _class_info(attr)
                own_public_names.append(name)
        elif callable(attr):
            if _is_own_attr(attr, mod):
                functions[name] = _signature_str(attr)
                own_public_names.append(name)
        else:
            constants[name] = type(attr).__name__
            own_public_names.append(name)

    return {
        "module": mod.__name__,
        "public_names": sorted(own_public_names),
        "functions": functions,
        "classes": classes,
        "top_level_constants_types": constants,
    }


def _live_snapshot() -> dict[str, Any]:
    """Build live snapshot of all 5 registries — must match golden file."""
    from luana_core_copilot.application.suggestions import registry as sug_reg
    from luana_core_copilot.application.tools import registry as tools_reg
    from luana_core_copilot.application.workflows import registry as wf_reg
    from luana_core_copilot.domain import extraction_domain_registry as ext_reg
    from luana_core_copilot.domain import module_registry as mod_reg

    return {
        "tools": _module_snapshot(tools_reg),
        "workflows": _module_snapshot(wf_reg),
        "module": _module_snapshot(mod_reg),
        "extraction_domain": _module_snapshot(ext_reg),
        "suggestions": _module_snapshot(sug_reg),
    }


def _format_diff(golden: dict, live: dict, key_path: str) -> list[str]:
    """Generate a human-readable diff of golden vs live snapshot sections."""
    diff: list[str] = []
    golden_keys = set(golden.keys()) if isinstance(golden, dict) else set()
    live_keys = set(live.keys()) if isinstance(live, dict) else set()
    added = live_keys - golden_keys
    removed = golden_keys - live_keys
    common = golden_keys & live_keys
    if added:
        diff.append(f"  {key_path}: ADDED keys = {sorted(added)}")
    if removed:
        diff.append(f"  {key_path}: REMOVED keys = {sorted(removed)}")
    for k in sorted(common):
        if golden[k] != live[k]:
            if isinstance(golden[k], dict) and isinstance(live[k], dict):
                diff.extend(_format_diff(golden[k], live[k], f"{key_path}.{k}"))
            else:
                diff.append(f"  {key_path}.{k}: {golden[k]!r} → {live[k]!r}")
    return diff


def test_snapshot_file_exists():
    """Golden snapshot file must exist (generated by _generate script)."""
    assert SNAPSHOT_PATH.exists(), (
        f"Golden snapshot missing: {SNAPSHOT_PATH}. "
        "Run `cd ~/luana-platform && uv run python "
        "core/tests/architecture/_snapshots/_generate_copilot_registry_snapshot.py` "
        "to regenerate (architect ratification required)."
    )


def test_registry_contracts_stable():
    """Live registries must match golden snapshot ``copilot_registry_v1.json``.

    If this test fails:
      1. Inspect the diff (printed in assertion message).
      2. If change is INTENTIONAL + architect-ratified (Story 8 EP-1..EP-5
         or similar bump), regenerate via the _generate script.
      3. If change is UNINTENTIONAL, revert the offending modification.
    """
    golden_data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    golden_registries = golden_data["registries"]
    live_registries = _live_snapshot()

    diff = _format_diff(golden_registries, live_registries, "registries")

    assert not diff, (
        "Copilot registry contract drift detected (V-AG-3 D-T1 cement). "
        "Public API surface MUST stay byte-stable until architect-ratified bump "
        "(Story 8 EP-1..EP-5 SDK introduction or later).\n\n"
        + "\n".join(diff)
        + "\n\nIf intentional, regenerate via:\n"
        "  cd ~/luana-platform && uv run python "
        "core/tests/architecture/_snapshots/_generate_copilot_registry_snapshot.py"
    )
