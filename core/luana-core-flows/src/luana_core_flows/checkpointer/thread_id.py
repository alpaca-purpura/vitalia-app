# cap: __shared__
"""Tenant-scoped durable-flow ``thread_id`` composition.

A LangGraph durable thread is keyed by ``thread_id``. For Luana durable flows the
key MUST embed the tenant segment so two tenants never collide on the same
persisted checkpoint stream (isolation by construction, mirrors the brand-DB
boundary one level down). The PHI variant additionally embeds ``clinic_id`` for
vitalia's hipaa-lite dual-filter.

Shape (stable contract — the 5 existing brand graphs map their current keys onto
these slots WITHOUT changing collision/isolation semantics):

    build_flow_thread_id(flow_id, tenant_id, instance_id)
        -> "{flow_id}:{tenant_id}:{instance_id}"
    build_phi_flow_thread_id(flow_id, tenant_id, clinic_id, instance_id)
        -> "{flow_id}:{tenant_id}:{clinic_id}:{instance_id}"

The ``flow_id`` namespaces the flow kind (e.g. ``vitalia.wizard``); ``tenant_id``
is the isolation segment; ``instance_id`` is the per-run discriminator (draft id,
treatment id, subscriber id, ...).
"""

from __future__ import annotations

_SEP = ":"


def _reject_separator(**segments: str) -> None:
    """Guard: no segment may contain the separator (would break parsing/collision-safety)."""
    for name, value in segments.items():
        if not value:
            msg = f"thread_id segment '{name}' must be a non-empty string"
            raise ValueError(msg)
        if _SEP in value:
            msg = f"thread_id segment '{name}'={value!r} must not contain {_SEP!r}"
            raise ValueError(msg)


def build_flow_thread_id(*, flow_id: str, tenant_id: str, instance_id: str) -> str:
    """Compose a tenant-scoped durable-flow thread_id.

    The ``tenant_id`` segment is the isolation boundary: two tenants running the
    same ``flow_id``/``instance_id`` get distinct threads.
    """
    _reject_separator(flow_id=flow_id, tenant_id=tenant_id, instance_id=instance_id)
    return _SEP.join((flow_id, tenant_id, instance_id))


def build_phi_flow_thread_id(*, flow_id: str, tenant_id: str, clinic_id: str, instance_id: str) -> str:
    """Compose a PHI-aware thread_id embedding ``clinic_id`` (vitalia dual-filter).

    Used by flows that touch PHI (e.g. vitalia lucas/treatment) so the durable
    stream is scoped to tenant + clinic, matching the hipaa-lite dual-filter rule.
    """
    _reject_separator(flow_id=flow_id, tenant_id=tenant_id, clinic_id=clinic_id, instance_id=instance_id)
    return _SEP.join((flow_id, tenant_id, clinic_id, instance_id))


__all__ = ["build_flow_thread_id", "build_phi_flow_thread_id"]
