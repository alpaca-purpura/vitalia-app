#!/usr/bin/env python3
"""HB-36 — guard pre-commit: un commit por pathspec no debe omitir un archivo LOCAL
importado por un source staged.

El repo prohíbe `git add -A/.` (índice compartido · parallel-safety): cada commit
stagea una lista explícita de rutas. Los gates (tsc/vitest) corren contra el disco,
donde la dep transitiva SÍ está → pasan. Pero el commit AISLADO sólo contiene lo
nombrado; si un import local resuelve a un archivo untracked o modified-unstaged, el
snapshot del commit no compila (rompe en CI o en otro worktree tras el merge).

Para cada `.ts`/`.tsx` staged, extrae sus imports LOCALES (`./ ../ @/`), resuelve a
ruta repo, y FLAGea si la dep está fuera del commit (untracked o modified-unstaged).
Bare specifiers (`react`, `zod`, `next/*`) y workspace pkgs (`@luana/*`) se saltan.
Specifiers que no resuelven a un archivo del repo → warn-not-block (probable type-only/.d.ts).

Usage: check_pathspec_transitive.py        # lee el staged set de git
Exit:  0 OK · 1 ≥1 dep local faltante. Fail-OPEN ante error de git/parse.
"""

from __future__ import annotations

import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

# import x from "S" · export ... from "S" · import "S" · import("S") · require("S")
_IMPORT_RE = re.compile(
    r"""(?:\bfrom\s+|\bimport\s*\(\s*|\brequire\s*\(\s*|\bimport\s+)['"]([^'"]+)['"]"""
)
_SRC_SUFFIXES = (".ts", ".tsx")
_SKIP_DIRS = ("node_modules/", ".next/", "dist/", "/e2e/", "e2e/")
_CANDIDATE_SUFFIXES = (".ts", ".tsx", ".d.ts", "/index.ts", "/index.tsx")


def _git(args: list[str]) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def _repo_root() -> Path:
    return Path(_git(["rev-parse", "--show-toplevel"]).strip())


@lru_cache(maxsize=512)
def _fe_root_for(importer_dir: str) -> Path | None:
    """Nearest ancestor dir con tsconfig.json (la raíz del paquete FE → base de `@/`)."""
    d = Path(importer_dir)
    for cand in [d, *d.parents]:
        if (cand / "tsconfig.json").is_file():
            return cand
    return None


def _resolve_local(spec: str, importer: Path, root: Path) -> Path | None:
    """Resuelve un specifier LOCAL a una ruta repo-relativa (sin sufijo aún). None si no es local."""
    if spec.startswith("."):
        base = (importer.parent / spec).resolve()
    elif spec.startswith("@/"):
        fe = _fe_root_for(str(importer.parent))
        if fe is None:
            return None
        base = (fe / "src" / spec[2:]).resolve()
    else:
        return None  # bare (react/zod/next/...) o @luana/* (workspace pkg) → no es local de este commit
    try:
        return base.relative_to(root)
    except ValueError:
        return None  # fuera del repo


def _first_existing(root: Path, rel: Path) -> Path | None:
    """Primer candidato (rel.ts, rel.tsx, rel/index.ts, …) que es un archivo real del repo."""
    for suf in _CANDIDATE_SUFFIXES:
        cand = Path(str(rel) + suf) if suf.startswith(".") else rel / suf.lstrip("/")
        if (root / cand).is_file():
            return cand
    if (root / rel).is_file():  # ya traía extensión explícita
        return rel
    return None


def main() -> int:
    try:
        root = _repo_root()
        staged = [
            f
            for f in _git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"]).splitlines()
            if f
        ]
    except subprocess.CalledProcessError:
        return 0  # fail-open: sin git context no bloqueamos

    staged_set = set(staged)
    sources = [
        f
        for f in staged
        if f.endswith(_SRC_SUFFIXES) and not any(s in ("/" + f) for s in _SKIP_DIRS)
    ]
    if not sources:
        return 0

    problems: list[str] = []
    for src in sources:
        try:
            content = _git(["show", f":{src}"])  # versión STAGED (no disco)
        except subprocess.CalledProcessError:
            continue
        importer = root / src
        for spec in _IMPORT_RE.findall(content):
            rel = _resolve_local(spec, importer, root)
            if rel is None:
                continue
            dep = _first_existing(root, rel)
            if dep is None:
                continue  # no resuelve a archivo del repo → warn-not-block (type-only/.d.ts)
            dep_str = str(dep)
            if dep_str in staged_set:
                continue  # incluido en el commit
            # No staged: ¿untracked o modified-unstaged? (ambos = fuera del snapshot del commit)
            try:
                unstaged = _git(["diff", "--name-only", "--", dep_str]).strip()
                untracked = _git(["ls-files", "--others", "--exclude-standard", "--", dep_str]).strip()
            except subprocess.CalledProcessError:
                continue
            if untracked:
                problems.append(f"{src} → {dep_str}  (UNTRACKED — nunca committeado)")
            elif unstaged:
                problems.append(f"{src} → {dep_str}  (modified-unstaged — el blob committeado está viejo)")

    if problems:
        for p in dict.fromkeys(problems):  # dedup, preserva orden
            print(f"  ✗ {p}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
