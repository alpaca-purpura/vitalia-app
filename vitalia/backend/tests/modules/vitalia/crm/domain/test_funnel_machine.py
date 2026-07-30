# cap: crm.adrian-embudo
"""Tests for FunnelMachine — RED first per TDD mandate (T-BE-1).

Tests the deterministic 6-stage dental funnel state machine:
- Stage transitions allowed/forbidden
- SLA configuration per stage
- HOT_BOARD_STAGES constant
- FREEZE_RULES constant
- Validator coverage: NF-1 (transitions), NF-2 (SLA), NF-3 (constants)
"""

from __future__ import annotations


class TestFunnelMachineStages:
    """Tests for STAGE_MACHINE transitions."""

    def test_interesado_can_transition_to_calificando(self) -> None:
        """Interesado → calificando is the primary forward step."""
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert "calificando" in STAGE_MACHINE["interesado"]

    def test_interesado_can_transition_to_decidio_no(self) -> None:
        """Interesado → decidio_no (rejection at any stage)."""
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert "decidio_no" in STAGE_MACHINE["interesado"]

    def test_calificando_can_transition_to_consulta(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert "consulta_agendada" in STAGE_MACHINE["calificando"]

    def test_calificando_can_transition_to_decidio_no(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert "decidio_no" in STAGE_MACHINE["calificando"]

    def test_consulta_can_transition_to_plan(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert "plan_presentado" in STAGE_MACHINE["consulta_agendada"]

    def test_plan_can_transition_to_reservado(self) -> None:
        """plan_presentado → reservado (webhook only, but listed in machine)."""
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert "reservado" in STAGE_MACHINE["plan_presentado"]

    def test_reservado_is_terminal(self) -> None:
        """reservado is a success terminal stage — no outgoing transitions."""
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert STAGE_MACHINE["reservado"] == []

    def test_decidio_no_is_terminal(self) -> None:
        """decidio_no is a failure terminal stage — no outgoing transitions."""
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        assert STAGE_MACHINE["decidio_no"] == []

    def test_all_6_stages_present(self) -> None:
        """All 6 dental funnel stages are defined in the machine."""
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        expected_stages = {
            "interesado",
            "calificando",
            "consulta_agendada",
            "plan_presentado",
            "reservado",
            "decidio_no",
        }
        assert set(STAGE_MACHINE.keys()) == expected_stages

    def test_no_backward_transitions_defined(self) -> None:
        """Forward-only machine: no stage points backward by default."""
        from src.modules.vitalia.crm.domain.funnel_machine import STAGE_MACHINE

        stage_order = [
            "interesado",
            "calificando",
            "consulta_agendada",
            "plan_presentado",
            "reservado",
        ]
        for i, stage in enumerate(stage_order):
            for predecessor in stage_order[:i]:
                assert predecessor not in STAGE_MACHINE.get(stage, []), (
                    f"Stage '{stage}' should not transition backward to '{predecessor}'"
                )


class TestFunnelMachineHelpers:
    """Tests for FunnelMachine helper functions."""

    def test_is_terminal_reservado(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import is_terminal_stage

        assert is_terminal_stage("reservado") is True

    def test_is_terminal_decidio_no(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import is_terminal_stage

        assert is_terminal_stage("decidio_no") is True

    def test_is_not_terminal_interesado(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import is_terminal_stage

        assert is_terminal_stage("interesado") is False

    def test_allowed_next_returns_list(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import allowed_next_stages

        result = allowed_next_stages("interesado")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_allowed_next_terminal_returns_empty(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import allowed_next_stages

        assert allowed_next_stages("reservado") == []
        assert allowed_next_stages("decidio_no") == []

    def test_is_manual_reservado_forbidden(self) -> None:
        """Reservado cannot be set manually — only via webhook (RN-4)."""
        from src.modules.vitalia.crm.domain.funnel_machine import is_manual_reservado_forbidden

        assert is_manual_reservado_forbidden("reservado") is True
        assert is_manual_reservado_forbidden("calificando") is False


class TestSLAConfiguration:
    """Tests for SLA_DAYS — NF-2 validator coverage."""

    def test_sla_days_has_4_active_stages(self) -> None:
        """SLA defined for 4 non-terminal active stages."""
        from src.modules.vitalia.crm.domain.funnel_machine import SLA_DAYS

        expected = {"interesado", "calificando", "consulta_agendada", "plan_presentado"}
        assert set(SLA_DAYS.keys()) == expected

    def test_interesado_sla_values(self) -> None:
        """Interesado SLA: green 7d, amber 7d, red 14d (RN-11)."""
        from src.modules.vitalia.crm.domain.funnel_machine import SLA_DAYS

        sla = SLA_DAYS["interesado"]
        assert sla["green"] == 7
        assert sla["amber"] == 7
        assert sla["red"] == 14

    def test_calificando_sla_values(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import SLA_DAYS

        sla = SLA_DAYS["calificando"]
        assert sla["green"] == 7
        assert sla["amber"] == 7
        assert sla["red"] == 14

    def test_consulta_sla_values(self) -> None:
        """Consulta agendada SLA: green 5d, amber 5d, red 10d."""
        from src.modules.vitalia.crm.domain.funnel_machine import SLA_DAYS

        sla = SLA_DAYS["consulta_agendada"]
        assert sla["green"] == 5
        assert sla["amber"] == 5
        assert sla["red"] == 10

    def test_plan_sla_values(self) -> None:
        """Plan presentado SLA: green 14d, amber 14d, red 21d."""
        from src.modules.vitalia.crm.domain.funnel_machine import SLA_DAYS

        sla = SLA_DAYS["plan_presentado"]
        assert sla["green"] == 14
        assert sla["amber"] == 14
        assert sla["red"] == 21

    def test_sla_state_calculation_green(self) -> None:
        """compute_sla_state returns green when days_in_stage <= green threshold."""
        from src.modules.vitalia.crm.domain.funnel_machine import compute_sla_state

        assert compute_sla_state("interesado", days_in_stage=5) == "green"
        assert compute_sla_state("interesado", days_in_stage=7) == "green"

    def test_sla_state_calculation_amber(self) -> None:
        """compute_sla_state returns amber when days_in_stage > amber threshold."""
        from src.modules.vitalia.crm.domain.funnel_machine import compute_sla_state

        assert compute_sla_state("interesado", days_in_stage=8) == "amber"

    def test_sla_state_calculation_red(self) -> None:
        """compute_sla_state returns red when days_in_stage > red threshold."""
        from src.modules.vitalia.crm.domain.funnel_machine import compute_sla_state

        assert compute_sla_state("interesado", days_in_stage=15) == "red"

    def test_sla_state_terminal_returns_none(self) -> None:
        """Terminal stages have no SLA — returns None."""
        from src.modules.vitalia.crm.domain.funnel_machine import compute_sla_state

        assert compute_sla_state("reservado", days_in_stage=100) is None
        assert compute_sla_state("decidio_no", days_in_stage=100) is None


class TestFreezeRules:
    """Tests for FREEZE_RULES — NF-3 coverage."""

    def test_freeze_rules_no_response_days(self) -> None:
        """No response 14d → freeze (RN-13)."""
        from src.modules.vitalia.crm.domain.funnel_machine import FREEZE_RULES

        assert FREEZE_RULES["no_response_days"] == 14

    def test_freeze_rules_hard_days(self) -> None:
        """30d hard cap freeze."""
        from src.modules.vitalia.crm.domain.funnel_machine import FREEZE_RULES

        assert FREEZE_RULES["hard_days"] == 30

    def test_freeze_rules_sla_multiplier(self) -> None:
        """2× SLA multiplier (>2×SLA = freeze)."""
        from src.modules.vitalia.crm.domain.funnel_machine import FREEZE_RULES

        assert FREEZE_RULES["sla_multiplier"] == 2.0


class TestHotBoardStages:
    """Tests for HOT_BOARD_STAGES — RN-18 board scope."""

    def test_hot_board_stages_contains_active_stages(self) -> None:
        from src.modules.vitalia.crm.domain.funnel_machine import HOT_BOARD_STAGES

        assert "interesado" in HOT_BOARD_STAGES
        assert "calificando" in HOT_BOARD_STAGES
        assert "consulta_agendada" in HOT_BOARD_STAGES
        assert "plan_presentado" in HOT_BOARD_STAGES

    def test_hot_board_stages_contains_reservado(self) -> None:
        """Reservado (success terminal) is visible on board as success column."""
        from src.modules.vitalia.crm.domain.funnel_machine import HOT_BOARD_STAGES

        assert "reservado" in HOT_BOARD_STAGES

    def test_hot_board_stages_excludes_decidio_no(self) -> None:
        """decidio_no goes to Recuperar tab, NOT the hot board."""
        from src.modules.vitalia.crm.domain.funnel_machine import HOT_BOARD_STAGES

        assert "decidio_no" not in HOT_BOARD_STAGES
