# cap: __shared__
"""FE<->BE contract parity gate — catches "imagined contract" fields at BUILD time.

Context (HB-42):
  vitalia-fase2-adrian-embudo experienced a class of bug where the FE TypeScript
  view-model declared fields the BE Pydantic DTO never emitted. The mismatch was
  invisible because BOTH sides were mocked in tests and the real integration was
  never exercised. The board crashed live with `undefined` field accesses.

This test provides a deterministic, server-free check:
  1. Import each registered BE Pydantic DTO class -> introspect `model_fields`.
  2. Parse the corresponding FE TypeScript interface -> extract declared field names.
  3. Convert BE field names from snake_case to camelCase.
  4. Assert: FE-declared fields (minus allowlist) <= BE-emitted fields (camelized).

If a FE field has no BE source, this test fails with a precise list of "imagined
fields" -- exactly the class of bug that caused the embudo crash.

Coverage limit (REGISTRY-BASED, not auto-all-pairs):
  This test covers only the pairs explicitly registered in CONTRACT_PAIRS below.
  It is NOT an automatic scanner of all FE<->BE pairs. When you build a new FE
  view-model against a BE DTO, ADD THE PAIR HERE before merging to main.

References:
  - HB-42 (harness backlog entry that motivated this gate)
  - .claude/rules/definition-of-done-live-verify.md (DoD live verification)
  - vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/ (origin story)
  - vitalia/backend/src/modules/vitalia/crm/application/dto/board_dto.py
  - vitalia/frontend/src/features/adrian/types/embudo.types.ts
"""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest

# -- Workspace root resolution --------------------------------------------------
# vitalia/backend/tests/architecture/ -> 4 parents up = workspace root
WS_ROOT = Path(__file__).resolve().parents[4]


# -- Contract pair descriptor ---------------------------------------------------


@dataclass(frozen=True)
class ContractPair:
    """Describes one FE<->BE contract that must stay in parity.

    Attributes:
        be_module: Python import path for the BE module (relative to vitalia/backend/src/).
                   Expressed as dotted module path suitable for importlib.import_module,
                   prefixed with "src." per the pytest pythonpath=["."] convention.
        be_class:  Name of the Pydantic class within be_module.
        fe_file:   Workspace-relative path to the TypeScript source file.
        fe_interface: Name of the TypeScript interface to extract fields from.
        fe_only_allowlist: FE fields deliberately absent from BE (e.g. client-only
                           computed fields). These are excluded from the parity check.
                           List every such field with a justification comment in the
                           contract entry below.
    """

    be_module: str
    be_class: str
    fe_file: str
    fe_interface: str
    fe_only_allowlist: frozenset[str] = field(default_factory=frozenset)
    fe_pending: bool = False  # True = FE file not yet built (planned ticket). Skip in both parity tests.


# -- CONTRACT_PAIRS registry ---------------------------------------------------
# Add one entry per FE<->BE pair you want to gate.
# KEEP THIS REGISTRY UP TO DATE: when a new FE view-model is built against a BE
# DTO, add its pair here in the same PR -- this is the anti-"imagined-contract" gate.

