// cap: clinics.lisa.doctores
// story-origin: vitalia-fase1-s10-TBD | vitalia-fase2-lisa-doctores
/**
 * lisa/index.ts — Feature public API (FSD-Lite boundary matrix).
 * F1-S10 vitalia-fase1-empty-states
 * F2-S8 vitalia-fase2-lisa-doctores (T-FE-1)
 *
 * Exposes placeholder components + Staff directory components.
 * DoctoresPlaceholder removed from barrel (lisa.staff now shipped as static route).
 *
 * downstream-regression-na: brand-local FE barrel; no cross-brand consumers
 */

// ── Placeholder components (T-2 generic EmptyState wrappers) ──────────────────
// NOTE: DoctoresPlaceholder REMOVED — lisa.staff is now a shipped static route (SHIPPED_STATIC_SUBTABS).
export { MarcaPlaceholder } from "./components/placeholders/MarcaPlaceholder";
export { CompliancePlaceholder } from "./components/placeholders/CompliancePlaceholder";

// ── Special placeholders (T-3) ─────────────────────────────────────────────────
export { ServiciosPlaceholder } from "./components/placeholders/ServiciosPlaceholder";

// ── Identidad sub-sub-tab (T-5) ────────────────────────────────────────────────
export { IdentidadView } from "./components/marca/identidad/IdentidadView";
export type { IdentidadViewProps } from "./components/marca/identidad/IdentidadView";

// ── Shared components (T-5 / T-6 / T-7) ──────────────────────────────────────
export { AutosaveBadge } from "@/components/marca/shared/AutosaveBadge";
export type { AutosaveStatus, AutosaveBadgeProps } from "@/components/marca/shared/AutosaveBadge";

// ── Voz y tono sub-sub-tab (T-6) ──────────────────────────────────────────────
export { VozTonoView } from "./components/marca/voz-y-tono/VozTonoView";
export type { VozTonoViewProps } from "./components/marca/voz-y-tono/VozTonoView";

export { ArchetypeSelector } from "./components/marca/voz-y-tono/ArchetypeSelector";
export { BrandVoicePreview } from "./components/marca/voz-y-tono/BrandVoicePreview";
export { VoiceTextareaWithWarning } from "./components/marca/voz-y-tono/VoiceTextareaWithWarning";

// ── Presencia sub-sub-tab (T-7) ───────────────────────────────────────────────
export { PresenciaView } from "./components/marca/presencia/PresenciaView";
export type { PresenciaViewProps } from "./components/marca/presencia/PresenciaView";

// ── Staff directory (T-FE-1) ───────────────────────────────────────────────────
export { LisaStaffView } from "./components/staff/LisaStaffView";
export { StaffDirectoryView } from "./components/staff/StaffDirectoryView";
export { StaffCard } from "./components/staff/StaffCard";
export { StaffDirectoryHeader } from "./components/staff/StaffDirectoryHeader";
export { NuevoIntegranteModal } from "./components/staff/NuevoIntegranteModal";
export { StaffEmptyState } from "./components/staff/StaffEmptyState";
export { StaffErrorBanner } from "./components/staff/StaffErrorBanner";

// ── Staff workspace (T-FE-2) ────────────────────────────────────────────────────
export { StaffWorkspaceShell } from "./components/staff/workspace/StaffWorkspaceShell";
export { DoctorPerfilView } from "./components/staff/workspace/perfil/DoctorPerfilView";
export { BioRepoInputs } from "./components/staff/workspace/perfil/BioRepoInputs";
export { GeneratedBioSections } from "./components/staff/workspace/perfil/GeneratedBioSections";
export { DoctorServiciosView } from "./components/staff/workspace/servicios/DoctorServiciosView";
export { AvatarUploader } from "./components/staff/workspace/AvatarUploader";

// ── Staff pagina workspace (T-FE-pagina-publica) ───────────────────────────────
export { DoctorPaginaView } from "./components/staff/workspace/pagina/DoctorPaginaView";
export { StructuredProfileEditor } from "./components/staff/workspace/pagina/StructuredProfileEditor";
export { PhonePreview } from "./components/staff/workspace/pagina/PhonePreview";
export { PublicLinkBar } from "./components/staff/workspace/pagina/PublicLinkBar";

// ── Staff horarios workspace (T-FE-3 + T-FE-vista-mes) ─────────────────────────
export { DoctorHorariosView } from "./components/staff/workspace/horarios/DoctorHorariosView";
export { AvailabilityCalendar } from "./components/staff/workspace/horarios/AvailabilityCalendar";
export { BloquePopover } from "./components/staff/workspace/horarios/BloquePopover";
export type { BloquePopoverAnchor } from "./components/staff/workspace/horarios/BloquePopover";
export { MonthCalendar } from "./components/staff/workspace/horarios/MonthCalendar";
export type { MonthCalendarProps } from "./components/staff/workspace/horarios/MonthCalendar";

