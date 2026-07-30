# cap: lisa.servicios
"""RED-first unit tests for SpecialistLinkService (T-2 § 6).

Linking a specialist verifies the doctor exists in the roster (via
DoctorRosterPort) — it NEVER creates a doctor. Unknown/inactive doctor → raise.
Unlink is idempotent. All scoped tenant_id (+ clinic_id for the roster read).

G2-F13-BE regression: list_for_offer enriches display_name + specialty via
roster when clinic_id is provided; gracefully degrades (None) when absent or
doctor not found.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.offer.application.ports.doctor_roster_port import DoctorRosterPort, RosterDoctor
from src.modules.vitalia.offer.application.services.specialist_link_service import (
    DoctorNotInRosterError,
    EnrichedSpecialistLink,
    SpecialistLinkService,
)
from src.modules.vitalia.offer.domain.specialist_link import ServiceSpecialistLink

TENANT = UUID("11111111-1111-1111-1111-111111111111")
CLINIC = UUID("33333333-3333-3333-3333-333333333333")
OFFER = UUID("44444444-4444-4444-4444-444444444444")
DOCTOR = UUID("55555555-5555-5555-5555-555555555555")


class _FakeRoster(DoctorRosterPort):
    def __init__(self, doctors: dict[UUID, RosterDoctor]) -> None:
        self._doctors = doctors

    async def get_doctor(self, *, tenant_id, clinic_id, doctor_id):
        return self._doctors.get(doctor_id)

    async def list_doctors(self, *, tenant_id, clinic_id):
        return list(self._doctors.values())


class _FakeLinkRepo:
    def __init__(self) -> None:
        self.links: list[ServiceSpecialistLink] = []
        self.created = False

    async def link(self, link: ServiceSpecialistLink) -> ServiceSpecialistLink:
        self.links.append(link)
        return link

    async def list_by_offer(self, offer_id, *, tenant_id):
        return [link for link in self.links if link.offer_id == offer_id and link.tenant_id == tenant_id]

    async def unlink(self, offer_id, doctor_id, *, tenant_id) -> None:
        self.links = [
            link
            for link in self.links
            if not (link.offer_id == offer_id and link.doctor_id == doctor_id and link.tenant_id == tenant_id)
        ]


def _svc(doctors: dict[UUID, RosterDoctor]) -> tuple[SpecialistLinkService, _FakeLinkRepo]:
    repo = _FakeLinkRepo()
    svc = SpecialistLinkService(roster=_FakeRoster(doctors), link_repo=repo)
    return svc, repo


@pytest.mark.asyncio
async def test_link_existing_doctor():
    doctor = RosterDoctor(id=DOCTOR, full_name="Dra. Ana Pérez", specialty="Odontología", active=True)
    svc, repo = _svc({DOCTOR: doctor})
    link = await svc.link(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER, doctor_id=DOCTOR)
    assert link.doctor_id == DOCTOR
    assert len(repo.links) == 1


@pytest.mark.asyncio
async def test_link_unknown_doctor_raises_and_creates_nothing():
    svc, repo = _svc({})  # empty roster
    with pytest.raises(DoctorNotInRosterError):
        await svc.link(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER, doctor_id=uuid4())
    assert len(repo.links) == 0  # never creates a doctor or a link


@pytest.mark.asyncio
async def test_list_specialists_for_offer():
    doctor = RosterDoctor(id=DOCTOR, full_name="Dra. Ana", specialty=None, active=True)
    svc, repo = _svc({DOCTOR: doctor})
    await svc.link(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER, doctor_id=DOCTOR)
    listed = await svc.list_for_offer(tenant_id=TENANT, offer_id=OFFER)
    assert [link.doctor_id for link in listed] == [DOCTOR]


@pytest.mark.asyncio
async def test_unlink_is_idempotent():
    doctor = RosterDoctor(id=DOCTOR, full_name="Dra. Ana", specialty=None, active=True)
    svc, repo = _svc({DOCTOR: doctor})
    await svc.link(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER, doctor_id=DOCTOR)
    await svc.unlink(tenant_id=TENANT, offer_id=OFFER, doctor_id=DOCTOR)
    await svc.unlink(tenant_id=TENANT, offer_id=OFFER, doctor_id=DOCTOR)  # no error second time
    assert len(repo.links) == 0


# ── G2-F13-BE regression: enrichment via roster ──────────────────────────────


@pytest.mark.asyncio
async def test_list_for_offer_enriches_name_and_specialty_when_clinic_id_given():
    """With clinic_id: EnrichedSpecialistLink carries doctor name + specialty."""
    doctor = RosterDoctor(id=DOCTOR, full_name="Dra. Ana Pérez", specialty="Odontología", active=True)
    svc, repo = _svc({DOCTOR: doctor})
    await svc.link(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER, doctor_id=DOCTOR)

    results = await svc.list_for_offer(tenant_id=TENANT, offer_id=OFFER, clinic_id=CLINIC)

    assert len(results) == 1
    item = results[0]
    assert isinstance(item, EnrichedSpecialistLink)
    assert item.display_name == "Dra. Ana Pérez"
    assert item.specialty == "Odontología"
    assert item.doctor_id == DOCTOR


@pytest.mark.asyncio
async def test_list_for_offer_no_clinic_id_returns_nones():
    """Without clinic_id: display_name and specialty are None; no crash."""
    doctor = RosterDoctor(id=DOCTOR, full_name="Dra. Ana", specialty="Estética", active=True)
    svc, repo = _svc({DOCTOR: doctor})
    await svc.link(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER, doctor_id=DOCTOR)

    results = await svc.list_for_offer(tenant_id=TENANT, offer_id=OFFER)

    assert len(results) == 1
    item = results[0]
    assert isinstance(item, EnrichedSpecialistLink)
    assert item.display_name is None
    assert item.specialty is None


@pytest.mark.asyncio
async def test_list_for_offer_doctor_not_in_roster_graceful():
    """Doctor linked but not in roster at enrichment time → display_name None, no crash."""
    # Link with a roster that has the doctor.
    doctor = RosterDoctor(id=DOCTOR, full_name="Dr. Borrado", specialty="Cirugía", active=True)
    svc, repo = _svc({DOCTOR: doctor})
    await svc.link(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER, doctor_id=DOCTOR)

    # Now replace the roster with an empty one (simulates doctor removed/inactive).
    svc2 = SpecialistLinkService(roster=_FakeRoster({}), link_repo=repo)
    results = await svc2.list_for_offer(tenant_id=TENANT, offer_id=OFFER, clinic_id=CLINIC)

    assert len(results) == 1
    assert results[0].display_name is None
    assert results[0].specialty is None
