# cap: __shared__
# story-origin: TBD
"""Vitalia fiscal brand-extension module.

Handles fiscal document emission (boleta/factura) for clinic appointments.
Service-blocker: vitalia-fiscal-emission-pe (refining → NOT developed).
Current phase: stub FiscalEmitPort + MSW mocks (Option A per 03-arch § 8.6).

Inside-Out DDD layers:
  domain/       — FiscalDocument dataclass + FiscalDocType (in payments/)
  infrastructure/ — SA 2.0 model + FiscalDocumentRepository
  application/  — FiscalEmitPort interface + stub impl
  api/          — emit_router (thin, delegates to port)
"""
