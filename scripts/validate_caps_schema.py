#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""validate_caps_schema.py — Capa 3 del enforcement determinístico (HB-51).

Schema FORMAL (pydantic v2) de una capability YAML. Derivado de
`docs/process/capability-protocol.md` § Sec 2/7/8/11 + `_template.yaml`. Valida CADA
cap de un brand: campos required, tipos, enums (`status`, `change_log[].type`),
formato `functional_area`. Es el gate que ataca "cap malformada llega silenciosa".

Diseño (verify-first · data 2026-06-05):
  · Las caps de comunify/nicolify NO tienen `functional_area` (predatan la dimensión v3).
    Por eso `functional_area` es OPCIONAL — pero si está, su FORMATO se valida.
  · `extra="allow"`: los bloques ricos (scenarios/access/business_rules/dev_preview/
    code_pointers) NO se modelan estrictamente acá (los validan los gates G1-G6 +
    cross_check_3/4). Este schema cubre la IDENTIDAD + enums + formato.
  · ADVISORY por default (exit 0 reportando). `--strict` → exit 1 si hay errores.
    No se prende HARD con fallas conocidas (handoff §0.4).

Parseo robusto: SOLO el frontmatter (las caps traen doc-cola en prosa que rompe
safe_load del stream entero).

Uso:
    python3 scripts/validate_caps_schema.py --brand vitalia
    python3 scripts/validate_caps_schema.py --brand vitalia --strict
    python3 scripts/validate_caps_schema.py --all-brands
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

WS = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
)

# Enums tolerantes a la realidad (data 2026-06-05): caps usan live/beta/planned/
# deprecated/sunset/partial/wip. `partial`/`wip` = in-development (no live aún).
VALID_STATUS = {"live", "beta", "planned", "deprecated", "sunset", "partial", "wip"}
VALID_CHANGE_TYPE = {"new", "fix", "extend", "derive"}
VALID_NATURE = {"feature", "scaffold", "extension-point"}
# functional_area = `<box>.<area>` — 2 segmentos kebab/snake (las áreas del
# SYSTEM-MAP usan `-` Y `_`: onboarding_clinic · patients-records · landing_public).
FA_RE = re.compile(r"^[a-z][a-z0-9_-]*\.[a-z][a-z0-9_-]*$")


class CapSchema(BaseModel):
    """Schema de identidad + enums de una cap. `extra=allow` para los bloques ricos."""

    model_config = ConfigDict(extra="allow")

    slug: str
    status: str
    # module O tech_module (uno de los dos required); se chequea post-parse.
    module: str | None = None
    tech_module: str | None = None
    functional_area: str | None = None
    user_visible: bool | None = None

    @field_validator("status")
    @classmethod
    def _status_enum(cls, v: str) -> str:
        if v not in VALID_STATUS:
            raise ValueError(f"status='{v}' inválido (∈ {sorted(VALID_STATUS)})")
        return v

    @field_validator("functional_area")
    @classmethod
    def _fa_format(cls, v: str | None) -> str | None:
        if v is not None and not FA_RE.match(v):
            raise ValueError(f"functional_area='{v}' no es `<box>.<area>` (2 segmentos kebab/snake)")
        return v


