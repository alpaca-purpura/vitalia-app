// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-attach-media.ts — Mutation hook for uploading media attachments.
 *
 * Endpoint: POST /api/v1/vitalia/inbox/conversations/{conversationId}/attach
 *
 * Multipart/form-data upload. Returns a CDN media_url that can be
 * included in a subsequent useSendMessage call.
 *
 * PHI note: media files may contain PHI (images of documents, etc.).
 * Dual filter enforced server-side (tenant_id + clinic_id).
 * Uploads stored in clinic-scoped CDN bucket.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useClinicId } from "@/hooks/useClinicId";
import { useTenantId } from "@/hooks/useTenantId";

export interface AttachMediaInput {
  conversationId: string;
  file: File;
}

export interface AttachMediaResult {
  /** CDN URL for the uploaded media */
  media_url: string;
  /** Detected media kind */
  media_kind: "audio" | "image" | "video" | "document";
  /** File size in bytes */
  size_bytes: number;
  /** Duration in seconds for audio/video */
  duration_s: number | null;
}

/**
 * Mutation to upload a media attachment for a conversation.
 * Returns media_url for use in useSendMessage.
 */
export function useAttachMedia() {
  const { getToken } = useAuth();
  const clinicId = useClinicId();
  const tenantId = useTenantId();

  return useMutation({
    mutationFn: async (input: AttachMediaInput): Promise<AttachMediaResult> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      const formData = new FormData();
      formData.append("file", input.file);

      const headers: Record<string, string> = {
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": tenantId,
      };
      if (clinicId) {
        headers["X-Clinic-ID"] = clinicId;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120_000); // 2min for large files

      let response: Response;
      try {
        response = await fetch(
          `/api/v1/vitalia/inbox/conversations/${input.conversationId}/attach`,
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
        throw new Error(`Attach failed: ${response.status}`);
      }

      return response.json() as Promise<AttachMediaResult>;
    },
  });
}
