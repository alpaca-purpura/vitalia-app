"""Architecture fitness: every mutation handler MUST use the committing session.

Per HB-50 (silent-killer · verification-≠-200, 3rd instance):
  `get_async_session` NEVER commits (it delegates the unit-of-work to the caller).
  A POST/PATCH/PUT/DELETE handler that depends on `get_async_session` and whose
  service never calls `session.commit()` returns HTTP 200/201 while the write is
  silently rolled back at session close — no DB row, green tests, lost write.
  (vitalia-fase2-adrian-inbox: 6 mutation factories returned 200 with `pause_until`
  NULL / `handler_mode` unchanged. Caught by golden e2e + direct DB read-back.)

  The convention the codebase converged on: mutation handlers use
  `get_async_session_committing` (db.py), which owns the unit-of-work (commits on
  clean return, rolls back on exception). This gate makes that durable.

Rule: a mutation route handler (POST/PATCH/PUT/DELETE) that takes a session via
  `Depends(get_async_session)` (the non-committing factory) is a violation unless
  allowlisted. Use `Depends(get_async_session_committing)` instead — or, if the
  handler legitimately delegates commit to a service that owns the transaction,
  add it to KNOWN_NON_COMMITTING_MUTATIONS with justification.

Scans all *router*.py / *routes*.py files under vitalia/backend/src/ via AST.
Known-violations allowlist follows ratchet pattern (shrink-only).

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import ast
from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_SRC = WS_ROOT / "vitalia" / "backend" / "src"

# HTTP method decorators that MUTATE state → must commit.
MUTATION_DECORATOR_ATTRS: frozenset[str] = frozenset(["post", "put", "patch", "delete"])

# The non-committing session factory (delegates unit-of-work to the caller).
NON_COMMITTING_FACTORY = "get_async_session"
# The committing factory that owns the unit-of-work (commits on clean return).
COMMITTING_FACTORY = "get_async_session_committing"

# Mutation handlers that legitimately use the non-committing session because a
# service / repository inside the handler owns the commit explicitly.
# Format: "relative/path/to/file.py::function_name"
# Add exemptions WITH justification in the commit message (shrink-only ratchet).
KNOWN_NON_COMMITTING_MUTATIONS: frozenset[str] = frozenset(
    [
        # ── AUDITED 2026-06-18 (HB-80) — genuine no-write handlers ────────────
        # The 2026-06-16 baseline of 11 was audited (code read-back of each
        # handler's write path). 8 were REAL silent-write-loss (HB-50 class) and
        # were FIXED by routing them through `get_async_session_committing`:
        #   wizard start_draft/confirm_slot/extract_tenant_context/complete_onboarding
        #     (draft writes via SqlAlchemyOnboardingProgressRepository.save = flush-only
        #      "Caller commits" → fixed at the `get_onboarding_progress_repo` provider),
        #   marketing approve/reject/undo_recommendation (status transition + sync
        #     audit-log INSERT, neither committed),
        #   scheduling send_appointment_reminder (HIPAA-lite sync audit-log INSERT).
        # simulate_personality came off the list too: its closure now reaches the
        # committing session via the shared draft provider (and it is read-only).
        #
        # The 2 below are genuine NO-WRITE mutation handlers: they hold a session
        # only for read-only auth/context resolution and delegate to a service
        # that does no DB write. Committing them would be misleading. Shrink-only.
        # SSoT: docs/process/harness-backlog.md HB-50 + HB-80.
        "vitalia/backend/src/modules/vitalia/inbox/api/router.py::transcribe_audio",  # Whisper; no DB write
        "vitalia/backend/src/modules/vitalia/marketing/api/routes.py::connect_channel",  # OAuth-init; returns auth URL
    ]
)

SKIP_FILE_SUFFIXES: tuple[str, ...] = ("conftest.py", "__init__.py")


def _route_files() -> list[Path]:
    """Find all potential route files under vitalia/backend/src/."""
    if not VITALIA_SRC.exists():
        return []
    candidates: list[Path] = []
    for p in VITALIA_SRC.rglob("*.py"):
        name = p.name
        if any(name.endswith(s) for s in SKIP_FILE_SUFFIXES):
            continue
        if "router" in name or "route" in name:
            candidates.append(p)
    return candidates


def _all_funcs() -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Global name→node map of every function under vitalia/backend/src/.

    Session-providing service factories (e.g. `get_complete_service`) live in
    `dependencies.py` / other modules, not next to the handler — so the closure
    has to resolve `Depends(...)` names across the whole brand backend, not just
    the route file. Names are distinctive enough that last-wins collisions are
    acceptable for this heuristic gate.
    """
    funcs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    if not VITALIA_SRC.exists():
        return funcs
    for p in VITALIA_SRC.rglob("*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs[n.name] = n
    return funcs


def _relative(p: Path) -> str:
    return str(p.relative_to(WS_ROOT))


def _is_mutation_decorator(decorator: ast.expr) -> bool:
    """Return True if a decorator is a router mutation method call (@router.post(...) etc.)."""
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Attribute):
            return func.attr in MUTATION_DECORATOR_ATTRS
    return False


