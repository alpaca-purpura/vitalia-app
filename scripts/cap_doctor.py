#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""cap_doctor.py — Capa 8 del enforcement determinístico (HB-51): health report.

Un comando que lista TODA la deriva code↔cap de un vistazo, en vez de clickear caja por
caja en el cockpit: orphan headers (G1), cajas live vacías (G2), caps sin hogar (G3),
paths rotos (G4), supersesiones rotas (G5), caps live invisibles en el mapa (G6) + errores
de schema (Capa 3). Reusa los MISMOS gates que el pre-commit (un solo SSoT de la deriva).

Uso:
    python3 scripts/cap_doctor.py --brand vitalia
    python3 scripts/cap_doctor.py --all-brands
    python3 scripts/cap_doctor.py --brand vitalia --json   # para el panel del cockpit
    python3 scripts/cap_doctor.py --all-brands --strict     # exit 1 si hay deriva

Exit: 0 sano · 1 deriva (solo con --strict).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

WS = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
)


def _imp(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


bidir = _imp("validate_code_cap_bidirectional")
schema = _imp("validate_caps_schema")

GATE_LABEL = {
    "G1": "headers huérfanos (→ cap inexistente)",
    "G2": "cajas live vacías (área sin cap)",
    "G3": "caps sin hogar (fa ∉ SYSTEM-MAP)",
    "G4": "paths rotos (declarados, no existen)",
    "G5": "supersesiones rotas",
    "G6": "caps live invisibles en el mapa",
    "G7": "caps ILEGIBLES por el cockpit (YAML dup-key → caja vacía)",
    "G8": "caps live+visible SIN user_facing_description (cockpit no dice qué hace)",
    "G9": "caps live+visible SIN scenarios (sin casos de uso · «✨ Qué puedo hacer» mudo)",
    "G10": "cajas fantasma (área live con cap forward-declared sin superseder · HB-90)",
}
GATE_IDS = ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10")


def diagnose(brand: str) -> dict:
    bidir.resolve_cap.clear_resolver_cache()
    caps = bidir.load_capabilities(brand, WS)
    gates = bidir.run_cap_gates(brand, WS, caps)
    # schema (Capa 3)
    schema_errors: list[dict] = []
    for f in schema.cap_files(brand):
        errs, _ = schema.validate_cap(f)
        if errs:
            schema_errors.append({"cap": f.relative_to(WS).as_posix(), "errors": errs})
    total_drift = sum(g["drift"] for g in gates.values()) + len(schema_errors)
    return {
        "brand": brand,
        "caps_loaded": len(caps),
        "gates": gates,
        "schema_errors": schema_errors,
        "total_drift": total_drift,
        "healthy": total_drift == 0,
    }


def accuracy_debt(brand: str) -> dict:
    """ADVISORY (NO afecta exit): scenarios `status:live` cuya VERDAD no está gateada.

    HB-57/HB-58: un scenario `live` sin `e2e_test` = claim sin test; sin `verified_real`
    = sin evidencia de live-verify. NO es HARD — el dato está backfill-blocked (en vitalia
    hoy 135/139 live sin verified_real, 33/139 sin e2e). Esto lo MIDE para el carril L4 del
    CIL (backfill incremental); el accuracy de CÓDIGO lo cubre `mutation_gate.py --cap`.
    """
    caps = bidir.load_capabilities(brand, WS)
    live = 0
    no_e2e: list[str] = []
    no_vr: list[str] = []
    for cid, c in caps.items():
        for s in c.get("scenarios") or []:
            if not isinstance(s, dict) or s.get("status") != "live":
                continue
            live += 1
            sid = f"{cid}::{s.get('id', '?')}"
            if not s.get("e2e_test"):
                no_e2e.append(sid)
            if not s.get("verified_real"):
                no_vr.append(sid)
    return {"brand": brand, "live": live, "no_e2e": no_e2e, "no_verified_real": no_vr}


def print_accuracy(acc: dict) -> None:
    print(f"\n┌─ accuracy-debt (advisory · HB-57/58 · NO bloquea) · {acc['brand']}")
    print(
        f"│  scenarios live: {acc['live']}  ·  sin e2e_test: {len(acc['no_e2e'])}"
        f"  ·  sin verified_real: {len(acc['no_verified_real'])}"
    )
    for s in acc["no_e2e"][:10]:
        print(f"│   ⚪ live sin e2e_test: {s}")
    if len(acc["no_e2e"]) > 10:
        print(f"│   … +{len(acc['no_e2e']) - 10} más")
    print("└─ backfill → CIL carril L4 · accuracy de código → `mutation_gate.py --cap <id>`")


def print_report(diag: dict) -> None:
    brand = diag["brand"]
    print(f"\n╔══ cap-doctor · {brand} ({diag['caps_loaded']} caps) ══")
    if diag["healthy"]:
        print("║  ✅ SANO — 0 deriva code↔cap")
        print("╚" + "═" * 40)
        return
    for gid in GATE_IDS:
        g = diag["gates"].get(gid, {})
        if g.get("drift"):
            print(f"║  ❌ {gid} · {GATE_LABEL[gid]} → {g['drift']}")
            for det in g["details"][:10]:
                key = det.get("header") or det.get("functional_area") or det.get("cap_id") or "?"
                extra = det.get("declared_path") or det.get("superseded_by") or det.get("supersedes") or ""
                print(f"║       • {key}{(' → ' + str(extra)) if extra else ''}")
    if diag["schema_errors"]:
        print(f"║  ❌ schema (Capa 3) → {len(diag['schema_errors'])} caps")
        for se in diag["schema_errors"][:10]:
            print(f"║       • {se['cap']}: {se['errors'][0]}")
    print(f"║  TOTAL deriva: {diag['total_drift']}")
    print("╚" + "═" * 40)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand")
    parser.add_argument("--all-brands", action="store_true")
    parser.add_argument("--json", action="store_true", help="salida JSON (panel cockpit)")
    parser.add_argument("--strict", action="store_true", help="exit 1 si hay deriva")
    parser.add_argument(
        "--accuracy",
        action="store_true",
        help="advisory: mide scenarios live sin e2e/verified_real (HB-57/58 · NO afecta exit)",
    )
    args = parser.parse_args()

    if not args.brand and not args.all_brands:
        parser.error("--brand SLUG o --all-brands requerido")

    if args.all_brands:
        brands = sorted(
            d.name
            for d in WS.iterdir()
            if d.is_dir()
            and (d / "docs" / "product" / "capabilities").is_dir()
            and any((d / "docs" / "product" / "capabilities").rglob("*.yaml"))
        )
    else:
        brands = [args.brand]

    diags = [diagnose(b) for b in brands]
    if args.json:
        print(json.dumps({"brands": diags}, ensure_ascii=False, indent=2))
    else:
        for d in diags:
            print_report(d)
        total = sum(d["total_drift"] for d in diags)
        print(f"\n{'✅ TODO SANO' if total == 0 else f'❌ {total} deriva total'} · brands: {', '.join(brands)}")
        if args.accuracy:
            for b in brands:
                print_accuracy(accuracy_debt(b))

    any_drift = any(d["total_drift"] > 0 for d in diags)
    return 1 if (args.strict and any_drift) else 0


if __name__ == "__main__":
    sys.exit(main())
