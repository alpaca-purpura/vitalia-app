// cap: shell-organism.shell-vitalia
// story-origin: TBD
// Components — T-fe-5 dashboard Client Components
export { TreatmentFollowupDashboardClient } from "./components/treatment-followup-dashboard-client";
export type {
  TreatmentFollowupDashboardClientProps,
  TreatmentDashboardStatus,
} from "./components/treatment-followup-dashboard-client";
export { TreatmentListTable } from "./components/treatment-list-table";
export type { TreatmentListTableProps } from "./components/treatment-list-table";
export { PatientListTable } from "./components/patient-list-table";
export type { PatientListTableProps } from "./components/patient-list-table";
export { PatientDetailPanel } from "./components/patient-detail-panel";
export type { PatientDetailPanelProps } from "./components/patient-detail-panel";
export { PatientMedicalPdfUpload } from "./components/patient-medical-pdf-upload";
export type { PatientMedicalPdfUploadProps } from "./components/patient-medical-pdf-upload";
export { AppointmentsCalendarClient } from "./components/appointments-calendar-client";
export type { AppointmentsCalendarClientProps } from "./components/appointments-calendar-client";
export {
  CompliancePageClient,
  generateCsvBlob,
} from "./components/compliance-page-client";
export type { CompliancePageClientProps } from "./components/compliance-page-client";
export {
  ComplianceEventRow,
  getSeverityBadgeVariant,
} from "./components/compliance-event-row";
export type {
  ComplianceEventRowProps,
  SeverityBadgeVariant,
} from "./components/compliance-event-row";

// Components — T-fe-4 interactive Client Components
export { OnboardingStep1Client } from "./components/onboarding-step-1-client";
export type { OnboardingStep1ClientProps } from "./components/onboarding-step-1-client";
export { OnboardingStep2Client } from "./components/onboarding-step-2-client";
export type { OnboardingStep2ClientProps } from "./components/onboarding-step-2-client";
export { OnboardingStep3Client } from "./components/onboarding-step-3-client";
export type { OnboardingStep3ClientProps } from "./components/onboarding-step-3-client";

// Components — T-fe-3 base components
export { ClinicTypePicker } from "./components/clinic-type-picker";
export type { ClinicTypePickerProps } from "./components/clinic-type-picker";
export { TreatmentTimeline } from "./components/treatment-timeline";
export type {
  TreatmentTimelineProps,
  TreatmentMilestone,
  MilestoneName,
} from "./components/treatment-timeline";
export { ConsentSignatureModal } from "./components/consent-signature-modal";
export type { ConsentSignatureModalProps } from "./components/consent-signature-modal";
export { ComplianceStatsCards } from "./components/compliance-stats-cards";
export type { ComplianceStatsCardsProps } from "./components/compliance-stats-cards";
export { DoctorAvatarPicker } from "./components/doctor-avatar-picker";
export type {
  DoctorAvatarPickerProps,
  DoctorOption,
} from "./components/doctor-avatar-picker";
export { MedicalDisclaimerBanner } from "./components/medical-disclaimer-banner";
export type {
  MedicalDisclaimerBannerProps,
  DisclaimerContext,
} from "./components/medical-disclaimer-banner";

// Microcopy SSoT
export {
  MICROCOPY_ONBOARDING,
  MICROCOPY_BRAND_STUDIO,
  MICROCOPY_OFFER_WIZARD,
  MICROCOPY_BOOKING,
  MICROCOPY_TREATMENT,
  MICROCOPY_COMPLIANCE,
  MICROCOPY_DISCLAIMER,
} from "./config/microcopy";