CONTRACT_PAIRS: list[ContractPair] = [
    # -- Embudo board card (origin of HB-42) ------------------------------------
    # BE:  vitalia/backend/src/modules/vitalia/crm/application/dto/board_dto.py :: LeadCardDTO
    # FE:  vitalia/frontend/src/features/adrian/types/embudo.types.ts :: LeadCardDTO
    #
    # History: T-FE2bis (2026-06-03) extended the BE DTO to match the FE contract.
    # This test LOCKS that contract so future BE changes that drop fields are caught
    # immediately at arch-test time, not at production runtime.
    ContractPair(
        be_module="src.modules.vitalia.crm.application.dto.board_dto",
        be_class="LeadCardDTO",
        fe_file="vitalia/frontend/src/features/adrian/types/embudo.types.ts",
        fe_interface="LeadCardDTO",
        fe_only_allowlist=frozenset(
            [
                # No FE-only fields for this pair.
                # All 23 FE LeadCardDTO fields are emitted by the BE DTO.
            ]
        ),
    ),
    # -- Lead detail autonomy block (HB-44: SAME imagined-contract class as HB-42) --
    # BE:  vitalia/backend/src/modules/vitalia/crm/application/dto/lead_detail_dto.py :: AutonomyInfo
    # FE:  vitalia/frontend/src/features/adrian/types/embudo.types.ts :: AutonomyInfo
    #
    # History: live-verify (Chris, 2026-06-04) hit a runtime crash on the Resumen tab
    # (ResumenView.tsx:184 `autonomy.canDo.join` — undefined). FE imagined
    # canDo/needsApproval/currentMode; BE emits operated_by/can/needs_ok. The board
    # (LeadCardDTO) was gated by HB-42 but THIS nested DTO was never registered -- the
    # exact coverage gap HB-42 flagged. FE realigned to BE; this pair locks it.
    ContractPair(
        be_module="src.modules.vitalia.crm.application.dto.lead_detail_dto",
        be_class="AutonomyInfo",
        fe_file="vitalia/frontend/src/features/adrian/types/embudo.types.ts",
        fe_interface="AutonomyInfo",
        fe_only_allowlist=frozenset(
            [
                # No FE-only fields: FE {operatedBy, can, needsOk} == camelized BE.
            ]
        ),
    ),
    # -- Lead detail full DTO (U2 / HB-44: ResumenView needs phone+email+assignedDoctorId) --
    # BE:  vitalia/backend/src/modules/vitalia/crm/application/dto/lead_dto.py :: LeadResponse
    # FE:  vitalia/frontend/src/features/adrian/types/embudo.types.ts :: LeadDetailLeadDTO
    #
    # Context (U2 / 2026-06-04):
    #   LeadDetailResponse.lead was typed as LeadCardDTO (board projection, no phone/email).
    #   The Resumen tab needs phone + email to display contact info, and assignedDoctorId so
    #   the Doctor row is populated. Fix: new LeadDetailLeadDTO mirrors LeadResponse (which
    #   already exposes email, phone, assigned_doctor_id post T-BE-2 + U2-BE fix).
    #   LeadCardDTO remains unchanged (board projection, deliberately excludes PII).
    ContractPair(
        be_module="src.modules.vitalia.crm.application.dto.lead_dto",
        be_class="LeadResponse",
        fe_file="vitalia/frontend/src/features/adrian/types/embudo.types.ts",
        fe_interface="LeadDetailLeadDTO",
        fe_only_allowlist=frozenset(),  # mirror puro ⊆ BE LeadResponse
    ),
    # -- Clinic Account (vitalia-fase2-config-cuenta T-2) -----------------------
    # BE:  vitalia/backend/src/modules/vitalia/clinics/api/dtos.py :: ClinicAccountResponse
    # FE:  vitalia/frontend/src/features/config/cuenta/types/cuenta.types.ts :: ClinicAccountDTO
    #
    # History: T-2 (2026-06-11) introduces the account surface (GET+PATCH /api/v1/clinics/account/).
    # This pair locks the contract so FE view-model divergence is caught at arch-test time.
    #
    # fe_only_allowlist rationale:
    #   - None currently — FE types file does not yet exist (will be created in T-FE-2).
    #     When T-FE-2 builds the FE, this pair must be verified to match.
    #     Registering here NOW ensures the gate is wired BEFORE the FE is built.
    #
    # NOTE: This pair is REGISTERED but the FE file is planned (T-FE-2 creates it).
    # The test will SKIP gracefully if the FE file doesn't exist yet (see _fe_interface_fields).
    ContractPair(
        be_module="src.modules.vitalia.clinics.api.dtos",
        be_class="ClinicAccountResponse",
        fe_file="vitalia/frontend/src/features/config/types/cuenta.types.ts",
        fe_interface="ClinicAccountDTO",
        fe_only_allowlist=frozenset(
            [
                # clinicType: FE-only display field derived client-side from
                # tenant.config_json.clinic_config.clinic_vertical.
                # The BE ClinicAccountResponse does not expose clinic_type per arch §1
                # ("vertical/clinic_type live in tenant.config_json, not Clinic entity").
                # FE displays it read-only with fallback "—" when absent.
                "clinicType",
                # fiscalIdLabel: FE-only computed field derived from clinic.country
                # (e.g. AR→"CUIT", PE→"RUC", MX→"RFC"). The BE prescribes this in
                # 03-arch §5 but does NOT emit it from ClinicAccountResponse. FE
                # computes it from the received `country` field using a local country-map.
                "fiscalIdLabel",
            ]
        ),
    ),
]


