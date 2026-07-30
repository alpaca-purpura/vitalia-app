#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""scan_harness_pointers.py — anti-rot de punteros del harness (HB · 2026-06-08).

Escanea los archivos del harness (`.claude/skills/**/SKILL.md`, `.claude/agents/*.md`,
`.claude/rules/*.md`) buscando referencias a paths **workspace-rooted** que NO existen
en el filesystem — la clase de rot que dejó ~25 punteros muertos (process-learnings,
generate_core_modules, e2e-tests.yml, docs/refactors purgados, etc.).

Diseño (defend-the-process, NO otra capa que friccione):
  * Solo flagea paths INEQUÍVOCAMENTE workspace-rooted (primer segmento ∈ ROOT_PREFIXES)
    o skill-relative (`references/...` / `<skill>/references/...`). El shorthand
    module-internal (`api/foo.py`, `domain/enums.py`) se IGNORA — es pedagogía, no puntero.
  * Ignora placeholders (`{brand}`, `<algo>`, globs `*`, `$VAR`, `...`).
  * ADVISORY + baseline-ratchet shrink-only: el baseline (scripts/machinery/
    harness-pointer-baseline.txt) congela los refs muertos conocidos; SOLO los refs
    NUEVOS (no baselined) se reportan como rot fresco. Drenás un ref → lo quitás del
    baseline (shrink-only). Cero bloqueo de commits (lo consume validate_machinery vía warn()).

Uso:
    python3 scripts/scan_harness_pointers.py                 # reporta NEW vs baseline (exit 0)
    python3 scripts/scan_harness_pointers.py --all           # lista TODOS los broken (debug)
    python3 scripts/scan_harness_pointers.py --update-baseline  # congela el scan actual como baseline
    python3 scripts/scan_harness_pointers.py --strict        # exit 1 si hay NEW (para un futuro gate hard)
