// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * useVoicePreview.ts — React Query hook for BRAND_VOICE slot preview.
 *
 * Fetches GET /lisa/marca/voice-preview?blocks_hash={hash} from BE.
 * Triggers refetch when blocksHash changes (autosave 600ms debounce chain).
 * OQ-C: preview is server-side compiled (LRU cache per tenant+profile+blocks_hash).
 *
 * NOT a client-side compile — just fetches the BE-compiled preview.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A4 + 04-validators.yaml fe_test_voice_preview_footer
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { marcaKeys } from "../api/marca";
import { getVoicePreview } from "../api/marca-voice-api";
import type { VoicePreviewResponse } from "../api/marca-voice-api";

interface UseVoicePreviewOptions {
  tenantId: string;
  personalityProfileId: string;
  /** Hash of current voice blocks — changes trigger refetch. */
  blocksHash: string;
  /** Disable query if parent is loading / no profile yet. */
  enabled?: boolean;
}

export interface UseVoicePreviewReturn {
  preview: VoicePreviewResponse | undefined;
  isLoading: boolean;
  isFetching: boolean;
  isError: boolean;
}

export function useVoicePreview({
  tenantId,
  personalityProfileId,
  blocksHash,
  enabled = true,
}: UseVoicePreviewOptions): UseVoicePreviewReturn {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  const { data, isLoading, isFetching, isError } = useQuery({
    queryKey: marcaKeys.voicePreview(tenantId, blocksHash),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return getVoicePreview({ token, tenantId }, blocksHash);
    },
    enabled: isLoaded && !!isSignedIn && !!personalityProfileId && enabled,
    staleTime: 30_000,
  });

  return {
    preview: data,
    isLoading,
    isFetching,
    isError,
  };
}