# -- Helpers -------------------------------------------------------------------


def _snake_to_camel(s: str) -> str:
    """Convert snake_case identifier to camelCase.

    Examples:
        tenant_id           -> tenantId
        assigned_doctor_id  -> assignedDoctorId
        stage_entered_at    -> stageEnteredAt
        id                  -> id  (single word unchanged)
    """
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _fe_interface_fields(fe_path: Path, interface_name: str) -> set[str]:
    """Parse a TypeScript source file and extract declared field names from an interface.

    Algorithm:
      1. Find the line starting with `export interface {interface_name} {`.
      2. Consume lines until the closing `}` at column 0 (end of top-level block).
      3. For each line inside the block, match `  fieldName?:` or `  fieldName:`.
      4. Skip comment lines (starting with `//` or `*`).

    Returns a set of camelCase field names exactly as declared in the TypeScript source.

    Raises:
        AssertionError: if the interface is not found in the file.
    """
    source = fe_path.read_text(encoding="utf-8")
    lines = source.splitlines()

    # Pattern to detect the interface opening line
    open_pattern = re.compile(r"^export\s+interface\s+" + re.escape(interface_name) + r"\s*\{")
    # Pattern to extract a field name from interface body lines
    field_pattern = re.compile(r"^\s{2,}(\w+)\??:")
    # Comment line patterns to skip
    comment_pattern = re.compile(r"^\s*(//|\*)")

    inside = False
    brace_depth = 0
    fields: set[str] = set()

    for line in lines:
        if not inside:
            if open_pattern.match(line):
                inside = True
                brace_depth = line.count("{") - line.count("}")
            continue

        # Track brace depth to handle nested objects within the interface
        brace_depth += line.count("{") - line.count("}")

        if brace_depth <= 0:
            # Reached the closing brace of the interface
            break

        # Skip comment lines
        if comment_pattern.match(line):
            continue

        # Only extract fields at depth 1 (direct interface members, not nested object props)
        if brace_depth == 1:
            m = field_pattern.match(line)
            if m:
                fields.add(m.group(1))

    assert inside, (
        f"Interface '{interface_name}' not found in {fe_path}.\nCheck the fe_interface name in CONTRACT_PAIRS."
    )

    return fields


def _be_emitted_fields(import_path: str, class_name: str) -> set[str]:
    """Import a Pydantic model and return its emitted field names as camelCase.

    Uses `model_fields` (Pydantic v2 API). Converts snake_case keys to camelCase
    to match the JSON serialization that FastAPI emits by default (no alias).

    Args:
        import_path: Dotted Python module path (e.g. "src.modules.vitalia.crm...").
        class_name:  Name of the Pydantic class in that module.

    Returns:
        set[str] of camelCase field names as emitted to API consumers.

    Raises:
        ImportError: if the module cannot be imported (dependency or path issue).
        AttributeError: if class_name not found in the module.
    """
    mod = importlib.import_module(import_path)
    cls = getattr(mod, class_name)
    return {_snake_to_camel(f) for f in cls.model_fields}


# -- Parametrized parity test --------------------------------------------------


