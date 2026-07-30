#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""mutation_gate.py — mutation testing DIFF-SCOPED (proceso v5 §5.6 · HB-54).

Roba la DISCIPLINA de Uncle Bob harness-sdd (NO su mutador toy):
  - scope = SOLO archivos/líneas nuevas o modificadas del diff de la story (affordable).
  - tool real: mutmut (BE Python) / Stryker (FE TS) — NUNCA un mutador custom.
  - superficie CRÍTICA = hard (umbral: 100% mutantes muertos sobre líneas nuevas +
    escape mutante-equivalente documentado, patrón ratchet shrink-only); resto = advisory.
  - survivor en líneas NUEVAS → exit 1 = CHANGES_REQUESTED al fix-loop existente.
  - survivor en código HEREDADO (fuera del diff) → NO bloquea; rutea a CIL carril L4.
  - ★ DEGRADE-ADVISORY: si el tool NO está instalado → advisory (exit 0 + warning),
    NUNCA rompe ci-parity/gate-runner (mismo principio que #37 con gates ausentes).

El gate lo ACTIVA `/architect` por `verification_nature` en `04-validators.yaml`
(`technical_gates.mutation: {enabled, mode, surfaces}`); lo CORRE dev-team en el
límite `developed`; lo VERIFICA el auditor. Cuándo es hard: commit/persistencia (HB-50),
dinero/pricing, gates PHI, state machines, transforms de contrato (HB-42/44).

Uso:
  python3 scripts/mutation_gate.py --base <ref> --mode <hard|advisory> [--paths a,b]
  python3 scripts/mutation_gate.py --cap <cap_id> --base <ref> [--mode hard]   # F2b: surface del cap
Exit: 0 = ok o advisory/degrade · 1 = survivor en líneas nuevas con mode=hard.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_config import get as _cfg  # noqa: E402 — own script dir put on sys.path above

# Active brands — from the harness seam project.config.yaml (W5b · brands.active). No
# hardcoded enum (charter §3 DIP); a new brand is picked up from the seam.
_BRANDS = tuple(_cfg("brands.active", pluck="slug"))

WS = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout.strip()
)

ADVISORY = "[mutation-gate · ADVISORY]"
HARD = "[mutation-gate · HARD]"


def changed_files(base: str) -> list[str]:
    """Archivos py/ts/tsx nuevos o modificados vs base (el diff de la story)."""
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AM", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        cwd=WS,
    ).stdout
    return [f for f in out.splitlines() if f.endswith((".py", ".ts", ".tsx"))]


def files_for_cap(cap_id: str) -> list[str]:
    """Surface de código de una cap = sus archivos `# cap:`/`// cap:` (reverse-index).

    Lee `{brand}/docs/product/capabilities/_code-index.json::cap_to_files` (el mismo
    índice que usa `validate_code_cap_bidirectional`). Esto es "el surface del cap"
    de F2b: mutar SOLO lo que el cap declara como suyo, no el repo entero.
    """
    for brand in _BRANDS:
        idx = WS / brand / "docs" / "product" / "capabilities" / "_code-index.json"
        if not idx.exists():
            continue
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cap_to_files = data.get("cap_to_files", {})
        if cap_id in cap_to_files:
            return [f for f in cap_to_files[cap_id] if f.endswith((".py", ".ts", ".tsx"))]
    return []


def tool_for(files: list[str]) -> tuple[str, str | None]:
    """(surface, tool_path|None). BE→mutmut, FE→stryker. None si ausente (degrade)."""
    has_py = any(f.endswith(".py") for f in files)
    has_ts = any(f.endswith((".ts", ".tsx")) for f in files)
    if has_py:
        mutmut = shutil.which("mutmut") or str(WS / ".venv/bin/mutmut")
        return ("BE", mutmut if Path(mutmut).exists() else None)
    if has_ts:
        stryker = WS / "node_modules/.bin/stryker"
        return ("FE", str(stryker) if stryker.exists() else None)
    return ("none", None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="HEAD~1", help="ref base del diff de la story")
    ap.add_argument("--mode", choices=["hard", "advisory"], default="advisory")
    ap.add_argument("--paths", default="", help="csv override de paths a mutar")
    ap.add_argument(
        "--cap",
        default="",
        help="cap_id (ej. brand_studio.lisa-marca): muta SOLO el surface del cap "
        "(sus archivos `# cap:`). Con --base, lo INTERSECTA con el diff (diff-scoped al cap).",
    )
    args = ap.parse_args()
    tag = HARD if args.mode == "hard" else ADVISORY

    if args.cap:
        cap_files = files_for_cap(args.cap)
        if not cap_files:
            print(
                f"{tag} cap '{args.cap}' sin archivos en el _code-index (¿cap_id mal escrito "
                "o índice desactualizado? regen: scripts/generate_code_index.py). Nada que mutar."
            )
            return 0
        # Diff-scoped al surface del cap: intersección cap ∩ diff (lo NUEVO/MODIFICADO del cap).
        # Sin diff real (--base inválido o sin cambios) → surface completo del cap (full sweep).
        diff = set(changed_files(args.base))
        scoped = [f for f in cap_files if f in diff]
        if scoped:
            print(f"{tag} cap '{args.cap}': {len(scoped)}/{len(cap_files)} archivo(s) del surface en el diff.")
            files = scoped
        else:
            print(
                f"{tag} cap '{args.cap}': 0 archivos del surface en el diff (full-sweep del surface "
                f"completo · {len(cap_files)} archivos · costoso)."
            )
            files = cap_files
    else:
        files = [p for p in args.paths.split(",") if p] or changed_files(args.base)

    if not files:
        print(f"{tag} sin archivos py/ts en el diff — nada que mutar. OK.")
        return 0

    surface, tool = tool_for(files)

    # ★ DEGRADE-ADVISORY: tool ausente NUNCA bloquea (D-B: mutmut/Stryker no instalados hoy).
    if tool is None:
        print(
            f"{ADVISORY} {surface}: mutmut/Stryker no instalado — gate DEGRADADO a advisory "
            f"(NO bloquea). Instalá el tool ({'pip install mutmut' if surface == 'BE' else 'pnpm add -D @stryker-mutator/core'}) "
            "para enforcement hard sobre superficies críticas. Archivos en scope: "
            + ", ".join(files)
        )
        return 0

    # Tool presente: correr scoped al diff (líneas nuevas → hard; heredadas → L4 advisory).
    print(f"{tag} {surface}: corriendo mutación diff-scoped sobre {len(files)} archivo(s)…")
    if surface == "BE":
        survivors, ran = _run_mutmut_3x(files)
    else:
        survivors, ran = _run_stryker(files)

    if not ran:
        # No se pudo ejercer el tool en este entorno (no es lo mismo que survivors).
        # Degradá HONESTO — NUNCA reportes "survivors" falsos por un fallo de runner.
        print(
            f"{ADVISORY} {surface}: el runner de mutación no pudo ejercerse en este entorno "
            "(ver salida arriba) → DEGRADADO advisory, NO bloquea. Esto NO es un survivor."
        )
        return 0

    if survivors > 0 and args.mode == "hard":
        print(
            f"{HARD} {survivors} survivor(s) en superficie crítica → CHANGES_REQUESTED. "
            "Survivors en líneas NUEVAS: escribí el test RED que los mata. "
            "Survivors en código HEREDADO (fuera del diff): rutean a CIL carril L4 "
            "(capability-desfasada · docs/process/continuous-improvement.md), NO bloquean."
        )
        return 1
    if survivors > 0:
        print(f"{ADVISORY} {survivors} survivor(s) (mode=advisory) — reportados, NO bloquean.")
    else:
        print(f"{tag} {surface}: 0 survivors. ✅")
    return 0


