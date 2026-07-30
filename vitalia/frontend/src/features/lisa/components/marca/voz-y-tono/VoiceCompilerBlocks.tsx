// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * VoiceCompilerBlocks.tsx — 6 voice compiler v2 textareas.
 *
 * Blocks (compiler v2, PersonalityProfile):
 *   1. identity        — ANCLA DE IDENTIDAD
 *   2. context         — CONTEXTO DE DOMINIO
 *   3. asi_hablo       — ASÍ HABLO (plain textarea)
 *   4. asi_no_hablo    — ASÍ NO HABLO (VoiceTextareaWithWarning — soft phrase detection)
 *   5. tech_context    — CONTEXTO TÉCNICO
 *   6. format          — INSTRUCCIONES DE FORMATO
 *
 * Only asi_no_hablo uses VoiceTextareaWithWarning (prohibited phrase detection).
 * All others are plain textareas (per mockup voz-tono-section.html).
 *
 * Props: RHF-controlled. onChange called per field → parent schedules autosave.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 deliverables + 03-arch.md § 5 VoiceCompilerBlocks
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { cn } from "@/lib/utils";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { VoiceTextareaWithWarning } from "./VoiceTextareaWithWarning";
import type { ProhibitedPhraseItem } from "../../../api/marca-voice-api";
import type { VoiceBlocksFormValues } from "../../../types/marca/personality-schema";

export interface VoiceCompilerBlocksProps {
  values: VoiceBlocksFormValues;
  onChange: (field: keyof VoiceBlocksFormValues, value: string) => void;
  prohibitedPhrases: ProhibitedPhraseItem[];
  onApplySuggestion?: (phraseId: string, suggestion: string) => void;
  onOverride?: (phraseId: string) => void;
  className?: string;
}

interface PlainBlockProps {
  id: string;
  label: string;
  value: string;
  onChange: (val: string) => void;
  placeholder: string;
  /** E2E test identifier — stable, semantic, non-visual. */
  testId?: string;
}

function PlainBlock({ id, label, value, onChange, placeholder, testId }: PlainBlockProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label
        htmlFor={id}
        className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
      >
        {label}
      </Label>
      <Textarea
        id={id}
        data-testid={testId}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={4}
        className="resize-none text-sm"
      />
    </div>
  );
}

export function VoiceCompilerBlocks({
  values,
  onChange,
  prohibitedPhrases,
  onApplySuggestion,
  onOverride,
  className,
}: VoiceCompilerBlocksProps) {
  return (
    <section className={cn("flex flex-col gap-4", className)}>
      <p className="text-sm font-semibold text-foreground">Bloques de voz</p>

      {/* Block 1: identity */}
      <PlainBlock
        id="voice-identity"
        testId="tone-block-identity-textarea"
        label="Ancla de identidad"
        value={values.identity ?? ""}
        onChange={(v) => onChange("identity", v)}
        placeholder="Ej: Clínica Dental Lima Centro — atención integral con tecnología de punta"
      />

      {/* Block 2: context */}
      <PlainBlock
        id="voice-context"
        testId="tone-block-context-textarea"
        label="Contexto de dominio"
        value={values.context ?? ""}
        onChange={(v) => onChange("context", v)}
        placeholder="Ej: Odontología general, Lima PE. Especialidades: ortodoncia, endodoncia"
      />

      {/* Block 3: asi_hablo — plain (no warning) */}
      <PlainBlock
        id="voice-asi-hablo"
        testId="tone-block-asi-hablo-textarea"
        label="Así hablo"
        value={values.asi_hablo ?? ""}
        onChange={(v) => onChange("asi_hablo", v)}
        placeholder="Ej: - Acompañamos con cuidado&#10;- Explicamos cada paso con claridad&#10;- Usamos términos accesibles"
      />

      {/* Block 4: asi_no_hablo — with prohibited phrase detection */}
      <VoiceTextareaWithWarning
        id="voice-asi-no-hablo"
        data-testid="tone-block-asi-no-hablo-textarea"
        label="Así no hablo"
        value={values.asi_no_hablo ?? ""}
        onChange={(v) => onChange("asi_no_hablo", v)}
        prohibitedPhrases={prohibitedPhrases}
        placeholder="Ej: - Sin frases milagrosas&#10;- Sin términos agresivos&#10;- Sin promesas no verificables"
        onApplySuggestion={onApplySuggestion}
        onOverride={onOverride}
      />

      {/* Block 5: tech_context */}
      <PlainBlock
        id="voice-tech-context"
        testId="tone-block-tech-context-textarea"
        label="Contexto técnico"
        value={values.tech_context ?? ""}
        onChange={(v) => onChange("tech_context", v)}
        placeholder="Ej: Respuestas breves, máx. 2 oraciones. Sin tecnicismos innecesarios"
      />

      {/* Block 6: format */}
      <PlainBlock
        id="voice-format"
        testId="tone-block-format-textarea"
        label="Instrucciones de formato"
        value={values.format ?? ""}
        onChange={(v) => onChange("format", v)}
        placeholder="Ej: Usar listas con guiones. Primera persona plural. Firma con nombre de agente"
      />
    </section>
  );
}

VoiceCompilerBlocks.displayName = "VoiceCompilerBlocks";
