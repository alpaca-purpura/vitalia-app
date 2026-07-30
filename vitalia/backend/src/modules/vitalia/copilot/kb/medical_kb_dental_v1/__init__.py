# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""``medical_kb_dental_v1`` — vitalia dental KB pack (Story 11 T-kb-1, R23 Opus 4.7).

Bootstrap dental KB for the vertical-medical sales_agent surface. Per spec:

  * ``02-design-agentic.md`` § 9.1 — pack contract
  * ``03-arch-agentic.md`` § 7.1 + § 7.2 + § 7.3 + § 7.4 + § 7.5 — Qdrant
    collection, chunk schema, tenant_id payload filter, ingestion script,
    citation contract.

What this module exports:

  * ``DENTAL_KB_PACK_ID``                — ``"medical_kb_dental_v1"`` (matches
                                            ``extensions.py::vitalia.medical_kb_dental_v1``
                                            EP-14 registration after CC-4 prefix removal)
  * ``DENTAL_KB_QDRANT_COLLECTION``      — ``"vitalia_medical_kb_dental_v1"``
                                            (Qdrant collection name per spec § 7.1)
  * ``DENTAL_KB_VECTOR_SIZE``            — ``1536`` (text-embedding-3-large dim)
  * ``DENTAL_KB_DEFAULT_SCORE_THRESHOLD`` — ``0.72`` (RAG retrieval threshold)
  * ``DENTAL_KB_DEFAULT_TOP_K``          — ``5`` (RAG retrieval top-k)
  * ``DentalKbChunk``                    — frozen dataclass with stable_id +
                                            tenant-aware payload
  * ``DentalKbStore``                    — Qdrant wrapper with tenant-aware
                                            search + idempotent upsert
  * ``load_dental_kb_chunks()``          — ingest from this package's bundled
                                            markdown files

Anti-duplication audit (Step 0 GATE pre-write, 2026-05-14):

  * grep ``class DentalKbStore`` cross luana-platform → zero collisions.
  * grep ``class DentalKbChunk`` cross luana-platform → zero collisions.
  * Pattern reuses ``MarketingKbStore`` SSoT (luana_core_copilot) — vitalia
    DentalKbStore is a per-pack tenant-aware variant, NOT a mirror:
       - Per-pack collection name (vitalia_<pack_id>) — MarketingKb is global
         singleton ``nicolify_marketing_kb``.
       - Tenant_id payload filter (None = generic, str(uuid) = clinic-specific)
         — MarketingKb has NO tenant_id (curated by Nicolify staff).
       - Vector dim 1536 (text-embedding-3-large) — MarketingKb is 3072.
    Lift-shared deferred per Story 11 T-kb-1 scope (single pack only). T-kb-2
    + T-kb-3 may extract a shared ``BasePerPackKbStore`` if the 3 stores
    converge structurally.

  * ``QdrantClient`` import deferred to ``__call__`` time per F4 gotcha (avoid
    network connection at module-import) — same pattern as MarketingKbStore.

Tenant isolation invariant (R2):
  Every search MUST filter ``tenant_id`` payload. ``tenant_id=None`` chunks
  are visible to ALL dental tenants (curated reference content); chunks with
  specific ``tenant_id`` are visible ONLY to that tenant. Cross-tenant leak
  test: ``test_tenant_filter`` enforces this in the eval suite (V-AE-9).

Idempotency invariant:
  ``DentalKbChunk.stable_id()`` derived from ``source_doc + chunk_index +
  version`` UUIDv5 — re-running ``upsert_chunks(...)`` overwrites in place,
  never creates duplicates. Pattern matches ``MarketingKbStore.stable_id()``.
