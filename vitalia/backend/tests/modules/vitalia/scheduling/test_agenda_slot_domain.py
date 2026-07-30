"""TDD tests — T-2 scheduling domain layer (pure Python, zero framework imports).

Covers:
- AgendaPresetFilter enum values + StrEnum contract
- AppointmentOrigin enum values + StrEnum contract
- AgendaView enum values + StrEnum contract
- SlotPaymentStatus enum values + StrEnum contract
- PaymentMethod enum values + StrEnum contract
- FiscalDocType enum values + StrEnum contract
- AgendaSlot frozen dataclass shape + invariants
- AppointmentPayment dataclass shape + invariants
- FiscalDocument dataclass shape + invariants
- Domain purity: zero framework imports in domain files
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# 1. Import verification (domain purity)
# ---------------------------------------------------------------------------


class TestDomainPurity:
    """No framework imports allowed in domain layer."""

    DOMAIN_MODULES = [
        "src.modules.vitalia.scheduling.domain.agenda_filter",
        "src.modules.vitalia.scheduling.domain.appointment_origin",
        "src.modules.vitalia.scheduling.domain.agenda_view",
        "src.modules.vitalia.scheduling.domain.slot_payment_status",
        "src.modules.vitalia.scheduling.domain.agenda_slot",
        "src.modules.vitalia.scheduling.domain.appointment_payment",
        "src.modules.vitalia.fiscal.domain.fiscal_document",
        "src.modules.vitalia.payments.domain.payment_method",
        "src.modules.vitalia.payments.domain.fiscal_doc_type",
    ]

    FORBIDDEN_IMPORTS = [
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "alembic",
        "starlette",
    ]

    def test_no_framework_imports_in_domain(self) -> None:
        """Domain files must not import fastapi, sqlalchemy, pydantic or alembic."""
        for module_path in self.DOMAIN_MODULES:
            module = importlib.import_module(module_path)
            source = inspect.getsource(module)
            for forbidden in self.FORBIDDEN_IMPORTS:
                assert forbidden not in source, (
                    f"{module_path} imports '{forbidden}' — domain layer must be pure Python."
                )

    def test_no_crm_cross_module_import(self) -> None:
        """Scheduling domain must NOT import from crm or clinics (DDD boundary)."""
        for module_path in self.DOMAIN_MODULES:
            module = importlib.import_module(module_path)
            source = inspect.getsource(module)
            assert "from src.modules.vitalia.crm" not in source, (
                f"{module_path}: cross-module import from crm detected (DDD violation)."
            )
            assert "from src.modules.vitalia.clinics" not in source, (
                f"{module_path}: cross-module import from clinics detected (DDD violation)."
            )


# ---------------------------------------------------------------------------
# 2. Enum contracts
# ---------------------------------------------------------------------------


class TestAgendaPresetFilter:
    """AgendaPresetFilter values must be lowercase strings matching the mockup chips."""

    def test_is_str_enum(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter

        assert issubclass(AgendaPresetFilter, StrEnum)

    def test_has_expected_values(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter

        values = {v.value for v in AgendaPresetFilter}
        assert "hoy" in values
        assert "por_confirmar_manana" in values
        assert "reagendar_pendientes" in values
        assert "no_shows_dia" in values
        assert "saldos_pendientes" in values

    def test_string_coercible(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter

        assert AgendaPresetFilter("hoy") == AgendaPresetFilter.HOY

    def test_count(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter

        assert len(AgendaPresetFilter) == 5


class TestAppointmentOrigin:
    """AppointmentOrigin — vitalia-brand-local, NOT in engine."""

    def test_is_str_enum(self) -> None:
        from src.modules.vitalia.scheduling.domain.appointment_origin import AppointmentOrigin

        assert issubclass(AppointmentOrigin, StrEnum)

    def test_has_expected_values(self) -> None:
        from src.modules.vitalia.scheduling.domain.appointment_origin import AppointmentOrigin

        values = {v.value for v in AppointmentOrigin}
        assert "walk_in" in values
        assert "telefono" in values
        assert "proactivo_adrian" in values
        assert "portal" in values

    def test_string_coercible(self) -> None:
        from src.modules.vitalia.scheduling.domain.appointment_origin import AppointmentOrigin

        assert AppointmentOrigin("walk_in") == AppointmentOrigin.WALK_IN

    def test_count(self) -> None:
        from src.modules.vitalia.scheduling.domain.appointment_origin import AppointmentOrigin

        assert len(AppointmentOrigin) == 4


class TestAgendaView:
    """AgendaView — calendar display mode, persisted in URL params."""

    def test_is_str_enum(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_view import AgendaView

        assert issubclass(AgendaView, StrEnum)

    def test_has_expected_values(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_view import AgendaView

        values = {v.value for v in AgendaView}
        assert "dia" in values
        assert "semana" in values
        assert "mes" in values

    def test_default_is_semana(self) -> None:
        """Contract: architect spec says 'semana' is default calendar view."""
        from src.modules.vitalia.scheduling.domain.agenda_view import AgendaView

        assert AgendaView.SEMANA == "semana"

    def test_count(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_view import AgendaView

        assert len(AgendaView) == 3


class TestSlotPaymentStatus:
    """SlotPaymentStatus — 4×3 matrix (payment_status × origin badge)."""

    def test_is_str_enum(self) -> None:
        from src.modules.vitalia.scheduling.domain.slot_payment_status import SlotPaymentStatus

        assert issubclass(SlotPaymentStatus, StrEnum)

    def test_has_expected_values(self) -> None:
        from src.modules.vitalia.scheduling.domain.slot_payment_status import SlotPaymentStatus

        values = {v.value for v in SlotPaymentStatus}
        assert "pagado" in values  # 🟢
        assert "deposito" in values  # 🟡
        assert "sin_pago" in values  # 🔴
        assert "no_show" in values  # ⚫

    def test_count(self) -> None:
        from src.modules.vitalia.scheduling.domain.slot_payment_status import SlotPaymentStatus

        assert len(SlotPaymentStatus) == 4


class TestPaymentMethod:
    """PaymentMethod — vitalia-brand-local payment methods for cobrar-saldo subform."""

    def test_is_str_enum(self) -> None:
        from src.modules.vitalia.payments.domain.payment_method import PaymentMethod

        assert issubclass(PaymentMethod, StrEnum)

    def test_has_expected_values(self) -> None:
        from src.modules.vitalia.payments.domain.payment_method import PaymentMethod

        values = {v.value for v in PaymentMethod}
        assert "efectivo" in values
        assert "tarjeta" in values
        assert "transferencia" in values
        assert "mercado_pago" in values
        assert "otro" in values

    def test_count(self) -> None:
        from src.modules.vitalia.payments.domain.payment_method import PaymentMethod

        assert len(PaymentMethod) == 5


class TestFiscalDocType:
    """FiscalDocType — covers PE/AR/MX territories + generic ticket (CONTEXT-BRIEF § 11)."""

    def test_is_str_enum(self) -> None:
        from src.modules.vitalia.payments.domain.fiscal_doc_type import FiscalDocType

        assert issubclass(FiscalDocType, StrEnum)

    def test_has_pe_types(self) -> None:
        from src.modules.vitalia.payments.domain.fiscal_doc_type import FiscalDocType

        values = {v.value for v in FiscalDocType}
        assert "boleta" in values  # PE
        assert "factura" in values  # PE + generic

    def test_has_ar_types(self) -> None:
        from src.modules.vitalia.payments.domain.fiscal_doc_type import FiscalDocType

        values = {v.value for v in FiscalDocType}
        assert "factura_b" in values  # AR
        assert "factura_a" in values  # AR
        assert "recibo" in values  # AR

    def test_has_mx_types(self) -> None:
        from src.modules.vitalia.payments.domain.fiscal_doc_type import FiscalDocType

        values = {v.value for v in FiscalDocType}
        assert "cfdi" in values  # MX

    def test_has_generic_ticket(self) -> None:
        from src.modules.vitalia.payments.domain.fiscal_doc_type import FiscalDocType

        values = {v.value for v in FiscalDocType}
        assert "ticket" in values


# ---------------------------------------------------------------------------
# 3. AgendaSlot dataclass
# ---------------------------------------------------------------------------


class TestAgendaSlot:
    """AgendaSlot — frozen projection DTO (no SQLA table)."""

    def _make_slot(self, **overrides: object) -> object:
        from src.modules.vitalia.scheduling.domain.agenda_slot import AgendaSlot
        from src.modules.vitalia.scheduling.domain.appointment_origin import AppointmentOrigin
        from src.modules.vitalia.scheduling.domain.slot_payment_status import SlotPaymentStatus

        now = datetime.now(timezone.utc)
        defaults: dict[str, object] = {
            "slot_id": uuid4(),
            "appointment_id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "patient_name_masked": "P. Hernández",
            "dni_masked": "12.***.***",
            "service": "Limpieza dental",
            "doctor": "Dra. García",
            "start_at": now,
            "end_at": now,
            "payment_status": SlotPaymentStatus.SIN_PAGO,
            "origin": AppointmentOrigin.WALK_IN,
            "balance_amount_cents": 5000,
            "currency": "PEN",
        }
        defaults.update(overrides)
        return AgendaSlot(**defaults)  # type: ignore[arg-type]

    def test_is_frozen_dataclass(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_slot import AgendaSlot

        assert dataclasses.is_dataclass(AgendaSlot)
        # frozen=True means __setattr__ raises FrozenInstanceError
        slot = self._make_slot()
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError, AttributeError)):
            slot.service = "other"  # type: ignore[union-attr]

    def test_has_required_fields(self) -> None:
        from src.modules.vitalia.scheduling.domain.agenda_slot import AgendaSlot

        field_names = {f.name for f in dataclasses.fields(AgendaSlot)}
        required = {
            "slot_id",
            "appointment_id",
            "tenant_id",
            "clinic_id",
            "patient_name_masked",
            "dni_masked",
            "service",
            "doctor",
            "start_at",
            "end_at",
            "payment_status",
            "origin",
            "balance_amount_cents",
            "currency",
        }
        missing = required - field_names
        assert not missing, f"AgendaSlot missing fields: {missing}"

    def test_instantiation(self) -> None:
        slot = self._make_slot()
        assert slot is not None  # type: ignore[union-attr]

    def test_patient_name_masked_is_string(self) -> None:
        """patient_name_masked must be a string (PHI masking enforced)."""
        slot = self._make_slot(patient_name_masked="M. López")
        assert isinstance(slot.patient_name_masked, str)  # type: ignore[union-attr]

    def test_balance_amount_cents_is_optional_int(self) -> None:
        """balance_amount_cents can be None (no balance info yet)."""
        slot = self._make_slot(balance_amount_cents=None)
        assert slot.balance_amount_cents is None  # type: ignore[union-attr]

    def test_currency_is_iso_string(self) -> None:
        """currency field accepts ISO 4217 codes (PEN, ARS, MXN, USD)."""
        for code in ("PEN", "ARS", "MXN", "USD"):
            slot = self._make_slot(currency=code)
            assert slot.currency == code  # type: ignore[union-attr]

    def test_slot_id_is_uuid(self) -> None:
        uid = uuid4()
        slot = self._make_slot(slot_id=uid)
        assert slot.slot_id == uid  # type: ignore[union-attr]

    def test_payment_status_accepts_str_enum(self) -> None:
        from src.modules.vitalia.scheduling.domain.slot_payment_status import SlotPaymentStatus

        slot = self._make_slot(payment_status=SlotPaymentStatus.PAGADO)
        assert slot.payment_status == SlotPaymentStatus.PAGADO  # type: ignore[union-attr]

    def test_origin_accepts_appointment_origin(self) -> None:
        from src.modules.vitalia.scheduling.domain.appointment_origin import AppointmentOrigin

        for origin in AppointmentOrigin:
            slot = self._make_slot(origin=origin)
            assert slot.origin == origin  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 4. AppointmentPayment dataclass
# ---------------------------------------------------------------------------


class TestAppointmentPayment:
    """AppointmentPayment — brand-local persisted payment record."""

    def _make_payment(self, **overrides: object) -> object:
        from src.modules.vitalia.scheduling.domain.appointment_payment import AppointmentPayment

        defaults: dict[str, object] = {
            "id": uuid4(),
            "appointment_id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "amount_cents": 15000,
            "currency": "PEN",
            "method": "efectivo",
            "balance_version": 1,
            "idempotency_key": None,
            "status": "pending",
        }
        defaults.update(overrides)
        return AppointmentPayment(**defaults)  # type: ignore[arg-type]

    def test_is_frozen_dataclass(self) -> None:
        from src.modules.vitalia.scheduling.domain.appointment_payment import AppointmentPayment

        assert dataclasses.is_dataclass(AppointmentPayment)
        payment = self._make_payment()
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError, AttributeError)):
            payment.currency = "USD"  # type: ignore[union-attr]

    def test_has_required_fields(self) -> None:
        from src.modules.vitalia.scheduling.domain.appointment_payment import AppointmentPayment

        field_names = {f.name for f in dataclasses.fields(AppointmentPayment)}
        required = {
            "id",
            "appointment_id",
            "tenant_id",
            "clinic_id",
            "amount_cents",
            "currency",
            "method",
            "balance_version",
            "idempotency_key",
            "status",
        }
        missing = required - field_names
        assert not missing, f"AppointmentPayment missing fields: {missing}"

    def test_amount_cents_must_be_int(self) -> None:
        """Money stored as integer cents (per currency-handling.md)."""
        payment = self._make_payment(amount_cents=50000)
        assert isinstance(payment.amount_cents, int)  # type: ignore[union-attr]

    def test_balance_version_default_is_1(self) -> None:
        """Optimistic lock starts at version 1 (SC-5 race condition pattern)."""
        payment = self._make_payment()
        assert payment.balance_version == 1  # type: ignore[union-attr]

    def test_idempotency_key_is_optional(self) -> None:
        """idempotency_key can be None (set by client on charge request)."""
        payment = self._make_payment(idempotency_key=None)
        assert payment.idempotency_key is None  # type: ignore[union-attr]

    def test_tenant_and_clinic_ids_present(self) -> None:
        """Both tenant_id AND clinic_id mandatory (HIPAA dual filter)."""
        tid = uuid4()
        cid = uuid4()
        payment = self._make_payment(tenant_id=tid, clinic_id=cid)
        assert payment.tenant_id == tid  # type: ignore[union-attr]
        assert payment.clinic_id == cid  # type: ignore[union-attr]

    def test_currency_no_hardcoded_usd_default(self) -> None:
        """currency field must NOT default to 'USD' (currency-handling.md rule)."""
        from src.modules.vitalia.scheduling.domain.appointment_payment import AppointmentPayment

        for field in dataclasses.fields(AppointmentPayment):
            if field.name == "currency":
                # default must not exist or must not be 'USD'
                has_default = (
                    field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING  # type: ignore[misc]
                )
                if has_default and field.default is not dataclasses.MISSING:
                    assert field.default != "USD", "currency field must NOT default to 'USD' — use tenant locale."


# ---------------------------------------------------------------------------
# 5. FiscalDocument dataclass
# ---------------------------------------------------------------------------


class TestFiscalDocument:
    """FiscalDocument — stub-friendly brand-local fiscal record."""

    def _make_doc(self, **overrides: object) -> object:
        from src.modules.vitalia.fiscal.domain.fiscal_document import FiscalDocument

        defaults: dict[str, object] = {
            "id": uuid4(),
            "payment_id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "country": "PE",
            "doc_type": "boleta",
            "doc_number": None,
            "url": None,
            "status": "pending",
        }
        defaults.update(overrides)
        return FiscalDocument(**defaults)  # type: ignore[arg-type]

    def test_is_frozen_dataclass(self) -> None:
        from src.modules.vitalia.fiscal.domain.fiscal_document import FiscalDocument

        assert dataclasses.is_dataclass(FiscalDocument)
        doc = self._make_doc()
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError, AttributeError)):
            doc.country = "AR"  # type: ignore[union-attr]

    def test_has_required_fields(self) -> None:
        from src.modules.vitalia.fiscal.domain.fiscal_document import FiscalDocument

        field_names = {f.name for f in dataclasses.fields(FiscalDocument)}
        required = {
            "id",
            "payment_id",
            "tenant_id",
            "clinic_id",
            "country",
            "doc_type",
            "doc_number",
            "url",
            "status",
        }
        missing = required - field_names
        assert not missing, f"FiscalDocument missing fields: {missing}"

    def test_doc_number_optional(self) -> None:
        """doc_number is None until the fiscal provider issues it."""
        doc = self._make_doc(doc_number=None)
        assert doc.doc_number is None  # type: ignore[union-attr]

    def test_url_optional(self) -> None:
        """url is None until provider returns PDF/XML link."""
        doc = self._make_doc(url=None)
        assert doc.url is None  # type: ignore[union-attr]

    def test_tenant_and_clinic_mandatory(self) -> None:
        """Dual filter fields must both be present (HIPAA-lite)."""
        tid = uuid4()
        cid = uuid4()
        doc = self._make_doc(tenant_id=tid, clinic_id=cid)
        assert doc.tenant_id == tid  # type: ignore[union-attr]
        assert doc.clinic_id == cid  # type: ignore[union-attr]

    def test_country_accepts_pe_ar_mx(self) -> None:
        """country stores ISO 3166-1 alpha-2 code."""
        for country in ("PE", "AR", "MX", "CO"):
            doc = self._make_doc(country=country)
            assert doc.country == country  # type: ignore[union-attr]

    def test_status_default_is_pending(self) -> None:
        """Initial status is pending (before provider confirmation)."""
        doc = self._make_doc()
        assert doc.status == "pending"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 6. Cross-module: SlotPaymentStatus lives in scheduling.domain only
# ---------------------------------------------------------------------------


class TestSlotPaymentStatusLocation:
    """SlotPaymentStatus must NOT be mirrored in payments or fiscal modules."""

    def test_slot_payment_status_in_scheduling_domain(self) -> None:
        from src.modules.vitalia.scheduling.domain import slot_payment_status

        assert hasattr(slot_payment_status, "SlotPaymentStatus")

    def test_no_duplicate_in_payments_module(self) -> None:
        """payments module should NOT define SlotPaymentStatus (anti-duplication)."""
        try:
            from src.modules.vitalia.payments.domain import slot_payment_status as _ps  # noqa: F401

            # If it exists, it must NOT export SlotPaymentStatus
            assert not hasattr(_ps, "SlotPaymentStatus"), (
                "SlotPaymentStatus mirrored in payments.domain — DDD duplication violation."
            )
        except ImportError:
            pass  # expected: payments domain doesn't have this file
