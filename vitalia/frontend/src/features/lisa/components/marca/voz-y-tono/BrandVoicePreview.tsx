// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * BrandVoicePreview.tsx — OQ-E: Single footer preview of BRAND_VOICE slot.
 *
 * CRITICAL (OQ-E): Exactly ONE instance per VozTonoView (footer only).
 * CRITICAL (OQ-C): Calls BE endpoint GET /lisa/marca/voice-preview (NOT client-side compile).
 *
 * Renders:
 *   - "Preview compilado" heading
 *   - Valeria (purple) WhatsApp bubble
 *   - Camila (indigo) email reactivación bubble
 *   - BRAND_VOICE slot chip
 *   - "Regenerar" button (invalidates React Query cache)
 *
 * debounceHash: changes when voice blocks are saved → triggers React Query refetch.
 * data-hash attribute on root section for tracking in tests (A4).
 *
 * Loading: skeleton with aria-label="Cargando preview de voz".
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A3 + A4 + 04-validators.yaml fe_test_voice_preview_footer
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useAuth } from "@clerk/nextjs";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { marcaKeys } from "../../../api/marca";
import { getVoicePreview } from "../../../api/marca-voice-api";

// ── BrandVoicePreview ─────────────────────────────────────────────────────────

export interface BrandVoicePreviewProps {
  tenantId: string;
  personalityProfileId: string;
  /** Hash of current voice blocks — changes when blocks are autosaved (OQ-C). */
  debounceHash: string;
  /** If true, shows skeleton (blocks are being saved — preview stale). */
  isLoading: boolean;
  className?: string;
}

export function BrandVoicePreview({
  tenantId,
  personalityProfileId,
  debounceHash,
  isLoading,
  className,
}: BrandVoicePreviewProps) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const queryClient = useQueryClient();

  const queryKey = marcaKeys.voicePreview(tenantId, debounceHash);

  const { data, isFetching, isError } = useQuery({
    queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return getVoicePreview({ token, tenantId }, debounceHash);
    },
    enabled: isLoaded && isSignedIn && !!personalityProfileId && !isLoading,
    staleTime: 30_000,
  });

  function handleRegenerate() {
    void queryClient.invalidateQueries({ queryKey });
  }

  // Show loading skeleton when parent signals blocks are being saved
  if (isLoading) {
    return (
      <section
        data-testid="brand-voice-preview"
        data-hash={debounceHash}
        aria-label="Cargando preview de voz"
        aria-busy="true"
        className={cn("flex flex-col gap-3 rounded-lg border border-border/50 bg-accent/20 p-4", className)}
      >
        <Skeleton className="h-4 w-[140px]" />
        <div className="flex flex-col gap-3">
          <Skeleton className="h-[80px] rounded-lg" />
          <Skeleton className="h-[80px] rounded-lg" />
        </div>
      </section>
    );
  }

  return (
    <section
      data-testid="brand-voice-preview"
      data-hash={debounceHash}
      aria-label="Preview compilado de voz de marca"
      className={cn("flex flex-col gap-3 rounded-lg border border-border/50 bg-accent/20 p-4", className)}
    >
      {/* Header — always rendered */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground">Preview compilado</span>
          <Badge variant="outline" className="text-[10px] font-mono uppercase">
            BRAND_VOICE
          </Badge>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleRegenerate}
          disabled={isFetching}
          className="h-7 text-xs"
        >
          {isFetching ? "Cargando..." : "Regenerar"}
        </Button>
      </div>

      {isError && (
        <p className="text-xs text-muted-foreground italic">
          No se pudo cargar el preview. Intenta de nuevo.
        </p>
      )}

      {/* Agent bubbles — always rendered (labels visible even before data loads) */}
      <div className="flex flex-col gap-3">
        {/* Valeria — WhatsApp bubble (agent-valeria token via Tailwind utilities) */}
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-agent-valeria">
            Valeria — WhatsApp
          </span>
          <div className="rounded-lg rounded-tl-none bg-agent-valeria-soft/20 border border-agent-valeria-soft p-3 text-sm text-foreground min-h-[48px]">
            {data?.sampleWhatsapp ?? (
              isFetching ? (
                <Skeleton className="h-4 w-[80%]" />
              ) : (
                <span className="text-muted-foreground italic text-xs">
                  Completa los bloques de voz para ver el preview.
                </span>
              )
            )}
          </div>
        </div>

        {/* Camila — email reactivación bubble (agent-camila token via Tailwind utilities) */}
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-agent-camila">
            Camila — Email reactivación
          </span>
          <div className="rounded-lg rounded-tl-none bg-agent-camila-soft/20 border border-agent-camila-soft p-3 text-sm text-foreground min-h-[48px]">
            {data?.sampleEmailReactivacion ?? (
              isFetching ? (
                <Skeleton className="h-4 w-[80%]" />
              ) : (
                <span className="text-muted-foreground italic text-xs">
                  Completa los bloques de voz para ver el preview.
                </span>
              )
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

BrandVoicePreview.displayName = "BrandVoicePreview";