"""

from __future__ import annotations

import hashlib
import re
import uuid as uuid_mod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Iterable

    from qdrant_client import QdrantClient

logger = structlog.get_logger(__name__)

# ─── Constants (extensions.py CC-4 namespace + spec § 7.1 SSoT) ────────────

DENTAL_KB_PACK_ID = "medical_kb_dental_v1"
"""Pack identifier (extensions.py CC-4 prefix prepended to ``vitalia.``)."""

DENTAL_KB_QDRANT_COLLECTION = "vitalia_medical_kb_dental_v1"
"""Qdrant collection name per spec § 7.1 + extensions.py registration."""

DENTAL_KB_VECTOR_SIZE = 1536
"""Embedding vector dimension — text-embedding-3-large (1536 dim) per spec § 7.1."""

DENTAL_KB_DEFAULT_SCORE_THRESHOLD = 0.72
"""Default similarity threshold per spec § 7.5 + § 9 RAG retrieval contract."""

DENTAL_KB_DEFAULT_TOP_K = 5
"""Default top-k per spec § 7.5 + § 9 RAG retrieval contract."""

DENTAL_KB_VERSION = 1
"""Pack version cement — bump invalidates all chunk stable_ids (full reseed)."""

DENTAL_KB_DOCS_DIR = Path(__file__).parent
"""Directory where bundled markdown chunks live (siblings of ``__init__.py``)."""


# ─── Chunk dataclass ───────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class DentalKbChunk:
    """Single chunk of dental KB content ready for Qdrant upsert.

    Per spec § 7.2 chunk schema:
        ``{ chunk_id, kb_pack, text, source_doc, topic_tags[], procedure_codes[],
            tenant_id, created_at, forced_retrieval, forced_retrieval_triggers[] }``

    Tenant scoping:
      * ``tenant_id=None``       → generic chunk, visible all dental tenants
                                    (curated reference content per spec § 9.1)
      * ``tenant_id=UUID(...)``  → tenant-specific chunk (clinic protocol),
                                    visible ONLY to that tenant.

    Idempotent stable_id:
      Derived from ``source_doc + chunk_index + version`` (UUIDv5). Re-seed
      flow overwrites in place — no duplicates created on re-run.
    """

    text: str
    source_doc: str
    chunk_index: int
    chunk_anchor: str = ""  # H2 heading text — semantic chunk_id (e.g., "Endodoncia (tratamiento de conducto)")
    topic_tags: tuple[str, ...] = ()
    procedure_codes: tuple[str, ...] = ()
    tenant_id: uuid_mod.UUID | None = None
    forced_retrieval: bool = False
    forced_retrieval_triggers: tuple[str, ...] = ()
    version: int = DENTAL_KB_VERSION

    def __post_init__(self) -> None:
        """Defensive validation at construction time."""
        if not self.text or not self.text.strip():
            msg = "DentalKbChunk.text must be non-empty"
            raise ValueError(msg)
        if not self.source_doc:
            msg = "DentalKbChunk.source_doc must be non-empty"
            raise ValueError(msg)
        if self.chunk_index < 0:
            msg = f"chunk_index must be >=0, got {self.chunk_index}"
            raise ValueError(msg)

    def stable_id(self) -> str:
        """Deterministic UUIDv5 derived from ``pack_id + source_doc + anchor``.

        Idempotent reseed: re-running the seeder produces the same id, so
        upsert overwrites in place instead of creating duplicates.

        SHARED FORMAT with ``scripts/seed_medical_kb.py::_stable_point_id``
        (T-kb-2 + T-kb-3) — unified chunk identity across loaders means
        the production seed script and tests refer to the same Qdrant
        point ids. Format: SHA1(``{pack_id}::{source_doc}::{anchor}``)[:32]
        as UUIDv5. NO ``version`` in seed — bump version → bump anchor or
        bump source_doc filename to invalidate cleanly.

        When ``chunk_anchor`` is empty (legacy/test chunk built without H2
        anchor), falls back to ``index::{chunk_index}`` so tests that build
        chunks programmatically still get unique ids.
        """
        anchor = self.chunk_anchor or f"index::{self.chunk_index}"
        seed = f"{DENTAL_KB_PACK_ID}::{self.source_doc}::{anchor}"
        digest = hashlib.sha1(seed.encode("utf-8"), usedforsecurity=False).hexdigest()
        return str(uuid_mod.UUID(digest[:32]))

    def payload(self) -> dict[str, Any]:
        """Qdrant payload — ``tenant_id`` rendered as ``str(UUID) | None``.

        ``tenant_id`` rendered as string for stable JSONB equality checks across
        Qdrant payload index implementations (some don't index UUID natively).
        ``None`` is preserved for the generic-chunk case.
        """
        return {
            "chunk_id": self.stable_id(),
            "kb_pack": DENTAL_KB_PACK_ID,
            "text": self.text,
            "source_doc": self.source_doc,
            "chunk_index": self.chunk_index,
            "chunk_anchor": self.chunk_anchor,
            "topic_tags": list(self.topic_tags),
            "procedure_codes": list(self.procedure_codes),
            "tenant_id": str(self.tenant_id) if self.tenant_id is not None else None,
            "forced_retrieval": self.forced_retrieval,
            "forced_retrieval_triggers": list(self.forced_retrieval_triggers),
            "version": self.version,
        }


# ─── Hit normaliser ────────────────────────────────────────────────────────


def _hit_to_dict(hit: Any) -> dict[str, Any]:
    """Normalise a qdrant-client ScoredPoint into the public search dict.

    Citation contract (spec § 7.5 + § 9.1): every hit MUST expose ``chunk_id``
    so downstream callers can record it in ``copilot_trace_event.context_used``.
    """
    payload = hit.payload or {}
    return {
        "chunk_id": payload.get("chunk_id", str(hit.id)),
        "id": str(hit.id),
        "score": float(hit.score),
        "text": payload.get("text", ""),
        "kb_pack": payload.get("kb_pack"),
        "source_doc": payload.get("source_doc"),
        "chunk_index": payload.get("chunk_index"),
        "chunk_anchor": payload.get("chunk_anchor", ""),
        "topic_tags": payload.get("topic_tags") or [],
        "procedure_codes": payload.get("procedure_codes") or [],
        "tenant_id": payload.get("tenant_id"),
        "forced_retrieval": payload.get("forced_retrieval", False),
        "forced_retrieval_triggers": payload.get("forced_retrieval_triggers") or [],
    }


# ─── Store ─────────────────────────────────────────────────────────────────


@dataclass
class DentalKbStore:
    """Qdrant wrapper for ``vitalia_medical_kb_dental_v1`` collection.

    Heavy resources (Qdrant client, embedding model) are created lazily so
    that ``import`` time stays cheap and unit tests can stub them out via
    constructor injection (``client=``, ``embedder=``).

    Same lazy-init pattern as ``MarketingKbStore`` (F4 gotcha: no network
    connection at module-import time).
    """

    client: QdrantClient | None = None
    embedder: Any | None = None
    _collection_ready: bool = field(default=False, init=False, repr=False)

    COLLECTION = DENTAL_KB_QDRANT_COLLECTION
    VECTOR_SIZE = DENTAL_KB_VECTOR_SIZE

    def _get_client(self) -> QdrantClient:
        """Open a Qdrant connection on demand.

        Production callers should construct with ``client=QdrantClient(url=...)``.
        Tests inject ``client=QdrantClient(":memory:")``.

        We DO NOT read settings here (vitalia has no global ``settings`` singleton);
        callers wire ``QDRANT_URL`` via their composition root and pass an
        instantiated ``QdrantClient`` at construction time. Same explicit-injection
        pattern as ``MarketingKbStore`` lazy ``_client()`` (lifted to caller per
        F4 gotcha — no network connection at module-import time).
        """
        if self.client is None:
            msg = (
                "DentalKbStore requires explicit ``client=`` injection. "
                "Production: construct DentalKbStore(client=QdrantClient(url=settings.QDRANT_URL)). "
                "Tests: construct DentalKbStore(client=QdrantClient(':memory:'))."
            )
            raise RuntimeError(msg)
        return self.client

    def _get_embedder(self) -> Any:
        """Resolve the embedding model on demand.

        Production callers inject the real ``OpenAIEmbeddings`` (text-embedding-3-large
        1536 dim) at construction. Tests inject deterministic stub embedder.
        """
        if self.embedder is None:
            msg = (
                "DentalKbStore requires explicit ``embedder=`` injection. "
                "Production: pass langchain_openai.OpenAIEmbeddings(model='text-embedding-3-large'). "
                "Tests: pass _StubEmbedder() that returns 1536-dim vectors."
            )
            raise RuntimeError(msg)
        return self.embedder

    def ensure_collection(self) -> None:
        """Create the dental kb collection if missing (idempotent).

        Hardcodes the dim invariant: any future embedding model with a
        different dimension forces a deliberate breaking change here +
        in the test ``test_vector_size_constant``.
        """
        if self._collection_ready:
            return
        from qdrant_client.http import models as qmodels

        client = self._get_client()
        collections = client.get_collections()
        if any(c.name == self.COLLECTION for c in collections.collections):
            self._collection_ready = True
            return

        logger.info(
            "dental_kb_creating_collection",
            collection=self.COLLECTION,
            vector_size=self.VECTOR_SIZE,
        )
        client.create_collection(
            collection_name=self.COLLECTION,
            vectors_config=qmodels.VectorParams(
                size=self.VECTOR_SIZE,
                distance=qmodels.Distance.COSINE,
            ),
        )
        self._collection_ready = True

    def search(
        self,
        query: str,
        *,
        tenant_id: uuid_mod.UUID | None = None,
        limit: int = DENTAL_KB_DEFAULT_TOP_K,
        score_threshold: float = DENTAL_KB_DEFAULT_SCORE_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """Dense cosine search with tenant_id payload filter (spec § 9.4).

        ``tenant_id=None`` → only generic chunks (curated reference) returned.
        ``tenant_id=UUID``  → generic chunks + that tenant's chunks merged.
                              CROSS-TENANT chunks excluded by Qdrant filter.

        Per spec § 9.4 ``vitalia_rag_retrieve``:

            FieldCondition(key="tenant_id",
                           match=MatchAny(any=[None, str(ctx.tenant_id)]))

        Note: Qdrant ``MatchAny`` does NOT match ``None`` payload values — it
        matches values present in the ``any=[...]`` list. We use a custom
        approach: query without tenant filter, then filter in Python (small
        result set — top-k ≤5 expanded to ≤25 retrieve, then narrowed). This
        keeps the test simple AND production-correct because per-tenant
        write volume is tiny (a clinic has dozens of custom chunks vs ~150
        generic ones).

        Future optimization (T-kb-3+): use Qdrant ``FilterSelector`` with
        ``Filter(should=[null_match, value_match])`` if perf measurable.
        """
        if not query.strip():
            return []

        self.ensure_collection()
        client = self._get_client()
        embedder = self._get_embedder()

        # Embed query
        if hasattr(embedder, "embed_query"):
            dense_query = embedder.embed_query(query)
        else:
            # Fallback for embedders that only expose embed_documents([...])
            dense_query = embedder.embed_documents([query])[0]

        # Over-fetch then filter by tenant_id in Python (see docstring rationale).
        # For limit=5 we fetch up to 25 (cap to keep payload predictable).
        over_fetch_limit = max(limit * 5, limit)

        try:
            response = client.query_points(
                collection_name=self.COLLECTION,
                query=dense_query,
                limit=over_fetch_limit,
                score_threshold=score_threshold if score_threshold > 0 else None,
            )
            points = response.points
        except Exception:
            # Fallback for in-memory clients that don't implement query_points
            points = client.search(
                collection_name=self.COLLECTION,
                query_vector=dense_query,
                limit=over_fetch_limit,
                score_threshold=score_threshold if score_threshold > 0 else None,
            )

        hits: list[dict[str, Any]] = [_hit_to_dict(p) for p in points]

        # Apply tenant_id filter in Python (see search() docstring).
        wanted_tenant: str | None = str(tenant_id) if tenant_id is not None else None
        filtered = [
            h
            for h in hits
            # Generic chunk (tenant_id=None) → always visible
            if h.get("tenant_id") is None
            # Tenant-specific chunk → matches caller's tenant only
            or (wanted_tenant is not None and h.get("tenant_id") == wanted_tenant)
        ]
        return filtered[:limit]

    def upsert_chunks(self, chunks: Iterable[DentalKbChunk]) -> int:
        """Embed and upsert dental chunks. Returns number indexed.

        Idempotent: chunks reuse ``stable_id()`` derived from
        ``source_doc + chunk_index + version`` so re-running the seeder
        overwrites in place.
        """
        from qdrant_client.http import models as qmodels

        chunks_list = list(chunks)
        if not chunks_list:
            return 0

        self.ensure_collection()
        client = self._get_client()
        embedder = self._get_embedder()

        texts = [c.text for c in chunks_list]
        vectors = embedder.embed_documents(texts)

        points = [
            qmodels.PointStruct(
                id=chunk.stable_id(),
                vector=vector,
                payload=chunk.payload(),
            )
            for chunk, vector in zip(chunks_list, vectors, strict=True)
        ]

        client.upsert(collection_name=self.COLLECTION, points=points)
        logger.info(
            "dental_kb_upserted",
            count=len(points),
            sources=sorted({c.source_doc for c in chunks_list}),
        )
        return len(points)

    def stats(self) -> dict[str, Any]:
        """Lightweight collection stats."""
        try:
            self.ensure_collection()
            client = self._get_client()
            info = client.get_collection(self.COLLECTION)
        except Exception as exc:
            logger.warning("dental_kb_stats_error", error=str(exc))
            return {"collection": self.COLLECTION, "error": str(exc)}
        return {
            "collection": self.COLLECTION,
            "points_count": info.points_count,
            "status": info.status.value if info.status else "unknown",
        }


# ─── Markdown chunk loader ─────────────────────────────────────────────────
#
# Parses ``## H2`` headings as chunk anchors — same convention as T-kb-2 +
# T-kb-3 (``scripts/seed_medical_kb.py::_split_md_into_h2_chunks``). Sharing
# this convention across packs means seed_medical_kb.py works uniformly +
# stable chunk_ids derive from H2 anchors (more semantic than positional
# index — easier to spot in audit logs and citations).
#
# Each chunk body MAY include a ``--meta--`` block at the end with optional
# topic_tags + procedure_codes (CDT codes for dental). The parser strips this
# block from text + extracts the metadata.


_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
"""Each ``## Heading`` introduces a new chunk. Body = text until next H2 or EOF."""

_META_BLOCK_RE = re.compile(r"\n--meta--\n(.*?)$", re.DOTALL)
"""Optional trailing ``--meta--`` block with ``key=value`` lines."""


def _parse_chunks_from_markdown(md_path: Path) -> list[DentalKbChunk]:
    """Parse a single markdown file into DentalKbChunk records via H2 anchors.

    Each file represents a topic family (procedures, materials, recovery,
    common_questions, complications). Chunks are split on ``## H2`` headings.
    Optional ``--meta--`` block at end of each chunk holds topic_tags +
    procedure_codes (CDT codes).

    Compatible with ``scripts/seed_medical_kb.py::_split_md_into_h2_chunks`` —
    same anchor convention. ``chunk_id`` derives from the H2 text (semantic,
    stable across re-parsing).
    """
    text = md_path.read_text(encoding="utf-8")
    matches = list(_H2_RE.finditer(text))
    if not matches:
        return []

    chunks: list[DentalKbChunk] = []
    for offset, m in enumerate(matches):
        chunk_anchor = m.group(1).strip()
        body_start = m.end()
        body_end = matches[offset + 1].start() if offset + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()

        # Strip optional --meta-- trailing block
        meta: dict[str, Any] = {}
        meta_match = _META_BLOCK_RE.search(body)
        if meta_match:
            meta_block = meta_match.group(1).strip()
            body = body[: meta_match.start()].rstrip()
            for raw_line in meta_block.splitlines():
                line = raw_line.strip()
                if not line or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                meta[key.strip()] = value.strip()

        topic_tags = tuple(t.strip() for t in meta.get("tags", "").split(",") if t.strip())
        procedure_codes = tuple(c.strip() for c in meta.get("codes", "").split(",") if c.strip())

        chunks.append(
            DentalKbChunk(
                text=body,
                source_doc=md_path.name,
                chunk_index=offset,
                chunk_anchor=chunk_anchor,
                topic_tags=topic_tags,
                procedure_codes=procedure_codes,
                tenant_id=None,  # All bundled chunks are generic (visible all dental tenants)
            )
        )

    return chunks


def load_dental_kb_chunks(docs_dir: Path | None = None) -> list[DentalKbChunk]:
    """Ingest all bundled markdown chunks from this package.

    Returns chunks sorted by ``(source_doc, chunk_index)`` for stable order.
    Caller pipes into ``DentalKbStore.upsert_chunks(...)``.

    Excluded files: ``manifest.yaml`` (metadata only, no chunks) + any file
    NOT matching ``*.md``.
    """
    base = docs_dir if docs_dir is not None else DENTAL_KB_DOCS_DIR
    md_files = sorted(p for p in base.glob("*.md") if p.is_file())

    all_chunks: list[DentalKbChunk] = []
    for md_path in md_files:
        all_chunks.extend(_parse_chunks_from_markdown(md_path))

    return all_chunks


__all__ = [
    "DENTAL_KB_DEFAULT_SCORE_THRESHOLD",
    "DENTAL_KB_DEFAULT_TOP_K",
    "DENTAL_KB_DOCS_DIR",
    "DENTAL_KB_PACK_ID",
    "DENTAL_KB_QDRANT_COLLECTION",
    "DENTAL_KB_VECTOR_SIZE",
    "DENTAL_KB_VERSION",
    "DentalKbChunk",
    "DentalKbStore",
    "load_dental_kb_chunks",
]
