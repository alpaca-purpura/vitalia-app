// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * prohibitedPhraseDetector.ts — Client-side scan of prohibited phrases.
 *
 * Anti-creep (sales-agent-brand-voice.md):
 *   NO health_voice_validator. Soft warning ONLY. Does NOT block save.
 *   NOT a LLM call. Simple substring/regex lookup against tenant phrase list.
 *
 * Usage:
 *   const matches = detectProhibitedPhrases(inputText, phrases);
 *   if (matches.length > 0) → show VoiceTextareaWithWarning alert
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 + 03-arch.md D2-voice
 * downstream-regression-na: brand-local vitalia FE util; no cross-brand consumers
 */

import type { ProhibitedPhraseItem } from "../../api/marca-voice-api";

export interface DetectedPhrase {
  phraseId: string;
  matchedText: string;
  suggestedAlternative: string;
  severity: "low" | "medium" | "high";
}

/**
 * Scan input text against a list of prohibited phrases (case-insensitive substring).
 *
 * Returns array of detected matches. Empty array = no warnings.
 * Does NOT modify text. Does NOT block persistence (soft warning only).
 */
export function detectProhibitedPhrases(
  inputText: string,
  phrases: ProhibitedPhraseItem[],
): DetectedPhrase[] {
  if (!inputText || !phrases.length) return [];

  const lowerInput = inputText.toLowerCase();
  const detected: DetectedPhrase[] = [];

  for (const item of phrases) {
    if (!item.phrase) continue;
    const lowerPhrase = item.phrase.toLowerCase();
    if (lowerInput.includes(lowerPhrase)) {
      detected.push({
        phraseId: item.id,
        matchedText: item.phrase,
        suggestedAlternative: item.suggestedAlternative,
        severity: item.severity,
      });
    }
  }

  return detected;
}

/**
 * Simple hash of voice block values for React Query key stability.
 * NOT a cryptographic hash — just a stable string representation for cache keying.
 */
export function hashVoiceBlocks(blocks: Record<string, string | undefined>): string {
  const canonical = Object.keys(blocks)
    .sort()
    .map((k) => `${k}=${blocks[k] ?? ""}`)
    .join("|");
  // djb2-like simple hash to keep string short
  let hash = 5381;
  for (let i = 0; i < canonical.length; i++) {
    hash = ((hash << 5) + hash) ^ canonical.charCodeAt(i);
  }
  return (hash >>> 0).toString(16);
}
