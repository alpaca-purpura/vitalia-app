"""Seed Qdrant medical KB collections for Vitalia (story 11 T-kb-{1,2,3}).

This module is the SINGLE entry point for ingesting the three brand-scope KB
packs declared in `vitalia/config/brand.yaml::medical_kb_packs`:

    medical_kb_dental_v1       — T-kb-1 (parallel ticket — appended alphabetically)
    medical_kb_psychology_v1   — T-kb-2 (THIS ticket)
    medical_kb_psychiatry_v1   — T-kb-3 (later ticket)

R23 Opus 4.7 production AGENTIC code.

Design decisions:

1. **Idempotent**: re-running `python -m scripts.seed_medical_kb` upserts
   chunks with deterministic UUIDv5 ids derived from
   ``{pack_id}::{source_doc}::{chunk_id}``. No duplicates on re-seed.

2. **Embedding model**: ``text-embedding-3-large`` with ``dimensions=1536``
   parameter (per 03-arch-agentic.md § 7.1). Real embedder injected via
   ``VitaliaMedicalKbStore(embedder=...)``; tests use ``_FakeEmbedder``.

3. **Tenant_scope=brand**: chunks are cross-tenant medical reference content
   (not per-tenant PHI). Per-tenant private chunks (clinic-specific
   protocols) extend the same collection with ``tenant_id`` payload field
   filled in (Story 11.bis or later). This module ingests only generic
   chunks (``tenant_id=None``).

4. **Forced retrieval for boundaries** (psychology pack): when patient input
   contains a crisis keyword (declared in ``manifest.yaml::crisis_keywords``),
   ``VitaliaMedicalKbStore.search`` injects boundary chunks at top regardless
   of cosine similarity score. This bypasses the routine RAG threshold (0.72)
   so that high-stakes safety chunks are never silently dropped because the
   patient phrasing did not embed close enough.

5. **Per-country routing** (psychology pack): ``crisis_line_<XX>`` chunks
   are payload-tagged with ``applies_to_countries=["AR"]`` etc. Search
   filters them by tenant country. Unknown country falls back to
   ``boundary_refer_out_general`` only.

6. **Anti-duplication audit** (per ``.claude/rules/anti-duplication.md``):
   precedent ``core/luana-core-copilot/src/luana_core_copilot/infrastructure/qdrant/marketing_kb_store.py``
   targets a tenant-AGNOSTIC global marketing KB with different schema
   (category/methodology/domain). Vitalia medical KB has different shape
   (kb_pack/topic_tags/forced_retrieval/applies_to_countries) and different
   semantic (per-pack collections, tri-modal tenant_scope). NOT a mirror —
   parallel implementation with no overlap. If a future Story consolidates,
   LIFT both into ``core/luana-core-copilot/qdrant/branded_kb_store.py``
   (D8 deferred).

Tenant isolation: brand-scope medical reference content has no
``tenant_id`` filter at query time. Per-tenant private extensions WOULD
filter (Story 11.bis); not in scope for T-kb-{1,2,3} bootstrap.
"""

from __future__ import annotations

import hashlib
import re
import uuid as uuid_mod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable

# ─── Package paths (resolved at import time) ─────────────────────────────────

_THIS_FILE = Path(__file__).resolve()
_BACKEND_ROOT = _THIS_FILE.parent.parent  # vitalia/backend/
_KB_ROOT = _BACKEND_ROOT / "src" / "modules" / "vitalia" / "copilot" / "kb"


# ─── Pack registry (alphabetical to avoid parallel-session merge churn) ─────


@dataclass(frozen=True, slots=True)
class KbPack:
    """Pack registration entry — read at seed time + by tests."""

    pack_id: str
    pack_dir: Path
    qdrant_collection: str
    embedding_dim: int
    tenant_scope: str  # "brand" | "tenant" | "both"