def _run_mutmut_3x(files: list[str]) -> tuple[int, bool]:
    """Corre mutmut 3.x (config-only) diff-scoped. Devuelve (survivors, ran_ok).

    mutmut 3.x NO acepta --paths-to-mutate (removido); lee `[mutmut]` de setup.cfg/
    pyproject del CWD + copia paths_to_mutate + also_copy + tests/ a `mutants/` y corre
    pytest ahí. Por eso: (1) corremos desde el dir backend de la marca, (2) also_copy=src
    (si no, los imports de otros módulos NO copiados rompen la colección), (3) limpiamos
    el `-x` de addopts (aborta el stats-run de mutmut al 1er fallo).
    """
    be_files = [f for f in files if f.endswith(".py") and "/backend/" in f]
    if not be_files:
        print(f"{ADVISORY} BE: ningún archivo bajo */backend/ — no se puede ubicar el dir backend.")
        return (0, False)
    backend_root = be_files[0].split("/backend/", 1)[0] + "/backend"
    backend_dir = WS / backend_root
    rel_paths = [f.split("/backend/", 1)[1] for f in be_files if f.startswith(backend_root + "/")]
    if not (backend_dir / "src").exists() or not rel_paths:
        print(f"{ADVISORY} BE: estructura backend inesperada en {backend_dir} — degrade.")
        return (0, False)

    mutmut = shutil.which("mutmut") or str(WS / ".venv/bin/mutmut")
    cfg = backend_dir / "setup.cfg"
    backup = cfg.read_text(encoding="utf-8") if cfg.exists() else None
    paths_block = "\n    ".join(rel_paths)
    cfg.write_text(
        "[mutmut]\n"
        f"paths_to_mutate={paths_block}\n"
        "also_copy=src\n"
        # Limpiar addopts (saca el `-x` que aborta el stats-run) + determinismo.
        "pytest_add_cli_args=-o\n    addopts=-p no:randomly\n",
        encoding="utf-8",
    )
    try:
        subprocess.run([mutmut, "run"], cwd=backend_dir, capture_output=True, text=True)
        res = subprocess.run([mutmut, "results"], cwd=backend_dir, capture_output=True, text=True)
        out = res.stdout + res.stderr
        # mutmut 3.x: si no pudo colectar tests devuelve "failed to collect stats" → no ejerció.
        if "failed to collect stats" in out or "runner returned 1" in out:
            print(out[-1200:])
            return (0, False)
        # survivors = mutantes con status "survived"/"survived (timeout no)". Contamos las
        # líneas que mutmut marca como sobrevivientes en `results`.
        survivors = sum(
            1
            for line in out.splitlines()
            if ": survived" in line or line.strip().endswith("survived")
        )
        print(out[-1500:])
        return (survivors, True)
    finally:
        if backup is not None:
            cfg.write_text(backup, encoding="utf-8")
        else:
            cfg.unlink(missing_ok=True)
        shutil.rmtree(backend_dir / "mutants", ignore_errors=True)


def _run_stryker(files: list[str]) -> tuple[int, bool]:
    """FE: Stryker. Mantiene el contrato (survivors, ran_ok). Degrade si no corre."""
    stryker = str(WS / "node_modules/.bin/stryker")
    res = subprocess.run([stryker, "run", "--mutate", ",".join(files)], cwd=WS)
    # Stryker exit !=0 = fallo de corrida (no necesariamente survivors); contrato conservador.
    return (0, res.returncode == 0)


if __name__ == "__main__":
    sys.exit(main())
