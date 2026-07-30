// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// FaqPairList — editable question/answer pairs that feed Adrián's knowledge
// base ("pares editables → KB del agente"). Controlled array editor: question
// + answer + remove, plus an "Agregar pregunta" action. Autosave is wired by
// the caller via onChange (no "Guardar" button — form-runtime-array doctrine).
//
// ADR-009 fix (G2-F12-FE): maintains LOCAL state seeded from `value` prop once
// per mount. Edits mutate local state and propagate via onChange (for autosave);
// the caller's stale re-renders no longer overwrite what the user typed.
// Re-seed on entity change: pass key={offerId} at the call site (ParaAdrianView).
"use client";

import { useState } from "react";
import { Button, Input, Textarea } from "@luana/ui-kit";
import { cn } from "@/lib/cn";

export interface FaqPair {
  id: string;
  question: string;
  answer: string;
}

interface FaqPairListProps {
  value: FaqPair[];
  onChange: (next: FaqPair[]) => void;
  disabled?: boolean;
  className?: string;
}

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `q-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function FaqPairList({ value: initialValue, onChange, disabled = false, className }: FaqPairListProps) {
  // ADR-009: local state seeded from prop ONCE per mount (or per key change).
  // value binding NEVER reads from the prop after mount — only from localPairs.
  // The caller must pass key={entityId} to force remount when the entity changes.
  const [localPairs, setLocalPairs] = useState<FaqPair[]>(initialValue);

  const commitChange = (next: FaqPair[]) => {
    setLocalPairs(next);
    onChange(next);
  };

  const patch = (id: string, fields: Partial<FaqPair>) =>
    commitChange(localPairs.map((p) => (p.id === id ? { ...p, ...fields } : p)));

  const remove = (id: string) => commitChange(localPairs.filter((p) => p.id !== id));

  const add = () => commitChange([...localPairs, { id: newId(), question: "", answer: "" }]);

  return (
    <div className={className}>
      <div className="my-2 space-y-2.5">
        {localPairs.length === 0 && (
          <p className="text-xs text-muted-foreground" data-testid="faq-empty">
            Aún no agregaste preguntas frecuentes. Cada par pregunta/respuesta alimenta lo que
            Adrián puede responder.
          </p>
        )}
        {localPairs.map((pair) => (
          <div
            key={pair.id}
            data-testid={`faq-row-${pair.id}`}
            className="flex items-start gap-2 rounded-lg border border-border p-2.5"
          >
            <div className="min-w-0 flex-1">
              <Input
                aria-label="Pregunta"
                placeholder="¿Pregunta del paciente?"
                value={pair.question}
                disabled={disabled}
                onChange={(e) => patch(pair.id, { question: e.target.value })}
                className="font-medium"
              />
              <Textarea
                rows={2}
                aria-label="Respuesta"
                placeholder="Respuesta que da Adrián…"
                value={pair.answer}
                disabled={disabled}
                onChange={(e) => patch(pair.id, { answer: e.target.value })}
                className="mt-1.5"
              />
            </div>
            <button
              type="button"
              data-testid={`faq-del-${pair.id}`}
              title="Quitar pregunta"
              aria-label="Quitar pregunta"
              disabled={disabled}
              onClick={() => remove(pair.id)}
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs text-muted-foreground transition-colors",
                "hover:bg-destructive/10 hover:text-destructive",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:cursor-not-allowed disabled:opacity-50",
              )}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      <Button type="button" variant="ghost" size="sm" disabled={disabled} onClick={add}>
        + Agregar pregunta
      </Button>
    </div>
  );
}
