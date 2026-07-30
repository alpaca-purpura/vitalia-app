// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-transcribe-audio.ts — Mutation hook for Whisper STT transcription.
 *
 * Endpoint: POST /api/v1/vitalia/inbox/conversations/{conversationId}/transcribe-audio
 *
 * Operator uploads an audio file; server returns transcription_text + confidence.
 * SC-02: If Whisper returns confidence < 0.5, UI shows fallback "No se pudo transcribir".
 *
 * PHI note: audio content may contain patient voice. Endpoint is clinic-scoped
 * (dual filter enforced server-side). Transcription result stored server-side.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useClinicId } from "@/hooks/useClinicId";
import { useTenantId } from "@/hooks/useTenantId";

export interface TranscribeAudioInput {
  conversationId: string;
  /** Audio file blob (Blob from MediaRecorder or File from <input type="file">) */
  audioBlob: Blob;
  /** MIME type hint for the server (e.g. "audio/webm;codecs=opus") */
  mimeType?: string;
}

export interface TranscribeAudioResult {
  transcription_text: string;
  /** Confidence 0..1. Values < 0.5 treated as low-confidence by UI */
  transcription_confidence: number;
  /** The media URL saved to CDN (for attaching to send-message) */
  media_url: string;
}

/**
 * Mutation to transcribe an audio blob via Whisper STT.
 * On success, caller uses media_url + transcription_text for message send.
 */
export function useTranscribeAudio() {
  const { getToken } = useAuth();
  const clinicId = useClinicId();
  const tenantId = useTenantId();

  return useMutation({
    mutationFn: async (
      input: TranscribeAudioInput,
    ): Promise<TranscribeAudioResult> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      const formData = new FormData();
      const filename = `recording-${Date.now()}.${input.mimeType?.includes("webm") ? "webm" : "ogg"}`;
      formData.append("audio", input.audioBlob, filename);
      if (input.mimeType) {
        formData.append("mime_type", input.mimeType);
      }

      // Note: fetchClient sets Content-Type: application/json by default;
      // for multipart we must override with no Content-Type (browser sets boundary).
      const requestToken = token;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60_000); // longer for audio

      const headers: Record<string, string> = {
        Authorization: `Bearer ${requestToken}`,
        "X-Tenant-ID": tenantId,
      };
      if (clinicId) {
        headers["X-Clinic-ID"] = clinicId;
      }

      let response: Response;
      try {
        response = await fetch(
          `/api/v1/vitalia/inbox/conversations/${input.conversationId}/transcribe-audio`,
          {
            method: "POST",
            headers,
            body: formData,
            signal: controller.signal,
          },
        );
      } finally {
        clearTimeout(timeoutId);
      }

      if (!response.ok) {
        throw new Error(`Transcribe failed: ${response.status}`);
      }

      return response.json() as Promise<TranscribeAudioResult>;
    },
  });
}
