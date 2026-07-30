"""Architecture fitness: every FE-called `/api/` URL must match a real BE route.

Per HB-71 (imagined-contract FE↔BE, 10th instance in one story):
  A FE mutation hook invented `PATCH /doctors/{id}/public-profile` — a URL the BE
  never registered (404 live). Green in isolation (the hook test mocked itself),
  red only in live-verify. The mechanical defense: extract every `/api/` URL the
  FE calls (method + path), extract every route the BE registers, and assert each
  FE URL resolves to a real BE (method, path). Kills the whole class.

BE routes come from the live FastAPI app (`app.routes`) — authoritative, includes
nested `include_router` mounts that static AST parsing misses. If the app can't
import (an incomplete local venv missing core packages), the matching test SKIPS
loudly rather than false-fail — it runs for real in a healthy venv / CI. FE URLs
are regex-extracted from `fetchClient`/`vitaliaFetch` call sites (no app needed).

Conservative by design (a HARD gate must not false-positive):
  - FE URLs that aren't a resolvable string/template literal (built from a base
    constant or a runtime variable) are SKIPPED and logged, not failed.
  - Path params are wildcarded: BE `{lead_id}` and FE `${leadId}` both → `{}`.
  - Only `/api/` paths are considered (external URLs ignored).
  - Known mismatches go in KNOWN_CONTRACT_GAPS (shrink-only ratchet).

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_FE_API = WS_ROOT / "vitalia" / "frontend" / "src" / "features"

MUTATION_AND_READ = frozenset(["get", "post", "put", "patch", "delete"])

# FE call sites whose URL the gate can't resolve to a literal (built from a base
# constant or runtime variable). Logged + skipped, not failed. Reducing this set
# (by making the FE URL a literal/template) is always welcome but not required.
# Format: "relative/fe/file.ts::<method> <raw-url-expr>"
KNOWN_UNRESOLVABLE_FE_URLS: frozenset[str] = frozenset()

# FE (method, path) pairs with no matching BE route. Shrink-only ratchet.
# ── TRIAGED 2026-06-18 (HB-82) — feature-reconciliation, NOT a URL typo ───────
# All 17 were diagnosed against the live BE routes + the FE hook+type. Verdict:
# they are the HB-44/HB-71 imagined-contract disease wholesale — the `fidelizacion`
# feature and the `features/vitalia/*` offers/treatments/booking hooks were built
# against an imagined contract that diverges from the real BE in THREE layers at
# once (URL + request body + response shape), so a URL rename alone would swap a
# 404 for a SILENT shape-mismatch (looks connected, still broken — worse). They
# need per-feature FE↔BE reconciliation WITH live-verify, owned by /pm-vitalia
# feature stories (the gate's whole point is to stop shipping these blind). The
# gate already blocks NEW imagined contracts today. Per-gap diagnosis:
#
#   fidelizacion summary/activity (reads): URL drift `fidelization`→`fidelizacion`
#     AND response shape diverges (BE `items`/snake_case vs FE `events`/camelCase).
#   fidelizacion re-engagement (5 POSTs): FE puts patient_id in the PATH, BE wants
#     patient_id+clinic_id (+pause_until/etc.) in the BODY (re_engagement_dtos.py).
#   fidelizacion nps/responses: no BE route — BE has nps/summary + nps/submit only.
#   vitalia offers (GET list/one, presets, POST): BE serves offers under
#     `/api/v1/offer/servicios/*` (engine module) + `/api/v1/vitalia/offer/presets`,
#     not `/api/v1/vitalia/offers*` — different module + missing POST create.
#   vitalia treatments (POST create): BE has GET treatments + per-id sub-routes,
#     no POST /treatments — missing endpoint.
#   vitalia bookings/{id} (GET one): BE has GET list + per-id POST actions, no
#     GET single — missing endpoint.
#   vitalia brand-studio/sections (GET/PATCH): no BE brand-studio; marca lives
#     under `/api/v1/lisa/marca/*` — superseded FE hooks, need decision.
#   notify/reminder (POST): BE is `/api/v1/scheduling/appointments/{id}/notify`.
#   lisa/marca/trust-signals (PUT): method mismatch — BE is POST (create) + DELETE.
#
# Each needs fix-or-remove in a /pm-vitalia story, then drop from this set.
# SSoT: docs/process/harness-backlog.md HB-82.
# Format: "<METHOD> <normalized-path>"
KNOWN_CONTRACT_GAPS: frozenset[str] = frozenset(
    [
        "GET /api/v1/vitalia/bookings/{}",
        "GET /api/v1/vitalia/brand-studio/sections",
        "GET /api/v1/vitalia/fidelization/activity",
        "GET /api/v1/vitalia/fidelization/nps/responses",
        "GET /api/v1/vitalia/fidelization/summary",
        "GET /api/v1/vitalia/offers/presets/{}",
        "GET /api/v1/vitalia/offers/{}",
        "PATCH /api/v1/vitalia/brand-studio/sections/{}",
        "POST /api/v1/notify/reminder",
        "POST /api/v1/vitalia/fidelization/patients/{}/log-call",
        "POST /api/v1/vitalia/fidelization/patients/{}/mark-external",
        "POST /api/v1/vitalia/fidelization/patients/{}/mark-no-continue",
        "POST /api/v1/vitalia/fidelization/patients/{}/pause",
        "POST /api/v1/vitalia/fidelization/patients/{}/send-proactive",
        "POST /api/v1/vitalia/offers",
        "POST /api/v1/vitalia/treatments",
        "PUT /api/v1/lisa/marca/trust-signals",
    ]
)

_PARAM_RE = re.compile(r"\{[^}]+\}")  # BE {lead_id}
_FE_TEMPLATE_RE = re.compile(r"\$\{[^}]+\}")  # FE ${leadId}


def _normalize(path: str) -> str:
    """Canonicalize a path for comparison: wildcard params, strip trailing slash."""
    path = _FE_TEMPLATE_RE.sub("{}", path)
    path = _PARAM_RE.sub("{}", path)
    if len(path) > 1:
        path = path.rstrip("/")
    return path


# ── BE side: authoritative routes from the live FastAPI app ──────────────────


class _AppUnavailable(Exception):
    """The FastAPI app could not be imported (incomplete venv) → skip, don't fail."""


