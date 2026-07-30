// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * VozTonoView.tsx — Client root for Voz y tono sub-sub-tab.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * "use client" root per ADR § 3. Props hydrated from Server Component page.tsx.
 *
 * Composition (in render order):
 *   1. ArchetypeSelector         — 4 salud archetypes (OQ-B)
 *   2. VoiceCompilerBlocks       — 6 blocks compiler v2
 *   3. TreatmentLanguageCard     — tratamiento + idioma
 *   4. BrandVoicePreview         — OQ-E: SINGLE footer instance
 *
 * Data layer:
 *   - useQuery personality       — GET /lisa/marca/personality
 *   - useQuery prohibitedPhrases — GET /lisa/marca/prohibited-phrases
 *   - usePersonalityAutosave     — PUT /lisa/marca/personality (debounce 600ms)
 *   - debounceHash               — hashVoiceBlocks() → triggers BrandVoicePreview refresh
 *
 * HIPAA-lite: fetchClient auto-injects X-Tenant-ID + X-Clinic-ID.
 * PHI never in URL/searchParams. All mutations via PUT body.
 *
 * Anti-creep: NO health_voice_validator. VoiceTextareaWithWarning is soft warning only.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 + 03-arch.md § 6 + ADR-vitalia-004 § 3
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useCallback, useMemo, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { marcaKeys } from "../../../api/marca";
import { getPersonality, getProhibitedPhrases } from "../../../api/marca-voice-api";
import { usePersonalityAutosave } from "../../../hooks/usePersonalityAutosave";
import { hashVoiceBlocks } from "../../../utils/marca/prohibitedPhraseDetector";
import { FloatingAutosaveIndicator } from "@/components/shared/FloatingAutosaveIndicator";
import { ArchetypeSelector } from "./ArchetypeSelector";
import { VoiceCompilerBlocks } from "./VoiceCompilerBlocks";
import { TreatmentLanguageCard } from "./TreatmentLanguageCard";
import { BrandVoicePreview } from "./BrandVoicePreview";
import type { SaludArchetype } from "../../../types/marca/personality-schema";
import type { VoiceBlocksFormValues } from "../../../types/marca/personality-schema";
import type { TreatmentLanguageValues } from "./TreatmentLanguageCard";

export interface VozTonoViewProps {
  /** Clerk org ID — used for X-Tenant-ID and React Query keys. */
  tenantId: string;
  /**
   * Clinic ID for HIPAA-lite dual filter.
   * Passed from page.tsx Server Component.
   */
  clinicId?: string | null;
  className?: string;
}

// ── VozTonoView ───────────────────────────────────────────────────────────────

