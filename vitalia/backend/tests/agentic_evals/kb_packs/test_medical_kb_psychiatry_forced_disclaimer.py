# voseo-allowed: test references medication keywords + AR voseo persona test fixtures per R25
"""Tests for medical_kb_psychiatry_v1 KB pack — forced disclaimer + medication query.

Story 11 T-kb-3 (R23 Opus 4.7).

Acceptance coverage:
  * A1 (test_forced_disclaimer) — Medication query triggers forced top-1
    retrieval of `disclaimer_psychiatric_prescription_only` chunk regardless
    of cosine similarity. Sales_agent prompt template MUST quote the
    disclaimer chunk verbatim in patient response (downstream concern;
    runtime grader cement Story G).
  * A2 (test_medication_name_recognition) — 200+ medication INN + brand names
    embedded as `medication_keywords` in manifest.yaml, recognized by
    `VitaliaMedicalKbStore._detect_medication_query` so any of the 200
    triggers forced retrieval.

Defensive paths covered:
  * Idempotent seed (re-run safe — same chunk ids).
  * Tenant-agnostic brand-scope retrieval (no per-tenant filter; pack is
    shared medical reference content per `extensions.py::tenant_scope='brand'`).
  * Embedding 1536 dim via `text-embedding-3-large` `dimensions=1536`.
  * Disclaimer chunk forced top-1 ONLY on medication query — routine
    psychiatry questions (e.g. "qué es la depresión") MUST NOT force.
  * Coexistence with crisis-keyword forced retrieval (psychology pack
    pattern preserved — psychiatry pack ALSO declares crisis lines for
    self-harm coverage; medication detection is ORTHOGONAL).
  * Voseo medication phrasing (AR patient input "querés que tome más
    sertralina") still detected.
  * Brand name + INN name parity (sertraline = Zoloft, paracetamol = Tylenol).

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
_PACK_DIR = _REPO_ROOT / "src" / "modules" / "vitalia" / "copilot" / "kb" / "medical_kb_psychiatry_v1"
_MANIFEST_PATH = _PACK_DIR / "manifest.yaml"

# Disclaimer chunk_id MUST be a stable contract string — sales_agent prompt
# template references this id verbatim downstream (Story 11 T-prompts-1 +
# T-eval-1).  Don't rename without coordinating prompts ticket.
DISCLAIMER_CHUNK_ID = "disclaimer_psychiatric_prescription_only"


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
            "ssri": 0,
            "antidepresivo": 1,
            "ansiolítico": 2,
            "benzodiacepina": 3,
            "antipsicótico": 4,
            "estabilizador": 5,
            "interacción": 6,
            "efecto": 7,
            "dosis": 8,
            "sertralina": 9,
            "escitalopram": 10,
            "fluoxetina": 11,
            "clonazepam": 12,
            "alprazolam": 13,
            "risperidona": 14,
            "olanzapina": 15,
            "litio": 16,
            "lamotrigina": 17,
            "paracetamol": 18,
            "ibuprofeno": 19,
            "psiquiatra": 20,
            "receta": 21,
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

    def test_disclaimer_md_present(self) -> None:
        # The disclaimer source file MUST exist — referenced by manifest +
        # sales_agent prompt template (downstream T-prompts-1).
        candidates = list(_PACK_DIR.glob("*disclaimer*.md"))
        assert candidates, "Expected at least one *disclaimer*.md file in pack dir"


class TestManifestSchema:
    """manifest.yaml declares pack metadata + medication_keywords + disclaimer chunk."""

    def test_manifest_yaml_parseable(self) -> None:
        import yaml

        data = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        assert data["pack_id"] == "medical_kb_psychiatry_v1"
        assert data["embedding_model"] == "text-embedding-3-large"
        assert data["embedding_dim"] == 1536
        assert data["qdrant_collection"] == "vitalia_medical_kb_psychiatry_v1"
        assert data["tenant_scope"] == "brand"

    def test_manifest_declares_disclaimer_chunk(self) -> None:
        import yaml

        data = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        boundaries = data.get("boundary_chunks", [])
        ids = {b["chunk_id"] for b in boundaries}
        assert DISCLAIMER_CHUNK_ID in ids, f"manifest must declare boundary chunk {DISCLAIMER_CHUNK_ID!r}"

        # Disclaimer chunk MUST trigger on medication keywords (NOT crisis)
        disclaimer_decl = next(b for b in boundaries if b["chunk_id"] == DISCLAIMER_CHUNK_ID)
        assert disclaimer_decl.get("forced_retrieval") is True, "disclaimer must be forced_retrieval"
        assert disclaimer_decl.get("triggers") == "medication_keywords", (
            "disclaimer chunk must declare triggers=medication_keywords (NOT crisis_keywords)"
        )

    def test_manifest_declares_medication_keywords_200_plus(self) -> None:
        import yaml

        data = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        meds = data.get("medication_keywords", [])
        # 02-design § 9.3: 200+ medication INN + brand names embedded.
        assert len(meds) >= 200, f"medication_keywords must have ≥200 entries (INN + brand names). Got {len(meds)}."

        # Spot-check INN coverage across psychiatric drug classes
        # (case-insensitive contains check — manifest may store lowercase).
        meds_low = {m.lower() for m in meds}
        ssri_examples = ["sertralina", "escitalopram", "fluoxetina", "paroxetina"]
        anxiolytics_examples = ["clonazepam", "alprazolam", "lorazepam", "diazepam"]
        antipsychotics_examples = ["risperidona", "olanzapina", "quetiapina", "haloperidol"]
        mood_examples = ["litio", "lamotrigina", "valproato"]
        for ex in ssri_examples + anxiolytics_examples + antipsychotics_examples + mood_examples:
            assert ex.lower() in meds_low, f"medication_keywords missing INN {ex!r}"

        # Spot-check brand name coverage (clinically equivalent — patients say "Zoloft" not "sertraline")
        brand_examples = ["zoloft", "lexapro", "prozac", "rivotril", "xanax"]
        for ex in brand_examples:
            assert ex.lower() in meds_low, f"medication_keywords missing brand {ex!r}"


class TestChunkCount:
    """V-AE-9 acceptance baseline — pack has ≥120 chunks (per 02-design § 9.3)."""

    def test_chunk_count_meets_baseline(self) -> None:
        from scripts.seed_medical_kb import load_chunks_from_pack

        chunks = load_chunks_from_pack(_PACK_DIR)
        assert len(chunks) >= 120, f"Pack has only {len(chunks)} chunks; V-AE-9 baseline is ≥120 (per 02-design § 9.3)."


class TestSeedingIdempotent:
    """Re-running seed produces same chunk ids (no duplicates)."""

    def test_stable_chunk_ids(self) -> None:
        from scripts.seed_medical_kb import load_chunks_from_pack

        chunks_first = load_chunks_from_pack(_PACK_DIR)
        chunks_second = load_chunks_from_pack(_PACK_DIR)

        chunk_ids_first = [c.chunk_id for c in chunks_first]
        chunk_ids_second = [c.chunk_id for c in chunks_second]
        assert chunk_ids_first == chunk_ids_second, "Chunk ids must be deterministic across runs"

        point_ids_first = [c.point_id for c in chunks_first]
        point_ids_second = [c.point_id for c in chunks_second]
        assert point_ids_first == point_ids_second, "Point ids must be deterministic (idempotent re-seed)"

        for pid in point_ids_first:
            UUID(pid)

    def test_disclaimer_chunk_loadable_from_md(self) -> None:
        from scripts.seed_medical_kb import load_chunks_from_pack

        chunks = load_chunks_from_pack(_PACK_DIR)
        disclaimer_chunks = [c for c in chunks if c.chunk_id == DISCLAIMER_CHUNK_ID]
        assert len(disclaimer_chunks) == 1, (
            f"Expected exactly one chunk with id {DISCLAIMER_CHUNK_ID!r}, found {len(disclaimer_chunks)}"
        )
        d = disclaimer_chunks[0]
        assert d.forced_retrieval is True
        # Body MUST mention the prescription-only constraint clearly enough
        # for sales_agent to quote verbatim.
        body_low = d.text.lower()
        assert "psiquiatra" in body_low or "psiquiátrico" in body_low, (
            "disclaimer body must mention psiquiatra/psiquiátrico"
        )
        assert "receta" in body_low or "prescr" in body_low, "disclaimer body must mention receta/prescripción"


# ─── Acceptance A1 — forced disclaimer on medication query ─────────────────


class TestForcedDisclaimer:
    """A1 — Medication query triggers `disclaimer_psychiatric_prescription_only` top-1."""

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
            collection_name="vitalia_medical_kb_psychiatry_v1",
            vector_size=1536,
            client=client,
            embedder=embedder,
            manifest=manifest,
        )
        chunks = load_chunks_from_pack(_PACK_DIR)
        seed_collection(store, chunks)
        return store

    def test_forced_disclaimer(self, in_memory_store: Any) -> None:
        """A1 — patient asking about specific medication → disclaimer top-1."""
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="¿puedo aumentar la dosis de sertralina por mi cuenta?",
            tenant_country="MX",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        assert top["payload"]["chunk_id"] == DISCLAIMER_CHUNK_ID, (
            f"Top-1 must be {DISCLAIMER_CHUNK_ID!r} on medication query; got {top['payload']['chunk_id']!r}"
        )

    def test_forced_disclaimer_brand_name(self, in_memory_store: Any) -> None:
        """Patient using BRAND name (Rivotril) → disclaimer top-1."""
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="estoy tomando rivotril, ¿puedo combinarlo con alcohol?",
            tenant_country="AR",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        assert top["payload"]["chunk_id"] == DISCLAIMER_CHUNK_ID, (
            f"Brand-name query must force disclaimer top-1; got {top['payload']['chunk_id']!r}"
        )

    def test_forced_disclaimer_voseo_input(self, in_memory_store: Any) -> None:
        """AR voseo patient input — must still trigger forced retrieval."""
        # voseo-allowed: medication_keywords detection MUST work on voseo INPUT
        # (Aurora AR tenant patients send voseo; sales_agent OUTPUT respects
        # tenant voice per spanish-text.md exception).
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="¿querés que tome más alprazolam o lo dejo?",
            tenant_country="AR",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        assert top["payload"]["chunk_id"] == DISCLAIMER_CHUNK_ID, (
            f"Voseo medication query must force disclaimer; got {top['payload']['chunk_id']!r}"
        )

    def test_routine_psychiatry_query_does_not_force_disclaimer(self, in_memory_store: Any) -> None:
        """Routine non-medication query MUST NOT force disclaimer top-1."""
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="¿qué es la depresión y cómo se diferencia de la tristeza?",
            tenant_country="MX",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        # Disclaimer SHOULD NOT dominate routine (non-medication) queries
        assert top["payload"]["chunk_id"] != DISCLAIMER_CHUNK_ID, (
            f"Routine query must NOT force disclaimer top-1; got {top['payload']['chunk_id']!r}"
        )


# ─── Acceptance A2 — 200+ medication name recognition ─────────────────────


class TestMedicationNameRecognition:
    """A2 — 200+ medication keywords cover INN + brand names across psychiatric classes."""

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
            collection_name="vitalia_medical_kb_psychiatry_v1",
            vector_size=1536,
            client=client,
            embedder=embedder,
            manifest=manifest,
        )
        chunks = load_chunks_from_pack(_PACK_DIR)
        seed_collection(store, chunks)
        return store

    @pytest.mark.parametrize(
        "query",
        [
            # SSRIs (INN)
            "¿qué efectos tiene la sertralina?",
            "tomo escitalopram desde hace dos meses",
            "paroxetina me da insomnio",
            "fluoxetina sigue siendo recomendada",
            "venlafaxina afectó mi peso",
            # Anxiolytics (INN)
            "uso clonazepam para dormir",
            "el alprazolam me da somnolencia",
            "lorazepam o diazepam, ¿cuál es mejor?",
            # Antipsychotics (INN)
            "tomo risperidona en gotas",
            "olanzapina me hizo subir de peso",
            "quetiapina me ayuda con la ansiedad",
            "haloperidol clásico vs atípicos",
            # Mood stabilizers
            "el litio me da temblores",
            "lamotrigina como alternativa",
            "valproato sódico para bipolaridad",
            # Brand names (patients say these MORE than INN)
            "rivotril me ayuda",
            "zoloft 50mg",
            "lexapro 10",
            "xanax efectos rebote",
            "prozac generación antigua",
            # Common analgesics referenced by psych patients (interactions)
            "puedo tomar paracetamol con sertralina",
            "ibuprofeno con litio interacción",
        ],
    )
    def test_medication_name_recognition(self, in_memory_store: Any, query: str) -> None:
        """Each medication query → forced disclaimer top-1."""
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query=query,
            tenant_country="MX",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        assert top["payload"]["chunk_id"] == DISCLAIMER_CHUNK_ID, (
            f"Query {query!r} must force disclaimer top-1; got {top['payload']['chunk_id']!r}"
        )

    def test_no_force_when_unrelated_word(self, in_memory_store: Any) -> None:
        """A control query with no medication name → no force."""
        results: Sequence[dict[str, Any]] = in_memory_store.search(
            query="¿cómo agendo una consulta inicial con el psiquiatra?",
            tenant_country="MX",
            limit=5,
        )
        assert len(results) >= 1
        top = results[0]
        # Mentions "psiquiatra" but NOT a medication — must NOT force disclaimer
        assert top["payload"]["chunk_id"] != DISCLAIMER_CHUNK_ID, (
            f"Non-medication query must NOT force disclaimer; got {top['payload']['chunk_id']!r}"
        )


class TestPackRegistration:
    """Ensure seed script registers `medical_kb_psychiatry_v1` in pack list."""

    def test_seed_script_lists_psychiatry_pack(self) -> None:
        from scripts.seed_medical_kb import KB_PACKS

        pack_ids = [p.pack_id for p in KB_PACKS]
        assert "medical_kb_psychiatry_v1" in pack_ids


# voseo-allowed: end-of-file marker
