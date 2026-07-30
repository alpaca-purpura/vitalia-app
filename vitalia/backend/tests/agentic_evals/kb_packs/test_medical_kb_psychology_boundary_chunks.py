# voseo-allowed: test references Spanish neutro crisis keywords + AR voseo persona test fixtures per R25
"""Tests for medical_kb_psychology_v1 KB pack — crisis boundary + per-country referral.

Story 11 T-kb-2 (R23 Opus 4.7).

Acceptance coverage:
  * A1 — Crisis keyword triggers `boundary_refer_out_*` chunk forced retrieval (top-1)
  * A2 — Per-country emergency line returned based on tenant country (AR/CL/MX/CO/PE/BR)

Defensive paths covered:
  * Idempotent seed (re-run safe — same chunk ids).
  * Tenant-agnostic brand-scope retrieval (no per-tenant filter; pack is shared
    medical reference content per `extensions.py::tenant_scope='brand'`).
  * Embedding 1536 dim via `text-embedding-3-large` `dimensions=1536` parameter.
  * Crisis keyword detection respects Spanish neutro variants AND voseo (AR
    tenants like Aurora send patient inputs in voseo).
  * Forced retrieval bypasses similarity threshold (boundary chunks ALWAYS top-1
    when crisis keyword present).

In-memory Qdrant + fake embedder for deterministic test execution.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

# ─── Paths to artifact under test (resolved against repo root, not cwd) ─────

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parents[2]  # tests/agentic_evals/kb_packs/ → vitalia/backend/
_PACK_DIR = _REPO_ROOT / "src" / "modules" / "vitalia" / "copilot" / "kb" / "medical_kb_psychology_v1"
_MANIFEST_PATH = _PACK_DIR / "manifest.yaml"


# ─── Fakes ──────────────────────────────────────────────────────────────────


class _FakeEmbedder:
    """Deterministic in-memory embedder.

    Embeds query → vector based on simple keyword presence so similarity scoring
    is predictable. Real `text-embedding-3-large` is not invoked in tests.
    """

    DIM = 1536

    def __init__(self) -> None:
        self.calls_log: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        self.calls_log.append(text)
        return self._vector_for(text)

    def _vector_for(self, text: str) -> list[float]:
        # Deterministic vector: bit-hash topic keywords across DIM positions.
        vec = [0.001] * self.DIM
        text_low = text.lower()
        keywords = {
            "cbt": 0,
            "gestalt": 1,
            "sistémico": 2,
            "psicoanálisis": 3,
            "ansiedad": 4,
            "depresión": 5,
            "duelo": 6,
            "pareja": 7,
            "consentimiento": 8,
            "encuadre": 9,
            "honorarios": 10,
            "supervisión": 11,
            "crisis": 12,
            "emergencia": 13,
            "argentina": 14,
            "chile": 15,
            "méxico": 16,
            "colombia": 17,
            "perú": 18,
            "brasil": 19,
        }
        for kw, idx in keywords.items():
            if kw in text_low:
                vec[idx] = 0.95
        return vec


# ─── Tests ──────────────────────────────────────────────────────────────────


class TestPackArtifactsPresent:
    """Sanity: KB pack files exist on disk."""

    def test_manifest_exists(self) -> None:
        assert _MANIFEST_PATH.exists(), f"manifest.yaml missing at {_MANIFEST_PATH}"

    def test_chunks_dir_has_markdown(self) -> None:
        md_files = list(_PACK_DIR.glob("*.md"))
        assert len(md_files) >= 1, f"No .md chunk files in {_PACK_DIR}"


class TestManifestSchema:
    """manifest.yaml declares pack metadata + chunk ids + boundary triggers."""

    def test_manifest_yaml_parseable(self) -> None:
        import yaml

        data = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        assert data["pack_id"] == "medical_kb_psychology_v1"
        assert data["embedding_model"] == "text-embedding-3-large"
        assert data["embedding_dim"] == 1536
        assert data["qdrant_collection"] == "vitalia_medical_kb_psychology_v1"
        assert data["tenant_scope"] == "brand"  # cross-tenant medical reference content

    def test_manifest_declares_boundary_chunks(self) -> None:
        import yaml

        data = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        boundaries = data.get("boundary_chunks", [])
        # MUST declare boundary_refer_out_general + per-country crisis lines
        ids = {b["chunk_id"] for b in boundaries}
        assert "boundary_refer_out_general" in ids
        assert "crisis_line_AR" in ids
        assert "crisis_line_CL" in ids
        assert "crisis_line_MX" in ids
        assert "crisis_line_CO" in ids
        assert "crisis_line_PE" in ids
        assert "crisis_line_BR" in ids

    def test_manifest_declares_crisis_keywords(self) -> None:
        import yaml

        data = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        keywords = data.get("crisis_keywords", [])
        # Must include both neutro AND voseo variants for AR coverage.
        # `spanish-text.md` exempts sales_agent OUTPUT, but INPUT detection MUST
        # accept voseo so AR patients (Aurora tenant) trigger boundary.
        for required_kw in [
            "suicidio",
            "matarme",
            "no quiero vivir",
            "autolesión",
            "lastimarme",
            "quitarme la vida",
        ]:
            assert required_kw in keywords, f"crisis_keyword {required_kw!r} missing from manifest"


class TestChunkCount:
    """V-AE-9 acceptance baseline — pack has ≥150 chunks (target ~200)."""

    def test_chunk_count_meets_baseline(self) -> None:
        from scripts.seed_medical_kb import load_chunks_from_pack

        chunks = load_chunks_from_pack(_PACK_DIR)
        # Allow some tolerance vs design target (~200) — 150 is hard floor for V-AE-9.
        assert len(chunks) >= 150, f"Pack has only {len(chunks)} chunks; V-AE-9 baseline is ≥150 (target ~200)."


class TestSeedingIdempotent:
    """Re-running seed produces same chunk ids (no duplicates)."""

    def test_stable_chunk_ids(self) -> None:
        from scripts.seed_medical_kb import load_chunks_from_pack

        chunks_first = load_chunks_from_pack(_PACK_DIR)
        chunks_second = load_chunks_from_pack(_PACK_DIR)

        # chunk_id is the human-readable H2 anchor; point_id is the
        # deterministic UUIDv5 used as Qdrant point id.
        chunk_ids_first = [c.chunk_id for c in chunks_first]
        chunk_ids_second = [c.chunk_id for c in chunks_second]
        assert chunk_ids_first == chunk_ids_second, "Chunk ids must be deterministic across runs"

        point_ids_first = [c.point_id for c in chunks_first]
        point_ids_second = [c.point_id for c in chunks_second]
        assert point_ids_first == point_ids_second, "Point ids must be deterministic across runs (idempotent re-seed)"

        # Each point_id must be UUID-parseable (Qdrant point id requirement).
        for pid in point_ids_first:
            UUID(pid)


class TestCrisisRefersOut:
    """A1 — Crisis keyword triggers boundary_refer_out_* chunk forced top-1."""

    @pytest.fixture
    def in_memory_store(self) -> Any:
        import yaml
        from qdrant_client import QdrantClient

        from scripts.seed_medical_kb import (
            VitaliaMedicalKbStore,
            load_chunks_from_pack,
            seed_collection,
        )

        client = QdrantClient(":memory:")
        embedder = _FakeEmbedder()
        manifest = yaml.safe_load((_PACK_DIR / "manifest.yaml").read_text(encoding="utf-8"))
        store = VitaliaMedicalKbStore(
            collection_name="vitalia_medical_kb_psychology_v1",
            vector_size=1536,
            client=client,
            embedder=embedder,
            manifest=manifest,
        )
        chunks = load_chunks_from_pack(_PACK_DIR)
        seed_collection(store, chunks)
        return store

    def test_crisis_keyword_suicidio_returns_boundary_top1(self, in_memory_store: Any) -> None:
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="estoy pensando en suicidio",
            tenant_country="AR",
            limit=5,
        )
        assert len(results) >= 1
        # Top-1 MUST be boundary_refer_out (forced retrieval bypasses similarity)
        top = results[0]
        assert top["payload"]["chunk_id"] in {
            "boundary_refer_out_general",
            "crisis_line_AR",
        }, f"Top-1 must be boundary chunk on crisis keyword; got {top['payload']['chunk_id']!r}"

    def test_crisis_keyword_voseo_matarme_returns_boundary(self, in_memory_store: Any) -> None:
        # AR patient using voseo — input "voy a matarme" must still trigger
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="ya no aguanto, voy a matarme",
            tenant_country="AR",
            limit=5,
        )
        assert len(results) >= 1
        top_chunk_ids = {r["payload"]["chunk_id"] for r in results[:2]}
        # boundary OR crisis_line must appear in top-2
        boundary_ids = {
            "boundary_refer_out_general",
            "crisis_line_AR",
        }
        assert top_chunk_ids & boundary_ids, (
            f"Boundary chunk missing from top-2 for crisis input; got {top_chunk_ids!r}"
        )

    def test_crisis_keyword_autolesion_returns_boundary(self, in_memory_store: Any) -> None:
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="he tenido autolesión esta semana",
            tenant_country="MX",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        assert top["payload"]["chunk_id"] in {
            "boundary_refer_out_general",
            "crisis_line_MX",
        }

    def test_non_crisis_query_does_not_force_boundary(self, in_memory_store: Any) -> None:
        # Routine therapy question — boundary MUST NOT be forced top-1
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="¿qué es la terapia cognitivo conductual cbt?",
            tenant_country="AR",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        # Boundary chunks SHOULD NOT dominate routine queries
        assert top["payload"]["chunk_id"] not in {
            "boundary_refer_out_general",
            "crisis_line_AR",
            "crisis_line_CL",
            "crisis_line_MX",
            "crisis_line_CO",
            "crisis_line_PE",
            "crisis_line_BR",
        }, f"Routine query must not force boundary top-1; got {top['payload']['chunk_id']!r}"


class TestPerCountryReferral:
    """A2 — Per-country emergency line returned based on tenant country."""

    @pytest.fixture
    def in_memory_store(self) -> Any:
        import yaml
        from qdrant_client import QdrantClient

        from scripts.seed_medical_kb import (
            VitaliaMedicalKbStore,
            load_chunks_from_pack,
            seed_collection,
        )

        client = QdrantClient(":memory:")
        embedder = _FakeEmbedder()
        manifest = yaml.safe_load((_PACK_DIR / "manifest.yaml").read_text(encoding="utf-8"))
        store = VitaliaMedicalKbStore(
            collection_name="vitalia_medical_kb_psychology_v1",
            vector_size=1536,
            client=client,
            embedder=embedder,
            manifest=manifest,
        )
        chunks = load_chunks_from_pack(_PACK_DIR)
        seed_collection(store, chunks)
        return store

    @pytest.mark.parametrize(
        "country,expected_chunk_id",
        [
            ("AR", "crisis_line_AR"),
            ("CL", "crisis_line_CL"),
            ("MX", "crisis_line_MX"),
            ("CO", "crisis_line_CO"),
            ("PE", "crisis_line_PE"),
            ("BR", "crisis_line_BR"),
        ],
    )
    def test_country_specific_crisis_line_returned(
        self, in_memory_store: Any, country: str, expected_chunk_id: str
    ) -> None:
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="estoy en crisis, necesito ayuda urgente",
            tenant_country=country,
            limit=5,
        )
        chunk_ids = {r["payload"]["chunk_id"] for r in results}
        assert expected_chunk_id in chunk_ids, (
            f"Country={country}: expected {expected_chunk_id!r} in results; got {chunk_ids!r}"
        )

    def test_unknown_country_falls_back_to_general(self, in_memory_store: Any) -> None:
        # Patient from US (no localized crisis_line) — falls back to general
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="estoy en crisis, necesito ayuda urgente",
            tenant_country="US",
            limit=5,
        )
        chunk_ids = {r["payload"]["chunk_id"] for r in results}
        # boundary_refer_out_general MUST be present as fallback
        assert "boundary_refer_out_general" in chunk_ids


class TestPackRegistration:
    """Ensure seed script registers `medical_kb_psychology_v1` to pack list."""

    def test_seed_script_lists_psychology_pack(self) -> None:
        from scripts.seed_medical_kb import KB_PACKS

        pack_ids = [p.pack_id for p in KB_PACKS]
        assert "medical_kb_psychology_v1" in pack_ids


# voseo-allowed: end-of-file marker
