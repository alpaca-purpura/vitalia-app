#!/usr/bin/env python3
"""Validate structural YAML integrity of story-folder files.

Closes HB-93 (checkpoint.md frontmatter inválido llegó a `developed` → el cockpit
no parsea la story) y HB-102 (mismo agujero para `04-validators.yaml` /
`06-tickets.yaml`). Un solo `yaml.safe_load` por archivo; si tira, el gate bloquea.

Dispatch por nombre de archivo:
  *checkpoint.md        → valida SOLO el bloque frontmatter (entre los primeros dos `---`)
  *.yaml / *.yml        → valida el archivo completo

Usage:
  validate_story_yaml.py <file> [<file> ...]

Exit: 0 todos válidos · 1 ≥1 inválido (imprime file:line + el error de PyYAML).
Archivos sin frontmatter (checkpoint.md sin `---`) se reportan como inválidos
— un checkpoint sin frontmatter tampoco lo lee el cockpit.
"""

from __future__ import annotations

import sys

try:
    import yaml
except ImportError:  # pragma: no cover - el caller (check shell) degrada si falta
    print("validate_story_yaml: PyYAML no disponible — skip", file=sys.stderr)
    sys.exit(0)


def _frontmatter(text: str) -> str | None:
    """Devuelve el bloque entre los primeros dos `---`, o None si no hay frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None  # abre `---` pero nunca cierra → frontmatter roto


def _err(path: str, exc: Exception) -> None:
    mark = getattr(exc, "problem_mark", None)
    where = f":{mark.line + 1}" if mark is not None else ""
    problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
    print(f"  ✗ {path}{where} — {problem}")


def validate(path: str) -> bool:
    """True si el archivo es YAML estructuralmente válido para su tipo."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"  ✗ {path} — no se pudo leer ({exc})")
        return False

    if path.endswith("checkpoint.md"):
        block = _frontmatter(text)
        if block is None:
            print(f"  ✗ {path} — checkpoint.md sin frontmatter `---...---` válido")
            return False
        try:
            fm = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            _err(path, exc)
            return False
        # HB-91: una story que se mueve a docs/archive/ DEBE estar `state: done`.
        # Fase F (story-closure) archiva con `git mv`; si no flipeó el state, el
        # cockpit (filesystem-as-DB) pinta developed/reviewing sobre algo ya merged.
        if "/docs/archive/" in path.replace("\\", "/") and "/stories/" in path.replace("\\", "/"):
            state = (fm or {}).get("state") if isinstance(fm, dict) else None
            if state != "done":
                print(
                    f"  ✗ {path} — checkpoint archivado con `state: {state!r}` (≠ done). "
                    "Fase F debe flipear `state: done` en el MISMO commit del git mv (HB-91)."
                )
                return False
        return True

    try:
        yaml.safe_load(text)
        return True
    except yaml.YAMLError as exc:
        _err(path, exc)
        return False


def main(argv: list[str]) -> int:
    bad = [p for p in argv if not validate(p)]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