@pytest.mark.parametrize(
    "pair",
    CONTRACT_PAIRS,
    ids=[f"{p.be_class}({p.fe_interface})" for p in CONTRACT_PAIRS],
)
def test_fe_fields_are_subset_of_be_fields(pair: ContractPair) -> None:
    """FE-declared fields (minus allowlist) MUST be a subset of BE-emitted fields.

    Failure means the FE interface declares fields that the BE DTO never sends.
    These "imagined fields" cause undefined at runtime (the embudo-board bug).

    Contract: FE-declared <= BE-emitted (camelized)
    Allowlisted FE-only fields are excluded from the check.

    To fix a failure:
      OPTION A (preferred): Extend the BE DTO to emit the missing field.
      OPTION B: If the field is genuinely client-only (computed/derived at FE,
                never from the API), add it to fe_only_allowlist in CONTRACT_PAIRS
                with a justification comment.
    """
    fe_path = WS_ROOT / pair.fe_file
    if not fe_path.exists():
        # FE file not yet created (planned for a future ticket, e.g. T-FE-2).
        # Skip gracefully so the BE can be merged and the gate wired in advance.
        pytest.skip(
            f"FE file not yet created (planned): {pair.fe_file}. "
            f"Wire the FE types file in T-FE-2 to activate this parity check."
        )

    fe_fields = _fe_interface_fields(fe_path, pair.fe_interface)
    be_fields = _be_emitted_fields(pair.be_module, pair.be_class)

    # FE fields that are neither in BE nor in the allowlist = imagined fields
    imagined = fe_fields - pair.fe_only_allowlist - be_fields

    assert not imagined, (
        f"\n{'=' * 70}\n"
        f"FE<->BE CONTRACT PARITY FAILURE -- '{pair.fe_interface}' imagined fields detected\n"
        f"{'=' * 70}\n\n"
        f"FE interface:  {pair.fe_file} :: {pair.fe_interface}\n"
        f"BE DTO:        {pair.be_module} :: {pair.be_class}\n\n"
        f"The following FE-declared fields have NO source in the BE DTO.\n"
        f"At runtime the API will never send these -> undefined crashes:\n\n"
        + "\n".join(f"  - {f}" for f in sorted(imagined))
        + "\n\n"
        f"Fix options:\n"
        f"  A) Add the field to the BE Pydantic class + ensure the service populates it.\n"
        f"  B) If the field is client-only (computed at FE, never from API), add it\n"
        f"     to fe_only_allowlist in CONTRACT_PAIRS with a justification comment.\n\n"
        f"Context: HB-42 -- this test exists to prevent the vitalia-fase2-adrian-embudo\n"
        f"class of bug where 6/8 tickets appeared GREEN while the board crashed live.\n"
        f"{'=' * 70}\n"
    )


# -- Registry health tests -----------------------------------------------------


def test_contract_registry_is_non_empty() -> None:
    """Registry must contain at least one pair -- an empty registry catches nothing.

    If this test fails, CONTRACT_PAIRS was accidentally cleared. Add pairs back.
    """
    assert len(CONTRACT_PAIRS) >= 1, (
        "CONTRACT_PAIRS registry is empty. This test file exists to prevent "
        "the 'imagined contract' class of FE<->BE bugs (HB-42). "
        "Add at least one ContractPair entry."
    )


def test_contract_registry_files_exist() -> None:
    """Every registered (non-pending) pair's FE file must exist on disk.

    Prevents registry rot: if a FE file is moved/renamed, the pair silently
    becomes a no-op. This test catches that immediately.

    Pairs with fe_pending=True are skipped here (FE ticket not yet built).
    """
    missing: list[str] = []
    for pair in CONTRACT_PAIRS:
        if pair.fe_pending:
            continue  # FE not yet built — planned in a future ticket
        fe_path = WS_ROOT / pair.fe_file
        if not fe_path.exists():
            missing.append(f"  - {pair.fe_file}  (for {pair.be_class}/{pair.fe_interface})")

    assert not missing, (
        "CONTRACT_PAIRS registry refers to FE files that no longer exist.\n"
        "Update the fe_file paths in CONTRACT_PAIRS:\n\n" + "\n".join(missing) + "\n\n"
        "Registry rot check: if the file was moved, update the path. "
        "If the interface was deleted, remove the pair from CONTRACT_PAIRS."
    )
