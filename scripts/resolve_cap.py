#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""resolve_cap.py — resuelve `cap_target` (de checkpoint.md) → archivo(s) cap YAML.

Origen: HB-43 (2026-06-04). El "cap-as-locator" estaba dormido porque `cap_target`
→ path del YAML NO es resoluble de forma ingenua: las formas son mixtas —
  · "crm/adrian-embudo"        (module/slug · path-style)
  · "lisa.doctores"           (functional_area · agent.feature)
  · "adrian.inbox"            (functional_area que abarca VARIAS caps → área)
  · "adrian-embudo"           (slug pelado)
  · "vitalia.crm.adrian-embudo" (capability_id)
No hay dir `adrian/`; el archivo vive en `capabilities/{tech_module}/{file-slug}.yaml`.

Este resolver es la pieza determinística que mata el footgun: los agentes
(architect-orchestrator, context-builder, builder-{backend,frontend}) lo llaman en vez
de adivinar el path. Determinístico + testeable (scripts/tests/test_resolve_cap.py) →
NO se vuelve paper-rule: si se rompe, los tests fallan.

Resolución por TIERS (gana el primer tier no-vacío, para no mezclar preciso con fuzzy):
  TIER 1 (preciso):  capability_id · functional_area · slug(==ct o dashed) ·
                     "{module}/{slug}" · "{module}.{slug}" · relpath-sin-.yaml
  TIER 2 (fuzzy):    stem == último segmento de ct (sólo si TIER 1 vacío)

Un `cap_target` que es un ÁREA funcional (`adrian.inbox`) resuelve a N archivos — correcto:
el agente lee el dev_preview de todo el área. Ambigüedad ≠ error.

Uso:
    python3 scripts/resolve_cap.py <brand> "<cap_target>"             # imprime path(s), 1 por línea
    python3 scripts/resolve_cap.py <brand> "<cap_target>" --extract   # + bloque compacto dev_preview/code_ref/scenarios

Exit: 0 si resolvió ≥1 · 2 si 0 matches · 1 si error de uso.

Gating (responsabilidad del CALLER, no de este script): sólo vale la pena llamarlo cuando
`cap_change_type ∈ {fix, extend, derive}` — una cap `new` tiene `dev_preview` vacío (nada
que navegar). El caller lee `cap_change_type` de checkpoint.md antes de invocar.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - el venv root siempre lo trae
    yaml = None  # type: ignore[assignment]

WS = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
)


def _norm(s: str) -> str:
    """Normaliza para comparar: lower + strip + colapsa separadores . / a `/`."""
    return s.strip().lower().replace(".", "/")


def _identity(text: str) -> dict[str, str]:
    """Extrae campos identidad por line-scan robusto (tolera YAML malformado)."""
    out: dict[str, str] = {}
    wanted = ("capability_id", "slug", "functional_area", "module", "tech_module")
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()  # drop inline comment
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if key in wanted and key not in out:
            v = val.strip().strip("'\"")
            if v:
                out[key] = v
    return out


def _cap_root(brand: str, root: Path | None) -> Path:
    return root if root is not None else WS / brand / "docs" / "product" / "capabilities"


def cap_files(brand: str, root: Path | None = None) -> list[Path]:
    base = _cap_root(brand, root)
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.yaml") if not p.name.startswith("_") and p.name != "README.md")


def resolve(brand: str, cap_target: str, root: Path | None = None) -> list[Path]:
    ct = _norm(cap_target)
    ct_dashed = ct.replace("/", "-")  # "lisa/doctores" -> "lisa-doctores"
    ct_tail = ct.rsplit("/", 1)[-1]  # último segmento
    base = _cap_root(brand, root)

    tier1: list[Path] = []
    tier2: list[Path] = []
    for f in cap_files(brand, root):
        ident = _identity(f.read_text(encoding="utf-8", errors="ignore"))
        cap_id = _norm(ident.get("capability_id", ""))
        slug = _norm(ident.get("slug", ""))
        fa = _norm(ident.get("functional_area", ""))
        module = _norm(ident.get("module") or ident.get("tech_module", ""))
        relpath = _norm(str(f.relative_to(base).with_suffix("")))  # "crm/adrian-embudo"
        stem = _norm(f.stem)

        precise = (
            cap_id == ct
            or cap_id.endswith("/" + ct)
            or fa == ct
            or slug == ct
            or slug == ct_dashed
            or relpath == ct
            or (module and (f"{module}/{slug}" == ct))
        )
        if precise:
            tier1.append(f)
        elif stem == ct_tail or stem == ct_dashed:
            tier2.append(f)

    return tier1 if tier1 else tier2


