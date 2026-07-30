/**
 * VoiceMessagePlayer.test.tsx
 *
 * SC-02 coverage: test_no_transcription_fallback_text
 * Given: audio message with transcription_confidence < 0.5 (or null)
 * When: VoiceMessagePlayer is rendered and transcript is opened
 * Then: shows INBOX_COPY fallback text, NOT the raw transcription
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VoiceMessagePlayer } from "../VoiceMessagePlayer";
import { INBOX_COPY } from "../../../lib/copy";

// Mock HTMLMediaElement (jsdom doesn't support it)
Object.defineProperty(window, "HTMLMediaElement", {
  value: class {
    play = vi.fn(async () => undefined);
    pause = vi.fn();
    load = vi.fn();
    currentTime = 0;
    duration = 0;
    paused = true;
    playbackRate = 1;
    preload = "auto";
  },
  writable: true,
});

describe("VoiceMessagePlayer", () => {
  /**
   * SC-02: test_no_transcription_fallback_text
   * Given: audio message where Whisper confidence < 0.5
   * When: user opens transcript section
   * Then: shows INBOX_COPY.multimedia.audioPlayer.transcriptFailed, not the raw text
   */
  it("test_no_transcription_fallback_text — shows fallback when confidence < 0.5", async () => {
    const user = userEvent.setup();
    render(
      <VoiceMessagePlayer
        mediaUrl="https://cdn.example.com/audio.webm"
        durationS={12}
        transcriptionText="Texto con baja confianza"
        transcriptionConfidence={0.3}
      />,
    );

    // Click to open transcript
    await user.click(
      screen.getByText(INBOX_COPY.multimedia.audioPlayer.transcript),
    );

    // Fallback text should be shown, NOT the raw transcription
    expect(
      screen.getByText(INBOX_COPY.multimedia.audioPlayer.transcriptFailed),
    ).toBeInTheDocument();
    expect(screen.queryByText("Texto con baja confianza")).toBeNull();
  });

  it("shows fallback when transcription_confidence is null", async () => {
    const user = userEvent.setup();
    render(
      <VoiceMessagePlayer
        mediaUrl="https://cdn.example.com/audio.webm"
        transcriptionText={null}
        transcriptionConfidence={null}
      />,
    );

    await user.click(
      screen.getByText(INBOX_COPY.multimedia.audioPlayer.transcript),
    );
    expect(
      screen.getByText(INBOX_COPY.multimedia.audioPlayer.transcriptFailed),
    ).toBeInTheDocument();
  });

  it("shows real transcript when confidence >= 0.5", async () => {
    const user = userEvent.setup();
    const transcript = "El paciente está interesado en la consulta.";
    render(
      <VoiceMessagePlayer
        mediaUrl="https://cdn.example.com/audio.webm"
        transcriptionText={transcript}
        transcriptionConfidence={0.85}
      />,
    );

    await user.click(
      screen.getByText(INBOX_COPY.multimedia.audioPlayer.transcript),
    );
    expect(screen.getByText(transcript)).toBeInTheDocument();
    expect(
      screen.queryByText(INBOX_COPY.multimedia.audioPlayer.transcriptFailed),
    ).toBeNull();
  });

  it("renders audio region with correct aria-label", () => {
    render(
      <VoiceMessagePlayer
        mediaUrl="https://cdn.example.com/audio.webm"
        durationS={30}
        transcriptionText="Prueba"
        transcriptionConfidence={0.9}
      />,
    );
    expect(
      screen.getByRole("region", {
        name: INBOX_COPY.multimedia.audioPlayer.ariaLabel,
      }),
    ).toBeInTheDocument();
  });

  it("renders play button", () => {
    render(
      <VoiceMessagePlayer mediaUrl="https://cdn.example.com/audio.webm" />,
    );
    expect(
      screen.getByRole("button", { name: "Reproducir" }),
    ).toBeInTheDocument();
  });

  it("cycles speed button through options", async () => {
    const user = userEvent.setup();
    render(
      <VoiceMessagePlayer mediaUrl="https://cdn.example.com/audio.webm" />,
    );
    const speedBtn = screen.getByRole("button", { name: /velocidad/i });
    expect(speedBtn).toHaveTextContent("1x");

    await user.click(speedBtn);
    expect(speedBtn).toHaveTextContent("1.25x");

    await user.click(speedBtn);
    expect(speedBtn).toHaveTextContent("1.5x");
  });
});