def _frontmatter_text(path: Path) -> str | None:
    """Extrae el TEXTO del frontmatter YAML (sin parsear). None si no hay."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    # salta comentarios/blank lines iniciales hasta el primer '---'
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
        after = body[3:].lstrip("\n")
        return after.split("\n---", 1)[0]
    # Sin fence de apertura (caps reconciladas estilo reconcile_capabilities.py:
    # comentarios + key:values, sin `---`). YAML = hasta el primer separador `---` o EOF.
    return re.split(r"(?m)^---[ \t]*$", body, maxsplit=1)[0]


# ── Loader STRICT que RECHAZA claves duplicadas (igual que js-yaml del cockpit) ──
# PyYAML safe_load TOLERA claves duplicadas (last-wins, sin error) → un cap con
# `map_box:`/`last_modified:` duplicado pasa en Python pero gray-matter/js-yaml del
# cockpit TIRA YAMLException → la cap queda INVISIBLE en el mapa (caja vacía, error
# silencioso · caso 15 caps vitalia 2026-06-05). El validador DEBE ser tan estricto
# como el consumidor real (el cockpit), si no el gate miente.
class _StrictLoader(yaml.SafeLoader):
    pass


def _strict_construct_mapping(loader: _StrictLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"clave duplicada '{key}'",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictLoader.add_constructor(  # type: ignore[no-untyped-call]
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _strict_construct_mapping
)


def strict_parse_error(path: Path) -> str | None:
    """Devuelve un mensaje si la cap NO parsea bajo YAML estricto (incl. claves
    duplicadas) — exactamente el criterio del cockpit (gray-matter/js-yaml). None si OK."""
    fm = _frontmatter_text(path)
    if fm is None:
        return "frontmatter ausente"
    try:
        data = yaml.load(fm, Loader=_StrictLoader)  # noqa: S506 - loader propio sin tags peligrosos
    except yaml.YAMLError as exc:
        msg = str(exc).replace("\n", " ")
        return f"YAML inválido para el cockpit (gray-matter/js-yaml lo rechaza): {msg[:160]}"
    if not isinstance(data, dict):
        return "frontmatter no es un mapping"
    return None


def parse_frontmatter(path: Path) -> dict[str, Any] | None:
    """Parsea SOLO el frontmatter YAML (tolerante · para extraer campos)."""
    yaml_text = _frontmatter_text(path)
    if yaml_text is None:
        return None
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _validate_change_log(data: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    cl = data.get("change_log")
    if cl is None:
        return errs  # opcional (warning aparte)
    if not isinstance(cl, list):
        return [f"change_log debe ser lista, es {type(cl).__name__}"]
    for i, entry in enumerate(cl):
        if not isinstance(entry, dict):
            errs.append(f"change_log[{i}] no es un mapping")
            continue
        t = entry.get("type")
        if t is not None and t not in VALID_CHANGE_TYPE:
            errs.append(f"change_log[{i}].type='{t}' inválido (∈ {sorted(VALID_CHANGE_TYPE)})")
    return errs


def validate_cap(path: Path) -> tuple[list[str], list[str]]:
    """Devuelve (errors, warnings) de una cap."""
    # HARD: parsea bajo el MISMO YAML estricto que el cockpit (claves duplicadas =
    # cap invisible en el mapa). Si falla acá, el cockpit no la puede leer.
    strict_err = strict_parse_error(path)
    if strict_err:
        return ([strict_err], [])
    data = parse_frontmatter(path)
    if data is None:
        return (["frontmatter ausente o no parseable"], [])
    errors: list[str] = []
    warnings: list[str] = []
    try:
        CapSchema.model_validate(data)
    except Exception as exc:  # noqa: BLE001 - agregamos cada error pydantic
        for line in str(exc).splitlines():
            line = line.strip()
            if line and not line.startswith("For further") and "validation error" not in line.lower():
                errors.append(line)
    # module O tech_module
    if not (data.get("module") or data.get("tech_module")):
        errors.append("falta `module` (o `tech_module`)")
    errors.extend(_validate_change_log(data))
    # Recomendados (warning, no error — para no false-blockear brands legacy)
    nature = data.get("nature")
    if nature is not None and nature not in VALID_NATURE:
        warnings.append(f"nature='{nature}' fuera del set canónico {sorted(VALID_NATURE)}")
    if data.get("user_visible") is True and not data.get("dev_preview"):
        warnings.append("user_visible:true sin bloque `dev_preview`")
    if data.get("change_log") is None:
        warnings.append("sin `change_log` (ledger append-only recomendado)")
    return (errors, warnings)


def cap_files(brand: str) -> list[Path]:
    base = WS / brand / "docs" / "product" / "capabilities"
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.yaml") if not p.name.startswith("_") and p.name != "README.md")


def validate_brand(brand: str, strict: bool, show_warnings: bool) -> bool:
    files = cap_files(brand)
    print(f"=== {brand}: {len(files)} caps ===")
    total_errors = 0
    total_warnings = 0
    for f in files:
        errs, warns = validate_cap(f)
        total_errors += len(errs)
        total_warnings += len(warns)
        rel = f.relative_to(WS).as_posix()
        for e in errs:
            print(f"  ❌ {rel}: {e}")
        if show_warnings:
            for w in warns:
                print(f"  ⚠️  {rel}: {w}")
    print(f"  → {total_errors} errores · {total_warnings} warnings")
    if total_errors == 0:
        print("  ✅ schema-válido (0 errores)")
    return not (strict and total_errors > 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand")
    parser.add_argument("--all-brands", action="store_true")
    parser.add_argument("--strict", action="store_true", help="exit 1 si hay errores")
    parser.add_argument("--warnings", action="store_true", help="mostrar warnings (recomendados)")
    args = parser.parse_args()

    if not args.brand and not args.all_brands:
        parser.error("--brand SLUG o --all-brands requerido")

    if args.all_brands:
        brands = [d.name for d in WS.iterdir() if d.is_dir() and (d / "docs" / "product" / "capabilities").is_dir()]
    else:
        brands = [args.brand]

    ok = True
    for brand in sorted(brands):
        ok = validate_brand(brand, args.strict, args.warnings) and ok
        print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
