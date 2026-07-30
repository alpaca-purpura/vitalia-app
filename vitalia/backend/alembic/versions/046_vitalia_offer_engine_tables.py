# cap: lisa.servicios
"""Migration 046 — engine offer-studio tables in the vitalia schema.

Live-verify (DoD#37, story vitalia-fase2-lisa-servicios) caught that the offer
module persists the offer-core via the engine ``OfferRepository`` (D-1), which
INSERTs into ``products`` — but no migration ever created the engine
offer-studio tables in vitalia's DB. Migration 045 explicitly deferred ``products``
to "a T-2/keystone concern", and T-2/T-4 only call the engine repo (BE tests pass
on a metadata.create_all test DB, so the gap never showed until live).

Materializes the 6 engine offer-studio tables from their SQLAlchemy models via
``metadata.create_all(checkfirst=True)`` — idempotent (skips existing) and FK-ordered
automatically (products first; launch_editions/offer_assets/offer_knowledge_sources/
external_product_mappings FK → products.id). Models are String/JSONB (no native PG
enum types) so create_all is safe. We do NOT hand-transcribe ~68 columns × 6 tables.

This is a vitalia migration that provisions the ENGINE schema vitalia consumes — it
does NOT edit ``core/luana-core-offer-studio`` src.

Revision ID: 046_vitalia
Revises: 045_vitalia
"""

from alembic import op

revision = "046_vitalia"
down_revision = "045_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from luana_core_offer_studio.infrastructure.models.external_product_mapping_model import (
        ExternalProductMappingModel,
    )
    from luana_core_offer_studio.infrastructure.models.knowledge_source_model import (
        KnowledgeSourceModel,
    )
    from luana_core_offer_studio.infrastructure.models.launch_edition_model import (
        LaunchEditionModel,
    )
    from luana_core_offer_studio.infrastructure.models.offer_asset_model import (
        OfferAssetModel,
    )
    from luana_core_offer_studio.infrastructure.models.offer_extraction_trace_model import (
        OfferExtractionTrace,
    )

    # Import engine offer-studio models so they register on Base.metadata.
    from luana_core_offer_studio.infrastructure.models.product_model import ProductModel
    from luana_core_platform.domain.base_entity import Base

    tables = [
        ProductModel.__table__,
        LaunchEditionModel.__table__,
        OfferAssetModel.__table__,
        KnowledgeSourceModel.__table__,
        ExternalProductMappingModel.__table__,
        OfferExtractionTrace.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables, checkfirst=True)


def downgrade() -> None:
    # ponytail: engine offer-studio tables are shared infra — no destructive downgrade.
    pass
