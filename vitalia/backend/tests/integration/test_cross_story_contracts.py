"""Cross-story contract shape tests — T-16 vitalia-slice-1-fidelizacion.

Cementa los contratos de eventos de dominio y DTOs de endpoint producidos
por la story vitalia-slice-1-fidelizacion (Ola 1) para consumo de Olas
paralelas y futuras (inbox, marketing, analytics).

Contratos verificados:
  1. NPSScoreCollected        — evento de dominio (T-5 emitter, /inbox consumer)
  2. ReEngagementTriggered    — evento de dominio (T-5 emitter, /inbox consumer)
  3. PatientOptedOut          — evento de dominio (T-2 emitter, T-5 OptOutService consumer)
  4. PatientPausedReEngagement — evento de dominio (T-5 emitter, fidelización UI consumer)
  5. NPSSummaryResponse       — DTO endpoint GET /nps/summary (inbox NPS tag chip)
  6. ReEngagementPatternListResponse — DTO endpoint GET /re-engagement/patterns

Estrategia de prueba:
  - Eventos (@dataclass heredan DomainEvent): dataclasses.fields() para inspección.
  - DTOs (Pydantic v2 BaseModel): model_fields para inspección.
  - Snapshot + assert sobre expected_fields: si el contrato cambia, el test
    falla explícitamente y el consumidor debe actualizar su schema.
  - Tests SIN Postgres — solo introspección estática de clases importadas.
  - Validator ID: be_cross_story_contracts

No se usa @pytest.mark.integration — no requiere Postgres.
Ref HANDOFF-cross-story-updates.md § 1.4 y § 5.

downstream-regression-na: cross-story shape tests T-16 fidelizacion vitalia
"""

from __future__ import annotations

import dataclasses
from uuid import UUID

from src.modules.vitalia.fidelizacion.application.dtos.nps_dtos import NPSSummaryResponse
from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ReEngagementPatternListResponse,
)