# ════════════════════════════════════════════════════════════════════════════
# TWO-WAY canonical resolution (HB-51 · Capa 1 del enforcement determinístico)
# ════════════════════════════════════════════════════════════════════════════
#
# `resolve()` arriba devuelve PATHS (navegación · área = N archivos). Las
# funciones de abajo devuelven CAP_IDS CANÓNICOS (`{module}.{slug}`) y son la
# pieza que unifica las DOS convenciones de header que rompían el bidirectional:
#   · forma cap_id   `# cap: inbox.adrian-inbox`   (BE · resuelve directo)
#   · forma alias/área `// cap: adrian.inbox`       (FE · functional_area)
# Ambas → el MISMO cap_id canónico `inbox.adrian-inbox`. SSoT único de "qué cap
# es este header" (Capa 5 — elimina la lógica de resolución paralela map-vs-índice).
#
# ★ Corrección de diseño verificada contra data (2026-06-05): `functional_area`
# NO es un alias 1:1 de un cap — es la AREA del cockpit (`${box}.${area}`) y es
# 1:N (ej. `configuracion.admin` → 5 caps live; `plataforma-tecnica.platform` → 5).
# Por eso `resolve_cap_ids` devuelve un SET y G1 pasa con ≥1. El caso `adrian.inbox`
# da 1 cap live por live-filter (las otras 2 son deprecated/superseded), por eso
# `canonical_cap_id("adrian.inbox") == "inbox.adrian-inbox"`. Ver
# docs/process/cap-deterministic-enforcement.md § Capa 1 (premisa "exactly one" corregida).

# Tokens reservados que NO son caps (markers de header) — nunca resuelven.
SPECIAL_MARKERS = frozenset({"__shared__", "__orphan__", "__skip__", "TBD", "null", "none", ""})

_LIVE_STATUSES = frozenset({"", "live", "beta"})  # "no superseded" se chequea aparte


def _cap_meta(path: Path) -> dict[str, str]:
    """Identidad + status + superseded_by por line-scan robusto (tolera YAML malformado)."""
    out: dict[str, str] = {}
    wanted = (
        "capability_id",
        "slug",
        "functional_area",
        "module",
        "tech_module",
        "status",
        "superseded_by",
    )
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip() == "---" and out:
            break  # fin del frontmatter
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if key in wanted and key not in out:
            v = val.strip().strip("'\"")
            if v:
                out[key] = v
    return out


class _CapRecord:
    """Un cap normalizado: cap_id canónico + formas-alias + flags de vida."""

    __slots__ = ("path", "cap_id", "functional_area", "status", "superseded_by", "is_live", "_meta", "_base")

    def __init__(self, path: Path, base: Path) -> None:
        meta = _cap_meta(path)
        # cap_id canónico = `{parent-dir}.{slug-o-stem}` — MISMA regla que
        # validate_code_cap_bidirectional.load_capabilities (un solo SSoT de cap_id).
        module = path.parent.name
        slug = meta.get("slug") or path.stem
        self.path = path
        self.cap_id = f"{module}.{slug}"
        self.functional_area = meta.get("functional_area", "")
        self.status = (meta.get("status") or "").lower()
        self.superseded_by = meta.get("superseded_by", "")
        self.is_live = (self.status in _LIVE_STATUSES) and not self.superseded_by
        # Pre-computa las formas-alias (norm) → para indexar
        self._meta = meta
        self._base = base

    def identity_forms(self) -> set[str]:
        """Formas IDENTIDAD (tier 1 · exact-match gana sobre área): cap_id, capability_id, slug, relpath."""
        m = self._meta
        forms = {self.cap_id, m.get("capability_id", ""), m.get("slug", "")}
        mod_field = m.get("module") or m.get("tech_module", "")
        if mod_field and m.get("slug"):
            forms.add(f"{mod_field}.{m['slug']}")  # cap_id vía campo module (si difiere del dir)
        try:
            forms.add(str(self.path.relative_to(self._base).with_suffix("")))  # crm/adrian-embudo
        except ValueError:
            pass
        return {_norm(x) for x in forms if x}

    def area_forms(self) -> set[str]:
        """Formas ALIAS/ÁREA (tier 2): functional_area + variantes module-prefijadas/dashed."""
        fa = self.functional_area
        if not fa:
            return set()
        module = self.path.parent.name
        mod_field = self._meta.get("module") or self._meta.get("tech_module") or module
        fa_dashed = fa.replace(".", "-")  # mateo.agenda -> mateo-agenda
        forms = {
            fa,  # adrian.inbox · lisa.doctores
            fa_dashed,  # mateo-agenda (bare)
            f"{module}.{fa}",  # clinics.lisa.doctores ({module}.{fa})
            f"{module}.{fa_dashed}",  # scheduling.mateo-agenda ({module}.{fa-dashed})
            f"{mod_field}.{fa}",
            f"{mod_field}.{fa_dashed}",
        }
        return {_norm(x) for x in forms if x}