// ── Staff API + types (T-FE-1) ─────────────────────────────────────────────────
export { staffKeys, useStaffList, useCreateDoctor, mapDoctorCreateToPayload, useDoctor, usePatchDoctor, useGenerateBio, useAvatarUpload, useAvailabilityBlocks, useAvailabilityOccurrences, useCreateBlock, useUpdateBlock, useDeleteBlock } from "./api/staff";
export type { CreateBlockPayload, UpdateBlockPayload, DeleteBlockResponse } from "./api/staff";
// Staff pagina API (T-FE-pagina-publica)
export { useGenerateProfile, useSavePublicProfile, useTogglePublicVisible } from "./api/staff";
export type { SavePublicProfilePayload } from "./api/staff";
// Staff server-side fetch helpers (for Server Component pages)
export { getStaffInitialState, getDoctorInitialState } from "./api/staff-server";
export type { DoctorListItem, DoctorDetail, PaginatedDoctors, StaffFilters, AvailabilityBlock, AvailabilityOccurrence, BioPublic } from "./types/staff.types";
// Pagina types (T-FE-pagina-publica)
// Note: StructuredCertificacion + StructuredIdioma DELETED (F3 fix — wire is string[])
export type { DoctorPublicProfile, ProfileState, PublicDoctorPageData, StructuredFormacion, StructuredExperiencia } from "./types/staff.types";
export type { DoctorCreateFormValues } from "./types/staff-schema";

// ── Staff hooks + store (T-FE-1) ───────────────────────────────────────────────
export { useStaffFilters } from "./hooks/use-staff-filters";
export { useStaffUiStore } from "./store/staff-ui-store";

// ── Servicios molecules (T-5 lisa-servicios) ───────────────────────────────────
export { RungPicker, RUNG_LABELS } from "./components/servicios/RungPicker";
export type { OfferValueLevel } from "./components/servicios/RungPicker";
export { ModalidadPicker } from "./components/servicios/ModalidadPicker";
export type { Modalidad } from "./components/servicios/ModalidadPicker";
export { VariantsRepeater } from "./components/servicios/VariantsRepeater";
export type { ServiceVariant } from "./components/servicios/VariantsRepeater";
export { TestimonialsList } from "./components/servicios/TestimonialsList";
export type { Testimonial } from "./components/servicios/TestimonialsList";
export { FaqPairList } from "./components/servicios/FaqPairList";
export type { FaqPair } from "./components/servicios/FaqPairList";
export { ObjecionPairList } from "./components/servicios/ObjecionPairList";
export type { ObjecionPair } from "./components/servicios/ObjecionPairList";
export { TagInput } from "./components/servicios/TagInput";
export { FichaCompletenessChip } from "./components/servicios/FichaCompletenessChip";
export { ChipOrigen } from "./components/servicios/ChipOrigen";
export type { ServiceOrigen } from "./components/servicios/ChipOrigen";

// ── Servicios views (T-6 lisa-servicios) ───────────────────────────────────────
export { LisaServiciosView } from "./components/servicios/LisaServiciosView";
export type { LisaServiciosViewProps } from "./components/servicios/LisaServiciosView";
export { CatalogoView } from "./components/servicios/CatalogoView";
export { EscaleraView } from "./components/servicios/EscaleraView";
export { ServiceCard } from "./components/servicios/ServiceCard";
export { ServiciosDirectoryHeader } from "./components/servicios/ServiciosDirectoryHeader";
export { RungColumn } from "./components/servicios/RungColumn";
export { RUNG_META, RUNG_LABEL_ES, RUNG_ORDER, MODALITY_LABEL } from "./types/servicios-labels";
export type {
  ServiceListItem,
  ServiceListResponse,
  ServiciosView as ServiciosViewKind,
  ServiciosFilters,
} from "./types/servicios.types";

// Servicios server-side fetch helper (for Server Component pages)
export { getServiciosInitialState, getServicioDetail } from "./api/servicios-server";
export type { ServiciosInitialState } from "./api/servicios-server";

// ── Servicios workspace (T-7 lisa-servicios) ───────────────────────────────────
export { ServicioWorkspaceShell } from "./components/servicios/workspace/ServicioWorkspaceShell";
export type { ServicioWorkspaceShellProps } from "./components/servicios/workspace/ServicioWorkspaceShell";
export { ServiceStatusBar } from "./components/servicios/ServiceStatusBar";
export { BibliotecaPicker } from "./components/servicios/BibliotecaPicker";
export { EspecialistaLinkPicker } from "./components/servicios/EspecialistaLinkPicker";
export { KnowledgeSourcesPanel } from "./components/servicios/KnowledgeSourcesPanel";
export { FieldTooltip } from "./components/servicios/FieldTooltip";
export { ResumenView } from "./components/servicios/leaves/ResumenView";
export { ParaAdrianView } from "./components/servicios/leaves/ParaAdrianView";
export { EspecialistasView } from "./components/servicios/leaves/EspecialistasView";
export { PlanPagoView } from "./components/servicios/leaves/PlanPagoView";
export { PruebaSocialView } from "./components/servicios/leaves/PruebaSocialView";

// Workspace types
export type {
  ServiceDetail,
  SalesBrief,
  SpecialistLink,
  ServicePatchRequest,
  SalesBriefPatchRequest,
  ServiceCase,
  ServiceTestimonial,
  BibliotecaItem,
  BibliotecaSearchResponse,
  ServiceCreateCustomRequest,
  ServiceCreateFromTemplateRequest,
  KnowledgeExtractResponse,
  ExtractionPrefill,
} from "./types/servicios.types";

// ── API (T-5 / T-6 / T-7) ──────────────────────────────────────────────────────
export { marcaKeys } from "./api/marca";
export type { IdentityResponse, VisualsResponse, LogoUploadResponse } from "./api/marca";
export type {
  BrandContactResponse,
  TrustSignalItem,
  TrustSignalsResponse,
  TrustCatalogItem,
  TrustCatalogResponse,
  LocationItem,
  LocationsResponse,
} from "./api/marca-presence-api";