export function VozTonoView({ tenantId, clinicId, className }: VozTonoViewProps) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  // Clerk `getToken()` puede devolver null por un breve instante tras isSignedIn
  // (token aún resolviéndose). En vez de tirar "Not authenticated" y dejar la
  // pantalla en error permanente, esperamos hasta ~2s a que el token esté listo.
  const getTokenReady = useCallback(async (): Promise<string> => {
    for (let attempt = 0; attempt < 10; attempt += 1) {
      const token = await getToken();
      if (token) return token;
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
    throw new Error("Not authenticated");
  }, [getToken]);

  // ── React Query: fetch personality profile ──────────────────────────────
  const {
    data: personality,
    isLoading: isPersonalityLoading,
    isError: isPersonalityError,
  } = useQuery({
    queryKey: marcaKeys.personality(tenantId),
    queryFn: async () => {
      const token = await getTokenReady();
      return getPersonality({ token, tenantId, clinicId });
    },
    enabled: isLoaded && !!isSignedIn,
    retry: 5,
    retryDelay: (attempt) => Math.min(300 * 2 ** attempt, 2000),
  });

  // ── React Query: fetch prohibited phrases ───────────────────────────────
  const { data: phrasesData } = useQuery({
    queryKey: marcaKeys.prohibitedPhrases(tenantId),
    queryFn: async () => {
      const token = await getTokenReady();
      return getProhibitedPhrases({ token, tenantId, clinicId });
    },
    enabled: isLoaded && !!isSignedIn,
    staleTime: 5 * 60_000,
    retry: 5,
    retryDelay: (attempt) => Math.min(300 * 2 ** attempt, 2000),
  });

  const prohibitedPhrases = phrasesData?.items ?? [];

  // ── Local form state (controlled, autosaved) ────────────────────────────
  const [archetype, setArchetype] = useState<SaludArchetype | null>(null);
  const [voiceBlocks, setVoiceBlocks] = useState<VoiceBlocksFormValues>({});
  const [treatmentLanguage, setTreatmentLanguage] = useState<TreatmentLanguageValues>({
    treatment: "tuteo",
    language: "es_neutro",
  });

  // Hydrate local state once from server data (idempotent — only on first load)
  const [hydrated, setHydrated] = useState(false);
  if (personality && !hydrated) {
    setArchetype(personality.archetype);
    setVoiceBlocks({
      identity: personality.identityAnchor,
      context: personality.domainContext,
      asi_hablo: personality.soISpeak,
      asi_no_hablo: personality.soIDontSpeak,
      tech_context: personality.technicalContext,
      format: personality.formatInstructions,
    });
    setHydrated(true);
  }

  // ── Autosave hook ────────────────────────────────────────────────────────
  const { autosaveStatus, savedAt, scheduleAutosave } = usePersonalityAutosave({
    tenantId,
    clinicId,
  });

  // ── Debounce hash for BrandVoicePreview (OQ-C) ──────────────────────────
  const debounceHash = useMemo(
    () =>
      hashVoiceBlocks({
        identity: voiceBlocks.identity,
        context: voiceBlocks.context,
        asi_hablo: voiceBlocks.asi_hablo,
        asi_no_hablo: voiceBlocks.asi_no_hablo,
        tech_context: voiceBlocks.tech_context,
        format: voiceBlocks.format,
      }),
    [voiceBlocks],
  );

  // ── Event handlers ───────────────────────────────────────────────────────
  const handleArchetypeSelect = useCallback(
    (value: SaludArchetype) => {
      setArchetype(value);
      scheduleAutosave({ archetype: value });
    },
    [scheduleAutosave],
  );

  const handleVoiceBlockChange = useCallback(
    (field: keyof VoiceBlocksFormValues, value: string) => {
      setVoiceBlocks((prev) => {
        const next = { ...prev, [field]: value };
        // Map block field names to API payload
        const apiFieldMap: Record<keyof VoiceBlocksFormValues, keyof import("../../../api/marca-voice-api").PersonalityPatchPayload> = {
          identity: "identityAnchor",
          context: "domainContext",
          asi_hablo: "soISpeak",
          asi_no_hablo: "soIDontSpeak",
          tech_context: "technicalContext",
          format: "formatInstructions",
        };
        scheduleAutosave({ [apiFieldMap[field]]: value });
        return next;
      });
    },
    [scheduleAutosave],
  );

  const handleTreatmentLanguageChange = useCallback(
    (values: TreatmentLanguageValues) => {
      setTreatmentLanguage(values);
      // Note: treatment/language map to BE fields; included in next autosave
    },
    [],
  );

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div
      data-testid="voz-tono-section-root"
      className={cn("flex flex-col gap-6 p-6", className)}
    >
      {/* 1. ArchetypeSelector — shows per-section skeleton while loading */}
      {isPersonalityError ? (
        <div role="alert">
          <p className="text-sm text-destructive">
            No se pudo cargar la configuración de voz. Intenta de nuevo.
          </p>
        </div>
      ) : (
        <ArchetypeSelector
          selected={archetype}
          onSelect={handleArchetypeSelect}
          isLoading={isPersonalityLoading}
          recommendedArchetype="caregiver"
        />
      )}

      {/* 2. VoiceCompilerBlocks */}
      <VoiceCompilerBlocks
        values={voiceBlocks}
        onChange={handleVoiceBlockChange}
        prohibitedPhrases={prohibitedPhrases}
      />

      {/* 3. TreatmentLanguageCard */}
      <TreatmentLanguageCard
        values={treatmentLanguage}
        onChange={handleTreatmentLanguageChange}
      />

      {/* 4. BrandVoicePreview — OQ-E: SINGLE instance (footer) */}
      <BrandVoicePreview
        tenantId={tenantId}
        personalityProfileId={personality?.personalityProfileId ?? ""}
        debounceHash={debounceHash}
        isLoading={autosaveStatus === "saving"}
      />

      <FloatingAutosaveIndicator status={autosaveStatus} savedAt={savedAt} />
    </div>
  );
}

VozTonoView.displayName = "VozTonoView";
