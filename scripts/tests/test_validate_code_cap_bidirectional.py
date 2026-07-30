"""Tests for scripts/validate_code_cap_bidirectional.py (cement 2026-05-28).

Atomics killed 2026-05-28 — cross_check_1 (atomics→headers) and cross_check_2
(headers→atomics) were removed. Only cross_check_3 (scenarios e2e_test paths)
and cross_check_4 (access roles ↔ decorators) remain.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


def _load_module():
    scripts_dir = Path(__file__).parent.parent
    spec = importlib.util.spec_from_file_location(
        "validate_code_cap_bidirectional",
        scripts_dir / "validate_code_cap_bidirectional.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Helper writers
# ---------------------------------------------------------------------------

_CAP_TEMPLATE = """\
---
{yaml_content}
---

# Body
"""


def _write_cap(caps_root: Path, module: str, slug: str, data: dict) -> Path:
    module_dir = caps_root / module
    module_dir.mkdir(parents=True, exist_ok=True)
    path = module_dir / f"{slug}.yaml"
    yaml_text = yaml.dump(data, allow_unicode=True, default_flow_style=False)
    path.write_text(_CAP_TEMPLATE.format(yaml_content=yaml_text), encoding="utf-8")
    return path


def _write_code(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _setup(tmp_path: Path, brand: str = "vitalia") -> tuple[Path, Path, Path, Path]:
    """Returns (caps_root, be_root, fe_root, e2e_root)."""
    caps_root = tmp_path / brand / "docs" / "product" / "capabilities"
    be_root = tmp_path / brand / "backend" / "src"
    fe_root = tmp_path / brand / "frontend" / "src"
    e2e_root = tmp_path / brand / "frontend" / "e2e"
    caps_root.mkdir(parents=True, exist_ok=True)
    be_root.mkdir(parents=True, exist_ok=True)
    fe_root.mkdir(parents=True, exist_ok=True)
    e2e_root.mkdir(parents=True, exist_ok=True)
    return caps_root, be_root, fe_root, e2e_root


def _write_code_index(
    tmp_path: Path,
    brand: str,
    cap_to_files: dict[str, list[str]],
    shared_files: list[str] | None = None,
    resolved_cap_to_files: dict[str, list[str]] | None = None,
) -> None:
    """Write a minimal _code-index.json so cross_check_4 can resolve files.

    HB-59: optional `shared_files` (god-files `# cap: __shared__`) + `resolved_cap_to_files`
    (canonical cap_id keyed) so tests can exercise the resolver + per-endpoint __shared__ scan.
    """
    import json

    idx_path = tmp_path / brand / "docs" / "product" / "capabilities" / "_code-index.json"
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict = {"cap_to_files": cap_to_files}
    if shared_files is not None:
        payload["shared_files"] = shared_files
    if resolved_cap_to_files is not None:
        payload["resolved_cap_to_files"] = resolved_cap_to_files
    idx_path.write_text(json.dumps(payload), encoding="utf-8")


# ---------------------------------------------------------------------------
# load_capabilities
# ---------------------------------------------------------------------------


def test_load_capabilities(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(caps_root, "scheduling", "valeria-agenda", {"slug": "valeria-agenda"})
    caps = mod.load_capabilities("vitalia", tmp_path)
    assert "scheduling.valeria-agenda" in caps


# ---------------------------------------------------------------------------
# Cross-check 3 — Scenarios e2e_test path existence
# ---------------------------------------------------------------------------


def test_cross_check_3_pass(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, e2e_root = _setup(tmp_path)

    spec = e2e_root / "agenda.spec.ts"
    _write_code(spec, "import { test } from '@playwright/test';\ntest('foo', async () => {});\n")

    cap_data = {
        "slug": "valeria-agenda",
        "scenarios": [{"id": "doctor-ve-agenda", "e2e_test": "vitalia/frontend/e2e/agenda.spec.ts"}],
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)
    assert result["total"] == 1
    assert result["pass"] == 1
    assert result["drift"] == 0


def test_cross_check_3_missing_file(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)

    cap_data = {
        "slug": "valeria-agenda",
        "scenarios": [{"id": "doctor-ve-agenda", "e2e_test": "vitalia/frontend/e2e/missing.spec.ts"}],
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)
    assert result["drift"] == 1
    assert result["details"][0]["status"] == "missing_file"


def test_cross_check_3_no_test_pattern(tmp_path: Path):
    """File exists but has no `test(` or `test.describe(`."""
    mod = _load_module()
    caps_root, _, _, e2e_root = _setup(tmp_path)

    spec = e2e_root / "not-a-test.spec.ts"
    _write_code(spec, "// Just some utility code\nexport const x = 1;\n")

    cap_data = {
        "slug": "valeria-agenda",
        "scenarios": [{"id": "doctor-ve-agenda", "e2e_test": "vitalia/frontend/e2e/not-a-test.spec.ts"}],
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)
    assert result["drift"] == 1
    assert result["details"][0]["status"] == "no_test_pattern"


def test_cross_check_3_null_e2e_skips(tmp_path: Path):
    """Scenarios with e2e_test: null should not be counted."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)

    cap_data = {
        "slug": "valeria-agenda",
        "scenarios": [
            {"id": "x", "e2e_test": None},
            {"id": "y", "e2e_test": None},
        ],
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)
    assert result["total"] == 0


