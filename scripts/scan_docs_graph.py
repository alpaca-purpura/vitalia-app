#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""scan_docs_graph.py — grafo de consumo de root docs/ (DOCS-SWEEP 2026-06-10).

Para cada doc tracked bajo `docs/` computa INBOUND refs desde superficies vivas
(`.claude/**`, `core-harness/**`, `scripts/**`, `tools/luana-cockpit/src/**`,
`Makefile`, `CLAUDE.md`, `AGENTS.md`, `{brand}/CLAUDE.md`, `project.config.yaml`)
y edges docs↔docs para CLAUSURA TRANSITIVA: un doc está VIVO si es alcanzable
desde una superficie viva; un doc citado SOLO por docs muertos está MUERTO.

Reusa el workspace-root discovery de `scan_harness_pointers.py` (import, no dup).
Tiers de evidencia: file (path exacto, braces `{a,b}` expandidas) > glob
(placeholder `{date}`/`<x>` → fnmatch) > dir (dir citado ⇒ contenido vivo débil).

Outputs:
    docs/process/DOCS-GRAPH.md        reporte humano (gitignored, regenerable)
    docs/process/_docs-graph.json     edge-list (gitignored)
    docs/process/HARNESS-DOCS.manifest  (--manifest) lista vivos TRACKED — source
                                        = este scanner; editar a mano PROHIBIDO

Uso:
    python3 scripts/scan_docs_graph.py                # reporte + json
    python3 scripts/scan_docs_graph.py --manifest     # además regenera el manifest
    python3 scripts/scan_docs_graph.py --check-manifest  # exit 1 si manifest desactualizado
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_harness_pointers import WS as DEFAULT_WS  # noqa: E402 — reuse, no dup

# Superficies vivas (dirs rglob + files sueltos). git-hooks viven dentro de
# scripts/ y core-harness/hooks/ — cubiertos por los dirs.
SURFACE_DIRS = (".claude", "scripts", "tools/cockpit/ui/app")
SURFACE_FILES = ("Makefile", "CLAUDE.md", "AGENTS.md", "project.config.yaml")
SURFACE_EXTS = {".md", ".py", ".sh", ".js", ".mjs", ".ts", ".tsx", ".yaml", ".yml", ".json", ".toml"}
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".venv", ".next", "dist", ".git"}

# Outputs de este scanner + manifest: NUNCA cuentan como fuente NI como corpus
# (citan todos los paths — revivirían huérfanos circularmente).
OUTPUT_BASENAMES = {"DOCS-GRAPH.md", "_docs-graph.json", "HARNESS-DOCS.manifest"}
# El scanner y su test contienen literales docs/ (clasificación + fixtures).
SOURCE_EXCLUDE_BASENAMES = OUTPUT_BASENAMES | {"scan_docs_graph.py", "test_scan_docs_graph.py"}

# Tokens path-like que terminan en extensión doc (backticks NO requeridos —
# cockpit/scripts citan paths en strings de código).
FILE_TOKEN_RE = re.compile(r"(?:\.\./|\./)?(?:[\w{}<>,$*@.-]+/)*[\w{}<>,$*@.-]+\.(?:md|ya?ml|json|txt|html)\b")
# Dir refs explícitos workspace-rooted: `docs/.../` con trailing slash.
# Lookbehind: NO matchear el substring `docs/` dentro de `{brand}/docs/...`
# (paths brand-scoped NO son refs a root docs/).
DIR_TOKEN_RE = re.compile(r"(?<![\w/.-])docs/[\w{}<>,$*.-]+(?:/[\w{}<>,$*.-]+)*/(?![\w{}<>,$*.-])")

BRACE_RE = re.compile(r"\{([^{}]*)\}")
KIND_PRIORITY = {"file": 0, "glob": 1, "dir": 2}


