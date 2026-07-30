// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ComposerAttachButton.tsx — File attachment trigger for composer.
 *
 * Hidden <input type="file"> with visible 📎 button.
 * On file select: calls useAttachMedia mutation + stores result in Zustand attachQueue.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useRef, useCallback } from "react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";
import { useAttachMedia } from "../../api/use-attach-media";
import { useInboxStore } from "../../store/inbox-store";

export interface ComposerAttachButtonProps {
  conversationId: string;
  disabled?: boolean;
  className?: string;
}

/**
 * ComposerAttachButton — hidden file input + 📎 icon button.
 */
export function ComposerAttachButton({
  conversationId,
  disabled,
  className,
}: ComposerAttachButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const attachMedia = useAttachMedia();
  const enqueueAttach = useInboxStore((s) => s.enqueueAttach);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      if (files.length === 0) return;
      // Enqueue files locally for display; upload each
      enqueueAttach(files);
      for (const file of files) {
        attachMedia.mutate({ conversationId, file });
      }
      // Reset input so the same file can be re-selected
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [conversationId, attachMedia, enqueueAttach],
  );

  const isLoading = attachMedia.isPending;

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
        onChange={handleFileChange}
        multiple
        accept="image/*,audio/*,video/*,.pdf,.doc,.docx"
        disabled={disabled || isLoading}
      />
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || isLoading}
        aria-label={INBOX_COPY.composer.attachAriaLabel}
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full",
          "flex items-center justify-center",
          "vt-bg-muted vt-text-muted border vt-border",
          "hover:vt-bg-cian-8 hover:vt-text-cian hover:vt-border-cian",
          "transition-colors duration-150",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          className,
        )}
      >
        <span aria-hidden="true" className="text-sm">
          📎
        </span>
      </button>
    </>
  );
}
