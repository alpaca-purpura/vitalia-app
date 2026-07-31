# voseo-allowed: test interno de maquinaria (no user-facing)
"""Tests de scripts/harness_config.py — el loader del seam DIP project.config.yaml (W5b).

Cubre las 4 facetas del contrato (RESEARCH-loader-mechanism.md): import python (load/get),
CLI por slot (scalar/list/pluck), sentinel __FILL_ME__ → exit 3, slot inexistente → exit 4,
y --doctor (el gate de extracción W8). Lee el project.config.yaml REAL del repo (es el
contrato vivo) — actualizado 2026-07-31 al seam single-brand de vitalia-app.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
_HC = _SCRIPTS / "harness_config.py"


def _imp():
    spec = importlib.util.spec_from_file_location("harness_config", _HC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(_HC), *args], capture_output=True, text=True)


# ── import API (class B: python scripts) ────────────────────────────────
def test_load_returns_product():
    cfg = _imp().load()
    assert cfg["meta"]["product"] == "vitalia-app"


def test_get_scalar():
    hc = _imp()
    assert hc.get("engine_prefix.python_glob") == "core/luana-core-*"
    assert hc.get("engine_prefix.python_package_count") == 27


def test_get_list():
    order = _imp().get("brands.loop_order")
    assert order == ["vitalia"]


def test_pluck_active_slugs():
    slugs = _imp().get("brands.active", pluck="slug")
    assert set(slugs) == {"vitalia"}


def test_wip_caps_seam_D1():
    hc = _imp()
    assert hc.get("wip_caps.coarse_session_net.developed_max") == 10
    assert hc.get("wip_caps.staleness_days.idea_stale") == 90
    assert hc.get("wip_caps.coarse_session_net.refining_max") == 3


# ── CLI (class A: bash / git-hooks) ─────────────────────────────────────
def test_cli_scalar():
    r = _cli("engine_prefix.python_glob")
    assert r.returncode == 0
    assert r.stdout.strip() == "core/luana-core-*"


def test_cli_list_newline():
    r = _cli("brands.loop_order")
    assert r.returncode == 0
    assert r.stdout.strip().splitlines() == ["vitalia"]


def test_cli_pluck_active_slugs():
    r = _cli("brands.active", "slug")
    assert r.returncode == 0
    assert set(r.stdout.split()) == {"vitalia"}


def test_where_filter_cap_gate_hard():
    # Fork 3 (W5b): per-brand cap_gate facet → derive the HARD set.
    hard = _imp().get("brands.active", pluck="slug", where=("cap_gate", "hard"))
    assert set(hard) == {"vitalia"}


def test_cli_where_filter():
    r = _cli("brands.active", "slug", "--where", "cap_gate=hard")
    assert r.returncode == 0
    assert set(r.stdout.split()) == {"vitalia"}


def test_cli_unfilled_exit3(tmp_path: Path):
    # El seam real está 100% lleno (single-brand) → el contrato exit-3 se prueba
    # con una copia del loader junto a un config stub con __FILL_ME__.
    shutil.copy(_HC, tmp_path / "harness_config.py")
    (tmp_path / "project.config.yaml").write_text(
        "meta:\n  product: stub\nslot_x: __FILL_ME__\n", encoding="utf-8"
    )
    r = subprocess.run(
        [sys.executable, str(tmp_path / "harness_config.py"), "slot_x"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 3
    assert "__FILL_ME__" in (r.stderr + r.stdout)


def test_cli_notfound_exit4():
    r = _cli("nope.not.here")
    assert r.returncode == 4


# ── --doctor (the W8 extraction gate) ───────────────────────────────────
def test_doctor_all_filled_exits_0():
    r = _cli("--doctor")
    # vitalia-app: todos los slots llenos → doctor OK (exit 0)
    assert r.returncode == 0
    assert "all slots filled" in r.stdout