# ─────────────────────────────────────────────────────────────────────────────
# Imports — domain events (producer: T-5 fidelizacion)
# ─────────────────────────────────────────────────────────────────────────────
from src.modules.vitalia.fidelizacion.domain.events.events import (
    FIDELIZACION_NPS_SCORE_COLLECTED,
    FIDELIZACION_PATIENT_OPTED_OUT,
    FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT,
    FIDELIZACION_RE_ENGAGEMENT_TRIGGERED,
    NPSScoreCollected,
    PatientOptedOut,
    PatientPausedReEngagement,
    ReEngagementTriggered,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _dataclass_field_names(cls: type) -> set[str]:
    """Retorna el conjunto de nombres de campos de un @dataclass (incluye heredados)."""
    return {f.name for f in dataclasses.fields(cls)}


def _pydantic_field_names(cls: type) -> set[str]:
    """Retorna el conjunto de nombres de campos de un BaseModel Pydantic v2."""
    return set(cls.model_fields.keys())


# ─────────────────────────────────────────────────────────────────────────────
# 1. NPSScoreCollected — shape contract
# ─────────────────────────────────────────────────────────────────────────────


class TestNPSScoreCollectedShape:
    """Verifica el shape del evento NPSScoreCollected (producer: T-5 fidelizacion).

    Consumer /inbox Ola 1 — usa el evento para renderizar el tag NPS badge
    por conversación. Campos esperados deben coincidir con la firma del
    handler del bus de eventos en /inbox.
    """

    # Campos esperados por el consumer (/inbox tag chip handler)
    # Incluye campos DomainEvent base (event_name, tenant_id, occurred_at, payload)
    # más campos específicos de NPSScoreCollected.
    EXPECTED_FIELDS: frozenset[str] = frozenset(
        {
            # Base DomainEvent fields
            "event_name",
            "tenant_id",
            "occurred_at",
            "payload",
            # NPSScoreCollected-specific fields
            "clinic_id",
            "patient_id",
            "nps_response_id",
            "score",
            "band",
            "appointment_id",
        }
    )

    def test_nps_score_collected_has_all_required_fields(self) -> None:
        """NPSScoreCollected contiene todos los campos requeridos por el consumer /inbox."""
        actual = _dataclass_field_names(NPSScoreCollected)
        missing = self.EXPECTED_FIELDS - actual
        assert not missing, (
            f"NPSScoreCollected le faltan campos requeridos por /inbox consumer: {missing!r}\n"
            "Si el contrato cambió, actualizar HANDOFF-cross-story-updates.md § 1.4."
        )

    def test_nps_score_collected_no_unexpected_phi_fields(self) -> None:
        """NPSScoreCollected NO expone comment_plain ni campos PHI directos."""
        actual = _dataclass_field_names(NPSScoreCollected)
        phi_fields = {"comment_plain", "patient_name", "patient_email", "patient_phone"}
        exposed_phi = phi_fields & actual
        assert not exposed_phi, (
            f"NPSScoreCollected expone PHI fields prohibidos: {exposed_phi!r}\n"
            "Solo IDs UUID se permiten en eventos de dominio (HIPAA-lite)."
        )

    def test_nps_score_collected_event_name_constant(self) -> None:
        """El event_name SSoT coincide con la constante del módulo."""
        assert FIDELIZACION_NPS_SCORE_COLLECTED == "vitalia.fidelizacion.nps_score_collected"

    def test_nps_score_collected_create_factory_produces_correct_event_name(self) -> None:
        """NPSScoreCollected.create() produce evento con event_name correcto (consumer-safe)."""
        import uuid as _uuid

        event = NPSScoreCollected.create(
            tenant_id=_uuid.uuid4(),
            clinic_id=_uuid.uuid4(),
            patient_id=_uuid.uuid4(),
            nps_response_id=_uuid.uuid4(),
            score=8,
            band="passive",
        )
        assert event.event_name == FIDELIZACION_NPS_SCORE_COLLECTED
        assert isinstance(event.tenant_id, UUID)
        assert isinstance(event.clinic_id, UUID)
        assert isinstance(event.nps_response_id, UUID)
        assert event.score == 8
        assert event.band == "passive"
        assert event.appointment_id is None  # opcional

    def test_nps_score_collected_band_values_match_inbox_filter_chips(self) -> None:
        """Los valores de band del evento coinciden con los filter chips del /inbox.

        /inbox Ola 1 filtra por band=detractor para mostrar badge rojo.
        """
        from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand

        assert NPSBand.DETRACTOR.value == "detractor"
        assert NPSBand.PASSIVE.value == "passive"
        assert NPSBand.PROMOTER.value == "promoter"
        # Derivación desde score — contract del consumer handler
        assert NPSBand.from_score(5) == NPSBand.DETRACTOR
        assert NPSBand.from_score(7) == NPSBand.PASSIVE
        assert NPSBand.from_score(9) == NPSBand.PROMOTER


# ─────────────────────────────────────────────────────────────────────────────
# 2. ReEngagementTriggered — shape contract
# ─────────────────────────────────────────────────────────────────────────────


class TestReEngagementTriggeredShape:
    """Verifica el shape del evento ReEngagementTriggered.

    Consumer /inbox Ola 1 — crea proactive_outbound conversation
    con attribution metadata 'Adrián abrió conv · solicitado por sistema (cron X)'.
    """

    EXPECTED_FIELDS: frozenset[str] = frozenset(
        {
            # Base DomainEvent fields
            "event_name",
            "tenant_id",
            "occurred_at",
            "payload",
            # ReEngagementTriggered-specific fields
            "clinic_id",
            "patient_id",
            "pattern",
            "re_engagement_event_id",
            "template_id",
            "triggered_by_user_id",
        }
    )

    def test_re_engagement_triggered_has_all_required_fields(self) -> None:
        """ReEngagementTriggered contiene todos los campos esperados por /inbox consumer."""
        actual = _dataclass_field_names(ReEngagementTriggered)
        missing = self.EXPECTED_FIELDS - actual
        assert not missing, (
            f"ReEngagementTriggered le faltan campos para /inbox: {missing!r}\n"
            "Si el contrato cambió, actualizar HANDOFF-cross-story-updates.md § 1.4."
        )

    def test_re_engagement_triggered_event_name_constant(self) -> None:
        """El event_name SSoT coincide con la constante del módulo."""
        assert FIDELIZACION_RE_ENGAGEMENT_TRIGGERED == "vitalia.fidelizacion.re_engagement_triggered"

    def test_re_engagement_triggered_create_factory(self) -> None:
        """ReEngagementTriggered.create() produce evento con todos los campos requeridos."""
        import uuid as _uuid

        re_event_id = _uuid.uuid4()
        event = ReEngagementTriggered.create(
            tenant_id=_uuid.uuid4(),
            clinic_id=_uuid.uuid4(),
            patient_id=_uuid.uuid4(),
            pattern="follow_up",
            re_engagement_event_id=re_event_id,
            template_id="tpl_follow_up_v2",
        )
        assert event.event_name == FIDELIZACION_RE_ENGAGEMENT_TRIGGERED
        assert event.pattern == "follow_up"
        assert event.re_engagement_event_id == re_event_id
        assert event.template_id == "tpl_follow_up_v2"
        assert event.triggered_by_user_id is None  # opcional

    def test_re_engagement_triggered_pattern_values_match_inbox_activity_event(self) -> None:
        """Los valores de pattern coinciden con los activity_event types del /inbox.

        /inbox actualiza el activity_event.description basado en el pattern
        del evento ReEngagementTriggered.
        """
        from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
            ReEngagementPattern,
        )

        expected_patterns = {"multi_session", "follow_up", "maintenance", "absence", "nps"}
        actual_patterns = {p.value for p in ReEngagementPattern}
        assert actual_patterns == expected_patterns, (
            f"Patterns cambiaron — /inbox debe actualizar su activity_event handler.\n"
            f"Esperados: {expected_patterns!r}\nActuales: {actual_patterns!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. PatientOptedOut — shape contract
# ─────────────────────────────────────────────────────────────────────────────


class TestPatientOptedOutShape:
    """Verifica el shape del evento PatientOptedOut.

    Producido por: T-2 opt_out_service (via CRM endpoint).
    Consumido por: T-5 OptOutService (fidelizacion) para filtrar crons +
                   /inbox (cascade cancel pending conversations) +
                   /pipeline + /marketing.
    """

    EXPECTED_FIELDS: frozenset[str] = frozenset(
        {
            # Base DomainEvent fields
            "event_name",
            "tenant_id",
            "occurred_at",
            "payload",
            # PatientOptedOut-specific fields
            "clinic_id",
            "patient_id",
            "reason",
            "triggered_by_user_id",
        }
    )

    def test_patient_opted_out_has_all_required_fields(self) -> None:
        """PatientOptedOut contiene todos los campos esperados por los consumers."""
        actual = _dataclass_field_names(PatientOptedOut)
        missing = self.EXPECTED_FIELDS - actual
        assert not missing, (
            f"PatientOptedOut le faltan campos: {missing!r}\n"
            "Consumer /inbox + /pipeline + /marketing deben poder filtrar por patient_id + clinic_id."
        )

    def test_patient_opted_out_event_name_constant(self) -> None:
        """El event_name SSoT es correcto (consumers filtran por este string)."""
        assert FIDELIZACION_PATIENT_OPTED_OUT == "vitalia.fidelizacion.patient_opted_out"

    def test_patient_opted_out_optional_fields_are_nullable(self) -> None:
        """reason y triggered_by_user_id son opcionales — consumer debe manejar None."""
        import uuid as _uuid

        event = PatientOptedOut.create(
            tenant_id=_uuid.uuid4(),
            clinic_id=_uuid.uuid4(),
            patient_id=_uuid.uuid4(),
            # reason=None (default)
            # triggered_by_user_id=None (default)
        )
        assert event.reason is None
        assert event.triggered_by_user_id is None
        assert event.event_name == FIDELIZACION_PATIENT_OPTED_OUT

    def test_patient_opted_out_no_phi_direct_fields(self) -> None:
        """PatientOptedOut NO expone campos PHI directo (solo IDs)."""
        actual = _dataclass_field_names(PatientOptedOut)
        phi_fields = {"patient_name", "patient_email", "patient_phone", "medical_notes"}
        exposed_phi = phi_fields & actual
        assert not exposed_phi, f"PatientOptedOut expone PHI: {exposed_phi!r}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. PatientPausedReEngagement — shape contract
# ─────────────────────────────────────────────────────────────────────────────


class TestPatientPausedReEngagementShape:
    """Verifica el shape del evento PatientPausedReEngagement.

    Producido por: T-5 pause_patient_service.
    Consumido por: fidelización UI refresh (own) + audit log.
    Slice 2: surface en /inbox CRM card toggle.
    """

    EXPECTED_FIELDS: frozenset[str] = frozenset(
        {
            # Base DomainEvent fields
            "event_name",
            "tenant_id",
            "occurred_at",
            "payload",
            # PatientPausedReEngagement-specific fields
            "clinic_id",
            "patient_id",
            "duration_days",
            "reason",
            "resume_at",
            "triggered_by_user_id",
        }
    )

    def test_patient_paused_re_engagement_has_all_required_fields(self) -> None:
        """PatientPausedReEngagement tiene todos los campos requeridos."""
        actual = _dataclass_field_names(PatientPausedReEngagement)
        missing = self.EXPECTED_FIELDS - actual
        assert not missing, (
            f"PatientPausedReEngagement le faltan campos: {missing!r}\n"
            "Consumer cron skip logic necesita duration_days + resume_at para filtrar."
        )

    def test_patient_paused_re_engagement_event_name_constant(self) -> None:
        """El event_name SSoT es correcto."""
        assert FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT == "vitalia.fidelizacion.patient_paused_re_engagement"

    def test_patient_paused_re_engagement_create_factory(self) -> None:
        """PatientPausedReEngagement.create() produce evento con campos correctos."""
        import uuid as _uuid
        from datetime import UTC, datetime, timedelta

        resume = datetime.now(UTC) + timedelta(days=30)
        event = PatientPausedReEngagement.create(
            tenant_id=_uuid.uuid4(),
            clinic_id=_uuid.uuid4(),
            patient_id=_uuid.uuid4(),
            duration_days=30,
            reason="Paciente viajando",
            resume_at=resume,
        )
        assert event.event_name == FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT
        assert event.duration_days == 30
        assert event.reason == "Paciente viajando"
        assert event.resume_at == resume


# ─────────────────────────────────────────────────────────────────────────────
# 5. NPSSummaryResponse DTO — endpoint shape contract
# ─────────────────────────────────────────────────────────────────────────────


class TestNPSSummaryResponseShape:
    """Verifica el shape del DTO NPSSummaryResponse (GET /nps/summary).

    Consumer: /inbox Ola 1 usa este endpoint para renderizar el tag chip
    'detractor' count en la sidebar de conversaciones.
    Future: /marketing Slice 2 NPS distribution analytics dashboard.
    """

    EXPECTED_FIELDS: frozenset[str] = frozenset(
        {
            "tenant_id",
            "clinic_id",
            "period_start",
            "period_end",
            "total_responses",
            "promoters",
            "passives",
            "detractors",
            "nps_score",
            "response_rate",
            "detractors_untagged",
        }
    )

    def test_nps_summary_response_has_all_consumer_fields(self) -> None:
        """NPSSummaryResponse tiene todos los campos que /inbox necesita para renderizar."""
        actual = _pydantic_field_names(NPSSummaryResponse)
        missing = self.EXPECTED_FIELDS - actual
        assert not missing, (
            f"NPSSummaryResponse le faltan campos: {missing!r}\n"
            "/inbox consumer usa detractors + detractors_untagged para tag chip."
        )

    def test_nps_summary_response_no_phi_fields(self) -> None:
        """NPSSummaryResponse NO incluye PHI per-patient (solo stats anónimas)."""
        actual = _pydantic_field_names(NPSSummaryResponse)
        phi_fields = {
            "rows",
            "patient_id",
            "patient_name",
            "comment",
            "comment_plain",
            "patients",
        }
        exposed_phi = phi_fields & actual
        assert not exposed_phi, (
            f"NPSSummaryResponse expone campos PHI prohibidos: {exposed_phi!r}\n"
            "GET /nps/summary solo devuelve estadísticas anónimas (HIPAA-lite)."
        )

    def test_nps_summary_response_schema_matches_expected(self) -> None:
        """Schema Pydantic v2 de NPSSummaryResponse es estable (snapshot contract)."""
        schema = NPSSummaryResponse.model_json_schema()
        schema_props = set(schema.get("properties", {}).keys())
        # Verificar que el schema JSON tiene los campos esperados
        missing = self.EXPECTED_FIELDS - schema_props
        assert not missing, (
            f"Schema JSON de NPSSummaryResponse no incluye: {missing!r}\n"
            "Los consumers generan code a partir de este schema."
        )

    def test_nps_summary_response_instantiation_with_zero_data(self) -> None:
        """NPSSummaryResponse puede instanciarse con datos vacíos (tenant nuevo)."""
        from datetime import UTC, datetime

        resp = NPSSummaryResponse(
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            clinic_id=UUID("00000000-0000-0000-0000-000000000002"),
            period_start=datetime(2026, 5, 1, tzinfo=UTC),
            period_end=datetime(2026, 5, 20, tzinfo=UTC),
            total_responses=0,
            promoters=0,
            passives=0,
            detractors=0,
            nps_score=0.0,
        )
        assert resp.total_responses == 0
        assert resp.detractors_untagged == 0  # default
        assert resp.response_rate is None  # default


# ─────────────────────────────────────────────────────────────────────────────
# 6. ReEngagementPatternListResponse DTO — endpoint shape contract
# ─────────────────────────────────────────────────────────────────────────────


class TestReEngagementPatternListResponseShape:
    """Verifica el shape del DTO ReEngagementPatternListResponse.

    Endpoint: GET /api/v1/vitalia/fidelization/re-engagement/patterns
    Consumer: /marketing Ola 2 Lucas card source (future Slice 2).
    """

    EXPECTED_FIELDS: frozenset[str] = frozenset(
        {
            "tenant_id",
            "clinic_id",
            "patterns",
        }
    )

    EXPECTED_PATTERN_SUMMARY_FIELDS: frozenset[str] = frozenset(
        {
            "pattern",
            "total_sent",
            "total_responded",
            "total_converted",
            "response_rate",
            "conversion_rate",
        }
    )

    def test_re_engagement_pattern_list_response_has_required_fields(self) -> None:
        """ReEngagementPatternListResponse tiene los campos del contract."""
        actual = _pydantic_field_names(ReEngagementPatternListResponse)
        missing = self.EXPECTED_FIELDS - actual
        assert not missing, (
            f"ReEngagementPatternListResponse le faltan campos: {missing!r}\n"
            "Consumer /marketing Slice 2 debe poder iterar patterns con rate metrics."
        )

    def test_pattern_summary_response_has_rate_metrics(self) -> None:
        """PatternSummaryResponse incluye rate metrics que /marketing necesita."""
        from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
            PatternSummaryResponse,
        )

        actual = _pydantic_field_names(PatternSummaryResponse)
        missing = self.EXPECTED_PATTERN_SUMMARY_FIELDS - actual
        assert not missing, (
            f"PatternSummaryResponse le faltan campos: {missing!r}\n"
            "Consumer /marketing usa response_rate + conversion_rate para Lucas analysis."
        )

    def test_re_engagement_pattern_list_response_schema(self) -> None:
        """Schema Pydantic v2 de ReEngagementPatternListResponse es estable."""
        schema = ReEngagementPatternListResponse.model_json_schema()
        assert "properties" in schema
        schema_props = set(schema["properties"].keys())
        missing = self.EXPECTED_FIELDS - schema_props
        assert not missing, f"Schema JSON de ReEngagementPatternListResponse no incluye: {missing!r}"

    def test_re_engagement_pattern_list_response_patterns_is_list(self) -> None:
        """El campo patterns es una lista (consumer itera sobre ella)."""
        from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
            PatternSummaryResponse,
        )
        from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
            ReEngagementPattern,
        )

        resp = ReEngagementPatternListResponse(
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            clinic_id=UUID("00000000-0000-0000-0000-000000000002"),
            patterns=[
                PatternSummaryResponse(
                    pattern=ReEngagementPattern.FOLLOW_UP,
                    total_sent=10,
                    total_responded=4,
                    total_converted=2,
                    response_rate=0.4,
                    conversion_rate=0.2,
                )
            ],
        )
        assert isinstance(resp.patterns, list)
        assert len(resp.patterns) == 1
        assert resp.patterns[0].pattern == ReEngagementPattern.FOLLOW_UP


