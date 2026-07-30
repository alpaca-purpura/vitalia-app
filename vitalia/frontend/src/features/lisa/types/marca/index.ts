// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * lisa/types/marca/index.ts — Zod schemas barrel for Lisa Marca sub-tab.
 *
 * T-8 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 5
 * downstream-regression-na: brand-local vitalia FE barrel; no cross-brand consumers
 */

// ── IMPORT verbatim from nicolify (adapted to Zod) ────────────────────────────
export {
  identitySchema,
  type IdentityFormValues,
} from "./identity-schema";

export {
  contactSchema,
  type ContactFormValues,
} from "./contact-schema";

export {
  visualsSchema,
  clinicVisualsSchema,
  type VisualsFormValues,
  type ClinicVisualsFormValues,
} from "./visuals-schema";

export {
  teamMemberItemSchema,
  type TeamMemberFormValues,
} from "./team-schema";

export {
  testimonialItemSchema,
  type TestimonialItemFormValues,
} from "./testimonial-item-schema";

// ── ADAPT salud overlay (NEW vitalia-specific) ────────────────────────────────
export {
  SALUD_ARCHETYPES,
  saludArchetypeEnum,
  voiceBlocksSchema,
  personalitySchema,
  type SaludArchetype,
  type PersonalityFormValues,
  type VoiceBlocksFormValues,
} from "./personality-schema";

export {
  phraseSeverityEnum,
  prohibitedPhraseSchema,
  type PhraseSeverity,
  type ProhibitedPhraseFormValues,
} from "./prohibited-phrase-schema";

export {
  certificationEntrySchema,
  trustSignalsSchema,
  type CertificationEntry,
  type TrustSignalsFormValues,
} from "./trust-signals-schema";

export {
  locationEntrySchema,
  socialMediaSchema,
  presenceSchema,
  type LocationEntry,
  type PresenceFormValues,
  type SocialMediaFormValues,
} from "./presence-schema";

export {
  voicePreviewRequestSchema,
  voicePreviewResponseSchema,
  voicePreviewSchema,
  type VoicePreviewRequest,
  type VoicePreviewResponse,
  type VoicePreviewPayload,
} from "./voice-preview-schema";