# Cache por (brand, root) → (records, identity_index, area_index).
_RESOLVER_CACHE: dict[tuple[str, str], tuple[list[_CapRecord], dict[str, set[str]], dict[str, set[str]]]] = {}


def _load_resolver(
    brand: str, root: Path | None = None
) -> tuple[list[_CapRecord], dict[str, set[str]], dict[str, set[str]]]:
    key = (brand, str(root) if root is not None else "")
    cached = _RESOLVER_CACHE.get(key)
    if cached is not None:
        return cached
    base = _cap_root(brand, root)
    records: list[_CapRecord] = []
    identity_index: dict[str, set[str]] = {}
    area_index: dict[str, set[str]] = {}
    for f in cap_files(brand, root):
        rec = _CapRecord(f, base)
        records.append(rec)
        for form in rec.identity_forms():
            identity_index.setdefault(form, set()).add(rec.cap_id)
        for form in rec.area_forms():
            area_index.setdefault(form, set()).add(rec.cap_id)
    result = (records, identity_index, area_index)
    _RESOLVER_CACHE[key] = result
    return result


def clear_resolver_cache() -> None:
    """Tests que mutan caps en tmp deben limpiar el cache entre asserts."""
    _RESOLVER_CACHE.clear()


def resolve_cap_ids(brand: str, token: str, *, live_only: bool = False, root: Path | None = None) -> set[str]:
    """Resuelve un header/cap_target → set de cap_ids canónicos (`{module}.{slug}`).

    Dos vías + tiers: las formas IDENTIDAD (cap_id/capability_id/slug/relpath) ganan
    sobre las ÁREA (functional_area + variantes); si ninguna identidad matchea, se usa
    la(s) cap(s) del área. `live_only=True` filtra a live non-superseded (la respuesta
    CANÓNICA del alias). Token vacío/marker → set vacío. ≥1 ⇒ G1 pasa.
    """
    if token is None:
        return set()
    t = token.strip()
    if t in SPECIAL_MARKERS or _norm(t) == "":
        return set()
    records, identity_index, area_index = _load_resolver(brand, root)
    nt = _norm(t)
    ids = identity_index.get(nt) or area_index.get(nt) or set()
    if not ids:
        return set()
    if live_only:
        by_id = {r.cap_id: r for r in records}
        live = {c for c in ids if by_id.get(c) and by_id[c].is_live}
        return live
    return set(ids)


def canonical_cap_id(brand: str, token: str, root: Path | None = None) -> str | None:
    """El cap_id canónico ÚNICO de un token, o None si es ambiguo/no resuelve.

    Prefiere la cap live non-superseded (alias → cap canónica). `adrian.inbox` y
    `inbox.adrian-inbox` → ambos `"inbox.adrian-inbox"`.
    """
    live = resolve_cap_ids(brand, token, live_only=True, root=root)
    if len(live) == 1:
        return next(iter(live))
    allids = resolve_cap_ids(brand, token, live_only=False, root=root)
    if len(allids) == 1:
        return next(iter(allids))
    return None