# ---------------------------------------------------------------------------
# Cross-check 4 — Access roles ↔ decorators
# ---------------------------------------------------------------------------


def test_cross_check_4_pass_roles_match(tmp_path: Path):
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root / "api.py"
    _write_code(
        py_file,
        "# cap: scheduling.valeria-agenda\n# story-origin: TBD\n"
        "@require_phi_access(roles=['doctor', 'admin_clinic'])\n"
        "def get_agenda(): pass\n",
    )
    _write_code_index(tmp_path, "vitalia", {"scheduling.valeria-agenda": ["vitalia/backend/src/api.py"]})

    cap_data = {
        "slug": "valeria-agenda",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/agenda",
                    "requires_role": ["doctor", "admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["pass"] == 1


def test_cross_check_4_drift_no_enforcement(tmp_path: Path):
    """API entry with roles but NO enforcement mechanism in code → drift."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root / "events.py"
    _write_code(
        py_file,
        "# cap: compliance.hipaa-lite-defensive-stack\n# story-origin: TBD\ndef emit_event(): pass\n",  # no gate at all
    )
    _write_code_index(
        tmp_path,
        "vitalia",
        {"compliance.hipaa-lite-defensive-stack": ["vitalia/backend/src/events.py"]},
    )

    cap_data = {
        "slug": "hipaa-lite-defensive-stack",
        "user_visible": True,
        "nature": "feature",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/vitalia/medical-compliance/events",
                    "requires_role": ["admin_clinic", "staff_vitalia"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "compliance", "hipaa-lite-defensive-stack", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["drift"] == 1
    assert result["details"][0]["status"] == "no_enforcement_found"


def test_cross_check_4_pass_require_brand_owner_access(tmp_path: Path):
    """Depends(require_brand_owner_access()) counts as ENFORCED."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root / "marca_router.py"
    _write_code(
        py_file,
        "# cap: brand_studio.lisa-marca\n# story-origin: TBD\n"
        "_brand_owner_required = Depends(require_brand_owner_access())\n"
        "def patch_identity(): pass\n",
    )
    _write_code_index(tmp_path, "vitalia", {"brand_studio.lisa-marca": ["vitalia/backend/src/marca_router.py"]})

    cap_data = {
        "slug": "lisa-marca",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/lisa/marca/identity",
                    "requires_role": ["admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "brand_studio", "lisa-marca", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["pass"] == 1
    assert result["drift"] == 0


def test_cross_check_4_pass_assert_phi_access_helper(tmp_path: Path):
    """_assert_phi_access(role) helper counts as ENFORCED."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root / "inbox_router.py"
    _write_code(
        py_file,
        "# cap: sales_agent.inbox-handler-mode-occ\n# story-origin: TBD\n"
        "_PHI_ROLES = frozenset({'doctor', 'nurse', 'admin_clinic'})\n"
        "def _assert_phi_access(role):\n"
        "    if role not in _PHI_ROLES:\n"
        "        raise PHIAccessDeniedError(role, list(_PHI_ROLES))\n"
        "def set_mode(): _assert_phi_access(user_role)\n",
    )
    _write_code_index(
        tmp_path,
        "vitalia",
        {"sales_agent.inbox-handler-mode-occ": ["vitalia/backend/src/inbox_router.py"]},
    )

    cap_data = {
        "slug": "inbox-handler-mode-occ",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/vitalia/inbox/conversations/{id}/mode",
                    "requires_role": ["doctor", "nurse", "admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "sales_agent", "inbox-handler-mode-occ", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["pass"] == 1
    assert result["drift"] == 0


def test_cross_check_4_pass_inline_frozenset_gate(tmp_path: Path):
    """Inline `if role not in _NPS_SUMMARY_ROLES: raise ...403` counts as ENFORCED."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root / "nps_endpoints.py"
    _write_code(
        py_file,
        "# cap: patients.nps-tracking\n# story-origin: TBD\n"
        "_NPS_SUMMARY_ROLES = ['doctor', 'nurse', 'admin_clinic', 'marketing']\n"
        "def get_summary(user_role):\n"
        "    if user_role not in _NPS_SUMMARY_ROLES:\n"
        "        raise HTTPException(status_code=403)\n",
    )
    _write_code_index(tmp_path, "vitalia", {"patients.nps-tracking": ["vitalia/backend/src/nps_endpoints.py"]})

    cap_data = {
        "slug": "nps-tracking",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/vitalia/fidelizacion/nps/summary",
                    "requires_role": ["doctor", "admin_clinic", "nurse"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "patients", "nps-tracking", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["pass"] == 1
    assert result["drift"] == 0


def test_cross_check_4_skip_null_path(tmp_path: Path):
    """entry_point with path: null is SKIPPED (not counted, not drift)."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)

    cap_data = {
        "slug": "luana-core-adoption",
        "user_visible": False,
        "nature": "extension-point",
        "access": {
            "entry_points": [
                {
                    "path": None,
                    "requires_role": ["admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "iam", "luana-core-adoption", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["total"] == 0
    assert result["drift"] == 0
    assert result["skipped"] == 1


def test_cross_check_4_skip_extension_point(tmp_path: Path):
    """BE-only extension point (user_visible: false + nature: extension-point) is SKIPPED."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)

    cap_data = {
        "slug": "luana-core-adoption",
        "user_visible": False,
        "nature": "extension-point",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/some/be/route",
                    "requires_role": ["admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "iam", "luana-core-adoption", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["total"] == 0
    assert result["drift"] == 0
    assert result["skipped"] == 1


def test_cross_check_4_null_role_skips(tmp_path: Path):
    """entry_point with requires_role: null (ungated by design) is not cross-checked."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root / "nps_submit.py"
    _write_code(py_file, "# cap: patients.nps-tracking\n# story-origin: TBD\ndef submit(): pass\n")
    _write_code_index(tmp_path, "vitalia", {"patients.nps-tracking": ["vitalia/backend/src/nps_submit.py"]})

    cap_data = {
        "slug": "nps-tracking",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/vitalia/fidelizacion/nps/submit",
                    "requires_role": None,
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "patients", "nps-tracking", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["total"] == 0
    assert result["drift"] == 0


def test_cross_check_4_drift_role_mismatch(tmp_path: Path):
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root / "api.py"
    _write_code(
        py_file,
        "# cap: scheduling.valeria-agenda\n# story-origin: TBD\n"
        "@require_phi_access(roles=['nurse'])\n"  # Different role!
        "def get_agenda(): pass\n",
    )
    _write_code_index(tmp_path, "vitalia", {"scheduling.valeria-agenda": ["vitalia/backend/src/api.py"]})

    cap_data = {
        "slug": "valeria-agenda",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/agenda",
                    "requires_role": ["doctor", "admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["drift"] == 1
    assert result["details"][0]["status"] == "role_mismatch"


# ---------------------------------------------------------------------------
# Cross-check 3 — pytest path-aware extension (T-0 backfill)
# ---------------------------------------------------------------------------


def test_cross_check_3_py_with_def_test_passes(tmp_path: Path):
    """(a) .py file with 'def test_foo():' → cross_check_3 drift=0, pass=1.

    RED against old code (old code checks 'test(' / 'test.describe(' — a
    Python def-test never matches those JS substrings → drift=1 before fix).
    """
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_test = be_root.parent / "tests" / "test_api_health.py"
    _write_code(
        py_test,
        "# cap: platform.api-health-endpoint\n"
        "import pytest\n\n"
        "def test_health_returns_200(client):\n"
        "    resp = client.get('/health')\n"
        "    assert resp.status_code == 200\n",
    )

    cap_data = {
        "slug": "api-health-endpoint",
        "scenarios": [
            {
                "id": "health-check-live",
                "e2e_test": str(py_test.relative_to(tmp_path)),
            }
        ],
    }
    _write_cap(caps_root, "platform", "api-health-endpoint", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)

    assert result["total"] == 1
    assert result["pass"] == 1, (
        "Expected pass=1 for .py file with 'def test_', got drift instead. "
        "Confirms path-aware pattern not yet implemented (RED)."
    )
    assert result["drift"] == 0


def test_cross_check_3_py_without_def_test_is_drift(tmp_path: Path):
    """(b) .py file with no 'def test' → drift=1, status 'no_test_pattern'."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)

    py_file = be_root.parent / "tests" / "helper.py"
    _write_code(
        py_file,
        "# A helper module without actual test functions\ndef setup_fixtures():\n    pass\n",
    )

    cap_data = {
        "slug": "api-health-endpoint",
        "scenarios": [
            {
                "id": "health-check-live",
                "e2e_test": str(py_file.relative_to(tmp_path)),
            }
        ],
    }
    _write_cap(caps_root, "platform", "api-health-endpoint", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)

    assert result["drift"] == 1
    assert result["details"][0]["status"] == "no_test_pattern"


def test_cross_check_3_ts_with_test_still_passes(tmp_path: Path):
    """(c) Regression: .ts file with 'test(' still passes (no change to JS behaviour)."""
    mod = _load_module()
    caps_root, _, _, e2e_root = _setup(tmp_path)

    ts_spec = e2e_root / "smoke.spec.ts"
    _write_code(
        ts_spec,
        "import { test, expect } from '@playwright/test';\n"
        "test('smoke', async ({ page }) => {\n"
        "  await page.goto('/');\n"
        "  await expect(page).toHaveTitle(/Vitalia/);\n"
        "});\n",
    )

    cap_data = {
        "slug": "valeria-agenda",
        "scenarios": [
            {
                "id": "agenda-smoke",
                "e2e_test": "vitalia/frontend/e2e/smoke.spec.ts",
            }
        ],
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)

    assert result["pass"] == 1
    assert result["drift"] == 0, "Regression: .ts files with test( must still pass"


def test_cross_check_3_ts_without_test_is_drift(tmp_path: Path):
    """(d) Bonus regression negative: .ts without 'test(' → drift 'no_test_pattern'."""
    mod = _load_module()
    caps_root, _, _, e2e_root = _setup(tmp_path)

    ts_util = e2e_root / "utils.ts"
    _write_code(
        ts_util,
        "// Utility helpers — no test functions here\nexport const BASE_URL = 'http://localhost:3002';\n",
    )

    cap_data = {
        "slug": "valeria-agenda",
        "scenarios": [
            {
                "id": "agenda-smoke",
                "e2e_test": "vitalia/frontend/e2e/utils.ts",
            }
        ],
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_3(caps, tmp_path)

    assert result["drift"] == 1
    assert result["details"][0]["status"] == "no_test_pattern"


def test_cross_check_4_ui_entry_lenient(tmp_path: Path):
    """UI entry without decorator should pass (Clerk middleware handles)."""
    mod = _load_module()
    caps_root, _, fe_root, _ = _setup(tmp_path)

    tsx_file = fe_root / "page.tsx"
    _write_code(
        tsx_file,
        "// cap: scheduling.valeria-agenda\n// story-origin: TBD\nexport default function Page() { return null; }\n",
    )
    _write_code_index(tmp_path, "vitalia", {"scheduling.valeria-agenda": ["vitalia/frontend/src/page.tsx"]})

    cap_data = {
        "slug": "valeria-agenda",
        "access": {
            "entry_points": [
                {
                    "path": "/valeria/agenda",
                    "requires_role": ["doctor"],
                    "entry_type": "ui",
                }
            ]
        },
    }
    _write_cap(caps_root, "scheduling", "valeria-agenda", cap_data)

    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["pass"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# HB-51 · Gates determinísticos G1-G6 — negative tests CON DIENTES + repro origen
# ═══════════════════════════════════════════════════════════════════════════
#
# Cada gate tiene un caso GREEN + un caso RED (drift>0). Sin negative test que lo
# prueba en rojo, el gate es decorativo (handoff §0.3). El test estrella reproduce
# el incidente origen: borrar la cap del inbox → G1+G2 RED.


def _write_system_map(tmp_path: Path, brand: str, agents: list[dict], zones: list[dict]) -> None:
    sm = tmp_path / brand / "docs" / "architecture" / "SYSTEM-MAP.yaml"
    sm.parent.mkdir(parents=True, exist_ok=True)
    sm.write_text(yaml.dump({"brand": brand, "agents": agents, "zones": zones}, allow_unicode=True), encoding="utf-8")


def _adrian_inbox_map() -> tuple[list[dict], list[dict]]:
    agents = [{"id": "adrian", "functional_areas": [{"id": "inbox", "name": "Inbox", "status": "live"}]}]
    zones = [{"id": "agentes", "user_visible": True, "boxes": ["adrian"]}]
    return agents, zones


# ── G1 · header-resuelve ─────────────────────────────────────────────────────


def test_g1_pass_header_resolves(tmp_path: Path):
    mod = _load_module()
    caps_root, be_root, fe_root, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "functional_area": "adrian.inbox"},
    )
    _write_code(be_root / "router.py", "# cap: inbox.adrian-inbox\ndef x(): pass\n")
    _write_code(fe_root / "View.tsx", "// cap: adrian.inbox\nexport const x = 1;\n")
    mod.resolve_cap.clear_resolver_cache()
    g1 = mod.gate_g1_header_resolves("vitalia", tmp_path)
    assert g1["total"] == 2 and g1["drift"] == 0


def test_g1_red_orphan_header(tmp_path: Path):
    """★ El bug origen: header → cap inexistente = drift (G1 RED)."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    _write_cap(caps_root, "inbox", "adrian-inbox", {"slug": "adrian-inbox", "status": "live"})
    _write_code(be_root / "wire.py", "# cap: sales_agent.adrian-override-context\ndef x(): pass\n")
    mod.resolve_cap.clear_resolver_cache()
    g1 = mod.gate_g1_header_resolves("vitalia", tmp_path)
    assert g1["drift"] == 1
    assert g1["details"][0]["status"] == "orphan_header"


def test_g1_ignores_special_markers(tmp_path: Path):
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    _write_cap(caps_root, "inbox", "adrian-inbox", {"slug": "adrian-inbox"})
    _write_code(be_root / "shared.py", "# cap: __shared__\ndef x(): pass\n")
    mod.resolve_cap.clear_resolver_cache()
    g1 = mod.gate_g1_header_resolves("vitalia", tmp_path)
    assert g1["total"] == 0 and g1["drift"] == 0


def test_g1_strips_inline_noqa(tmp_path: Path):
    """Header con `# noqa` inline → captura solo el cap-token (no falso orphan)."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    _write_cap(caps_root, "abel", "icp-buyer", {"slug": "icp-buyer", "status": "live"})
    _write_code(be_root / "x.py", "# cap: abel.icp-buyer  # noqa: ERA001\ndef x(): pass\n")
    mod.resolve_cap.clear_resolver_cache()
    g1 = mod.gate_g1_header_resolves("vitalia", tmp_path)
    assert g1["drift"] == 0


# ── G2 · área-viva-tiene-cap ─────────────────────────────────────────────────


def test_g2_pass_live_area_has_cap(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "functional_area": "adrian.inbox"},
    )
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)
    g2 = mod.gate_g2_live_area_has_cap("vitalia", tmp_path, caps)
    assert g2["total"] == 1 and g2["drift"] == 0


def test_g2_red_empty_live_area(tmp_path: Path):
    """★ La caja Inbox vacía: área live en SYSTEM-MAP sin cap → G2 RED."""
    mod = _load_module()
    _setup(tmp_path)
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)  # vacío
    g2 = mod.gate_g2_live_area_has_cap("vitalia", tmp_path, caps)
    assert g2["drift"] == 1
    assert g2["details"][0]["functional_area"] == "adrian.inbox"


def test_g2_partial_cap_not_empty(tmp_path: Path):
    """Área con una cap `partial` NO está vacía (el cockpit la pinta) → G2 pasa."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "partial", "functional_area": "adrian.inbox"},
    )
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)
    g2 = mod.gate_g2_live_area_has_cap("vitalia", tmp_path, caps)
    assert g2["drift"] == 0


def test_g2_skips_legacy_pseudo_agents(tmp_path: Path):
    """Áreas de agentes legacy NO referenciados por ninguna zona → no cuentan (mirror cockpit)."""
    mod = _load_module()
    _setup(tmp_path)
    agents = [
        {"id": "adrian", "functional_areas": [{"id": "inbox", "status": "live"}]},
        {"id": "config", "functional_areas": [{"id": "auth", "status": "live"}]},  # legacy, no en zona
    ]
    zones = [{"id": "agentes", "boxes": ["adrian"]}]  # config NO está
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)
    g2 = mod.gate_g2_live_area_has_cap("vitalia", tmp_path, caps)
    # solo adrian.inbox cuenta (config.auth excluido) → 1 total
    assert g2["total"] == 1


# ── G3 · cap-tiene-hogar ─────────────────────────────────────────────────────


def test_g3_red_fa_not_in_map(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "functional_area": "fantasma.inexistente"},
    )
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)
    g3 = mod.gate_g3_cap_has_home("vitalia", tmp_path, caps)
    assert g3["drift"] == 1
    assert g3["details"][0]["status"] == "fa_not_in_system_map"


def test_g3_pass_fa_in_map(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "functional_area": "adrian.inbox"},
    )
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)
    g3 = mod.gate_g3_cap_has_home("vitalia", tmp_path, caps)
    assert g3["drift"] == 0


# ── G4 · paths-existen ───────────────────────────────────────────────────────


def test_g4_red_missing_path_live_cap(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {
            "slug": "adrian-inbox",
            "status": "live",
            "dev_preview": {"main_component": "vitalia/frontend/src/features/adrian/NoExiste.tsx"},
        },
    )
    caps = mod.load_capabilities("vitalia", tmp_path)
    g4 = mod.gate_g4_paths_exist("vitalia", tmp_path, caps)
    assert g4["drift"] == 1
    assert g4["details"][0]["status"] == "path_missing"


def test_g4_pass_existing_path(tmp_path: Path):
    mod = _load_module()
    caps_root, _, fe_root, _ = _setup(tmp_path)
    comp = fe_root / "features" / "adrian" / "View.tsx"
    _write_code(comp, "export const x = 1;\n")
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {
            "slug": "adrian-inbox",
            "status": "live",
            "dev_preview": {"main_component": str(comp.relative_to(tmp_path))},
        },
    )
    caps = mod.load_capabilities("vitalia", tmp_path)
    g4 = mod.gate_g4_paths_exist("vitalia", tmp_path, caps)
    assert g4["total"] == 1 and g4["drift"] == 0


def test_g4_skips_deprecated_cap(tmp_path: Path):
    """Cap deprecated con path removido NO es drift (código legítimamente borrado)."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "old",
        {
            "slug": "old",
            "status": "deprecated",
            "dev_preview": {"main_component": "vitalia/frontend/src/features/Gone.tsx"},
        },
    )
    caps = mod.load_capabilities("vitalia", tmp_path)
    g4 = mod.gate_g4_paths_exist("vitalia", tmp_path, caps)
    assert g4["total"] == 0 and g4["drift"] == 0


def test_g4_strips_double_colon_symbol(tmp_path: Path):
    """code_pointer `db.py::symbol` → valida solo `db.py`."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    db = be_root / "db.py"
    _write_code(db, "def get(): pass\n")
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {
            "slug": "adrian-inbox",
            "status": "live",
            "code_pointers": {"backend": {"session": str(db.relative_to(tmp_path)) + "::get_session"}},
        },
    )
    caps = mod.load_capabilities("vitalia", tmp_path)
    g4 = mod.gate_g4_paths_exist("vitalia", tmp_path, caps)
    assert g4["total"] == 1 and g4["drift"] == 0


# ── G5 · superseded-válido ───────────────────────────────────────────────────


def test_g5_red_broken_superseded_by(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "superseded_by": "ghost.no-existe"},
    )
    mod.resolve_cap.clear_resolver_cache()
    caps = mod.load_capabilities("vitalia", tmp_path)
    g5 = mod.gate_g5_superseded_valid("vitalia", tmp_path, caps)
    assert g5["drift"] == 1
    assert g5["details"][0]["status"] == "broken_supersession"


def test_g5_pass_valid_supersedes(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "supersedes": ["sales_agent.old-occ"]},
    )
    _write_cap(caps_root, "sales_agent", "old-occ", {"slug": "old-occ", "status": "deprecated"})
    mod.resolve_cap.clear_resolver_cache()
    caps = mod.load_capabilities("vitalia", tmp_path)
    g5 = mod.gate_g5_superseded_valid("vitalia", tmp_path, caps)
    assert g5["total"] == 1 and g5["drift"] == 0


# ── G6 · map-coverage ────────────────────────────────────────────────────────


def test_g6_red_live_cap_no_fa(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(caps_root, "platform", "foundation", {"slug": "foundation", "status": "live"})  # sin functional_area
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)
    g6 = mod.gate_g6_map_coverage("vitalia", tmp_path, caps)
    assert g6["drift"] == 1
    assert g6["details"][0]["status"] == "live_cap_not_on_map"


def test_g6_pass_live_cap_on_map(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "functional_area": "adrian.inbox"},
    )
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)
    caps = mod.load_capabilities("vitalia", tmp_path)
    g6 = mod.gate_g6_map_coverage("vitalia", tmp_path, caps)
    assert g6["total"] == 1 and g6["drift"] == 0


# ── G7 · cockpit-readable (YAML estricto · sin claves duplicadas) ────────────


def test_g7_red_duplicate_key_cap(tmp_path: Path):
    """★ Caso 2026-06-05: cap con clave duplicada (map_box ×2) → PyYAML la tolera pero
    el cockpit (gray-matter) la dropea → caja vacía. G7 debe cazarla en ROJO."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    # _write_cap usa yaml.dump (no genera dups) → escribimos el YAML a mano con el dup
    cap = caps_root / "inbox" / "adrian-inbox.yaml"
    cap.parent.mkdir(parents=True, exist_ok=True)
    cap.write_text(
        "---\nslug: adrian-inbox\nstatus: live\nmodule: inbox\n"
        "map_box: adrian\nfunctional_area: adrian.inbox\nmap_box: adrian\n---\n# body\n",
        encoding="utf-8",
    )
    g7 = mod.gate_g7_cockpit_readable("vitalia", tmp_path)
    assert g7["drift"] == 1
    assert g7["details"][0]["status"] == "cockpit_unreadable"


def test_g7_pass_clean_cap(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "functional_area": "adrian.inbox"},
    )
    g7 = mod.gate_g7_cockpit_readable("vitalia", tmp_path)
    assert g7["total"] == 1 and g7["drift"] == 0


# ── G8 · cap live+visible DEBE tener user_facing_description (F2 cap-levels) ──


def test_g8_red_user_visible_no_description(tmp_path: Path):
    """Una cap live + user_visible:true SIN user_facing_description → el cockpit «✨ Qué
    puedo hacer» queda mudo. G8 debe cazarla en ROJO."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "user_visible": True, "functional_area": "adrian.inbox"},
    )  # sin user_facing_description
    caps = mod.load_capabilities("vitalia", tmp_path)
    g8 = mod.gate_g8_user_visible_has_description("vitalia", tmp_path, caps)
    assert g8["drift"] == 1
    assert g8["details"][0]["status"] == "user_visible_no_description"


def test_g8_pass_user_visible_with_description(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {
            "slug": "adrian-inbox",
            "status": "live",
            "user_visible": True,
            "user_facing_description": "Inbox unificado cross-canal para responder pacientes.",
        },
    )
    caps = mod.load_capabilities("vitalia", tmp_path)
    g8 = mod.gate_g8_user_visible_has_description("vitalia", tmp_path, caps)
    assert g8["total"] == 1 and g8["drift"] == 0


def test_g8_ignores_infra_and_non_live(tmp_path: Path):
    """G8 NO aplica a infra (user_visible:false) ni a planned/deprecated."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(caps_root, "platform", "infra", {"slug": "infra", "status": "live", "user_visible": False})
    _write_cap(caps_root, "inbox", "planned", {"slug": "planned", "status": "planned", "user_visible": True})
    caps = mod.load_capabilities("vitalia", tmp_path)
    g8 = mod.gate_g8_user_visible_has_description("vitalia", tmp_path, caps)
    assert g8["total"] == 0 and g8["drift"] == 0


# ── G9 · cap live+visible DEBE tener ≥1 scenario (F2 cap-levels) ──────────────


def test_g9_red_user_visible_no_scenario(tmp_path: Path):
    """Una cap live + user_visible:true SIN scenarios → caja de valor sin casos de uso.
    G9 debe cazarla en ROJO (deja de ser paper-rule el «≥1 scenario al merge»)."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {
            "slug": "adrian-inbox",
            "status": "live",
            "user_visible": True,
            "user_facing_description": "Inbox unificado.",
        },
    )  # sin scenarios
    caps = mod.load_capabilities("vitalia", tmp_path)
    g9 = mod.gate_g9_user_visible_has_scenario("vitalia", tmp_path, caps)
    assert g9["drift"] == 1
    assert g9["details"][0]["status"] == "user_visible_no_scenario"


def test_g9_pass_user_visible_with_scenario(tmp_path: Path):
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {
            "slug": "adrian-inbox",
            "status": "live",
            "user_visible": True,
            "user_facing_description": "Inbox unificado.",
            "scenarios": [
                {
                    "id": "operador-pausa",
                    "name": "El operador pausa una conversación",
                    "actor": "receptionist",
                    "given": "Conversación activa",
                    "when": "Clic en Pausar",
                    "then": "handler_mode = paused",
                }
            ],
        },
    )
    caps = mod.load_capabilities("vitalia", tmp_path)
    g9 = mod.gate_g9_user_visible_has_scenario("vitalia", tmp_path, caps)
    assert g9["total"] == 1 and g9["drift"] == 0


def test_g9_ignores_infra_and_non_live(tmp_path: Path):
    """G9 NO aplica a infra (user_visible:false) ni a deprecated/planned (los 39 stubs)."""
    mod = _load_module()
    caps_root, _, _, _ = _setup(tmp_path)
    _write_cap(caps_root, "platform", "infra", {"slug": "infra", "status": "live", "user_visible": False})
    _write_cap(caps_root, "old", "dep", {"slug": "dep", "status": "deprecated", "user_visible": True})
    caps = mod.load_capabilities("vitalia", tmp_path)
    g9 = mod.gate_g9_user_visible_has_scenario("vitalia", tmp_path, caps)
    assert g9["total"] == 0 and g9["drift"] == 0


# ── ★ REPRODUCCIÓN DEL INCIDENTE ORIGEN (borrar la cap inbox → G1+G2 RED) ─────


def test_repro_delete_inbox_cap_trips_g1_and_g2(tmp_path: Path):
    """★ El test que reproduce el incidente: con la cap inbox presente G1+G2 pasan;
    al BORRARLA, los headers quedan huérfanos (G1 RED) y la caja Inbox queda vacía
    (G2 RED). Antes de HB-51 esto pasaba SILENCIOSO."""
    mod = _load_module()
    caps_root, be_root, fe_root, _ = _setup(tmp_path)
    cap_path = _write_cap(
        caps_root,
        "inbox",
        "adrian-inbox",
        {"slug": "adrian-inbox", "status": "live", "functional_area": "adrian.inbox"},
    )
    _write_code(be_root / "inbox" / "router.py", "# cap: inbox.adrian-inbox\ndef x(): pass\n")
    _write_code(fe_root / "features" / "adrian" / "InboxView.tsx", "// cap: adrian.inbox\nexport const x = 1;\n")
    agents, zones = _adrian_inbox_map()
    _write_system_map(tmp_path, "vitalia", agents, zones)

    # ── ANTES: todo verde ──
    mod.resolve_cap.clear_resolver_cache()
    caps = mod.load_capabilities("vitalia", tmp_path)
    assert mod.gate_g1_header_resolves("vitalia", tmp_path)["drift"] == 0
    assert mod.gate_g2_live_area_has_cap("vitalia", tmp_path, caps)["drift"] == 0

    # ── BORRAR la cap canónica (el incidente) ──
    cap_path.unlink()
    mod.resolve_cap.clear_resolver_cache()
    caps = mod.load_capabilities("vitalia", tmp_path)

    # ── DESPUÉS: G1 (headers huérfanos) + G2 (caja vacía) en ROJO ──
    g1 = mod.gate_g1_header_resolves("vitalia", tmp_path)
    g2 = mod.gate_g2_live_area_has_cap("vitalia", tmp_path, caps)
    assert g1["drift"] >= 1, "G1 debe cazar los headers huérfanos tras borrar la cap"
    assert g2["drift"] == 1, "G2 debe cazar la caja Inbox vacía tras borrar la cap"
    assert g2["details"][0]["functional_area"] == "adrian.inbox"


# ─────────────────────────────────────────────────────────────────────────────
# HB-59 · cross_check_4 attribution: resolved index + __shared__ god-file scan
# ─────────────────────────────────────────────────────────────────────────────


def test_cross_check_4_shared_godfile_enforcement_pass(tmp_path: Path):
    """HB-59: endpoint del cap vive en un god-file `# cap: __shared__` CON gate en
    su función → cc4 lo atribuye vía scan per-endpoint → drift 0."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    _write_code(
        be_root / "routes.py",
        "# cap: __shared__\n# story-origin: TBD\n"
        '@router.get("/events")\n'
        "async def list_events(user = Depends(require_brand_owner_access())):\n"
        "    return []\n\n"
        '@router.get("/public-ping")\n'
        "async def ping():\n"
        "    return 'ok'\n",
    )
    _write_code_index(tmp_path, "vitalia", {}, shared_files=["vitalia/backend/src/routes.py"])
    cap_data = {
        "slug": "hipaa-lite-defensive-stack",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/vitalia/medical-compliance/events",
                    "requires_role": ["admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "compliance", "hipaa-lite-defensive-stack", cap_data)
    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["drift"] == 0
    assert result["pass"] == 1


def test_cross_check_4_shared_godfile_no_enforcement_drift(tmp_path: Path):
    """HB-59: endpoint en god-file __shared__ SIN gate → sigue drift (safe direction)."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    _write_code(
        be_root / "routes.py",
        "# cap: __shared__\n# story-origin: TBD\n"
        '@router.get("/events")\n'
        "async def list_events():\n"
        "    return []\n",
    )
    _write_code_index(tmp_path, "vitalia", {}, shared_files=["vitalia/backend/src/routes.py"])
    cap_data = {
        "slug": "hipaa-lite-defensive-stack",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/vitalia/medical-compliance/events",
                    "requires_role": ["admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "compliance", "hipaa-lite-defensive-stack", cap_data)
    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["drift"] == 1


def test_cross_check_4_shared_godfile_no_false_attribution(tmp_path: Path):
    """HB-59 safety: el gate de un endpoint VECINO en el god-file NO se atribuye al
    endpoint del cap (scan per-función, no per-file) → drift 1, sin false-'enforced'."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    _write_code(
        be_root / "routes.py",
        "# cap: __shared__\n# story-origin: TBD\n"
        '@router.get("/events")\n'
        "async def list_events(user = Depends(require_brand_owner_access())):\n"
        "    return []\n\n"
        '@router.get("/export-csv")\n'
        "async def export_csv():\n"
        "    return 'csv'\n",
    )
    _write_code_index(tmp_path, "vitalia", {}, shared_files=["vitalia/backend/src/routes.py"])
    cap_data = {
        "slug": "hipaa-lite-defensive-stack",
        "access": {
            "entry_points": [
                {
                    "path": "/api/v1/vitalia/medical-compliance/export-csv",
                    "requires_role": ["admin_clinic"],
                    "entry_type": "api",
                }
            ]
        },
    }
    _write_cap(caps_root, "compliance", "hipaa-lite-defensive-stack", cap_data)
    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["drift"] == 1


def test_cross_check_4_resolved_index_alias(tmp_path: Path):
    """HB-59 B.1: cc4 lee resolved_cap_to_files → un header alias (functional-area)
    se atribuye al cap_id canónico (antes daba false drift)."""
    mod = _load_module()
    caps_root, be_root, _, _ = _setup(tmp_path)
    _write_code(
        be_root / "servicios_router.py",
        "# cap: lisa.servicios\n# story-origin: TBD\n"
        "_g = Depends(require_brand_owner_access())\n"
        "def patch_servicio(): pass\n",
    )
    _write_code_index(
        tmp_path,
        "vitalia",
        {"lisa.servicios": ["vitalia/backend/src/servicios_router.py"]},
        resolved_cap_to_files={"offer.lisa-servicios": ["vitalia/backend/src/servicios_router.py"]},
    )
    cap_data = {
        "slug": "lisa-servicios",
        "access": {
            "entry_points": [
                {"path": "/api/v1/lisa/servicios", "requires_role": ["admin_clinic"], "entry_type": "api"}
            ]
        },
    }
    _write_cap(caps_root, "offer", "lisa-servicios", cap_data)
    caps = mod.load_capabilities("vitalia", tmp_path)
    result = mod.cross_check_4(caps, tmp_path, "vitalia")
    assert result["drift"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# HB-90 · G10 — caja fantasma (forward-declared cap sobrevive a la live)
# ─────────────────────────────────────────────────────────────────────────────


def test_g10_pass_single_live_cap(tmp_path: Path):
    mod = _load_module()
    caps = {
        "offer.lisa-servicios": {
            "user_visible": True, "status": "live", "functional_area": "lisa.servicios",
        }
    }
    g10 = mod.gate_g10_stale_forward_decl("vitalia", tmp_path, caps)
    assert g10["drift"] == 0


def test_g10_red_phantom_box(tmp_path: Path):
    """live + planned (sin superseded_by) en la MISMA functional_area → drift 1."""
    mod = _load_module()
    caps = {
        "offer.lisa-servicios": {
            "user_visible": True, "status": "live", "functional_area": "lisa.servicios",
        },
        "offer_studio.medical-services-offer-preset": {
            "user_visible": True, "status": "planned", "functional_area": "lisa.servicios",
        },
    }
    g10 = mod.gate_g10_stale_forward_decl("vitalia", tmp_path, caps)
    assert g10["drift"] == 1
    assert g10["details"][0]["cap_id"] == "offer_studio.medical-services-offer-preset"


def test_g10_pass_superseded(tmp_path: Path):
    """el placeholder con superseded_by ya NO cuenta → drift 0."""
    mod = _load_module()
    caps = {
        "offer.lisa-servicios": {
            "user_visible": True, "status": "live", "functional_area": "lisa.servicios",
        },
        "offer_studio.medical-services-offer-preset": {
            "user_visible": True, "status": "planned", "functional_area": "lisa.servicios",
            "superseded_by": "offer.lisa-servicios",
        },
    }
    g10 = mod.gate_g10_stale_forward_decl("vitalia", tmp_path, caps)
    assert g10["drift"] == 0
