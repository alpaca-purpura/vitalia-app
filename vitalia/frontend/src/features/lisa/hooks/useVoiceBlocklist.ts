// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * useVoiceBlocklist.ts — React Query hook for tenant prohibited phrases.
 *
 * Fetches GET /lisa/marca/prohibited-phrases.
 * Returns list of ProhibitedPhraseItem for client-side soft warning detection.
 *
 * Anti-creep (sales-agent-brand-voice.md):
 *   NOT a health_voice_validator. Just tenant phrase list for soft warning.
 *   detectProhibitedPhrases() does substring scan on the client — no LLM call.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A2 + 03-arch.md § 4.2
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { marcaKeys } from "../api/marca";
import { getProhibitedPhrases } from "../api/marca-voice-api";
import type { ProhibitedPhraseItem } from "../api/marca-voice-api";

interface UseVoiceBlocklistOptions {
  tenantId: string;
}

export interface UseVoiceBlocklistReturn {
  phrases: ProhibitedPhraseItem[];
  isLoading: boolean;
}

export function useVoiceBlocklist({
  tenantId,
}: UseVoiceBlocklistOptions): UseVoiceBlocklistReturn {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: marcaKeys.prohibitedPhrases(tenantId),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return getProhibitedPhrases({ token, tenantId });
    },
    enabled: isLoaded && !!isSignedIn,
    staleTime: 5 * 60_000, // 5 min — phrase list rarely changes
  });

  return {
    phrases: data?.items ?? [],
    isLoading,
  };
}
