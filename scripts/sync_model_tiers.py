#!/usr/bin/env python3
"""sync_model_tiers.py — frontmatter `model:` = ARTEFACTO GENERADO desde el seam.

SSoT: project.config.yaml :: models.{tiers,agents,skills} (SLOT 12).
La doctrina habla en TIERS; este script materializa el tier→alias en el
frontmatter literal que Claude Code SÍ lee (no hay interpolación nativa).

Uso:
    python3 scripts/sync_model_tiers.py --check    # reporta drift, exit 1 si hay
    python3 scripts/sync_model_tiers.py --write    # parchea frontmatter desde el seam

Superficies (por nombre, si el archivo existe):
    agents : .claude/agents/{n}.md · .claude-shared/agents/{n}.md · core-harness/agents/{n}.md
    skills : .claude/skills/{n}/SKILL.md · .claude-shared/skills/{n}/SKILL.md

Reglas:
    · valor en agents/skills = tier (flagship|coordinator|workhorse|mechanical)
      O alias literal (fable|opus|sonnet|haiku) — override puntual por superficie.
    · archivo con `model:` en frontmatter SIN entrada en el seam → drift
      (mapa incompleto: agregalo al seam, no al archivo).
    · solo toca la línea `model:` DENTRO del frontmatter (primer bloque ---...---).

machinery CHECK 31 corre `--check`. Swap de modelo = 1 línea en el seam + `make models-sync`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

WS = Path(__file__).resolve().parent.parent
CONFIG = WS / "project.config.yaml"
VALID_ALIASES = {"fable", "opus", "sonnet", "haiku"}

AGENT_DIRS = [".claude/agents", ".claude-shared/agents", "core-harness/agents"]
SKILL_DIRS = [".claude/skills", ".claude-shared/skills"]

FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
MODEL_LINE_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)


def load_models() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    models = cfg.get("models") or {}
    tiers = models.get("tiers") or {}
    agents = models.get("agents") or {}
    skills = models.get("skills") or {}
    if not tiers or not agents or not skills:
        print("ERROR: project.config.yaml::models incompleto (tiers/agents/skills)")
        sys.exit(2)
    return tiers, agents, skills


def resolve(value: str, tiers: dict[str, str]) -> str:
    """tier name → alias; alias literal pasa directo (override puntual)."""
    if value in tiers:
        return tiers[value]
    if value in VALID_ALIASES:
        return value
    print(f"ERROR: valor '{value}' no es tier ({sorted(tiers)}) ni alias ({sorted(VALID_ALIASES)})")
    sys.exit(2)


def frontmatter_model(text: str) -> str | None:
    fm = FRONTMATTER_RE.match(text)
    if not fm:
        return None
    m = MODEL_LINE_RE.search(fm.group(1))
    return m.group(1) if m else None


def patch_model(text: str, new_alias: str) -> str:
    fm = FRONTMATTER_RE.match(text)
    assert fm, "patch_model llamado sin frontmatter"
    body = fm.group(1)
    new_body = MODEL_LINE_RE.sub(f"model: {new_alias}", body, count=1)
    return text[: fm.start(1)] + new_body + text[fm.end(1) :]


def surface_paths(name: str, kind: str) -> list[Path]:
    if kind == "agent":
        return [WS / d / f"{name}.md" for d in AGENT_DIRS]
    return [WS / d / name / "SKILL.md" for d in SKILL_DIRS]


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("--check", "--write"):
        print(__doc__)
        return 2

    tiers, agents, skills = load_models()
    drift: list[str] = []
    patched: list[str] = []
    mapped_files: set[Path] = set()

    for mapping, kind in ((agents, "agent"), (skills, "skill")):
        for name, tier_or_alias in mapping.items():
            want = resolve(str(tier_or_alias), tiers)
            for path in surface_paths(name, kind):
                if not path.exists():
                    continue
                mapped_files.add(path.resolve())
                text = path.read_text(encoding="utf-8")
                have = frontmatter_model(text)
                if have is None:
                    continue  # superficie sin model: (hereda sesión) — el seam no la fuerza
                if have != want:
                    rel = path.relative_to(WS)
                    if mode == "--write":
                        path.write_text(patch_model(text, want), encoding="utf-8")
                        patched.append(f"{rel}: {have} → {want}")
                    else:
                        drift.append(f"{rel}: model={have}, seam dice {want} ({tier_or_alias})")

    # Completitud: archivo con model: en frontmatter SIN entrada en el seam → drift
    for d in AGENT_DIRS + SKILL_DIRS:
        base = WS / d
        if not base.exists():
            continue
        candidates = base.glob("*.md") if "agents" in d else base.glob("*/SKILL.md")
        for path in candidates:
            if path.resolve() in mapped_files:
                continue
            model = frontmatter_model(path.read_text(encoding="utf-8"))
            if model is not None:
                drift.append(
                    f"{path.relative_to(WS)}: model={model} SIN entrada en seam models.* "
                    "(agregalo a project.config.yaml, no edites el archivo)"
                )

    if mode == "--write":
        for line in patched:
            print(f"  ✎ {line}")
        print(f"models-sync: {len(patched)} archivo(s) parcheado(s)")
        # post-write, drift de completitud sigue siendo error
        if drift:
            for line in drift:
                print(f"  ✗ {line}")
            return 1
        return 0

    if drift:
        for line in drift:
            print(f"  ✗ {line}")
        print(f"models-check: DRIFT — {len(drift)} hallazgo(s). Fix: editar seam + `make models-sync`")
        return 1
    print("models-check: OK — frontmatter `model:` = project.config.yaml::models")
    return 0


if __name__ == "__main__":
    sys.exit(main())
