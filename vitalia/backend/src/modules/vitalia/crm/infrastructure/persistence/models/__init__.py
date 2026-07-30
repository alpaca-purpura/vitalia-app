# cap: crm.crm-consent-optout
# story-origin: TBD
"""CRM infrastructure models — 4 inbox tables (T-inbox-be-2).

Exports SQLAlchemy 2.0 mapped models for:
- ConversationModel  → vitalia_conversations
- MessageModel       → vitalia_messages
- ActivityEventModel → vitalia_activity_events
- ActionReceiptModel → vitalia_action_receipts

All models carry tenant_id + clinic_id (HIPAA-lite dual filter).
"""

from src.modules.vitalia.crm.infrastructure.persistence.models.action_receipt_model import (
    ActionReceiptModel,
)
from src.modules.vitalia.crm.infrastructure.persistence.models.activity_event_model import (
    ActivityEventModel,
)
from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import (
    ConversationModel,
)
from src.modules.vitalia.crm.infrastructure.persistence.models.message_model import (
    MessageModel,
)

__all__ = [
    "ActionReceiptModel",
    "ActivityEventModel",
    "ConversationModel",
    "MessageModel",
]
