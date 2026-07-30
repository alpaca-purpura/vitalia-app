"""Root conftest.py for vitalia backend tests.

Adds luana workspace packages' source to sys.path so ORM models, the
Extension SDK, and observability primitives can import without requiring
a full workspace install (cyclic deps prevent pip install).

Layers (Story 11 T-tools-1 extension — same pattern as T-be-1 originally
added for luana_core_platform):
  * luana_core_platform        — Base (ORM declarative_base) + locale VO
  * luana_core_extension_sdk   — ExtensionPointRegistry + ToolDef + … (Story 9)
  * luana_core_observability   — sanitize_payload + BaseTraceEventRepoProtocol
  * luana_core_channels        — payment.MercadoPagoAdapter base (T-payment-1)
  * luana_core_extraction      — BaseExtractionOrchestrator (T-extractors-1, T-extractors-2)
"""

from __future__ import annotations

import sys

# All workspace packages — not published to PyPI; cyclic deps prevent pip install.
_WORKSPACE_SRC_PATHS = (
    "/home/chris/luana-platform/core/luana-core-platform/src",
    "/home/chris/luana-platform/core/luana-core-extension-sdk/src",
    "/home/chris/luana-platform/core/luana-core-observability/src",
    "/home/chris/luana-platform/core/luana-core-channels/src",
    "/home/chris/luana-platform/core/luana-core-extraction/src",
)
for _src in _WORKSPACE_SRC_PATHS:
    if _src not in sys.path:
        sys.path.insert(0, _src)
