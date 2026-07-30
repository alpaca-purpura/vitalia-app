// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * VoiceTextareaWithWarning.tsx — Textarea with inline prohibited phrase detection.
 *
 * Behavior:
 *   - Renders a standard textarea (never disabled — soft warning only).
 *   - When prohibited phrase detected: shows Alert variant=warning with suggestion.
 *   - "Aplicar sugerencia" button: replaces value with suggestedAlternative.
 *   - "Guardar igual" button: calls onOverride audit log + dismisses alert.
 *   - NEVER blocks save (soft warning per 06-tickets.yaml T-6 A2).
 *
 * Anti-creep (sales-agent-brand-voice.md):
 *   NO health_voice_validator. Simple substring scan via detectProhibitedPhrases.
 *
 * Accessibility: Alert has role="alert" (announced by screen readers automatically).
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A2 + 04-validators.yaml fe_test_voice_warning_inline
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import type { ProhibitedPhraseItem } from "../../../api/marca-voice-api";
import { detectProhibitedPhrases } from "../../../utils/marca/prohibitedPhraseDetector";

export interface VoiceTextareaWithWarningProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  prohibitedPhrases: ProhibitedPhraseItem[];
  placeholder?: string;
  /** Called when user clicks "Aplicar sugerencia" — provides phraseId + suggested text. */
  onApplySuggestion?: (phraseId: string, suggestion: string) => void;
  /** Called when user clicks "Guardar igual" — provides phraseId for audit log. */
  onOverride?: (phraseId: string) => void;
  className?: string;
  id?: string;
  /** E2E test identifier for the internal textarea. Non-visual, stable. */
  "data-testid"?: string;
}

export function VoiceTextareaWithWarning({
  label,
  value,
  onChange,
  prohibitedPhrases,
  placeholder,
  onApplySuggestion,
  onOverride,
  className,
  id: externalId,
  "data-testid": testId,
}: VoiceTextareaWithWarningProps) {
  const textareaId = externalId ?? `voice-textarea-${label.toLowerCase().replace(/\s+/g, "-")}`;

  // Detect phrases on value change — client-side substring scan (NOT LLM)
  const detectedPhrases = detectProhibitedPhrases(value, prohibitedPhrases);
  const firstDetected = detectedPhrases[0];

  // Track dismissed overrides per phrase session
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());

  // Reset dismissals when value changes significantly
  useEffect(() => {
    setDismissedIds(new Set());
  }, [value]);

  const showWarning =
    firstDetected !== undefined && !dismissedIds.has(firstDetected.phraseId);

  function handleApplySuggestion() {
    if (!firstDetected) return;
    onApplySuggestion?.(firstDetected.phraseId, firstDetected.suggestedAlternative);
    // Replace value with suggestion
    onChange(firstDetected.suggestedAlternative);
  }

  function handleOverride() {
    if (!firstDetected) return;
    onOverride?.(firstDetected.phraseId);
    setDismissedIds((prev) => new Set(prev).add(firstDetected.phraseId));
  }

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <Label htmlFor={textareaId} className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </Label>
      <Textarea
        id={textareaId}
        data-testid={testId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={4}
        // NEVER disabled — soft warning only (A2)
        className="resize-none text-sm"
      />
      {showWarning && firstDetected && (
        <Alert
          role="alert"
          className="border-amber-400/60 bg-amber-50 dark:bg-amber-950/30"
        >
          <AlertDescription className="flex flex-col gap-2">
            <p className="text-sm text-amber-800 dark:text-amber-200">
              <span className="font-semibold">Frase a revisar:</span>{" "}
              &ldquo;{firstDetected.matchedText}&rdquo;
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-300">
              <span className="font-semibold">Sugerencia:</span>{" "}
              {firstDetected.suggestedAlternative}
            </p>
            <div className="flex gap-2">
              <Button
                type="button"
                size="sm"
                variant="default"
                onClick={handleApplySuggestion}
                className="h-7 text-xs"
              >
                Aplicar sugerencia
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={handleOverride}
                className="h-7 text-xs text-amber-700 hover:text-amber-800 dark:text-amber-400"
              >
                Guardar igual
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}

VoiceTextareaWithWarning.displayName = "VoiceTextareaWithWarning";