def _depends_factory_names(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Collect the names passed to `Depends(<name>)` in a handler's signature.

    Catches both `= Depends(factory)` defaults and `Annotated[T, Depends(factory)]`
    annotations by walking only the function's arguments node (not its body).
    """
    names: set[str] = set()
    for call in ast.walk(func_node.args):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        is_depends = (isinstance(func, ast.Name) and func.id == "Depends") or (
            isinstance(func, ast.Attribute) and func.attr == "Depends"
        )
        if not is_depends or not call.args:
            continue
        first = call.args[0]
        if isinstance(first, ast.Name):
            names.add(first.id)
        elif isinstance(first, ast.Attribute):
            names.add(first.attr)
    return names


def _session_closure(
    handler: ast.FunctionDef | ast.AsyncFunctionDef,
    funcs_by_name: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> set[str]:
    """Resolve every session factory reachable from a handler's dependency graph.

    A handler may keep a NON-committing session only for read-only context/auth
    resolution and delegate the actual write to a `_get_*_service` provider that
    injects `get_async_session_committing` (the convention the codebase converged
    on for HB-50). So the durability of the write lives in the *closure* of the
    handler's `Depends(...)` factories, not just its own signature. We follow
    local provider functions (defined in the same module) a couple of levels deep.
    """
    seen: set[str] = set()
    closure: set[str] = set()
    frontier = [handler.name]
    while frontier:
        fname = frontier.pop()
        if fname in seen:
            continue
        seen.add(fname)
        fnode = funcs_by_name.get(fname)
        if fnode is None:
            continue
        for dep in _depends_factory_names(fnode):
            closure.add(dep)
            if dep in funcs_by_name:  # local provider → recurse into its deps
                frontier.append(dep)
    return closure


class TestMutationHandlersCommit:
    """Mutation route handlers must use the committing session factory (HB-50)."""

    def test_route_files_exist(self) -> None:
        """Sanity: at least one route file must exist."""
        assert len(_route_files()) >= 1, (
            "No router/routes files found under vitalia/backend/src/ — expected at least one."
        )

    def test_mutations_use_committing_session(self) -> None:
        """POST/PATCH/PUT/DELETE handlers must not depend on the non-committing session.

        Using `Depends(get_async_session)` on a mutation handler returns 200/201
        while the write is rolled back at session close (HB-50 silent-killer).
        Use `Depends(get_async_session_committing)` instead, or allowlist with
        justification if a service owns the commit.
        """
        violations: list[str] = []
        funcs_by_name = _all_funcs()

        for route_file in _route_files():
            source = route_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(route_file))
            except SyntaxError:
                continue  # Caught by ruff lint gate

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                is_mutation = any(_is_mutation_decorator(dec) for dec in node.decorator_list)
                if not is_mutation:
                    continue

                rel_file = _relative(route_file)
                exempt_key = f"{rel_file}::{node.name}"
                if exempt_key in KNOWN_NON_COMMITTING_MUTATIONS:
                    continue

                factories = _session_closure(node, funcs_by_name)
                # Flag only when the entire dependency closure touches the
                # non-committing session and NEVER the committing one — i.e. the
                # write has no committing unit-of-work anywhere in its graph.
                if NON_COMMITTING_FACTORY in factories and COMMITTING_FACTORY not in factories:
                    method = next(
                        (
                            dec.func.attr  # type: ignore[union-attr]
                            for dec in node.decorator_list
                            if _is_mutation_decorator(dec)
                        ),
                        "?",
                    )
                    violations.append(
                        f"{rel_file}:{node.lineno}: "
                        f"@router.{method}(...) on `{node.name}` uses "
                        f"Depends({NON_COMMITTING_FACTORY}) — a mutation handler must use "
                        f"Depends({COMMITTING_FACTORY}) or its write is silently rolled back."
                    )

        assert violations == [], (
            "Mutation handlers on the non-committing session detected (HB-50 silent-killer):\n\n"
            + "\n".join(violations)
            + f"\n\nFix: change the session dependency to `Depends({COMMITTING_FACTORY})` "
            "(db.py — commits on clean return, rolls back on error).\n"
            "If a service inside the handler owns the commit explicitly, add the handler "
            "to KNOWN_NON_COMMITTING_MUTATIONS with justification (shrink-only)."
        )