# ─────────────────────────────────────────────────────────────────────────────
# 7. Event name constants — SSoT registry (consumido por bus handlers)
# ─────────────────────────────────────────────────────────────────────────────


class TestEventNameConstants:
    """Verifica que los event_name constants sean estables (consumers filtran por string).

    Si un event_name cambia, todos los handlers del bus de eventos del consumer
    dejan de recibir el evento silenciosamente.
    """

    def test_all_event_name_constants_are_stable(self) -> None:
        """Todos los event_name constants del módulo son estables (no cambiar sin migración)."""
        expected_constants = {
            FIDELIZACION_RE_ENGAGEMENT_TRIGGERED: "vitalia.fidelizacion.re_engagement_triggered",
            FIDELIZACION_NPS_SCORE_COLLECTED: "vitalia.fidelizacion.nps_score_collected",
            FIDELIZACION_PATIENT_OPTED_OUT: "vitalia.fidelizacion.patient_opted_out",
            FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT: "vitalia.fidelizacion.patient_paused_re_engagement",
        }
        for const, expected_value in expected_constants.items():
            assert const == expected_value, (
                f"Constante de event_name cambió: {const!r} != {expected_value!r}\n"
                "Cambiar un event_name rompe todos los handlers del consumer silenciosamente."
            )

    def test_event_names_are_namespaced_correctly(self) -> None:
        """Todos los event_names tienen el prefijo vitalia.fidelizacion."""
        event_names = [
            FIDELIZACION_RE_ENGAGEMENT_TRIGGERED,
            FIDELIZACION_NPS_SCORE_COLLECTED,
            FIDELIZACION_PATIENT_OPTED_OUT,
            FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT,
        ]
        for name in event_names:
            assert name.startswith("vitalia.fidelizacion."), (
                f"Event name sin prefijo correcto: {name!r}. El namespace vitalia.fidelizacion es el SSoT del bus."
            )