// Types
export type {
  ClinicType,
  Country,
  PlanTierSlug,
  CreateClinicProfileResponse,
  OnboardingStatusResponse,
  SubscribeResponse,
  OfferPresetResponse,
} from "./types/vitalia.types";
export type {
  PlanTierItem,
  PlanTierListResponse,
} from "./types/plan-tier.types";
export type {
  BookingStatus,
  PaymentStatus,
  DeliveryChannel,
  CreateBookingRequest,
  CreateBookingResponse,
  BookingSummary,
  BookingListResponse,
  RescheduleBookingRequest,
  RescheduleBookingResponse,
  CancelBookingRequest,
  CancelBookingResponse,
  ConsentSignRequest,
  ConsentSignResponse,
  SlotItem,
  AvailableSlotsResponse,
} from "./types/booking.types";
export type {
  TreatmentSummary,
  TreatmentListResponse,
  TreatmentDetailResponse,
  TreatmentFollowupStateResponse,
  ManualHandoffRequest,
  ManualHandoffResponse,
  ReleaseHandoffResponse,
  StartFollowupRequest,
  PatientSummary,
  PatientListResponse,
  PatientDetailResponse,
  UploadMedicalPdfRequest,
  UploadMedicalPdfResponse,
} from "./types/treatment.types";
export type {
  ConsentRecordResponse,
  ConsentRecordListResponse,
} from "./types/consent.types";
export type {
  ComplianceSeverity,
  ActorType,
  ComplianceEventItem,
  ComplianceEventListResponse,
} from "./types/compliance.types";

// Schemas
export { clinicProfileSchema } from "./schemas/clinic-profile-schema";
export type { ClinicProfileInput } from "./schemas/clinic-profile-schema";
export { bookingCreateSchema } from "./schemas/booking-schema";
export type { BookingCreateInput } from "./schemas/booking-schema";
export { consentSignSchema } from "./schemas/consent-schema";
export type { ConsentSignInput } from "./schemas/consent-schema";
export { manualHandoffSchema } from "./schemas/handoff-schema";
export type { ManualHandoffInput } from "./schemas/handoff-schema";
export { complianceFilterSchema } from "./schemas/compliance-schema";
export type { ComplianceFilterInput } from "./schemas/compliance-schema";
export { medicalPdfUploadSchema } from "./schemas/patient-schema";
export type { MedicalPdfUploadInput } from "./schemas/patient-schema";
export { startFollowupSchema } from "./schemas/treatment-schema";
export type { StartFollowupInput } from "./schemas/treatment-schema";
export { rescheduleBookingSchema } from "./schemas/appointment-schema";
export type { RescheduleBookingInput } from "./schemas/appointment-schema";

// API hooks — T-fe-4 brand studio hooks
export { useBrandStudioSections } from "./api/use-brand-studio-sections";
export type {
  BrandStudioSection,
  BrandStudioSectionsResponse,
} from "./api/use-brand-studio-sections";
export { useBrandStudioSectionPatch } from "./api/use-brand-studio-section-patch";
export type { PatchBrandStudioSectionPayload } from "./api/use-brand-studio-section-patch";

// API hooks
export { vitaliaQueryKeys } from "./api/query-keys";
export { useClinicProfileCreate } from "./api/use-clinic-profile-create";
export type { CreateClinicProfilePayload } from "./api/use-clinic-profile-create";
export { useOnboardingStatus } from "./api/use-onboarding-status";
export { usePlanTiers } from "./api/use-plan-tiers";
export { useBookingAvailability } from "./api/use-booking-availability";
export type { AvailableSlotsFilters } from "./api/use-booking-availability";
export { useBookingCreate } from "./api/use-booking-create";
export { useBookings } from "./api/use-bookings";
export { useBooking } from "./api/use-booking";
export { useBookingReschedule } from "./api/use-booking-reschedule";
export { useBookingCancel } from "./api/use-booking-cancel";
export { useTreatments } from "./api/use-treatments";
export { useTreatment } from "./api/use-treatment";
export { useTreatmentCreate } from "./api/use-treatment-create";
export type { TreatmentCreatePayload } from "./api/use-treatment-create";
export { useTreatmentFollowupStart } from "./api/use-treatment-followup-start";
export { useTreatmentSnapshot } from "./api/use-treatment-snapshot";
export { usePatients } from "./api/use-patients";
export { usePatient } from "./api/use-patient";
export { usePatientUploadPdf } from "./api/use-patient-upload-pdf";
export { useComplianceEvents } from "./api/use-compliance-events";
export type { ComplianceEventsFilters } from "./api/use-compliance-events";
