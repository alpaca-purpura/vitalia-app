// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ComposerVoiceButton.tsx — MediaRecorder voice note button for composer.
 *
 * Fork adapter from Nicolify VoiceOverlay pattern.
 * Retokenized: violet-* → vt-* CSS utility classes.
 *
 * On 🎤 press: starts MediaRecorder → shows recording indicator.
 * On stop: uploads via useTranscribeAudio → passes result to onVoiceReady callback.
 *
 * Graceful degradation: if MediaRecorder not supported, button is hidden.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";
import { useTranscribeAudio } from "../../api/use-transcribe-audio";

export interface VoiceReadyResult {
  mediaUrl: string;
  transcriptionText: string;
  transcriptionConfidence: number;
  durationS: number;
  mimeType: string;
}

export interface ComposerVoiceButtonProps {
  conversationId: string;
  onVoiceReady: (result: VoiceReadyResult) => void;
  onError?: (error: Error) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * ComposerVoiceButton — 🎤 MediaRecorder trigger + recording indicator.
 */
export function ComposerVoiceButton({
  conversationId,
  onVoiceReady,
  onError,
  disabled,
  className,
}: ComposerVoiceButtonProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const transcribeAudio = useTranscribeAudio();

  // Check MediaRecorder support on mount (client-only browser API)
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !window.MediaRecorder ||
      !navigator.mediaDevices
    ) {
      setIsSupported(false);
    }
  }, []);

  const handleStop = useCallback(
    (mimeType: string) => {
      const chunks = chunksRef.current;
      if (chunks.length === 0) return;
      const blob = new Blob(chunks, { type: mimeType });
      const durationS = (Date.now() - startTimeRef.current) / 1000;
      transcribeAudio.mutate(
        { conversationId, audioBlob: blob, mimeType },
        {
          onSuccess: (result) => {
            onVoiceReady({
              mediaUrl: result.media_url,
              transcriptionText: result.transcription_text,
              transcriptionConfidence: result.transcription_confidence,
              durationS,
              mimeType,
            });
          },
          onError: (err) => {
            onError?.(err instanceof Error ? err : new Error(String(err)));
          },
        },
      );
      chunksRef.current = [];
    },
    [conversationId, onVoiceReady, onError, transcribeAudio],
  );

  const startRecording = useCallback(async () => {
    if (!isSupported) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/ogg;codecs=opus";

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      startTimeRef.current = Date.now();

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        // Stop all tracks to release mic
        stream.getTracks().forEach((t) => t.stop());
        setIsRecording(false);
        handleStop(mimeType);
      };

      recorder.start(100); // collect chunks every 100ms
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      onError?.(
        err instanceof Error ? err : new Error("Microphone access denied"),
      );
    }
  }, [isSupported, handleStop, onError]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  const handleClick = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      void startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  // Don't render if MediaRecorder not supported
  if (!isSupported) return null;

  const isUploading = transcribeAudio.isPending;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled || isUploading}
      aria-label={
        isRecording
          ? INBOX_COPY.composer.recordingStop
          : INBOX_COPY.composer.voiceAriaLabel
      }
      aria-pressed={isRecording}
      className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full",
        "flex items-center justify-center",
        "border transition-colors duration-150",
        isRecording
          ? "vt-bg-danger-12 vt-text-danger vt-border-danger-30 animate-pulse"
          : "vt-bg-muted vt-text-muted vt-border hover:vt-bg-cian-8 hover:vt-text-cian hover:vt-border-cian",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        className,
      )}
    >
      <span aria-hidden="true" className="text-sm">
        {isUploading ? "⏳" : isRecording ? "⏹" : "🎤"}
      </span>
    </button>
  );
}
