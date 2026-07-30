"""ESC-4 — engine LeadModel.messages must be module-qualified so a brand MessageModel
homonym on the shared Base does not break configure_mappers().

Runs the mapper-init probe in a SUBPROCESS for a deterministic import state
(the package conftest registers synthetic models that pollute the global registry).
Architect-verified: RED (InvalidRequestError: Multiple classes found for path
"MessageModel") before the fix; GREEN after qualifying crm.py LeadModel.messages.
"""

import subprocess
import sys
import textwrap

_PROBE = textwrap.dedent(
    """
    import uuid
    from luana_core_platform.domain.base_entity import Base
    from luana_core_platform.infrastructure.models import crm  # LeadModel/SaleModel/CustomerProfileModel
    from luana_core_sales_agent.infrastructure.models.message_model import MessageModel  # engine
    # relationship targets LeadModel needs resolvable:
    from luana_core_scheduling.infrastructure.models.appointment_model import AppointmentModel  # noqa: F401
    from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
    from luana_core_offer_studio.infrastructure.models.product_model import ProductModel  # noqa: F401
    from sqlalchemy import Column, String  # noqa: F401
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import configure_mappers

    # Brand homonym (e.g. vitalia MessageModel -> vitalia_messages): SAME class name,
    # different table, NO relationships. This is the collision source.
    class MessageModel(Base):  # noqa: F811
        __tablename__ = "brand_messages_probe"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        tenant_id = Column(UUID(as_uuid=True), nullable=True)

    configure_mappers()
    print("CONFIGURE_OK")
    """
)


def test_engine_leadmodel_messages_resolves_with_brand_homonym() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "ESC-4 regression — configure_mappers() failed with a brand MessageModel "
        f"homonym on the shared Base:\n{result.stderr[-2000:]}"
    )
    assert "CONFIGURE_OK" in result.stdout
