"""Tests TDD para scan_docs_graph.py (DOCS-SWEEP 2026-06-10).

Workspace sintético en tmp_path — el scanner recibe ws + corpus explícitos
(no depende de git en tests).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scan_docs_graph import (  # noqa: E402
    build_graph,
    classify_docs,
    expand_token,
    extract_path_tokens,
    render_manifest,
    render_report,
)


@pytest.fixture()
def ws(tmp_path: Path) -> Path:
    """Workspace sintético: superficies vivas + docs corpus."""
    # --- superficies vivas ---
    (tmp_path / ".claude/rules").mkdir(parents=True)
    (tmp_path / ".claude/rules/some-rule.md").write_text(
        "Detalle en `docs/rules-detail/some-rule.md` — load on-demand.\n"
        "Ver tabla `docs/process/{ticket-states,checkpoint-protocol}.md`.\n"
        "Learnings: `docs/learnings/{date}-{slug}.md`.\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/some_gate.py").write_text(
        'SSOT = "docs/process/lifecycle.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "tools/luana-cockpit/src").mkdir(parents=True)
    (tmp_path / "tools/luana-cockpit/src/route.ts").write_text(
        "const p = path.join(root, 'docs/process/harness-backlog.md')\nconst dir = 'docs/learnings/tooling/'\n",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text(
        "Vista master: `docs/portfolio/PORTFOLIO.md`.\n",
        encoding="utf-8",
    )

    # --- docs corpus ---
    d = tmp_path / "docs"
    for sub in (
        "rules-detail",
        "process",
        "learnings/tooling",
        "portfolio",
        "architecture/luana-platform",
        "old-stuff",
    ):
        (d / sub).mkdir(parents=True)

    (d / "rules-detail/some-rule.md").write_text("detalle\n", encoding="utf-8")
    (d / "process/ticket-states.md").write_text("estados\n", encoding="utf-8")
    (d / "process/checkpoint-protocol.md").write_text("ckpt\n", encoding="utf-8")
    (d / "process/lifecycle.md").write_text(
        # docs↔docs: lifecycle (vivo directo) cita un ADR → transitivo vivo
        "Ver `docs/architecture/luana-platform/ADR-010-orquestacion.md`.\n",
        encoding="utf-8",
    )
    (d / "process/harness-backlog.md").write_text("HB\n", encoding="utf-8")
    (d / "learnings/tooling/2026-01-01-algo.md").write_text("l\n", encoding="utf-8")
    (d / "learnings/2026-02-02-otro.md").write_text("l2\n", encoding="utf-8")
    (d / "portfolio/PORTFOLIO.md").write_text("p\n", encoding="utf-8")
    (d / "architecture/luana-platform/ADR-010-orquestacion.md").write_text("adr\n", encoding="utf-8")
    # huérfano puro
    (d / "old-stuff/dead-doc.md").write_text("nadie me cita\n", encoding="utf-8")
    # cadena muerta: dead-a cita dead-b → ambos huérfanos (clausura desde superficies)
    (d / "old-stuff/dead-a.md").write_text("ver `docs/old-stuff/dead-b.md`\n", encoding="utf-8")
    (d / "old-stuff/dead-b.md").write_text("b\n", encoding="utf-8")
    # relativo dentro de docs: INDEX cita sibling por path relativo
    (d / "process/INDEX.md").write_text("- [estados](ticket-states.md)\n", encoding="utf-8")

    return tmp_path


def _corpus(ws: Path) -> list[str]:
    return sorted(str(p.relative_to(ws)) for p in (ws / "docs").rglob("*.md"))


# ─── extract_path_tokens ────────────────────────────────────────────────


def test_extract_tokens_backticks_and_plain() -> None:
    text = "ver `docs/process/lifecycle.md` y docs/learnings/x.md y 'docs/process/foo.md'"
    toks = extract_path_tokens(text)
    assert "docs/process/lifecycle.md" in toks
    assert "docs/learnings/x.md" in toks
    assert "docs/process/foo.md" in toks


def test_extract_tokens_dir_refs() -> None:
    toks = extract_path_tokens("lee docs/promotion-protocol/proposals/ y `docs/learnings/tooling/`")
    assert "docs/promotion-protocol/proposals/" in toks
    assert "docs/learnings/tooling/" in toks


def test_brand_scoped_dir_not_matched_as_root() -> None:
    # `{brand}/docs/...` NO es ref a root docs/ — el lookbehind lo excluye.
    toks = extract_path_tokens("ver vitalia/docs/product/stories/ y `nicolify/docs/learnings/`")
    assert not any(t.startswith("docs/") for t in toks)


# ─── expand_token (braces + placeholders → variantes/globs) ─────────────


def test_expand_brace_comma() -> None:
    out = expand_token("docs/process/{ticket-states,checkpoint-protocol}.md")
    assert out == ["docs/process/ticket-states.md", "docs/process/checkpoint-protocol.md"]


def test_expand_placeholder_to_glob() -> None:
    out = expand_token("docs/learnings/{date}-{slug}.md")
    assert out == ["docs/learnings/*-*.md"]


def test_expand_plain_passthrough() -> None:
    assert expand_token("docs/process/lifecycle.md") == ["docs/process/lifecycle.md"]


# ─── build_graph + closure ──────────────────────────────────────────────


def test_direct_surface_refs_alive(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    alive = graph.alive
    assert "docs/rules-detail/some-rule.md" in alive  # backtick desde rule
    assert "docs/process/lifecycle.md" in alive  # string en script .py
    assert "docs/process/harness-backlog.md" in alive  # cockpit literal
    assert "docs/portfolio/PORTFOLIO.md" in alive  # CLAUDE.md
    assert "docs/process/ticket-states.md" in alive  # brace expansion
    assert "docs/process/checkpoint-protocol.md" in alive


def test_glob_placeholder_marks_learnings_alive(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    assert "docs/learnings/2026-02-02-otro.md" in graph.alive  # {date}-{slug} glob
    info = graph.docs["docs/learnings/2026-02-02-otro.md"]
    assert info["via"] == "glob"


def test_dir_ref_marks_contents_alive_weak(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    rel = "docs/learnings/tooling/2026-01-01-algo.md"
    assert rel in graph.alive
    assert graph.docs[rel]["via"] in ("dir", "glob")  # glob {date}-{slug} no matchea subdir


def test_transitive_closure_doc_to_doc(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    adr = "docs/architecture/luana-platform/ADR-010-orquestacion.md"
    assert adr in graph.alive  # citado SOLO por lifecycle.md (vivo) → transitivo
    assert graph.docs[adr]["liveness"] == "transitive"


def test_doc_source_dir_ref_does_not_revive(ws: Path) -> None:
    # Un doc VIVO que menciona un dir al pasar NO revive su contenido
    # (dir-edges solo desde superficies — anti liveness-laundering).
    lc = ws / "docs/process/lifecycle.md"
    lc.write_text(lc.read_text(encoding="utf-8") + "\nhistoria en docs/old-stuff/\n", encoding="utf-8")
    graph = build_graph(ws, _corpus(ws))
    assert "docs/process/lifecycle.md" in graph.alive
    assert "docs/old-stuff/dead-doc.md" not in graph.alive


def test_strength_tracks_worst_link(ws: Path) -> None:
    # learnings/tooling vivo SOLO via dir-ref del cockpit → strength 'dir';
    # lifecycle vivo por path exacto → strength 'file'.
    graph = build_graph(ws, _corpus(ws))
    assert graph.docs["docs/process/lifecycle.md"]["strength"] == "file"
    assert graph.docs["docs/learnings/tooling/2026-01-01-algo.md"]["strength"] == "dir"


def test_dead_chain_stays_dead(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    assert "docs/old-stuff/dead-doc.md" not in graph.alive
    assert "docs/old-stuff/dead-a.md" not in graph.alive
    assert "docs/old-stuff/dead-b.md" not in graph.alive  # citado solo por doc muerto


def test_relative_ref_within_docs(ws: Path) -> None:
    # INDEX.md no es citado por nadie → muerto; PERO si lo vuelvo vivo, su
    # ref relativa cuenta. Lo cito desde una superficie y verifico la edge.
    (ws / "scripts/another.py").write_text('X = "docs/process/INDEX.md"\n', encoding="utf-8")
    graph = build_graph(ws, _corpus(ws))
    assert "docs/process/INDEX.md" in graph.alive
    # ticket-states ya era vivo directo; verifico que la edge relativa existe
    edges_to_ts = [e for e in graph.edges if e["dst"] == "docs/process/ticket-states.md"]
    assert any(e["src"] == "docs/process/INDEX.md" for e in edges_to_ts)


def test_outputs_excluded_from_sources(ws: Path) -> None:
    # DOCS-GRAPH.md cita todos los paths — NO debe revivir nada.
    (ws / "docs/process/DOCS-GRAPH.md").write_text(
        "`docs/old-stuff/dead-doc.md` listado como huérfano\n", encoding="utf-8"
    )
    corpus = _corpus(ws)
    graph = build_graph(ws, corpus)
    assert "docs/old-stuff/dead-doc.md" not in graph.alive


# ─── classify ───────────────────────────────────────────────────────────


def test_classify_rules_detail_paired(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    classes = classify_docs(ws, graph)
    assert classes["docs/rules-detail/some-rule.md"] == "detail-pareado"


def test_classify_orphan_and_ssot(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    classes = classify_docs(ws, graph)
    assert classes["docs/old-stuff/dead-doc.md"] == "huérfano"
    assert classes["docs/process/lifecycle.md"] == "SSoT-vivo"


def test_classify_program_record(ws: Path) -> None:
    d = ws / "docs/process/harness-refactor-w6"
    d.mkdir(parents=True)
    (d / "W6-OUTPUT.md").write_text("output\n", encoding="utf-8")
    (d / "RESEARCH-batch-T.md").write_text("research\n", encoding="utf-8")
    graph = build_graph(ws, _corpus(ws))
    classes = classify_docs(ws, graph)
    assert classes["docs/process/harness-refactor-w6/W6-OUTPUT.md"] == "program-record"
    assert classes["docs/process/harness-refactor-w6/RESEARCH-batch-T.md"] == "program-record"


# ─── render ─────────────────────────────────────────────────────────────


def test_render_report_and_manifest(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    classes = classify_docs(ws, graph)
    report = render_report(ws, graph, classes)
    assert "docs/old-stuff/dead-doc.md" in report
    assert "huérfano" in report
    manifest = render_manifest(graph, classes)
    # manifest = SOLO vivos, una línea por doc, regenerable
    assert "docs/old-stuff/dead-doc.md" not in manifest
    assert "docs/process/lifecycle.md" in manifest


def test_edges_json_serializable(ws: Path) -> None:
    graph = build_graph(ws, _corpus(ws))
    json.dumps(graph.edges)  # no raise