def _be_routes() -> set[tuple[str, str]]:
    """{(METHOD, normalized full path)} from the live app.routes (authoritative)."""
    import os

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    try:
        from src.main import app  # type: ignore[import-not-found]
    except Exception as e:  # ModuleNotFoundError on an incomplete venv, etc.
        raise _AppUnavailable(f"{type(e).__name__}: {e}") from e

    routes: set[tuple[str, str]] = set()
    for r in app.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None)
        if not path or not methods:
            continue
        norm = _normalize(path)
        for m in methods:
            if m.upper() in {"HEAD", "OPTIONS"}:
                continue
            routes.add((m.upper(), norm))
    return routes


# ── FE side: regex extract fetchClient/vitaliaFetch call sites ───────────────

# Matches: fetchClient<...>("URL", { ... method: "POST" ... })  and the
# vitaliaFetch variant. URL is group 1 (the literal inside the quotes/backticks).
_FE_CALL_RE = re.compile(
    r"""(?:fetchClient|vitaliaFetch)\s*<[^>]*>\s*\(\s*[`"']([^`"')]+)[`"']\s*,\s*\{(.*?)\}""",
    re.DOTALL,
)
_FE_METHOD_RE = re.compile(r"""method\s*:\s*["']([A-Za-z]+)["']""")


def _fe_calls() -> tuple[set[tuple[str, str]], list[str]]:
    """Return ({(METHOD, normalized path)}, [unresolvable raw urls])."""
    calls: set[tuple[str, str]] = set()
    unresolvable: list[str] = []
    if not VITALIA_FE_API.exists():
        return calls, unresolvable

    for f in WS_ROOT.glob("vitalia/frontend/src/features/*/api/*.ts"):
        src = f.read_text(encoding="utf-8")
        rel = str(f.relative_to(WS_ROOT))
        for m in _FE_CALL_RE.finditer(src):
            url, opts = m.group(1), m.group(2)
            method_m = _FE_METHOD_RE.search(opts)
            method = (method_m.group(1) if method_m else "GET").upper()
            # Only consider absolute /api/ literals; anything else (base-const
            # interpolation, runtime-built) is unresolvable by static analysis.
            if not url.startswith("/api/"):
                key = f"{rel}::{method} {url}"
                if key not in KNOWN_UNRESOLVABLE_FE_URLS:
                    unresolvable.append(key)
                continue
            norm = _normalize(url.split("?", 1)[0])  # drop query string
            # A `{}` glued to a path segment (e.g. `/bookings{}`) means the template
            # concatenated a query/var without a `/` separator → not a clean route,
            # unresolvable by static matching. Skip rather than false-flag.
            if re.search(r"[^/]\{\}", norm):
                key = f"{rel}::{method} {url}"
                if key not in KNOWN_UNRESOLVABLE_FE_URLS:
                    unresolvable.append(key)
                continue
            calls.add((method, norm))
    return calls, unresolvable


class TestHttpContractParity:
    """Every FE-called /api/ URL must resolve to a real BE route (HB-71)."""

    def test_app_routes_available(self) -> None:
        """Sanity: the live app exposes a non-trivial route set (or skip if no venv)."""
        try:
            routes = _be_routes()
        except _AppUnavailable as e:
            pytest.skip(f"FastAPI app not importable (incomplete venv) — gate runs in a healthy env/CI. {e}")
        assert len(routes) >= 10, f"Only {len(routes)} app routes — app mounting likely broke."

    def test_fe_urls_match_be_routes(self) -> None:
        """Each FE fetchClient/vitaliaFetch `/api/` URL must match a BE (method, path).

        A FE URL with no BE route is an imagined contract (404 live, green in
        isolation) — the HB-71 class. Add to KNOWN_CONTRACT_GAPS only with a real
        justification (e.g. served by a core-package router).
        """
        try:
            be = _be_routes()
        except _AppUnavailable as e:
            pytest.skip(f"FastAPI app not importable (incomplete venv) — gate runs in a healthy env/CI. {e}")
        be_paths = {p for _, p in be}
        fe, _unresolvable = _fe_calls()

        violations: list[str] = []
        for method, path in sorted(fe):
            if f"{method} {path}" in KNOWN_CONTRACT_GAPS:
                continue
            if (method, path) in be:
                continue
            if path in be_paths:
                # path exists but under a different method → still a contract bug,
                # report it with the available methods.
                methods = sorted(m for m, p in be if p == path)
                violations.append(f"{method} {path} — path exists but only for {methods} (method mismatch)")
            else:
                violations.append(f"{method} {path} — no BE route registers this path")

        assert violations == [], (
            "FE calls /api/ URLs with no matching BE route (HB-71 imagined contract):\n\n"
            + "\n".join(violations)
            + "\n\nFix: declare the endpoint in the BE router (method + exact path), "
            "or correct the FE URL. If it's legitimately served elsewhere (e.g. a core "
            "package router), add to KNOWN_CONTRACT_GAPS with justification."
        )
