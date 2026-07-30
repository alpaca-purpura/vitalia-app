# cap: brand_studio.lisa-marca
# story-origin: vitalia-fase2-s7-TBD
"""MarcaService — core orchestrator for sub-tab Lisa > Marca.

Wraps engine brand_studio repos + brand-local audit + telemetry.
Audit log sync write BEFORE return on every mutation.
Telemetry fire-forget (never propagates error).

Architecture:
  - Engine repos (BrandRepository, PersonalityProfileRepository) use sync Session.
  - Vitalia FastAPI uses AsyncSession.
  - Bridge: session.run_sync() for engine calls.
  - NO PhiRepositoryBase — owner config, no PHI dual filter.
  - Tenant isolation: every engine call passes tenant_id.

Anti-creep: NO brand_voice_summary, NO health_voice_validator.

downstream-regression-na: brand-local service vitalia
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
    BrandContactDTO,
    BrandContactPatchDTO,
    BrandIdentityDTO,
    BrandIdentityPatchDTO,
    BrandPersonalityDTO,
    BrandPersonalityPatchDTO,
    BrandTeamPreviewDTO,
    BrandVisualsDTO,
    BrandVisualsPatchDTO,
    ClinicConfigDTO,
    LogoUploadResponseDTO,
    MarcaInitialStateDTO,
    TeamMemberPreviewItemDTO,
    TrustSignalCreateRequestDTO,
    TrustSignalDTO,
    VoicePreviewDTO,
)
from src.modules.vitalia.brand_studio.application.services.trust_catalog_service import (
    TrustCatalogService,
)
from src.modules.vitalia.brand_studio.application.services.voice_blocklist_service import (
    VoiceBlocklistService,
)
from src.modules.vitalia.brand_studio.application.services.voice_preview_service import (
    VoicePreviewService,
)
from src.modules.vitalia.brand_studio.infrastructure.repositories.trust_signal_repository import (
    TrustSignalRepository,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# Sentinel clinic_id for brand_studio (owner-level config, no clinic context)
_NULL_CLINIC_ID = UUID(int=0)
_COMPILER_VERSION = "v2"


class MarcaService:
    """Orchestrator for sub-tab Marca — wraps engine brand_studio + audit + telemetry.

    Engine repos are sync; bridged via AsyncSession.run_sync().
    Every mutation writes audit_log row sync (awaited) pre-return.
    Telemetry is fire-forget (exception logged, never propagated).
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: AsyncAuditWriter,
        telemetry: GrowthStudioEmitter,
        voice_preview_service: VoicePreviewService,
        voice_blocklist_service: VoiceBlocklistService,
        trust_signal_repo: TrustSignalRepository,
        trust_catalog_service: TrustCatalogService,
    ) -> None:
        """Initialize MarcaService.

        Args:
            session: AsyncSession for DB operations.
            audit: AsyncAuditWriter for audit_log sync writes.
            telemetry: GrowthStudioEmitter for fire-forget telemetry.
            voice_preview_service: VoicePreviewService for slot 5 compile + cache.
            voice_blocklist_service: VoiceBlocklistService for prohibited phrases.
            trust_signal_repo: TrustSignalRepository for tenant trust signals.
            trust_catalog_service: TrustCatalogService for hybrid catalog.
        """
        self._session = session
        self._audit = audit
        self._telemetry = telemetry
        self._voice_preview = voice_preview_service
        self._voice_blocklist = voice_blocklist_service
        self._trust_signal_repo = trust_signal_repo
        self._trust_catalog = trust_catalog_service

    # ---------- Engine repo helpers ----------------------------------------

    async def _get_brand_settings(self, tenant_id: UUID) -> Any:
        """Load BrandSettings from engine via run_sync bridge."""
        from luana_core_brand_studio.infrastructure.repositories.brand_repository import (  # noqa: PLC0415
            BrandRepository,
        )

        def _sync_get(sync_session: Any) -> Any:
            repo = BrandRepository(db=sync_session)
            return repo.get_settings(tenant_id)

        return await self._session.run_sync(_sync_get)

    async def _save_brand_settings(self, tenant_id: UUID, settings: Any) -> Any:
        """Save BrandSettings via engine run_sync bridge."""
        from luana_core_brand_studio.infrastructure.repositories.brand_repository import (  # noqa: PLC0415
            BrandRepository,
        )

        def _sync_save(sync_session: Any) -> Any:
            repo = BrandRepository(db=sync_session)
            return repo.save_settings(tenant_id, settings)

        return await self._session.run_sync(_sync_save)

    async def _get_personality_profile(self, tenant_id: UUID) -> Any | None:
        """Load active PersonalityProfile from engine via run_sync bridge."""
        from luana_core_brand_studio.infrastructure.repositories.personality_repository import (  # noqa: PLC0415
            PersonalityProfileRepository,
        )

        def _sync_get(sync_session: Any) -> Any | None:
            repo = PersonalityProfileRepository(db=sync_session)
            return repo.get_active_for_tenant(tenant_id=tenant_id)

        try:
            return await self._session.run_sync(_sync_get)
        except AttributeError:
            # Fallback if get_active_for_tenant not available — query directly
            return await self._get_personality_profile_fallback(tenant_id)

    async def _get_personality_profile_fallback(self, tenant_id: UUID) -> Any | None:
        """Fallback query for personality profile (SQLA 2.0 direct query)."""
        from luana_core_brand_studio.infrastructure.models.personality_model import (  # noqa: PLC0415
            PersonalityProfileModel,
        )
        from sqlalchemy import select  # noqa: PLC0415

        stmt = (
            select(PersonalityProfileModel)
            .where(
                PersonalityProfileModel.tenant_id == tenant_id,
                PersonalityProfileModel.is_active.is_(True),
                PersonalityProfileModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def _emit_telemetry(
        self,
        event_type: str,
        *,
        tenant_id: UUID,
        user_id: UUID | None = None,
        **props: Any,
    ) -> None:
        """Fire-forget telemetry — swallow all exceptions.

        Args:
            event_type: Snake_case event identifier (e.g. 'lisa_marca_personality_saved').
            tenant_id: Root tenant UUID — forwarded to GrowthStudioEmitter (required kwarg).
            user_id: Actor user UUID (optional).
            **props: Additional event properties passed as the `props` dict.
        """
        try:
            await self._telemetry.emit_event(
                event_type=event_type,
                tenant_id=tenant_id,
                user_id=user_id,
                props=props,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("telemetry_emit_failed", event_type=event_type, error=str(exc))

    # ---------- GET identity ------------------------------------------------

    async def get_identity(self, *, tenant_id: UUID) -> BrandIdentityDTO:
        """Get current brand identity for tenant.

        Args:
            tenant_id: Tenant UUID.

        Returns:
            BrandIdentityDTO with current brand name, tagline, etc.
        """
        settings = await self._get_brand_settings(tenant_id)
        identity = settings.identity if settings and settings.identity else None

        return BrandIdentityDTO(
            tenant_id=tenant_id,
            name=identity.brand_name if identity and identity.brand_name else "",
            slug="",  # from tenant.subdomain — enriched at router layer
            tagline=identity.tagline if identity else None,
            clinic_vertical="",  # from clinic config — enriched at router layer
            primary_specialties=[],
            updated_at=None,
        )

    # ---------- PATCH identity ----------------------------------------------

    async def patch_identity(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        patch: BrandIdentityPatchDTO,
    ) -> BrandIdentityDTO:
        """Partial update of brand identity fields.

        Audit log sync write action='brand_identity_updated' pre-return.

        Args:
            tenant_id: Tenant UUID.
            user_id: User UUID performing the update.
            patch: BrandIdentityPatchDTO with fields to update.

        Returns:
            Updated BrandIdentityDTO.
        """
        settings = await self._get_brand_settings(tenant_id)

        if settings.identity is None:
            from luana_core_brand_studio.domain.identity import BrandIdentity  # noqa: PLC0415

            settings.identity = BrandIdentity()

        patch_data = patch.model_dump(exclude_none=True)
        if "name" in patch_data:
            settings.identity.brand_name = patch_data["name"]
        if "tagline" in patch_data:
            settings.identity.tagline = patch_data["tagline"]

        await self._save_brand_settings(tenant_id, settings)

        # Audit log sync write BEFORE return
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="brand_identity_updated",
            resource_type="brand_identity",
            resource_id=tenant_id,
            payload={
                "fields_updated": list(patch_data.keys()),
                "has_name": "name" in patch_data,
                "has_tagline": "tagline" in patch_data,
            },
        )

        await self._emit_telemetry(
            "lisa_marca_identity_saved",
            tenant_id=tenant_id,
            user_id=user_id,
            field_count_changed=len(patch_data),
        )

        logger.info(
            "brand_identity_updated",
            tenant_id=str(tenant_id),
            fields=list(patch_data.keys()),
        )

        return BrandIdentityDTO(
            tenant_id=tenant_id,
            name=settings.identity.brand_name or "",
            slug="",
            tagline=settings.identity.tagline,
            clinic_vertical="",
            primary_specialties=[],
            updated_at=datetime.now(timezone.utc),
        )

    # ---------- GET visuals -------------------------------------------------

    @staticmethod
    def _coerce_visuals(visuals_raw: Any) -> Any:
        """Normaliza `identity.visuals` a un BrandVisuals para acceso por atributo.

        El engine `BrandIdentity` NO declara `visuals` (atributo dinámico). El brand
        repo lo PERSISTE y lo RECARGA como **dict** (JSON) → acceder `.primary_color`
        en un dict da AttributeError 500. Acá unificamos: None → None; dict →
        BrandVisuals(**dict); objeto → tal cual. Origen: estabilizar-harness-e2e
        (el fix del PATCH visuals destapó el dict-reload).
        """
        if visuals_raw is None:
            return None
        if isinstance(visuals_raw, dict):
            from luana_core_brand_studio.domain.identity import BrandVisuals  # noqa: PLC0415

            return BrandVisuals(**visuals_raw)
        return visuals_raw

    async def get_visuals(self, *, tenant_id: UUID) -> BrandVisualsDTO:
        """Get brand visuals for tenant.

        Args:
            tenant_id: Tenant UUID.

        Returns:
            BrandVisualsDTO with colors, fonts, logo_url.
        """
        settings = await self._get_brand_settings(tenant_id)
        # El modelo de dominio del engine `BrandIdentity` NO declara `visuals`
        # (atributo dinámico que puede faltar, o venir como dict tras recargar).
        # getattr defensivo + coerción dict→BrandVisuals → nunca 500.
        identity = settings.identity if settings else None
        visuals = self._coerce_visuals(getattr(identity, "visuals", None)) if identity else None

        return BrandVisualsDTO(
            tenant_id=tenant_id,
            primary_color=visuals.primary_color if visuals else None,
            accent_color=visuals.accent_color if visuals else None,
            background_color=visuals.background_color if visuals else None,
            text_primary_color=visuals.text_primary_color if visuals else None,
            font_heading=visuals.font_heading if visuals else None,
            font_body=visuals.font_body if visuals else None,
            logo_url=visuals.logo_url if visuals else None,
            updated_at=None,
        )

    # ---------- PATCH visuals -----------------------------------------------

    async def patch_visuals(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        patch: BrandVisualsPatchDTO,
    ) -> BrandVisualsDTO:
        """Partial update of brand visuals (colors + fonts).

        Audit log sync write action='brand_visuals_updated' pre-return.

        Args:
            tenant_id: Tenant UUID.
            user_id: User UUID performing the update.
            patch: BrandVisualsPatchDTO with fields to update.

        Returns:
            Updated BrandVisualsDTO.
        """
        settings = await self._get_brand_settings(tenant_id)

        if settings.identity is None:
            from luana_core_brand_studio.domain.identity import BrandIdentity  # noqa: PLC0415

            settings.identity = BrandIdentity()

        # Normaliza: el atributo puede faltar, ser None, o venir como dict tras
        # recargar. Coerción → BrandVisuals para poder hacer setattr de los campos.
        existing_visuals = self._coerce_visuals(getattr(settings.identity, "visuals", None))
        if existing_visuals is None:
            from luana_core_brand_studio.domain.identity import BrandVisuals  # noqa: PLC0415

            existing_visuals = BrandVisuals()
        settings.identity.visuals = existing_visuals

        patch_data = patch.model_dump(exclude_none=True)
        for field_name, value in patch_data.items():
            setattr(settings.identity.visuals, field_name, value)

        await self._save_brand_settings(tenant_id, settings)

        # Audit log sync write BEFORE return
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="brand_visuals_updated",
            resource_type="brand_visuals",
            resource_id=tenant_id,
            payload={
                "fields_updated": list(patch_data.keys()),
                "has_color_changes": any("color" in f for f in patch_data),
                "has_font_changes": any("font" in f for f in patch_data),
            },
        )

        await self._emit_telemetry(
            "lisa_marca_visuals_saved",
            tenant_id=tenant_id,
            user_id=user_id,
            field_count_changed=len(patch_data),
            has_logo=bool(settings.identity.visuals.logo_url),
        )

        logger.info(
            "brand_visuals_updated",
            tenant_id=str(tenant_id),
            fields=list(patch_data.keys()),
        )

        return BrandVisualsDTO(
            tenant_id=tenant_id,
            primary_color=settings.identity.visuals.primary_color,
            accent_color=settings.identity.visuals.accent_color,
            background_color=settings.identity.visuals.background_color,
            text_primary_color=settings.identity.visuals.text_primary_color,
            font_heading=settings.identity.visuals.font_heading,
            font_body=settings.identity.visuals.font_body,
            logo_url=settings.identity.visuals.logo_url,
            updated_at=datetime.now(timezone.utc),
        )

    # ---------- GET personality ---------------------------------------------

    async def get_personality(self, *, tenant_id: UUID) -> BrandPersonalityDTO:
        """Get brand personality (compiler v2 6 blocks) for tenant.

        Args:
            tenant_id: Tenant UUID.

        Returns:
            BrandPersonalityDTO with 6 compiler blocks + archetype.
        """
        profile = await self._get_personality_profile(tenant_id)

        if profile is None:
            # Return empty placeholder
            from uuid import uuid4  # noqa: PLC0415

            return BrandPersonalityDTO(
                tenant_id=tenant_id,
                personality_profile_id=uuid4(),
                archetype="caregiver",
                so_i_speak="",
                so_i_dont_speak="",
                technical_context="",
                format_instructions="",
                identity_anchor="",
                domain_context="",
                compiled_at=None,
                compiler_version=_COMPILER_VERSION,
            )

        # Map PersonalityProfileModel → DTO
        source_meta = profile.source_metadata or {}
        return BrandPersonalityDTO(
            tenant_id=tenant_id,
            personality_profile_id=profile.id,
            archetype=source_meta.get("archetype", "caregiver"),
            so_i_speak=source_meta.get("so_i_speak", ""),
            so_i_dont_speak=source_meta.get("so_i_dont_speak", ""),
            technical_context=source_meta.get("technical_context", ""),
            format_instructions=source_meta.get("format_instructions", ""),
            identity_anchor=source_meta.get("identity_anchor", ""),
            domain_context=source_meta.get("domain_context", ""),
            compiled_at=getattr(profile, "updated_at", None),
            compiler_version=_COMPILER_VERSION,
        )

    # ---------- PATCH personality -------------------------------------------

    async def patch_personality(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        patch: BrandPersonalityPatchDTO,
    ) -> BrandPersonalityDTO:
        """Partial update of personality compiler v2 blocks.

        Also invalidates voice_preview cache for this tenant.
        Audit log sync write action='brand_personality_updated' pre-return.

        Args:
            tenant_id: Tenant UUID.
            user_id: User UUID performing the update.
            patch: BrandPersonalityPatchDTO with blocks to update.

        Returns:
            Updated BrandPersonalityDTO.
        """
        profile = await self._get_personality_profile(tenant_id)
        patch_data = patch.model_dump(exclude_none=True)

        if profile is not None:
            # Update source_metadata with patched fields
            meta: dict[str, Any] = dict(profile.source_metadata or {})
            meta.update(patch_data)

            # Update personality model via run_sync
            async def _save_meta() -> None:
                from luana_core_brand_studio.infrastructure.models.personality_model import (  # noqa: PLC0415
                    PersonalityProfileModel,
                )
                from sqlalchemy import update as sa_update  # noqa: PLC0415

                stmt = (
                    sa_update(PersonalityProfileModel)
                    .where(
                        PersonalityProfileModel.id == profile.id,
                        PersonalityProfileModel.tenant_id == tenant_id,
                    )
                    .values(source_metadata=meta)
                )
                await self._session.execute(stmt)

            await _save_meta()

        # Invalidate voice preview cache
        try:
            await self._voice_preview.invalidate(tenant_id=tenant_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "voice_preview_cache_invalidate_failed",
                tenant_id=str(tenant_id),
                error=str(exc),
            )

        # Audit log sync write BEFORE return
        archetype = patch_data.get("archetype", "")
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="brand_personality_updated",
            resource_type="brand_personality",
            resource_id=tenant_id,
            payload={
                "fields_updated": list(patch_data.keys()),
                "archetype_changed": "archetype" in patch_data,
                "new_archetype": archetype,
                # NO verbatim text of voice blocks (sanitize_payload in audit_writer handles)
            },
        )

        await self._emit_telemetry(
            "lisa_marca_personality_saved",
            tenant_id=tenant_id,
            user_id=user_id,
            archetype=archetype or "unchanged",
            voice_warning_triggered=False,
        )

        logger.info(
            "brand_personality_updated",
            tenant_id=str(tenant_id),
            fields=list(patch_data.keys()),
        )

        # Reload after save
        return await self.get_personality(tenant_id=tenant_id)

    # ---------- GET contact -------------------------------------------------

    async def get_contact(self, *, tenant_id: UUID) -> BrandContactDTO:
        """Get brand contact and social media for tenant.

        Args:
            tenant_id: Tenant UUID.

        Returns:
            BrandContactDTO with social links and URLs.
        """
        settings = await self._get_brand_settings(tenant_id)
        contact = settings.team.contact if settings and settings.team and settings.team.contact else None  # type: ignore[union-attr]

        return BrandContactDTO(
            tenant_id=tenant_id,
            public_landing_url=None,  # enriched at router layer from tenant.subdomain
            website_url=None,
            instagram_handle=contact.social_instagram if contact else None,
            tiktok_handle=contact.social_tiktok if contact else None,
            facebook_page=contact.social_facebook if contact else None,
            google_business_url=None,
            updated_at=None,
        )

    # ---------- PATCH contact -----------------------------------------------

    async def patch_contact(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        patch: BrandContactPatchDTO,
    ) -> BrandContactDTO:
        """Partial update of brand contact.

        Audit log sync write action='brand_contact_updated' pre-return.

        Args:
            tenant_id: Tenant UUID.
            user_id: User UUID performing the update.
            patch: BrandContactPatchDTO with fields to update.

        Returns:
            Updated BrandContactDTO.
        """
        settings = await self._get_brand_settings(tenant_id)
        patch_data = patch.model_dump(exclude_none=True)

        # Store in source_metadata of settings (contact-like struct)
        if settings.team is None:
            # Initialize team wrapper if missing
            from luana_core_brand_studio.domain.team import BrandTeamWrapper  # noqa: PLC0415

            settings.team = BrandTeamWrapper()

        if settings.team.contact is None:
            from luana_core_brand_studio.domain.team import BrandContact  # noqa: PLC0415

            settings.team.contact = BrandContact()

        contact = settings.team.contact
        if "instagram_handle" in patch_data:
            contact.social_instagram = patch_data["instagram_handle"]
        if "tiktok_handle" in patch_data:
            contact.social_tiktok = patch_data["tiktok_handle"]
        if "facebook_page" in patch_data:
            contact.social_facebook = patch_data["facebook_page"]

        await self._save_brand_settings(tenant_id, settings)

        # Audit log sync write BEFORE return
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="brand_contact_updated",
            resource_type="brand_contact",
            resource_id=tenant_id,
            payload={
                "fields_updated": list(patch_data.keys()),
            },
        )

        await self._emit_telemetry(
            "lisa_marca_contact_saved",
            tenant_id=tenant_id,
            user_id=user_id,
            field_count_changed=len(patch_data),
        )

        logger.info(
            "brand_contact_updated",
            tenant_id=str(tenant_id),
            fields=list(patch_data.keys()),
        )

        return BrandContactDTO(
            tenant_id=tenant_id,
            public_landing_url=None,
            website_url=patch_data.get("website_url"),
            instagram_handle=contact.social_instagram,
            tiktok_handle=contact.social_tiktok,
            facebook_page=contact.social_facebook,
            google_business_url=patch_data.get("google_business_url"),
            updated_at=datetime.now(timezone.utc),
        )

    # ---------- GET team preview --------------------------------------------

    async def get_team_preview(
        self,
        *,
        tenant_id: UUID,
        limit: int = 3,
    ) -> BrandTeamPreviewDTO:
        """Get read-only top-N team preview.

        Args:
            tenant_id: Tenant UUID.
            limit: Max team members to return (default 3).

        Returns:
            BrandTeamPreviewDTO with top members.
        """
        settings = await self._get_brand_settings(tenant_id)
        key_leadership = []
        if settings and settings.team and settings.team.key_leadership:
            key_leadership = settings.team.key_leadership

        preview = key_leadership[:limit]
        members = [
            TeamMemberPreviewItemDTO(
                member_id=_stable_uuid(str(m.id), tenant_id),
                display_name=m.name,
                role=m.role,
                avatar_url=m.headshot_url,
            )
            for m in preview
        ]
        return BrandTeamPreviewDTO(
            tenant_id=tenant_id,
            total_count=len(key_leadership),
            preview_count=len(members),
            members=members,
        )

    # ---------- GET clinic config -------------------------------------------

    async def get_clinic_config(self, *, tenant_id: UUID) -> ClinicConfigDTO:
        """Get read-only clinic_vertical + primary_specialties.

        Args:
            tenant_id: Tenant UUID.

        Returns:
            ClinicConfigDTO (from tenant config captured at onboarding-clinica).
        """
        # Read from tenant.config_json
        from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: PLC0415
        from sqlalchemy import select  # noqa: PLC0415

        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self._session.execute(stmt)
        tenant = result.scalars().first()

        config = tenant.config_json if tenant else {}
        clinic_config_data = (config or {}).get("clinic_config", {})

        return ClinicConfigDTO(
            tenant_id=tenant_id,
            clinic_vertical=clinic_config_data.get("clinic_vertical", "general_clinic"),
            primary_specialties=clinic_config_data.get("primary_specialties", []),
        )

    # ---------- GET voice preview -------------------------------------------

    async def get_voice_preview(
        self,
        *,
        tenant_id: UUID,
    ) -> VoicePreviewDTO:
        """Get compiled voice preview (slot 5 BRAND_VOICE, deterministic).

        Args:
            tenant_id: Tenant UUID.

        Returns:
            VoicePreviewDTO with 2 samples (WhatsApp + email).
        """
        profile = await self._get_personality_profile(tenant_id)

        if profile is None:
            from uuid import uuid4  # noqa: PLC0415

            return VoicePreviewDTO(
                personality_profile_id=uuid4(),
                sample_whatsapp="Hola, ¿en qué puedo ayudarte hoy?",
                sample_email_reactivation="Hola,\n\nQueríamos saber cómo te has sentido.",
                compiled_at=datetime.now(timezone.utc),
                compiler_version=_COMPILER_VERSION,
                cache_hit=False,
            )

        blocks = dict(profile.source_metadata or {})
        system_instruction = profile.system_instruction or ""

        whatsapp, email_sample, cache_hit = await self._voice_preview.get_preview(
            tenant_id=tenant_id,
            personality_profile_id=profile.id,
            system_instruction=system_instruction,
            blocks=blocks,
        )

        return VoicePreviewDTO(
            personality_profile_id=profile.id,
            sample_whatsapp=whatsapp,
            sample_email_reactivation=email_sample,
            compiled_at=datetime.now(timezone.utc),
            compiler_version=_COMPILER_VERSION,
            cache_hit=cache_hit,
        )

    # ---------- GET initial state -------------------------------------------

    async def get_initial_state(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        subsubtab: Literal["identidad", "voz-y-tono", "presencia"],
    ) -> MarcaInitialStateDTO:
        """SSR-friendly state hydration per subsubtab.

        Audit log row `read_marca_initial_state` (defense-in-depth).

        Args:
            tenant_id: Tenant UUID.
            user_id: User UUID requesting state.
            subsubtab: One of identidad / voz-y-tono / presencia.

        Returns:
            MarcaInitialStateDTO with relevant fields populated.
        """
        identity = None
        visuals = None
        personality = None
        contact = None
        team_preview = None
        clinic_config = None
        voice_preview = None
        prohibited_phrases = None
        trust_signals = None
        trust_catalog = None

        try:
            identity = await self.get_identity(tenant_id=tenant_id)
            visuals = await self.get_visuals(tenant_id=tenant_id)
            clinic_config = await self.get_clinic_config(tenant_id=tenant_id)

            if subsubtab == "identidad":
                team_preview = await self.get_team_preview(tenant_id=tenant_id, limit=3)

            elif subsubtab == "voz-y-tono":
                personality = await self.get_personality(tenant_id=tenant_id)
                voice_preview = await self.get_voice_preview(tenant_id=tenant_id)
                prohibited_phrases = await self._voice_blocklist.list_for_tenant(tenant_id=tenant_id, country="PE")

            elif subsubtab == "presencia":
                contact = await self.get_contact(tenant_id=tenant_id)
                trust_signals_domain = await self._trust_signal_repo.list_for_tenant(tenant_id=tenant_id)
                trust_signals = [
                    TrustSignalDTO(
                        id=s.id,
                        label=s.label,
                        catalog_code=s.catalog_code,
                        logo_url=s.logo_url,
                        issued_year=s.issued_year,
                        is_seed=s.is_seed,
                    )
                    for s in trust_signals_domain
                ]
                trust_catalog = await self._trust_catalog.get_catalog(country="PE")

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "initial_state_partial_load_error",
                tenant_id=str(tenant_id),
                subsubtab=subsubtab,
                error=str(exc),
            )

        # Audit log sync write (defense-in-depth for read)
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="read_marca_initial_state",
            resource_type="brand_identity",
            resource_id=tenant_id,
            payload={"subsubtab": subsubtab},
        )

        return MarcaInitialStateDTO(
            subsubtab=subsubtab,
            identity=identity,
            visuals=visuals,
            personality=personality,
            contact=contact,
            team_preview=team_preview,
            clinic_config=clinic_config,
            voice_preview=voice_preview,
            prohibited_phrases=prohibited_phrases,
            trust_signals=trust_signals,
            trust_catalog=trust_catalog,
        )

    async def get_trust_signals(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
    ) -> list[TrustSignalDTO]:
        """Return all active trust signals for a tenant.

        Args:
            tenant_id: Tenant UUID.
            user_id: Requesting user UUID (audit).

        Returns:
            List of TrustSignalDTO items.
        """
        signals = await self._trust_signal_repo.list_for_tenant(tenant_id=tenant_id)
        return [
            TrustSignalDTO(
                id=s.id,
                label=s.label,
                catalog_code=s.catalog_code,
                logo_url=s.logo_url,
                issued_year=s.issued_year,
                is_seed=s.is_seed,
            )
            for s in signals
        ]

    async def create_trust_signal(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        request: TrustSignalCreateRequestDTO,
    ) -> TrustSignalDTO:
        """Create a trust signal and write audit log.

        Args:
            tenant_id: Tenant UUID.
            user_id: Requesting user UUID.
            request: Trust signal create request DTO.

        Returns:
            TrustSignalDTO of the created signal.
        """
        from src.modules.vitalia.brand_studio.domain.trust_signal import TrustSignal  # noqa: PLC0415

        signal = TrustSignal(
            tenant_id=tenant_id,
            label=request.label,
            catalog_code=request.catalog_code,
            issued_year=request.issued_year,
        )
        saved = await self._trust_signal_repo.create(signal)

        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="trust_signal_created",
            resource_type="trust_signal",
            resource_id=saved.id,
            payload={"label": saved.label, "catalog_code": saved.catalog_code},
        )

        logger.info(
            "trust_signal_created",
            tenant_id=str(tenant_id),
            signal_id=str(saved.id),
            label=saved.label,
        )

        await self._emit_telemetry("lisa_marca_trust_signal_added", tenant_id=tenant_id, user_id=user_id)

        return TrustSignalDTO(
            id=saved.id,
            label=saved.label,
            catalog_code=saved.catalog_code,
            logo_url=saved.logo_url,
            issued_year=saved.issued_year,
            is_seed=saved.is_seed,
        )

    async def delete_trust_signal(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        signal_id: UUID,
    ) -> None:
        """Soft-delete a trust signal and write audit log.

        Args:
            tenant_id: Tenant UUID.
            user_id: Requesting user UUID.
            signal_id: Trust signal UUID to delete.
        """
        await self._trust_signal_repo.soft_delete(signal_id, tenant_id=tenant_id)

        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="trust_signal_deleted",
            resource_type="trust_signal",
            resource_id=signal_id,
            payload={"signal_id": str(signal_id)},
        )

        logger.info(
            "trust_signal_deleted",
            tenant_id=str(tenant_id),
            signal_id=str(signal_id),
        )

    async def upload_logo(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        content: bytes,
        ext: str,
        size_bytes: int,
    ) -> LogoUploadResponseDTO:
        """Store logo content and update brand visuals logo_url.

        Stores via brand settings JSONB. Returns logo metadata.
        Visual extraction pipeline is STUBBED (promotion proposal pending).

        Args:
            tenant_id: Tenant UUID.
            user_id: Requesting user UUID.
            content: Logo image bytes (validated by router ≤ 5MB).
            ext: File extension (png|jpg|jpeg|webp).
            size_bytes: Logo size in bytes.

        Returns:
            LogoUploadResponseDTO with generated logo_id and placeholder logo_url.
        """
        import io as _io  # noqa: PLC0415
        import uuid as _uuid  # noqa: PLC0415

        from luana_core_assets.infrastructure.storage import get_storage_strategy  # noqa: PLC0415

        # Real storage via the engine StorageStrategy (R2 in staging/prod, Local in dev).
        # We consume the storage layer DIRECTLY (not AssetsService): a brand logo is
        # referenced by visuals.logo_url and does NOT need the assets-catalog DB entity
        # (AssetsService.upload_asset builds an Asset row whose FK assets.offer_id ->
        # products.id requires the `assets`+`products` tables that vitalia never migrates
        # -> NoReferencedTableError 500). The storage layer has no DB dependency. The
        # previous stub discarded the bytes (`logo:{uuid}`); now the bytes are persisted
        # to object storage and a real public URL is returned + saved.
        logo_id = _uuid.uuid4()
        storage = get_storage_strategy()
        storage_path, logo_url = storage.save(
            _io.BytesIO(content),
            f"logo-{logo_id}.{ext}",
            f"{tenant_id}/logo",
        )

        # Persist the real public URL to settings.identity.visuals (MISMO lugar que
        # patch_visuals + get_visuals: visuals viven anidados bajo identity). El stub
        # viejo escribía settings.visuals top-level, que NO es donde get_visuals lee →
        # el logo subía pero no aparecía al recargar (bug cazado por el demo de Chris).
        settings = await self._get_brand_settings(tenant_id)
        if settings is not None and settings.identity is not None:
            existing_visuals = self._coerce_visuals(getattr(settings.identity, "visuals", None))
            if existing_visuals is None:
                from luana_core_brand_studio.domain.identity import BrandVisuals  # noqa: PLC0415

                existing_visuals = BrandVisuals()
            settings.identity.visuals = existing_visuals
            settings.identity.visuals.logo_url = logo_url
            await self._save_brand_settings(tenant_id, settings)

        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="brand_logo_uploaded",
            resource_type="brand_visuals",
            resource_id=tenant_id,
            payload={
                "logo_id": str(logo_id),
                "ext": ext,
                "size_bytes": size_bytes,
                "storage_path": storage_path,
            },
        )

        await self._emit_telemetry("lisa_marca_logo_uploaded", tenant_id=tenant_id, user_id=user_id)

        literal_ext = ext
        from typing import get_args  # noqa: PLC0415

        allowed_exts = get_args(LogoUploadResponseDTO.model_fields["format"].annotation)
        if literal_ext not in allowed_exts:
            literal_ext = "jpg"

        return LogoUploadResponseDTO(
            logo_id=logo_id,
            logo_url=logo_url,
            size_bytes=size_bytes,
            format=literal_ext,  # type: ignore[arg-type]
        )

    async def delete_logo(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        """Remove the brand logo (soft delete — unset visuals.logo_url + storage cleanup).

        Una marca tiene UN solo logo → no se necesita logo_id; se desreferencia el campo
        visuals.logo_url y se borra el objeto del storage por tenant.

        Args:
            tenant_id: Tenant UUID.
            user_id: Requesting user UUID (audit actor).
        """
        settings = await self._get_brand_settings(tenant_id)
        old_url: str | None = None
        identity = getattr(settings, "identity", None) if settings is not None else None
        if identity is not None:
            existing_visuals = self._coerce_visuals(getattr(identity, "visuals", None))
            if existing_visuals is not None:
                old_url = existing_visuals.logo_url
                existing_visuals.logo_url = None
                identity.visuals = existing_visuals
                await self._save_brand_settings(tenant_id, settings)

        # Best-effort object-storage cleanup via the engine StorageStrategy (no DB).
        # Must not block the field unset nor the HIPAA audit write. Derive the storage
        # key from the stored public URL (strip the configured public base).
        if old_url:
            from luana_core_assets.infrastructure.storage import get_storage_strategy  # noqa: PLC0415
            from luana_core_platform.core.config import settings as _cfg  # noqa: PLC0415

            try:
                public_base = (_cfg.R2_PUBLIC_URL or "").rstrip("/")
                key = old_url[len(public_base) + 1 :] if public_base and old_url.startswith(public_base) else old_url
                get_storage_strategy().delete(key)
            except Exception as exc:  # noqa: BLE001 — storage cleanup is best-effort
                logger.warning("brand_logo_storage_delete_failed", tenant_id=str(tenant_id), error=str(exc))

        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=_NULL_CLINIC_ID,
            user_id=user_id,
            action="brand_logo_deleted",
            resource_type="brand_visuals",
            resource_id=tenant_id,
            payload={"logo_url_removed": old_url},
        )

        logger.info(
            "brand_logo_deleted",
            tenant_id=str(tenant_id),
            had_logo=old_url is not None,
        )


def _stable_uuid(key: str, tenant_id: UUID) -> UUID:
    """Generate stable UUID from string key + tenant_id (for team preview)."""
    import hashlib  # noqa: PLC0415

    return UUID(hashlib.md5(f"{tenant_id}:{key}".encode()).hexdigest())  # noqa: S324
