# cap: fiscal.fiscal-emission-pe
# story-origin: TBD
"""FiscalDocument — brand-local fiscal record (boleta/factura/CFDI).

Stub-friendly domain entity for fiscal emission.
Service-blocker: vitalia-fiscal-emission-pe (refining → NOT developed F2-S1).
When service-blocker ships, replace stub impl with real Nubefact/AFIP/SAT adapter.

Covers LatAm territories per CONTEXT-BRIEF § 11 (validator gap confirmed):
  PE: boleta, factura
  AR: factura_a, factura_b, recibo
  MX: cfdi
  Generic: ticket

Charge saga compensation (03-arch A6):
  Payment OK + fiscal fail → retry emit standalone.
  FiscalDocument status tracks: pending → emitted | failed.

PHI context:
  tenant_id + clinic_id = dual filter (HIPAA-lite).
  payment_id links to AppointmentPayment (no direct patient reference).

Per 03-arch § 2.4 + vitalia/.claude/rules/hipaa-lite.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class FiscalDocument:
    """Brand-local fiscal document record.

    Frozen: represents an issued (or attempted) fiscal document state snapshot.
    Infrastructure model is mutable; domain projection is immutable.

    Status lifecycle:
      pending  → provider called, awaiting response
      emitted  → document issued, doc_number + url available
      failed   → provider returned error (retry eligible)

    Attributes:
        id:          Unique fiscal document identifier.
        payment_id:  FK to vitalia_appointment_payments.id.
        tenant_id:   Tenant identifier (dual filter key 1).
        clinic_id:   Clinic identifier (dual filter key 2 — HIPAA-lite).
        country:     ISO 3166-1 alpha-2 country code (PE/AR/MX/CO/CL/BR).
        doc_type:    FiscalDocType value (boleta/factura/cfdi/ticket/...).
        doc_number:  Provider-issued serial (None until emitted).
        url:         PDF/XML download link (None until emitted).
        status:      Document emission status (pending/emitted/failed).
    """

    id: UUID
    payment_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    country: str
    doc_type: str
    doc_number: str | None
    url: str | None
    status: str
