"""One-off script to generate the copilot registry contract golden snapshot.

Story 6 T-20 — D-T1 cement. Captures the public API surface of all 5
copilot registries at lift moment. Story 8 EP-1..EP-5 (Extension SDK
formalization) is the next allowed bump occasion.

Usage:
    cd $WS && uv run python \\
        core/tests/architecture/_snapshots/_generate_copilot_registry_snapshot.py

Output: ``core/tests/architecture/_snapshots/copilot_registry_v1.json``

Re-run only when:
- Story 8 EP-1..EP-5 SDK introduction (architect-ratified bump)
- New registry added (NOT modification of existing public API)
"""

from __future__ import annotations

import inspect
import json
import os
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

# Mirror tests/architecture/conftest.py env defaults so importable
_ENV_DEFAULTS = {
    "LOG_LEVEL": "DEBUG",
    "DOMAIN_NAME": "localhost",
    "TRAEFIK_NETWORK": "test_network",
    "API_SECRET_KEY": "ci-test-secret-key-not-for-prod",
    "WHATSAPP_API_TOKEN": "ci-dummy-token",
    "WHATSAPP_PHONE_NUMBER_ID": "000000000",
    "WHATSAPP_VERIFY_TOKEN": "ci-verify-token",
    "OPENAI_API_KEY": "sk-ci-dummy-key",
    "REDIS_URL": "redis://localhost:6379/0",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "POSTGRES_DB": "test_db",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "API_URL": "http://localhost:8000",
    "DASHBOARD_DOMAIN": "http://localhost:3000",
    "PROMPT_SOURCE": "file",
    "AI_PROVIDER": "openai",
    "AI_MODEL_NANO": "gpt-4o-mini",
    "AI_MODEL_FAST": "deepseek-v4-flash",
    "AI_MODEL_REASONING": "deepseek-v4-pro",
    "AI_MODEL_AGENT": "kimi-k2.6",
    "AI_MODEL_VISION": "gpt-4o",
    "AI_MODEL_EMBEDDING": "text-embedding-3-large",
    "AI_PROVIDER_NANO": "openai",
    "AI_PROVIDER_FAST": "deepseek",
    "AI_PROVIDER_REASONING": "deepseek",
    "AI_PROVIDER_AGENT": "kimi",
    "AI_PROVIDER_VISION": "openai",
    "AI_PROVIDER_EMBEDDING": "openai",
    "KIMI_API_KEY": "ci-dummy-key",
    "DEEPSEEK_API_KEY": "ci-dummy-key",
    "DASHSCOPE_API_KEY": "ci-dummy-key",
}
for _k, _v in _ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)


def public_names(mod: Any) -> list[str]:
    return sorted([n for n in dir(mod) if not n.startswith("_")])


def signature_str(fn: Any) -> str | None:
    try:
        return str(inspect.signature(fn))
    except (TypeError, ValueError):
        return None


def class_info(cls: type) -> dict[str, Any]:
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


def module_snapshot(mod: Any) -> dict[str, Any]:
    """Snapshot mod's OWN public surface (exclude imported callables/classes).

    Top-level constants (no __module__) are still captured by type-name only.
    """
    names = public_names(mod)
    own_public_names: list[str] = []
    functions: dict[str, str | None] = {}
    classes: dict[str, Any] = {}
    constants: dict[str, str] = {}

    for name in names:
        attr = getattr(mod, name)
        if inspect.isclass(attr):
            if _is_own_attr(attr, mod):
                classes[name] = class_info(attr)
                own_public_names.append(name)
        elif callable(attr):
            if _is_own_attr(attr, mod):
                functions[name] = signature_str(attr)
                own_public_names.append(name)
        else:
            # Top-level constants — keep type name only (deterministic)
            constants[name] = type(attr).__name__
            own_public_names.append(name)

    return {
        "module": mod.__name__,
        "public_names": sorted(own_public_names),
        "functions": functions,
        "classes": classes,
        "top_level_constants_types": constants,
    }


def main() -> None:
    # Tools registry
    # Suggestions registry
    from luana_core_copilot.application.suggestions import registry as sug_reg
    from luana_core_copilot.application.tools import registry as tools_reg

    # Workflows registry
    from luana_core_copilot.application.workflows import registry as wf_reg

    # Extraction domain registry
    from luana_core_copilot.domain import extraction_domain_registry as ext_reg

    # Module registry
    from luana_core_copilot.domain import module_registry as mod_reg

    snapshot = {
        "schema_version": 1,
        "story": "luana-copilot-engine",
        "ticket": "T-20",
        "rationale": (
            "D-T1 registry contracts FROZEN at Story 6 lift moment. "
            "Story 8 EP-1..EP-5 SDK introduction is the next allowed bump occasion."
        ),
        "registries": {
            "tools": module_snapshot(tools_reg),
            "workflows": module_snapshot(wf_reg),
            "module": module_snapshot(mod_reg),
            "extraction_domain": module_snapshot(ext_reg),
            "suggestions": module_snapshot(sug_reg),
        },
    }

    out_path = Path(__file__).parent / "copilot_registry_v1.json"
    out_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
