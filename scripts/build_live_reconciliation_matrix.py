#!/usr/bin/env python3
# cap: ops.live-reconciliation-sweep
# story-origin: vitalia-cockpit-live-reconciliation
"""
build_live_reconciliation_matrix.py — Genera la matriz cap↔realidad live v1.

Pasos:
  1. Corre compute_capability_status.py --brand vitalia (regenera _status-computed.json)
  2. Lee vitalia/frontend/e2e/regression/live-reconciliation/.sweep-findings.json
  3. Cruza findings con _status-computed.json por cap_id
  4. Escribe vitalia/docs/domains/ops/live-reconciliation.md

Columnas de la matriz:
  cap_id | declared_status | computed_status | ruta | sweep_verdict |
  evidencia | technical_verdict | acción | story_mapeada

Las últimas 3 columnas (technical_verdict, acción, story_mapeada) = "pendiente T-3" en v1.

Usage:
  python3 scripts/build_live_reconciliation_matrix.py [--brand vitalia]
  python3 scripts/build_live_reconciliation_matrix.py --no-recompute

downstream-regression-na: tooling script brand-local vitalia; no cross-brand consumers
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

WS = Path(__file__).parent.parent  # workspace root
BRAND = "vitalia"


def _paths(brand: str) -> dict[str, Path]:
    return {
        "status_computed": WS / brand / "docs/product/capabilities/_status-computed.json",
        "sweep_findings": (
            WS / brand / "frontend/e2e/regression/live-reconciliation/.sweep-findings.json"
        ),
        "output_md": WS / brand / "docs/domains/ops/live-reconciliation.md",
        "output_dir": WS / brand / "docs/domains/ops",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _run_compute(brand: str) -> bool:
    """Run compute_capability_status.py and return True on success."""
    script = WS / "scripts/compute_capability_status.py"
    venv_python = WS / ".venv/bin/python"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable

    cmd = [python_bin, str(script), "--brand", brand]
    print(f"[matrix] Running: {' '.join(cmd)}", flush=True)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[matrix] WARNING: compute_capability_status.py returned {result.returncode}")
        print(result.stderr[:500] if result.stderr else "")
        return False
    print(f"[matrix] compute_capability_status.py OK", flush=True)
    return True


def _load_json(path: Path, label: str) -> Any:
    if not path.exists():
        print(f"[matrix] WARNING: {label} not found at {path}")
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"[matrix] ERROR loading {label}: {e}")
        return None


def _escape_md(value: str | None) -> str:
    """Escape pipe characters in markdown table cells."""
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _truncate(value: str | None, max_len: int = 80) -> str:
    if value is None:
        return "—"
    s = str(value)
    return s if len(s) <= max_len else s[:max_len] + "…"


def _verdict_emoji(verdict: str | None) -> str:
    mapping = {
        "OK": "✅ OK",
        "ROTO": "❌ ROTO",
        "INACCESIBLE": "⚠️ INACCESIBLE",
        "SIN-UI": "🔲 SIN-UI",
    }
    return mapping.get(verdict or "", f"❓ {verdict or '?'}")


def _status_emoji(status: str | None) -> str:
    mapping = {
        "verified-live": "🟢 verified-live",
        "partial": "🟡 partial",
        "declared-live": "🟠 declared-live",
        "drift": "🔴 drift",
        "stub": "⬜ stub",
        "deprecated": "🚫 deprecated",
        "sunset": "🌅 sunset",
        "wip": "🔵 wip",
    }
    return mapping.get(status or "", f"❓ {status or '?'}")


# ─────────────────────────────────────────────────────────────────────────────
# Matrix builder
# ─────────────────────────────────────────────────────────────────────────────

def build_matrix(brand: str, no_recompute: bool = False) -> int:
    paths = _paths(brand)

    # Ensure output dir exists
    paths["output_dir"].mkdir(parents=True, exist_ok=True)

    # Step 1: Recompute capability status
    if not no_recompute:
        _run_compute(brand)

    # Step 2: Load _status-computed.json
    status_data = _load_json(paths["status_computed"], "_status-computed.json")
    capabilities: dict[str, Any] = {}
    if status_data and isinstance(status_data, dict):
        capabilities = status_data.get("capabilities", {})
    else:
        print("[matrix] WARNING: No capabilities data loaded — matrix will have empty computed_status")

    # Step 3: Load sweep findings
    findings_data = _load_json(paths["sweep_findings"], ".sweep-findings.json")
    findings_list: list[dict[str, Any]] = []
    if findings_data and isinstance(findings_data, list):
        findings_list = findings_data
    else:
        print("[matrix] WARNING: No sweep findings loaded — sweep_verdict column will be empty")

    # Index findings by cap_id (take last finding per capId for dedup)
    findings_by_cap: dict[str, dict[str, Any]] = {}
    findings_by_route: dict[str, dict[str, Any]] = {}
    for f in findings_list:
        cap_id = f.get("capId")
        route = f.get("surface", {}).get("route", "")
        if cap_id:
            findings_by_cap[cap_id] = f
        if route:
            findings_by_route[route] = f

    # Step 4: Build unified rows
    # Union of: cap IDs from _status-computed + cap IDs from findings
    all_cap_ids: set[str] = set(capabilities.keys())
    for f in findings_list:
        cap_id = f.get("capId")
        if cap_id:
            all_cap_ids.add(cap_id)

    rows: list[dict[str, Any]] = []

    for cap_id in sorted(all_cap_ids):
        cap_status = capabilities.get(cap_id, {})
        finding = findings_by_cap.get(cap_id)

        declared = cap_status.get("declared_status", "—")
        computed = cap_status.get("computed_status", "—")

        if finding:
            route = finding.get("surface", {}).get("route", "—")
            sweep_verdict = finding.get("sweep_verdict", "—")
            evidence_parts: list[str] = []
            screenshot = finding.get("screenshot")
            if screenshot:
                evidence_parts.append(f"screenshot: `{screenshot}`")
            console_errors = finding.get("consoleErrors", [])
            if console_errors:
                evidence_parts.append(f"console_errors: {len(console_errors)}")
            http_status = finding.get("httpStatus")
            if http_status:
                evidence_parts.append(f"HTTP {http_status}")
            notes = finding.get("notes", [])
            if notes:
                evidence_parts.append(f"notes: {'; '.join(notes[:2])}")
            evidencia = _truncate(", ".join(evidence_parts) if evidence_parts else "—", 120)
        else:
            route = "—"
            sweep_verdict = "SIN-UI"
            evidencia = "sin hallazgo de sweep"

        rows.append({
            "cap_id": cap_id,
            "declared_status": declared,
            "computed_status": computed,
            "ruta": route,
            "sweep_verdict": sweep_verdict,
            "evidencia": evidencia,
            # These 3 are filled in T-3
            "technical_verdict": "pendiente T-3",
            "accion": "pendiente T-3",
            "story_mapeada": "pendiente T-3",
        })

    # Also add findings that have no cap_id but have useful route info
    for f in findings_list:
        cap_id = f.get("capId")
        if cap_id is None:
            route = f.get("surface", {}).get("route", "?")
            label = f.get("surface", {}).get("label", route)
            sweep_verdict = f.get("sweep_verdict", "?")
            rows.append({
                "cap_id": f"(sin-cap) {_truncate(label, 40)}",
                "declared_status": "—",
                "computed_status": "—",
                "ruta": route,
                "sweep_verdict": sweep_verdict,
                "evidencia": f"HTTP {f.get('httpStatus', '?')}",
                "technical_verdict": "pendiente T-3",
                "accion": "pendiente T-3",
                "story_mapeada": "pendiente T-3",
            })

    # Step 5: Build markdown
    now_utc = datetime.now(timezone.utc).isoformat()
    total_rows = len(rows)
    counts: dict[str, int] = {}
    for r in rows:
        verdict = r["sweep_verdict"]
        counts[verdict] = counts.get(verdict, 0) + 1

    status_counts: dict[str, int] = {}
    for r in rows:
        s = r["computed_status"]
        if s and s != "—":
            status_counts[s] = status_counts.get(s, 0) + 1

    lines: list[str] = []

    lines.append(
        "<!-- AUTO-GENERATED por scripts/build_live_reconciliation_matrix.py — NO editar a mano -->"
    )
    lines.append(f"<!-- Generado: {now_utc} | brand: {brand} -->")
    lines.append("")
    lines.append("# Live Reconciliation Matrix — Vitalia v1")
    lines.append("")
    lines.append(
        "> Artefacto vivo `ops.live-reconciliation-sweep`. "
        "Regenerar: `python3 scripts/build_live_reconciliation_matrix.py --brand vitalia`"
    )
    lines.append("")
    lines.append(f"**Generado:** {now_utc}")
    lines.append(f"**Total superficies en matriz:** {total_rows}")
    lines.append("")

    lines.append("## Resumen")
    lines.append("")
    lines.append("### Conteos por sweep_verdict")
    lines.append("")
    lines.append("| sweep_verdict | Count |")
    lines.append("|---|---|")
    for verdict_key in ["OK", "ROTO", "INACCESIBLE", "SIN-UI"]:
        lines.append(f"| {_verdict_emoji(verdict_key)} | {counts.get(verdict_key, 0)} |")
    if "—" in counts:
        lines.append(f"| ❓ desconocido | {counts.get('—', 0)} |")
    lines.append("")

    lines.append("### Conteos por computed_status")
    lines.append("")
    lines.append("| computed_status | Count |")
    lines.append("|---|---|")
    for s in [
        "verified-live",
        "partial",
        "declared-live",
        "drift",
        "stub",
        "wip",
        "deprecated",
        "sunset",
    ]:
        if s in status_counts:
            lines.append(f"| {_status_emoji(s)} | {status_counts[s]} |")
    lines.append("")

    lines.append("## Matriz completa")
    lines.append("")
    lines.append(
        "| cap_id | declared_status | computed_status | ruta | sweep_verdict | evidencia | technical_verdict | acción | story_mapeada |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for r in rows:
        row_parts = [
            _escape_md(r["cap_id"]),
            _escape_md(r["declared_status"]),
            _escape_md(r["computed_status"]),
            _escape_md(_truncate(r["ruta"], 60)),
            _escape_md(_verdict_emoji(r["sweep_verdict"])),
            _escape_md(_truncate(r["evidencia"], 100)),
            _escape_md(r["technical_verdict"]),
            _escape_md(r["accion"]),
            _escape_md(r["story_mapeada"]),
        ]
        lines.append("| " + " | ".join(row_parts) + " |")

    lines.append("")
    lines.append("## Backlog mapeado")
    lines.append("")
    lines.append("> Placeholder T-3 — los items con sweep_verdict=ROTO o computed_status=drift")
    lines.append("> se mapean a stories F2 con evidencia concreta durante Fase 3.")
    lines.append("")
    lines.append(
        "| cap_id | sweep_verdict | computed_status | story_mapeada propuesta |"
    )
    lines.append("|---|---|---|---|")

    roto_rows = [r for r in rows if r["sweep_verdict"] in ("ROTO", "INACCESIBLE")]
    if roto_rows:
        for r in roto_rows:
            lines.append(
                f"| {_escape_md(r['cap_id'])} | {_escape_md(_verdict_emoji(r['sweep_verdict']))} "
                f"| {_escape_md(r['computed_status'])} | pendiente T-3 |"
            )
    else:
        lines.append("| — | — | — | (sin superficies ROTO detectadas en sweep v1) |")

    lines.append("")
    lines.append("---")
    lines.append(f"*Generado por `scripts/build_live_reconciliation_matrix.py` · {now_utc}*")
    lines.append("")

    output = "\n".join(lines)

    # Step 6: Write output
    paths["output_md"].write_text(output, encoding="utf-8")
    print(f"[matrix] Wrote {paths['output_md']} ({len(rows)} rows)", flush=True)

    # Quick validation
    assert "sweep_verdict" in output, "Matrix missing sweep_verdict column"

    return 0


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build live reconciliation matrix from sweep findings + capability status."
    )
    parser.add_argument(
        "--brand",
        default="vitalia",
        help="Brand name (default: vitalia)",
    )
    parser.add_argument(
        "--no-recompute",
        action="store_true",
        help="Skip running compute_capability_status.py (use existing _status-computed.json)",
    )
    args = parser.parse_args()
    return build_matrix(args.brand, no_recompute=args.no_recompute)


if __name__ == "__main__":
    sys.exit(main())
