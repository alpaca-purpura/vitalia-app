// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * VoiceMessagePlayer.tsx — HTML5 audio player for voice messages.
 *
 * Features:
 *   - Play/pause toggle with progress scrubber
 *   - Playback speed: 0.75x / 1x / 1.25x / 1.5x / 2x
 *   - Collapsible transcript section (show/hide)
 *   - SC-02: shows fallback text when transcription_confidence < 0.5 or null
 *
 * Accessibility: aria-label on audio controls, aria-live on time display.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState, useRef, useCallback } from "react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5, 2] as const;
type PlaybackSpeed = (typeof SPEED_OPTIONS)[number];

/** Confidence threshold — SC-02: below this value, show fallback text */
const LOW_CONFIDENCE_THRESHOLD = 0.5;

export interface VoiceMessagePlayerProps {
  /** CDN URL for the audio file */
  mediaUrl: string;
  /** Duration in seconds (for display before audio loads) */
  durationS?: number | null;
  /** Whisper transcription text */
  transcriptionText?: string | null;
  /** Whisper confidence 0..1; < 0.5 shows fallback */
  transcriptionConfidence?: number | null;
  className?: string;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

/**
 * VoiceMessagePlayer — inline audio player for inbox messages.
 */
export function VoiceMessagePlayer({
  mediaUrl,
  durationS,
  transcriptionText,
  transcriptionConfidence,
  className,
}: VoiceMessagePlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState<number>(durationS ?? 0);
  const [speed, setSpeed] = useState<PlaybackSpeed>(1);
  const [transcriptOpen, setTranscriptOpen] = useState(false);

  const hasValidTranscript =
    transcriptionText &&
    transcriptionConfidence !== null &&
    transcriptionConfidence !== undefined &&
    transcriptionConfidence >= LOW_CONFIDENCE_THRESHOLD;

  const handlePlayPause = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
    } else {
      void audio.play();
    }
  }, [isPlaying]);

  const handleTimeUpdate = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    setCurrentTime(audio.currentTime);
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    setDuration(audio.duration);
  }, []);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
  }, []);

  const handleScrubberChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newTime = Number(e.target.value);
      if (audioRef.current) {
        audioRef.current.currentTime = newTime;
      }
      setCurrentTime(newTime);
    },
    [],
  );

  const handleSpeedCycle = useCallback(() => {
    const idx = SPEED_OPTIONS.indexOf(speed);
    const next = SPEED_OPTIONS[(idx + 1) % SPEED_OPTIONS.length] ?? 1;
    setSpeed(next);
    if (audioRef.current) {
      audioRef.current.playbackRate = next;
    }
  }, [speed]);

  const displayDuration = duration > 0 ? duration : (durationS ?? 0);

  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-xl p-3 vt-bg-muted border vt-border",
        "min-w-[200px] max-w-xs",
        className,
      )}
      role="region"
      aria-label={INBOX_COPY.multimedia.audioPlayer.ariaLabel}
    >
      {/* Hidden native audio element */}
      <audio
        ref={audioRef}
        src={mediaUrl}
        preload="metadata"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={handleEnded}
      />

      {/* Controls row */}
      <div className="flex items-center gap-2">
        {/* Play/Pause button */}
        <button
          type="button"
          onClick={handlePlayPause}
          className={cn(
            "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
            "vt-bg-cian-10 vt-text-cian border vt-border-cian",
            "hover:vt-bg-cian hover:vt-text-white transition-colors",
          )}
          aria-label={isPlaying ? "Pausar" : "Reproducir"}
        >
          {isPlaying ? (
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="currentColor"
              aria-hidden="true"
            >
              <rect x="2" y="1" width="3" height="10" rx="1" />
              <rect x="7" y="1" width="3" height="10" rx="1" />
            </svg>
          ) : (
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M2 1.5v9l8-4.5-8-4.5z" />
            </svg>
          )}
        </button>

        {/* Scrubber + time */}
        <div className="flex-1 flex flex-col gap-0.5 min-w-0">
          <input
            type="range"
            min={0}
            max={displayDuration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleScrubberChange}
            className="w-full h-1.5 rounded accent-[var(--vitalia-cian-color)] cursor-pointer"
            aria-label="Progreso del audio"
          />
          <div
            className="flex justify-between text-[10px] vt-text-muted"
            aria-live="polite"
            aria-atomic="true"
          >
            <span>{formatTime(currentTime)}</span>
            <span>
              {displayDuration > 0 ? formatTime(displayDuration) : "--:--"}
            </span>
          </div>
        </div>

        {/* Speed button */}
        <button
          type="button"
          onClick={handleSpeedCycle}
          className={cn(
            "flex-shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded",
            "vt-bg-surface vt-text-muted border vt-border",
            "hover:vt-text-cian hover:vt-border-cian transition-colors",
          )}
          aria-label={`${INBOX_COPY.multimedia.audioPlayer.speedLabel}: ${speed}x`}
        >
          {speed}x
        </button>
      </div>

      {/* Transcript section */}
      <div className="border-t vt-border-soft pt-2">
        <button
          type="button"
          onClick={() => setTranscriptOpen((v) => !v)}
          className="text-xs vt-text-muted hover:vt-text-cian transition-colors flex items-center gap-1"
          aria-expanded={transcriptOpen}
        >
          <span aria-hidden="true">{transcriptOpen ? "▾" : "▸"}</span>
          {INBOX_COPY.multimedia.audioPlayer.transcript}
        </button>

        {transcriptOpen && (
          <p className="mt-1 text-xs vt-text leading-relaxed">
            {hasValidTranscript
              ? transcriptionText
              : INBOX_COPY.multimedia.audioPlayer.transcriptFailed}
          </p>
        )}
      </div>
    </div>
  );
}