"""

from __future__ import annotations

import argparse
import re
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

BASELINE = WS / "scripts/machinery/harness-pointer-baseline.txt"

# Archivos del harness que escaneamos.
SCAN_GLOBS = [
    (".claude/skills", "SKILL.md"),
    (".claude/agents", "*.md"),
    (".claude/rules", "*.md"),
]

# Primer segmento de un path → es inequívocamente workspace-rooted.
ROOT_PREFIXES = {
    "docs",
    "core",
    "scripts",
    ".claude",
    ".github",
    "tools",
    "vitalia",
    "nicolify",
    "comunify",
    "lupulo",
    "saasora",
    "inmoflow",
    "retailly",
    "fixia",
    "guestly",
    "fitflow",
}
ROOT_FILES = {"Makefile", "AGENTS.md", "CLAUDE.md", "pyproject.toml", "pnpm-workspace.yaml"}

# Token con extensión conocida dentro de backticks.
TOKEN_RE = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|py|ya?ml|tsx?|sh|json|mjs|toml))`")
# Placeholders que descartan un token (template vars + fechas-plantilla).
PLACEHOLDER_RE = re.compile(r"[{}<>*$]|\.\.\.|YYYY|HHmm|\bMM-DD\b|\bNNN?\b")


def _resolve(ref: str, src_file: Path) -> Path | None:
    """Devuelve el Path absoluto que `ref` debería resolver, o None si NO es un
    puntero workspace-rooted (shorthand module-internal → se ignora)."""
    first = ref.split("/", 1)[0]
    if first in ROOT_PREFIXES or ref in ROOT_FILES:
        return WS / ref
    # bare `references/...` → relativo al skill SOLO si la fuente es un SKILL.md
    # (los skills tienen su propio references/). En agents/rules un `references/X`
    # es shorthand "el references/ del skill mencionado en contexto" → ambiguo, se ignora.
    if ref.startswith("references/"):
        if src_file.name == "SKILL.md":
            return src_file.parent / ref
        return None
    # `<skill>/references/...` → .claude/skills/<skill>/references/... (auto-resoluble)
    m = re.match(r"^([a-z][a-z0-9-]+)/references/", ref)
    if m and (WS / ".claude/skills" / m.group(1)).is_dir():
        return WS / ".claude/skills" / ref
    return None  # ambiguo / module-internal shorthand → no es puntero


def _is_gitignored(target: Path) -> bool:
    """True si `target` matchea una pattern de .gitignore → NO es rot: es un pointer R3
    correcto a un OUTPUT auto-gen (PORTFOLIO/BACKLOG/INFRA-MATRIX · «edita la fuente + regen»),
    que no se versiona y por eso ausente en un worktree fresco. `git check-ignore` matchea por
    pattern aunque el archivo no exista en disco (CHECK 28 false-positive class · HB fix 2026-06-23)."""
    try:
        rel = target.relative_to(WS)
    except ValueError:
        return False
    return (
        subprocess.run(
            ["git", "check-ignore", "-q", str(rel)],
            cwd=WS,
            capture_output=True,
        ).returncode
        == 0
    )


def find_broken_pointers(ws: Path = WS) -> set[str]:
    """Set de `<rel_file> :: <ref>` para cada puntero workspace-rooted roto."""
    broken: set[str] = set()
    for subdir, pattern in SCAN_GLOBS:
        base = ws / subdir
        if not base.exists():
            continue
        for f in base.rglob(pattern):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = f.relative_to(ws)
            for m in TOKEN_RE.finditer(text):
                ref = m.group(1)
                if PLACEHOLDER_RE.search(ref):
                    continue
                target = _resolve(ref, f)
                if target is None:
                    continue
                if not target.exists() and not _is_gitignored(target):
                    broken.add(f"{rel} :: {ref}")
    return broken


def load_baseline() -> set[str]:
    if not BASELINE.exists():
        return set()
    return {
        ln.strip()
        for ln in BASELINE.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    }


def write_baseline(broken: set[str]) -> None:
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# harness-pointer-baseline — refs workspace-rooted ROTOS conocidos (anti-rot, HB 2026-06-08).\n"
        "# Baseline-ratchet SHRINK-ONLY: drená un ref (arreglá el puntero) → quitalo de acá.\n"
        "# NO agregués líneas a mano salvo que ratifiques un ref muerto deliberado.\n"
        "# Regen: python3 scripts/scan_harness_pointers.py --update-baseline\n"
    )
    BASELINE.write_text(header + "\n".join(sorted(broken)) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="anti-rot de punteros del harness")
    ap.add_argument("--all", action="store_true", help="lista TODOS los broken (no solo NEW)")
    ap.add_argument("--update-baseline", action="store_true", help="congela el scan actual como baseline")
    ap.add_argument("--strict", action="store_true", help="exit 1 si hay refs NUEVOS (gate hard futuro)")
    args = ap.parse_args()

    broken = find_broken_pointers()

    if args.update_baseline:
        write_baseline(broken)
        print(f"✓ baseline actualizado: {len(broken)} refs rotos conocidos → {BASELINE.relative_to(WS)}")
        return 0

    baseline = load_baseline()
    new = broken - baseline
    fixed = baseline - broken

    if args.all:
        print(f"TODOS los punteros rotos workspace-rooted ({len(broken)}):")
        for b in sorted(broken):
            print(f"  {b}")
        print()

    print(
        f"harness-pointers: {len(broken)} rotos · baseline {len(baseline)} · NEW {len(new)} · FIXED-vs-baseline {len(fixed)}"
    )
    if fixed:
        print(
            f"  ↓ {len(fixed)} refs del baseline YA están arreglados — corré --update-baseline para drenarlos (shrink-only):"
        )
        for b in sorted(fixed):
            print(f"      ✓ {b}")
    if new:
        print(f"  ⚠ {len(new)} refs ROTOS NUEVOS (rot fresco — arreglá el puntero o ratificá en baseline):")
        for b in sorted(new):
            print(f"      ✗ {b}")
        if args.strict:
            return 1
    else:
        print("  ✓ sin rot nuevo (todos los broken están baselined)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