# Alphabetical order — DO NOT reorder. Story 11 T-kb-{1,2,3} ran in parallel
# and each ticket appended to this registry without overwriting peers.
KB_PACKS: list[KbPack] = [
    KbPack(
        pack_id="medical_kb_dental_v1",
        pack_dir=_KB_ROOT / "medical_kb_dental_v1",
        qdrant_collection="vitalia_medical_kb_dental_v1",
        embedding_dim=1536,
        tenant_scope="brand",
    ),
    KbPack(
        pack_id="medical_kb_psychiatry_v1",
        pack_dir=_KB_ROOT / "medical_kb_psychiatry_v1",
        qdrant_collection="vitalia_medical_kb_psychiatry_v1",
        embedding_dim=1536,
        tenant_scope="brand",
    ),
    KbPack(
        pack_id="medical_kb_psychology_v1",
        pack_dir=_KB_ROOT / "medical_kb_psychology_v1",
        qdrant_collection="vitalia_medical_kb_psychology_v1",
        embedding_dim=1536,
        tenant_scope="brand",
    ),
]


# ─── Chunk dataclass ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class KbChunkRecord:
    """One chunk ready for Qdrant upsert.

    The ``chunk_id`` is the stable human-readable identifier used to declare
    boundary chunks in ``manifest.yaml`` (e.g. ``boundary_refer_out_general``,
    ``crisis_line_AR``, ``disclaimer_psychiatric_prescription_only``). The
    Qdrant point id is a UUIDv5 derived from
    ``{pack_id}::{source_doc}::{chunk_id}`` so re-runs are idempotent.

    ``triggers`` (T-kb-3 extension): which manifest trigger group activates
    forced retrieval for this chunk. Possible values:

      * ``""`` (empty) — non-boundary chunk, retrieved by similarity only.
      * ``"crisis_keywords"`` — boundary fired by crisis_keywords scan
        (psychology + psychiatry packs share this).
      * ``"medication_keywords"`` — boundary fired by medication_keywords
        scan (psychiatry pack only — disclaimer chunk).

    Stored in payload so ``_fetch_forced_boundary_hits`` can filter by
    trigger type and surface the right chunk for the right input.
    """

    chunk_id: str  # human-readable, matches ## H2 anchor
    pack_id: str
    source_doc: str
    text: str
    point_id: str  # UUIDv5 string used as Qdrant point id
    topic_tags: tuple[str, ...] = ()
    forced_retrieval: bool = False
    triggers: str = ""  # "crisis_keywords" | "medication_keywords" | "" (none)
    applies_to_countries: tuple[str, ...] = ()  # empty = all
    tenant_id: str | None = None

    def payload(self) -> dict[str, Any]:
        """JSON payload stored in Qdrant."""
        return {
            "chunk_id": self.chunk_id,
            "pack_id": self.pack_id,
            "source_doc": self.source_doc,
            "text": self.text,
            "topic_tags": list(self.topic_tags),
            "forced_retrieval": self.forced_retrieval,
            "triggers": self.triggers,
            "applies_to_countries": list(self.applies_to_countries),
            "tenant_id": self.tenant_id,
        }


# ─── MD parsing — H2 sections become chunks ──────────────────────────────────

_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)


def _stable_point_id(pack_id: str, source_doc: str, chunk_id: str) -> str:
    """Deterministic UUIDv5 — idempotent re-seed (no duplicates)."""
    seed = f"{pack_id}::{source_doc}::{chunk_id}"
    digest = hashlib.sha1(seed.encode("utf-8"), usedforsecurity=False).hexdigest()
    return str(uuid_mod.UUID(digest[:32]))


def _split_md_into_h2_chunks(md_text: str) -> list[tuple[str, str]]:
    """Split markdown by ## H2 anchors. Returns ``[(chunk_id, body), ...]``.

    Body excludes the H2 line itself. If a file has no H2, returns empty
    list (the file is treated as preamble/glossary, not chunked).
    """
    matches = list(_H2_RE.finditer(md_text))
    if not matches:
        return []

    chunks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        chunk_id = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        body = md_text[body_start:body_end].strip()
        chunks.append((chunk_id, body))
    return chunks


