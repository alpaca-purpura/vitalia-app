#!/usr/bin/env python3
"""Compute derived capability status from YAML scenarios state-machine.

Produces ``{brand}/docs/product/capabilities/_status-computed.json``
(gitignored R3 v2) with a computed_status badge per capability, scenario
counters, verification counters and drift reasons.

The unit of behavior is the ``scenario`` (Gherkin). Each scenario may declare
an optional ``e2e_test`` path (relative to workspace root). A scenario is
"verified" when its ``e2e_test`` is non-null AND the file exists on disk.

State-machine (declared = cap frontmatter ``status``):
  stub            0 scenarios — nothing described yet
  deprecated      declared=deprecated
  sunset          declared=sunset
  wip             declared=beta (OR any other non-live declared, e.g. planned)
  verified-live   declared=live + all scenarios verified (exist == scenarios_total)
  drift           declared=live + decl>0 + exist<decl (broken e2e refs)
  declared-live   declared=live + decl==0 (no verification at all)
  partial         declared=live + otherwise (some verified, not all)

Where ``decl``  = # scenarios with a non-null e2e_test
      ``exist`` = # of those whose file exists on disk

Usage:
  python3 scripts/compute_capability_status.py --brand vitalia [--out PATH] [--verbose] [--strict]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Valid declared status values from cap YAML frontmatter
VALID_DECLARED = {"live", "beta", "deprecated", "sunset", "planned"}


def _parse_frontmatter(path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from a capability file.

    Supports ``---\\n<yaml>\\n---`` (markdown style) and bare YAML.
    Returns None and logs a warning on parse error.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"  [WARN] No se pudo leer {path}: {exc}", file=sys.stderr)
        return None

    # Strip leading comment/blank lines to reach first '---'
    lines = text.splitlines(keepends=True)
    cursor = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped in {"", "\n"}:
            cursor += len(line)
            continue
        break

    body = text[cursor:]
    if body.startswith("---"):
        # Markdown-style frontmatter: ``---\n<yaml>\n---``
        after = body[3:].lstrip("\n")
        yaml_text = after.split("\n---", 1)[0]
    else:
        # Bare YAML (sin fences ``---``) — parsear el archivo completo.
        # yaml.safe_load ignora comentarios ``#`` nativamente. Antes esto se
        # omitía silenciosamente con WARN (caps mal formateadas no contaban).
        yaml_text = text

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        print(f"  [WARN] YAML malformado en {path}: {exc}", file=sys.stderr)
        return None

    if not isinstance(data, dict):
        print(f"  [WARN] Frontmatter no es mapping en {path} — omitido", file=sys.stderr)
        return None

    return data


def _build_metrics(
    scenarios_total: int,
    decl: int,
    exist: int,
    drift_reasons: list[str],
) -> dict[str, Any]:
    """Build the metrics dict for the status JSON contract.

    Keys (must match the cockpit contract):
      scenarios_total, scenarios_verified, verification_total,
      verification_pass, drift_reasons
    """
    return {
        "scenarios_total": scenarios_total,
        "scenarios_verified": exist,
        "verification_total": decl,
        "verification_pass": exist,
        "drift_reasons": drift_reasons,
    }


def _compute_status(
    declared: str,
    scenarios: list[Any],
    workspace_root: Path,
    cap_slug: str,
) -> tuple[str, dict[str, Any]]:
    """Apply scenarios state-machine and return (computed_status, metrics_dict)."""
    scenarios_total = len(scenarios)

    # -- deprecated / sunset passthrough (before stub check — declared status wins) --
    if declared == "deprecated":
        return "deprecated", _build_metrics(scenarios_total, 0, 0, [])
    if declared == "sunset":
        return "sunset", _build_metrics(scenarios_total, 0, 0, [])

    # -- stub: no scenarios (independent of declared, except deprecated/sunset above) --
    if scenarios_total == 0:
        return "stub", _build_metrics(0, 0, 0, [])

    # Count declared (e2e_test non-null) + existing on disk
    decl = 0
    exist = 0
    drift_reasons: list[str] = []

    for idx, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            continue
        e2e_test = scenario.get("e2e_test")
        if not e2e_test:
            continue
        decl += 1
        full_path = workspace_root / e2e_test
        if full_path.exists():
            exist += 1
        else:
            scenario_id = scenario.get("id") or scenario.get("name") or f"scenario[{idx}]"
            drift_reasons.append(
                f"scenario '{scenario_id}' e2e_test='{e2e_test}' no existe en filesystem"
            )

    # -- beta → wip --
    if declared == "beta":
        return "wip", _build_metrics(scenarios_total, decl, exist, drift_reasons)

    # -- live --
    if declared == "live":
        # all scenarios verified
        if exist == scenarios_total:
            return "verified-live", _build_metrics(scenarios_total, decl, exist, [])
        # broken e2e refs declared but missing → drift
        if decl > 0 and exist < decl:
            return "drift", _build_metrics(scenarios_total, decl, exist, drift_reasons)
        # no verification declared at all → declared-live
        if decl == 0:
            return "declared-live", _build_metrics(scenarios_total, decl, exist, drift_reasons)
        # else: some verified, not all scenarios → partial
        return "partial", _build_metrics(scenarios_total, decl, exist, drift_reasons)

    # -- any other declared (planned, etc.) → wip --
    return "wip", _build_metrics(scenarios_total, decl, exist, drift_reasons)


def process_brand(brand: str, workspace_root: Path, verbose: bool) -> dict[str, Any]:
    """Glob all cap YAMLs for brand and compute status for each.

    Returns the full output dict (without computed_at / brand header).
    """
    caps_root = workspace_root / brand / "docs" / "product" / "capabilities"

    if not caps_root.exists():
        print(f"[ERROR] Directorio de capabilities no encontrado: {caps_root}", file=sys.stderr)
        sys.exit(1)

    yaml_paths = sorted(caps_root.rglob("*.yaml"))
    # Exclude template and mapping files
    yaml_paths = [
        p for p in yaml_paths
        if p.name not in {"_template.yaml", "_v3-mapping.yaml"}
        and not p.name.startswith("_")
    ]

    capabilities: dict[str, Any] = {}
    summary_counts: dict[str, int] = {
        "verified-live": 0,
        "declared-live": 0,
        "partial": 0,
        "wip": 0,
        "stub": 0,
        "drift": 0,
        "deprecated": 0,
        "sunset": 0,
    }

    total = len(yaml_paths)
    if not verbose:
        print(f"Procesando {total} capabilities de {brand}...", end="", flush=True)

    for idx, path in enumerate(yaml_paths):
        if not verbose:
            if (idx + 1) % 10 == 0 or (idx + 1) == total:
                print(".", end="", flush=True)

        data = _parse_frontmatter(path)
        if data is None:
            continue

        slug = data.get("slug") or path.stem
        declared = str(data.get("status", "live")).strip()
        scenarios_raw = data.get("scenarios")
        scenarios: list[Any] = []

        if isinstance(scenarios_raw, list):
            scenarios = scenarios_raw
        elif scenarios_raw is not None:
            print(
                f"  [WARN] 'scenarios' no es lista en {path} — tratado como stub",
                file=sys.stderr,
            )

        computed_status, metrics = _compute_status(declared, scenarios, workspace_root, slug)

        if verbose:
            drift_info = ""
            if metrics["drift_reasons"]:
                drift_info = f" | {len(metrics['drift_reasons'])} drift reasons"
            print(f"  {slug:<60} {declared:<12} → {computed_status}{drift_info}")

        capabilities[slug] = {
            "declared_status": declared,
            "computed_status": computed_status,
            **metrics,
        }

        if computed_status in summary_counts:
            summary_counts[computed_status] += 1
        else:
            summary_counts[computed_status] = summary_counts.get(computed_status, 0) + 1

    if not verbose:
        print()  # newline after dots

    # Normaliza guion→underscore para alinear con el contrato TS
    # (ComputedStatusReport.summary en tools/luana-cockpit/lib/types.ts usa
    # verified_live / declared_live, no verified-live / declared-live).
    summary = {
        "total_caps": len(capabilities),
        **{key.replace("-", "_"): count for key, count in summary_counts.items()},
    }

    return {"capabilities": capabilities, "summary": summary}


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Computa el status derivado de cada capability según scenarios state-machine.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--brand", required=True, help="Slug de la brand (ej. vitalia)")
    parser.add_argument(
        "--out",
        default=None,
        help="Path de salida JSON. Default: {brand}/docs/product/capabilities/_status-computed.json",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Log detallado por capability"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Sale con código 1 si existen caps en estado 'drift'",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Raíz del workspace. Default: detectado via git rev-parse",
    )
    args = parser.parse_args()

    # Resolve workspace root
    if args.repo:
        workspace_root = Path(args.repo).resolve()
    else:
        # Try to detect from git
        import subprocess  # noqa: PLC0415

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            workspace_root = Path(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            workspace_root = Path.cwd()

    out_path = (
        Path(args.out).resolve()
        if args.out
        else workspace_root / args.brand / "docs" / "product" / "capabilities" / "_status-computed.json"
    )

    if args.verbose:
        print(f"Workspace root : {workspace_root}")
        print(f"Brand          : {args.brand}")
        print(f"Output         : {out_path}")
        print()

    result_data = process_brand(args.brand, workspace_root, args.verbose)

    now_iso = datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")
    output: dict[str, Any] = {
        "computed_at": now_iso,
        "brand": args.brand,
        "capabilities": result_data["capabilities"],
        "summary": result_data["summary"],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    summary = result_data["summary"]
    print(
        f"Completado: {summary['total_caps']} caps · "
        f"stub={summary.get('stub', 0)} · "
        f"declared-live={summary.get('declared_live', 0)} · "
        f"verified-live={summary.get('verified_live', 0)} · "
        f"drift={summary.get('drift', 0)} · "
        f"partial={summary.get('partial', 0)} · "
        f"wip={summary.get('wip', 0)} · "
        f"deprecated={summary.get('deprecated', 0)}"
    )
    print(f"Guardado en: {out_path}")

    if args.strict and summary.get("drift", 0) > 0:
        print(
            f"[STRICT] {summary['drift']} caps en estado 'drift' detectadas.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