def extract_path_tokens(text: str) -> set[str]:
    """Tokens path-like (files con extensión doc + dirs docs/.../ explícitos)."""
    toks = set(FILE_TOKEN_RE.findall(text))
    toks |= set(DIR_TOKEN_RE.findall(text))
    return toks


def expand_token(tok: str) -> list[str]:
    """Expande braces con coma a variantes; placeholders ({x}, <x>, $VAR) → glob `*`."""
    m = BRACE_RE.search(tok)
    if m:
        inner = m.group(1)
        if "," in inner:
            out: list[str] = []
            for part in inner.split(","):
                out.extend(expand_token(tok[: m.start()] + part.strip() + tok[m.end() :]))
            return out
        return expand_token(tok[: m.start()] + "*" + tok[m.end() :])
    out_tok = re.sub(r"<[^<>]*>", "*", tok)
    out_tok = re.sub(r"\$\w+", "*", out_tok)
    return [out_tok]


def _resolve(variant: str, src_rel: str) -> str | None:
    """Path candidato workspace-rooted bajo docs/, o None si no es resoluble."""
    if variant.startswith("docs/"):
        return posixpath.normpath(variant)
    # Relativo: solo dentro de docs/ (docs↔docs); en superficies solo cuenta docs/-rooted.
    if src_rel.startswith("docs/"):
        cand = posixpath.normpath(posixpath.join(posixpath.dirname(src_rel), variant))
        if cand.startswith("docs/"):
            return cand
    return None


@dataclass
class Graph:
    docs: dict[str, dict] = field(default_factory=dict)
    edges: list[dict] = field(default_factory=list)
    alive: set[str] = field(default_factory=set)


def _iter_surface_files(ws: Path):
    seen: set[Path] = set()
    for d in SURFACE_DIRS:
        base = ws / d
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in f.parts):
                continue
            if f.suffix not in SURFACE_EXTS:
                continue
            if f.name in SOURCE_EXCLUDE_BASENAMES:
                continue
            real = f.resolve()
            if real in seen:  # symlinks .claude/rules → core-harness: dedup
                continue
            seen.add(real)
            yield f
    for name in SURFACE_FILES:
        f = ws / name
        if f.is_file():
            yield f
    for f in ws.glob("*/CLAUDE.md"):  # brand overlays
        if f.is_file():
            yield f


def _edges_from_text(ws: Path, src_rel: str, text: str, corpus: set[str], src_type: str) -> list[dict]:
    edges: list[dict] = []
    for tok in extract_path_tokens(text):
        is_dir = tok.endswith("/")
        for variant in expand_token(tok):
            if is_dir:
                # Dir-edges SOLO desde superficies vivas: un doc que menciona un dir
                # al pasar NO revive su contenido (laundering de vida — fan-outs >1000).
                if src_type != "surface" or "*" in variant:
                    continue
                dirpath = posixpath.normpath(variant)
                for dst in corpus:
                    if dst.startswith(dirpath + "/") and dst != src_rel:
                        edges.append({"src": src_rel, "dst": dst, "kind": "dir", "src_type": src_type})
                continue
            cand = _resolve(variant, src_rel)
            if cand is None:
                continue
            if "*" in cand:
                # Glob path-aware: `*` NO cruza `/` (fnmatch sí lo haría —
                # `docs/learnings/*-*.md` no debe matchear subdirs).
                rx = re.compile("^" + re.escape(cand).replace("\\*", "[^/]*") + "$")
                for dst in corpus:
                    if rx.match(dst) and dst != src_rel:
                        edges.append({"src": src_rel, "dst": dst, "kind": "glob", "src_type": src_type})
            elif cand in corpus and cand != src_rel:
                edges.append({"src": src_rel, "dst": cand, "kind": "file", "src_type": src_type})
    return edges


