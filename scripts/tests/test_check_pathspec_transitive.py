"""HB-36 — tests del guard pathspec-transitive (temp git repo)."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


def _load():
    p = Path(__file__).parent.parent / "check_pathspec_transitive.py"
    spec = importlib.util.spec_from_file_location("check_pathspec_transitive", p)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "tsconfig.json").write_text('{"compilerOptions":{"paths":{"@/*":["./src/*"]}}}', encoding="utf-8")
    (repo / "src").mkdir()
    return repo


def test_blocks_untracked_dep(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    repo = _init_repo(tmp_path)
    (repo / "src" / "A.ts").write_text('import { b } from "./B";\nexport const a = b;\n', encoding="utf-8")
    (repo / "src" / "B.ts").write_text("export const b = 1;\n", encoding="utf-8")
    _git(repo, "add", "src/A.ts")  # B queda untracked, fuera del commit
    monkeypatch.chdir(repo)
    assert mod.main() == 1


def test_passes_when_dep_staged(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    repo = _init_repo(tmp_path)
    (repo / "src" / "A.ts").write_text('import { b } from "./B";\nexport const a = b;\n', encoding="utf-8")
    (repo / "src" / "B.ts").write_text("export const b = 1;\n", encoding="utf-8")
    _git(repo, "add", "src/A.ts", "src/B.ts")
    monkeypatch.chdir(repo)
    assert mod.main() == 0


def test_ignores_bare_and_passes_committed_clean(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    repo = _init_repo(tmp_path)
    (repo / "src" / "util.ts").write_text("export const u = 1;\n", encoding="utf-8")
    _git(repo, "add", "src/util.ts")
    _git(repo, "commit", "-qm", "util")
    (repo / "src" / "A.ts").write_text(
        'import x from "react";\nimport { u } from "@/util";\nexport const a = u;\n', encoding="utf-8"
    )
    _git(repo, "add", "src/A.ts")
    monkeypatch.chdir(repo)
    assert mod.main() == 0  # `react` bare → ignorado · `@/util` committed-clean → OK
