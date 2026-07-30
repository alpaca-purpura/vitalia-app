"""Unit tests — tenant-scoped durable-flow thread_id composition (T-flows-2)."""

import pytest

from luana_core_flows.checkpointer import build_flow_thread_id, build_phi_flow_thread_id


def test_build_flow_thread_id_composes_in_order() -> None:
    tid = build_flow_thread_id(flow_id="vitalia.wizard", tenant_id="t-123", instance_id="draft-9")
    assert tid == "vitalia.wizard:t-123:draft-9"


def test_tenant_segment_is_isolation_boundary() -> None:
    a = build_flow_thread_id(flow_id="f", tenant_id="tenant-a", instance_id="x")
    b = build_flow_thread_id(flow_id="f", tenant_id="tenant-b", instance_id="x")
    assert a != b  # same flow + instance, different tenant → distinct durable threads


def test_phi_variant_embeds_clinic() -> None:
    tid = build_phi_flow_thread_id(
        flow_id="vitalia.lucas", tenant_id="t-1", clinic_id="clinic-7", instance_id="2026-06"
    )
    assert tid == "vitalia.lucas:t-1:clinic-7:2026-06"


def test_phi_clinic_is_part_of_isolation() -> None:
    a = build_phi_flow_thread_id(flow_id="f", tenant_id="t", clinic_id="c1", instance_id="i")
    b = build_phi_flow_thread_id(flow_id="f", tenant_id="t", clinic_id="c2", instance_id="i")
    assert a != b  # same tenant, different clinic → distinct (hipaa-lite dual-filter)


@pytest.mark.parametrize("bad", ["with:colon", "", "a:b"])
def test_rejects_separator_or_empty_segment(bad: str) -> None:
    with pytest.raises(ValueError):
        build_flow_thread_id(flow_id="f", tenant_id=bad, instance_id="i")


def test_phi_rejects_separator_in_clinic() -> None:
    with pytest.raises(ValueError):
        build_phi_flow_thread_id(flow_id="f", tenant_id="t", clinic_id="bad:clinic", instance_id="i")