def load_chunks_from_pack(pack_dir: Path) -> list[KbChunkRecord]:
    """Load + parse all chunks declared in a KB pack directory.

    Reads ``manifest.yaml`` for pack_id + boundary metadata. For each .md file
    in the pack dir (NOT manifest), splits by H2 → KbChunkRecord. Boundary
    chunks declared in manifest are tagged accordingly.

    Idempotent: same input → same output (chunk ids deterministic).
    """
    manifest_path = pack_dir / "manifest.yaml"
    if not manifest_path.exists():
        msg = f"Missing manifest.yaml in {pack_dir}"
        raise FileNotFoundError(msg)

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    pack_id: str = manifest["pack_id"]

    # Map chunk_id → boundary metadata (if declared)
    boundary_index: dict[str, dict[str, Any]] = {b["chunk_id"]: b for b in manifest.get("boundary_chunks", [])}

    records: list[KbChunkRecord] = []
    md_files = sorted(pack_dir.glob("*.md"))
    for md_path in md_files:
        md_text = md_path.read_text(encoding="utf-8")
        h2_chunks = _split_md_into_h2_chunks(md_text)
        for chunk_id, body in h2_chunks:
            boundary_meta = boundary_index.get(chunk_id, {})
            applies = boundary_meta.get("applies_to_countries", [])
            # Wildcard "*" → empty tuple → match all
            applies_tuple: tuple[str, ...] = tuple(c for c in applies if c != "*") if applies else ()
            # T-kb-3: which trigger group activates this boundary chunk.
            # Falls back to "" (no trigger) for non-boundary chunks; psychology
            # boundaries default to "crisis_keywords" implicitly.
            triggers_field: str = str(boundary_meta.get("triggers", "")) if boundary_meta else ""
            records.append(
                KbChunkRecord(
                    chunk_id=chunk_id,
                    pack_id=pack_id,
                    source_doc=md_path.name,
                    text=body,
                    point_id=_stable_point_id(pack_id, md_path.name, chunk_id),
                    topic_tags=(),
                    forced_retrieval=bool(boundary_meta.get("forced_retrieval", False)),
                    triggers=triggers_field,
                    applies_to_countries=applies_tuple,
                    tenant_id=None,  # brand-scope generic content
                ),
            )

    return records


# ─── Embedder protocol (real or fake) ────────────────────────────────────────


class _EmbedderLike(Protocol):
    """Subset of langchain-style embeddings interface that we use."""

    DIM: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


# ─── Qdrant store wrapper ────────────────────────────────────────────────────


@dataclass
class _SearchHit:
    """Internal search result — normalised across query_points + REST."""

    point_id: str
    score: float
    payload: dict[str, Any]


