# cap: __shared__
# story-origin: TBD
"""File size bucketing helper for telemetry events.

Used in `lisa_marca_logo_uploaded` event props (per 03-arch § 10.3).
Returns a human-readable bucket label instead of raw bytes to avoid
PII/PHI leakage risk via precise size fingerprinting and to ensure
telemetry payloads contain only bucketed metadata.

Buckets:
    0-500KB   — small (avatar/icon quality)
    500KB-1MB — medium (compressed standard)
    1-2MB     — large (high resolution)
    2-5MB     — very large (near limit)
    5MB+      — oversized (rejected by server validation)

Usage:
    from vitalia.modules.vitalia._shared.telemetry.file_size_bucket import bucket_file_size

    event_props = {
        "file_size_bucket": bucket_file_size(file.size),
        "format": file.content_type,
    }
"""

from __future__ import annotations


def bucket_file_size(size_bytes: int) -> str:
    """Return a string bucket label for a file size in bytes.

    Args:
        size_bytes: File size in bytes (non-negative integer).

    Returns:
        Human-readable bucket label string:
        - "0-500KB"    → size < 500 * 1024
        - "500KB-1MB"  → 500KB <= size < 1MB
        - "1-2MB"      → 1MB <= size < 2MB
        - "2-5MB"      → 2MB <= size < 5MB
        - "5MB+"       → size >= 5MB

    Example:
        >>> bucket_file_size(100 * 1024)
        '0-500KB'
        >>> bucket_file_size(3 * 1024 * 1024)
        '2-5MB'
        >>> bucket_file_size(6 * 1024 * 1024)
        '5MB+'
    """
    mb = size_bytes / (1024 * 1024)
    if mb < 0.5:
        return "0-500KB"
    if mb < 1:
        return "500KB-1MB"
    if mb < 2:
        return "1-2MB"
    if mb < 5:
        return "2-5MB"
    return "5MB+"