def functional_area_of(brand: str, cap_id: str, root: Path | None = None) -> str | None:
    """cap_id canónico → su `functional_area` (alias secundario), o None."""
    records, _, _ = _load_resolver(brand, root)
    for r in records:
        if r.cap_id == cap_id:
            return r.functional_area or None
    return None


def cap_id_of(path: Path, brand: str | None = None, root: Path | None = None) -> str | None:
    """Path de un cap YAML → su cap_id canónico. `brand`/`root` opcionales (deriva el base dir)."""
    p = Path(path)
    if root is not None:
        base = root
    elif brand is not None:
        base = _cap_root(brand, None)
    else:
        # deriva: .../capabilities/{module}/{slug}.yaml → base = .../capabilities
        base = p.parent.parent
    rec = _CapRecord(p, base)
    return rec.cap_id


def _extract_block(f: Path) -> str:
    try:
        rel = f.relative_to(WS)
    except ValueError:  # fixture fuera de WS (tests)
        rel = f
    lines = [f"# cap: {rel}"]
    data: dict | None = None
    if yaml is not None:
        # Las cap YAML traen >1 documento (`---`) y el doc-cola suele ser prosa
        # malformada (colon suelto) que revienta safe_load_all entero. Split por
        # separador + parse por chunk con try/except → un doc roto no tumba el resto.
        merged: dict = {}
        for chunk in re.split(r"(?m)^---[ \t]*$", f.read_text(encoding="utf-8", errors="ignore")):
            if not chunk.strip():
                continue
            try:
                doc = yaml.safe_load(chunk)
            except Exception:  # noqa: BLE001 - extract es best-effort
                continue
            if isinstance(doc, dict):
                merged.update(doc)
        data = merged or None
    if not isinstance(data, dict):
        lines.append("  (no parseable — leé el archivo directo)")
        return "\n".join(lines)

    lines.append(f"  slug: {data.get('slug')} · status: {data.get('status')}")
    pkg = data.get("package_path")
    if pkg:
        lines.append(f"  package_path: {pkg}")

    dp = data.get("dev_preview")
    if isinstance(dp, dict):
        mc = dp.get("main_component")
        if mc:
            lines.append(f"  dev_preview.main_component: {mc}")
        for key in ("backend_endpoint", "backend_endpoints", "api", "route", "primary_route"):
            if dp.get(key):
                lines.append(f"  dev_preview.{key}: {dp[key]}")
        eps = dp.get("entry_points")
        if isinstance(eps, list):
            for ep in eps:
                if isinstance(ep, dict) and ep.get("path"):
                    lines.append(f"  entry_point: {ep['path']} (roles={ep.get('roles')})")
    elif dp:
        lines.append(f"  dev_preview: {dp}")

    brs = data.get("business_rules")
    if isinstance(brs, list):
        refs = [b["code_ref"] for b in brs if isinstance(b, dict) and b.get("code_ref")]
        for r in refs:
            lines.append(f"  code_ref: {r}")

    scs = data.get("scenarios")
    if isinstance(scs, list):
        names = []
        for s in scs:
            if isinstance(s, dict):
                names.append(str(s.get("id") or s.get("name") or s.get("title") or "?"))
        if names:
            lines.append(f"  scenarios ({len(names)}): {', '.join(names[:12])}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    extract = "--extract" in argv
    if len(args) != 2:
        print("uso: resolve_cap.py <brand> <cap_target> [--extract]", file=sys.stderr)
        return 1
    brand, cap_target = args
    if cap_target.lower() in ("null", "none", ""):
        print(f"UNRESOLVED: cap_target nulo ({cap_target!r}) — cap `new` sin hogar o story sin cap", file=sys.stderr)
        return 2

    matches = resolve(brand, cap_target)
    if not matches:
        print(f"UNRESOLVED: ningún cap matchea '{cap_target}' en {brand}/docs/product/capabilities/", file=sys.stderr)
        return 2

    if extract:
        if len(matches) > 1:
            print(f"# {len(matches)} caps en el área '{cap_target}' — navegá los punteros de TODAS:")
        for f in matches:
            print(_extract_block(f))
    else:
        for f in matches:
            print(f.relative_to(WS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