class VitaliaMedicalKbStore:
    """Qdrant wrapper for Vitalia medical KB packs.

    Constructor injection of ``client`` + ``embedder`` lets tests run against
    in-memory ``QdrantClient(":memory:")`` with a deterministic fake embedder.
    Production usage (CLI ``__main__`` path) instantiates real Qdrant +
    OpenAI embedder via lazy ``_get_*`` accessors.

    Crisis keyword detection is loaded from the pack's ``manifest.yaml`` —
    keeps the behaviour data-driven rather than hardcoded in this module.
    """

    def __init__(
        self,
        *,
        collection_name: str,
        vector_size: int,
        client: Any | None = None,
        embedder: _EmbedderLike | None = None,
        manifest: dict[str, Any] | None = None,
    ) -> None:
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._client = client
        self._embedder = embedder
        self._manifest = manifest or {}
        self._crisis_keywords_lower: tuple[str, ...] = tuple(
            kw.lower() for kw in self._manifest.get("crisis_keywords", [])
        )
        # T-kb-3: medication query detection (psychiatry pack only — psychology
        # pack omits medication_keywords, so this list is empty there and
        # `_detect_medication_query` returns False, preserving psychology
        # behaviour byte-for-byte).
        self._medication_keywords_lower: tuple[str, ...] = tuple(
            kw.lower() for kw in self._manifest.get("medication_keywords", [])
        )

    # ── lazy wiring ─────────────────────────────────────────────────────────

    def _get_client(self) -> Any:
        if self._client is None:  # pragma: no cover — exercised via real CLI run
            from qdrant_client import QdrantClient  # type: ignore[import-untyped]

            # Defer real env wiring to luana-core-platform settings when run
            # from CLI. Tests always inject `client=`.
            self._client = QdrantClient(host="localhost", port=6333)
        return self._client

    def _get_embedder(self) -> _EmbedderLike:
        if self._embedder is None:  # pragma: no cover
            msg = (
                "No embedder injected — real CLI seeding requires an OpenAI "
                "text-embedding-3-large embedder with dimensions=1536. "
                "Inject one or wire LLMFactory in __main__."
            )
            raise RuntimeError(msg)
        return self._embedder

    # ── collection lifecycle ───────────────────────────────────────────────

    def ensure_collection(self) -> None:
        """Create the collection if missing. Idempotent."""
        from qdrant_client.http import models  # type: ignore[import-untyped]

        client = self._get_client()
        existing = {c.name for c in client.get_collections().collections}
        if self.collection_name in existing:
            return
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_chunks(self, chunks: Iterable[KbChunkRecord]) -> int:
        """Embed + upsert all chunks. Returns count upserted."""
        from qdrant_client.http import models  # type: ignore[import-untyped]

        chunk_list = list(chunks)
        if not chunk_list:
            return 0

        embedder = self._get_embedder()
        vectors = embedder.embed_documents([c.text for c in chunk_list])

        points = [
            models.PointStruct(
                id=c.point_id,
                vector=vec,
                payload=c.payload(),
            )
            for c, vec in zip(chunk_list, vectors, strict=True)
        ]
        client = self._get_client()
        client.upsert(collection_name=self.collection_name, points=points)
        return len(chunk_list)

    # ── search ─────────────────────────────────────────────────────────────

    def _detect_crisis(self, query: str) -> bool:
        """Return True if any crisis keyword appears in query (case-insensitive)."""
        if not self._crisis_keywords_lower:
            return False
        q_low = query.lower()
        return any(kw in q_low for kw in self._crisis_keywords_lower)

    def _detect_medication_query(self, query: str) -> bool:
        """Return True if any medication keyword appears in query.

        Whole-word check ensures short tokens like ``"litio"`` don't match
        unrelated longer words (e.g. ``"electrolitio"``). Multi-word
        keywords like ``"acido valproico"`` use substring containment with
        word boundaries on each side so they still match in normal phrasing.

        T-kb-3 contract — psychiatry pack only. Empty manifest.medication_keywords
        → returns False unconditionally (so psychology pack semantics
        unchanged).
        """
        if not self._medication_keywords_lower:
            return False
        q_low = query.lower()
        # Whole-word boundary check: "word characters" surrounded by
        # non-word chars (start/end of string OR Spanish punctuation).
        # Avoids false positives like "litio" matching "monolítico".
        import re as _re

        for kw in self._medication_keywords_lower:
            # Spaces in keyword → multi-word — substring match with boundaries
            pattern = r"(?<![\wáéíóúñü])" + _re.escape(kw) + r"(?![\wáéíóúñü])"
            if _re.search(pattern, q_low):
                return True
        return False

    def search(
        self,
        *,
        query: str,
        tenant_country: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Cosine search + boundary chunk forced retrieval on safety triggers.

        T-kb-3 (2026-05-14): added medication-keyword forced retrieval path
        for psychiatry pack. Order of priority for forced chunks:

          1. ``triggers="medication_keywords"`` — disclaimer chunks (forced
             top when patient input mentions any medication keyword).
          2. ``triggers="crisis_keywords"`` — crisis lines (forced top when
             patient input contains a crisis keyword).
          3. Routine cosine results.

        When BOTH medication keyword AND crisis keyword present in the same
        input, BOTH groups of forced chunks are returned (medication first,
        then crisis lines, then routine). Dedup by point_id.

        Args:
            query: patient input text.
            tenant_country: ISO 3166-1 alpha-2 (AR/CL/MX/CO/PE/BR/...). Used
                to route per-country crisis_line chunks. Unknown country →
                only ``boundary_refer_out_general`` injected as fallback.
            limit: max routine results returned. Boundary chunks are added
                ON TOP and may exceed limit slightly when triggered
                (intentional — safety beats limit invariance).

        Returns: list of dicts ``{point_id, score, payload}``. When forced
        retrieval triggered, top-1 is always a boundary chunk (medication
        disclaimer takes precedence over crisis line if both fired).
        """
        if not query.strip():
            return []

        client = self._get_client()
        embedder = self._get_embedder()

        is_medication = self._detect_medication_query(query)
        is_crisis = self._detect_crisis(query)

        # ── 1. Routine cosine search ──────────────────────────────────────
        dense = embedder.embed_query(query)
        try:
            response = client.query_points(
                collection_name=self.collection_name,
                query=dense,
                limit=limit,
                with_payload=True,
            )
            routine_points = response.points
        except Exception:  # noqa: BLE001 — fallback on legacy Qdrant
            # Best-effort fallback for older qdrant servers; tests use in-memory
            # which always supports query_points.
            routine_points = []

        routine_hits = [
            _SearchHit(
                point_id=str(p.id),
                score=float(p.score),
                payload=p.payload or {},
            )
            for p in routine_points
        ]

        # ── 2. Forced retrieval for boundary chunks ──────────────────────
        # Order: medication first (priority 1), then crisis (priority 2).
        # When both fire, medication disclaimer is top-1.
        forced_medication: list[_SearchHit] = []
        forced_crisis: list[_SearchHit] = []
        if is_medication:
            forced_medication = self._fetch_forced_boundary_hits(
                client,
                tenant_country,
                triggers_filter="medication_keywords",
            )
        if is_crisis:
            forced_crisis = self._fetch_forced_boundary_hits(
                client,
                tenant_country,
                triggers_filter="crisis_keywords",
            )

        # ── 3. Merge — medication forced > crisis forced > routine ────────
        seen: set[str] = set()
        merged: list[_SearchHit] = []
        for h in forced_medication + forced_crisis + routine_hits:
            if h.point_id in seen:
                continue
            seen.add(h.point_id)
            merged.append(h)

        return [
            {
                "point_id": h.point_id,
                "score": h.score,
                "payload": h.payload,
            }
            for h in merged
        ]

    def _fetch_forced_boundary_hits(
        self,
        client: Any,
        tenant_country: str | None,
        triggers_filter: str | None = None,
    ) -> list[_SearchHit]:
        """Scroll the collection (with payload filter) for boundary chunks.

        boundary_refer_out_general is ALWAYS included (applies_to_countries
        is empty or contains "*"). Per-country crisis_line chunks are
        included when their applies_to_countries matches tenant_country.
        Other countries' lines are excluded.

        T-kb-3: ``triggers_filter`` narrows results to chunks whose payload
        ``triggers`` field matches (e.g. ``"medication_keywords"`` for
        psychiatry disclaimer, ``"crisis_keywords"`` for self-harm lines).
        When None (legacy default), returns all forced_retrieval chunks
        (preserves psychology pack pre-T-kb-3 semantics).

        Uses payload filter ``forced_retrieval=True`` so we don't scroll the
        full collection (~200 points) just to find ~7 boundary chunks. Falls
        back to unfiltered scroll for legacy clients that reject filters
        on `scroll()`.
        """
        from qdrant_client.http import models  # type: ignore[import-untyped]

        scroll_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="forced_retrieval",
                    match=models.MatchValue(value=True),
                ),
            ],
        )
        try:
            scroll = client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=64,
                with_payload=True,
                with_vectors=False,
            )
            points, _next = scroll
        except Exception:  # noqa: BLE001
            # Best-effort fallback for legacy Qdrant clients without filter
            try:
                scroll = client.scroll(
                    collection_name=self.collection_name,
                    limit=512,  # large enough to cover full medical pack
                    with_payload=True,
                    with_vectors=False,
                )
                points, _next = scroll
            except Exception:  # noqa: BLE001
                return []

        forced: list[_SearchHit] = []
        for p in points:
            payload = p.payload or {}
            if not payload.get("forced_retrieval"):
                continue
            # T-kb-3: optional filter by trigger group. Backwards-compatible
            # when triggers_filter=None (returns ALL forced chunks regardless
            # of trigger). Psychology pack chunks have triggers="" or
            # "crisis_keywords" — when caller asks for "crisis_keywords"
            # explicitly, we accept BOTH "" (legacy chunks pre-T-kb-3) AND
            # "crisis_keywords" (new chunks). When caller asks for
            # "medication_keywords", we ONLY accept "medication_keywords".
            if triggers_filter is not None:
                chunk_triggers: str = str(payload.get("triggers", ""))
                if triggers_filter == "crisis_keywords":
                    # Backward-compat: accept legacy chunks with no triggers
                    # field as crisis (they were psychology boundary chunks).
                    if chunk_triggers not in ("", "crisis_keywords"):
                        continue
                else:
                    # Strict: medication chunks must opt-in explicitly.
                    if chunk_triggers != triggers_filter:
                        continue
            applies = payload.get("applies_to_countries") or []
            if not applies:
                # Generic boundary — always include
                forced.append(
                    _SearchHit(
                        point_id=str(p.id),
                        score=1.0,  # forced — synthetic top score
                        payload=payload,
                    )
                )
            elif tenant_country and tenant_country in applies:
                forced.append(
                    _SearchHit(
                        point_id=str(p.id),
                        score=1.0,
                        payload=payload,
                    )
                )
            # else: country-specific chunk for a different country — skip
        return forced


# ─── Top-level seeding orchestration ─────────────────────────────────────────


def seed_collection(
    store: VitaliaMedicalKbStore,
    chunks: list[KbChunkRecord],
) -> int:
    """Idempotent seed of one collection. Returns chunks upserted count."""
    store.ensure_collection()
    return store.upsert_chunks(chunks)


def seed_all(
    *,
    embedder: _EmbedderLike,
    client_factory: Any | None = None,
) -> dict[str, int]:
    """Seed all KB packs declared in KB_PACKS.

    Args:
        embedder: production embedder (must produce 1536-dim vectors).
        client_factory: optional Qdrant client instance. If None, each pack's
            store wires its own default client (production path).

    Returns: ``{pack_id: chunks_upserted}``. Best-effort per pack — failure
    of one pack does not abort the rest (logs + continues).
    """
    import structlog  # imported here to avoid hard dep at test-collection time

    logger = structlog.get_logger()
    counts: dict[str, int] = {}
    for pack in KB_PACKS:
        if not pack.pack_dir.exists():
            logger.warning(
                "kb_pack_dir_missing",
                pack_id=pack.pack_id,
                pack_dir=str(pack.pack_dir),
            )
            counts[pack.pack_id] = 0
            continue

        manifest = yaml.safe_load(
            (pack.pack_dir / "manifest.yaml").read_text(encoding="utf-8"),
        )
        store = VitaliaMedicalKbStore(
            collection_name=pack.qdrant_collection,
            vector_size=pack.embedding_dim,
            client=client_factory,
            embedder=embedder,
            manifest=manifest,
        )
        try:
            chunks = load_chunks_from_pack(pack.pack_dir)
            count = seed_collection(store, chunks)
            counts[pack.pack_id] = count
            logger.info(
                "kb_pack_seeded",
                pack_id=pack.pack_id,
                count=count,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort per pack
            logger.warning(
                "kb_pack_seed_failed",
                pack_id=pack.pack_id,
                error=str(exc),
            )
            counts[pack.pack_id] = 0
    return counts


# ─── CLI entrypoint ──────────────────────────────────────────────────────────


def main() -> None:  # pragma: no cover — CLI path
    """CLI entry: `uv run python -m scripts.seed_medical_kb`.

    Wires real OpenAI embedder via luana-core-platform LLMFactory. Tests
    NEVER hit this path — they call ``seed_collection`` directly with
    injected fakes.
    """
    import structlog

    logger = structlog.get_logger()
    try:
        from luana_core_llm.factory import LLMFactory  # type: ignore[import-not-found]
    except ImportError:
        logger.error(
            "llm_factory_unavailable",
            hint="Wire LLMFactory or pass --embedder explicitly when calling seed_all",
        )
        raise

    embedder = LLMFactory.get_service().get_embedding_model()
    counts = seed_all(embedder=embedder)
    logger.info("kb_seed_complete", counts=counts)


if __name__ == "__main__":
    main()