def build_graph(ws: Path, corpus: list[str]) -> Graph:
    corpus_set = {c for c in corpus if posixpath.basename(c) not in OUTPUT_BASENAMES}
    g = Graph(
        docs={rel: {"liveness": None, "via": None, "strength": None, "evidence": []} for rel in sorted(corpus_set)}
    )

    # 1 · edges desde superficies vivas
    for f in _iter_surface_files(ws):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = f.relative_to(ws).as_posix()
        g.edges.extend(_edges_from_text(ws, rel, text, corpus_set, "surface"))

    # 2 · edges docs↔docs
    for rel in sorted(corpus_set):
        f = ws / rel
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        g.edges.extend(_edges_from_text(ws, rel, text, corpus_set, "doc"))

    # 3 · clausura con STRENGTH = peor link del camino (file < glob < dir),
    # relajación a fixpoint (un doc puede ser alcanzable por varios caminos —
    # gana el más fuerte). El strength permite distinguir "vivo por path exacto"
    # de "vivo solo porque un dir entero está citado" al juzgar el sweep.
    surface_edges = [e for e in g.edges if e["src_type"] == "surface"]
    doc_edges = [e for e in g.edges if e["src_type"] == "doc"]

    strength: dict[str, int] = {}
    direct_kind: dict[str, int] = {}
    for e in surface_edges:
        k = KIND_PRIORITY[e["kind"]]
        d = e["dst"]
        if k < direct_kind.get(d, 99):
            direct_kind[d] = k
        if k < strength.get(d, 99):
            strength[d] = k

    changed = True
    while changed:
        changed = False
        for e in doc_edges:
            s, d = e["src"], e["dst"]
            if s not in strength:
                continue
            k = max(strength[s], KIND_PRIORITY[e["kind"]])
            if k < strength.get(d, 99):
                strength[d] = k
                changed = True

    g.alive = set(strength)
    kind_name = {v: k for k, v in KIND_PRIORITY.items()}
    for d in g.alive:
        info = g.docs[d]
        info["strength"] = kind_name[strength[d]]
        if d in direct_kind:
            info["liveness"] = "direct"
            info["via"] = kind_name[direct_kind[d]]
        else:
            info["liveness"] = "transitive"

    # evidence (≤3, surface-first) + via para transitivos (primer edge desde src vivo)
    ordered = sorted(g.edges, key=lambda e: (e["src_type"] != "surface", KIND_PRIORITY[e["kind"]]))
    for e in ordered:
        d = e["dst"]
        if d not in g.alive:
            continue
        if e["src_type"] == "doc" and e["src"] not in g.alive:
            continue
        info = g.docs[d]
        if info["via"] is None:
            info["via"] = e["kind"]
        if e["src"] not in info["evidence"] and len(info["evidence"]) < 3:
            info["evidence"].append(e["src"])
    return g


PROGRAM_RECORD_RE = re.compile(r"docs/process/harness-refactor-w[^/]*/")


def classify_docs(ws: Path, graph: Graph) -> dict[str, str]:
    """Clase por doc: detail-pareado · program-record · SSoT-vivo · vivo-transitivo · huérfano."""
    classes: dict[str, str] = {}
    for rel, info in graph.docs.items():
        base = posixpath.basename(rel)
        if rel.startswith("docs/rules-detail/") and (ws / ".claude/rules" / base).exists():
            classes[rel] = "detail-pareado"  # rule viva ⇒ detail vivo, sin excepción
        elif PROGRAM_RECORD_RE.search(rel):
            classes[rel] = "program-record"
        elif info["liveness"] == "direct":
            classes[rel] = "SSoT-vivo"
        elif info["liveness"] == "transitive":
            classes[rel] = "vivo-transitivo"
        else:
            classes[rel] = "huérfano"
    return classes


def render_report(ws: Path, graph: Graph, classes: dict[str, str]) -> str:
    counts: dict[str, int] = {}
    by_dir: dict[str, list[str]] = {}
    for rel in graph.docs:
        counts[classes[rel]] = counts.get(classes[rel], 0) + 1
        parts = rel.split("/")
        top = "/".join(parts[:2]) if len(parts) > 2 else "docs (raíz)"
        by_dir.setdefault(top, []).append(rel)

    lines = [
        "# DOCS-GRAPH — grafo de consumo de root docs/ (auto-gen, NO editar)",
        "",
        f"Regen: `python3 scripts/scan_docs_graph.py` · docs analizados: {len(graph.docs)}",
        "",
        "## Resumen por clase",
        "",
        "| clase | count |",
        "|---|---|",
    ]
    for cls in sorted(counts, key=lambda c: -counts[c]):
        lines.append(f"| {cls} | {counts[cls]} |")
    lines.append("")
    for top in sorted(by_dir):
        docs = by_dir[top]
        n_dead = sum(1 for d in docs if classes[d] == "huérfano")
        lines.append(f"## {top} ({len(docs)} docs · {n_dead} huérfanos)")
        lines.append("")
        for rel in sorted(docs):
            info = graph.docs[rel]
            ev = f" ← {info['evidence'][0]}" if info["evidence"] else ""
            via = f" [{info['via']}]" if info["via"] else ""
            lines.append(f"- `{rel}` · **{classes[rel]}**{via}{ev}")
        lines.append("")
    return "\n".join(lines)


def render_manifest(graph: Graph, classes: dict[str, str]) -> str:
    """Manifest tracked: SOLO docs vivos (clase ≠ huérfano) + consumidor principal.

    Source = este scanner; el manifest es OUTPUT committeado. Editar a mano PROHIBIDO.
    """
    lines = [
        "# HARNESS-DOCS.manifest — docs vivos bajo root docs/ (DOCS-SWEEP gate).",
        "# AUTO-GEN por scripts/scan_docs_graph.py --manifest — editar a mano PROHIBIDO.",
        "# Formato: <path> · <clase> · <consumidor principal>",
    ]
    for rel in sorted(graph.docs):
        if classes[rel] == "huérfano":
            continue
        ev = graph.docs[rel]["evidence"]
        lines.append(f"{rel} · {classes[rel]} · {ev[0] if ev else '(par/clase)'}")
    return "\n".join(lines) + "\n"


def _tracked_corpus(ws: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "docs"], cwd=ws, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    exts = (".md", ".yaml", ".yml", ".json", ".txt", ".html")
    return [ln for ln in out if ln.endswith(exts)]


def main() -> int:
    ap = argparse.ArgumentParser(description="grafo de consumo de root docs/")
    ap.add_argument("--manifest", action="store_true", help="regenera HARNESS-DOCS.manifest")
    ap.add_argument("--check-manifest", action="store_true", help="exit 1 si el manifest tracked está desactualizado")
    args = ap.parse_args()

    ws = DEFAULT_WS
    graph = build_graph(ws, _tracked_corpus(ws))
    classes = classify_docs(ws, graph)

    report_path = ws / "docs/process/DOCS-GRAPH.md"
    report_path.write_text(render_report(ws, graph, classes), encoding="utf-8")
    (ws / "docs/process/_docs-graph.json").write_text(
        json.dumps(graph.edges, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    manifest = render_manifest(graph, classes)
    manifest_path = ws / "docs/process/HARNESS-DOCS.manifest"
    if args.check_manifest:
        current = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
        if current != manifest:
            print("✗ HARNESS-DOCS.manifest desactualizado — corré: python3 scripts/scan_docs_graph.py --manifest")
            return 1
        print("✓ HARNESS-DOCS.manifest al día")
        return 0
    if args.manifest:
        manifest_path.write_text(manifest, encoding="utf-8")
        print(f"✓ manifest regenerado → {manifest_path.relative_to(ws)}")

    n_dead = sum(1 for c in classes.values() if c == "huérfano")
    print(
        f"docs-graph: {len(graph.docs)} docs · {len(graph.alive)} vivos-por-grafo · "
        f"{n_dead} huérfanos · reporte → {report_path.relative_to(ws)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
