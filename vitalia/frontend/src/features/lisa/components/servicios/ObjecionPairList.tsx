// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// ObjecionPairList — editable objection/response pairs ("🛡️ Objeciones → cómo
// responder"): a short objection tag (Precio, Miedo, Tiempo…) + the response
// Adrián gives. Controlled array editor with add/remove. Autosave is wired by
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

export interface ObjecionPair {
  id: string;
  /** Short objection label: "Precio", "Miedo", "Tiempo", "Lo pienso"… */
  tag: string;
  /** How Adrián responds to that objection. */
  response: string;
}

interface ObjecionPairListProps {
  value: ObjecionPair[];
  onChange: (next: ObjecionPair[]) => void;
  disabled?: boolean;
  className?: string;
}

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `o-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function ObjecionPairList({
  value: initialValue,
  onChange,
  disabled = false,
  className,
}: ObjecionPairListProps) {
  // ADR-009: local state seeded from prop ONCE per mount (or per key change).
  // value binding NEVER reads from the prop after mount — only from localPairs.
  // The caller must pass key={entityId} to force remount when the entity changes.
  const [localPairs, setLocalPairs] = useState<ObjecionPair[]>(initialValue);

  const commitChange = (next: ObjecionPair[]) => {
    setLocalPairs(next);
    onChange(next);
  };

  const patch = (id: string, fields: Partial<ObjecionPair>) =>
    commitChange(localPairs.map((o) => (o.id === id ? { ...o, ...fields } : o)));

  const remove = (id: string) => commitChange(localPairs.filter((o) => o.id !== id));

  const add = () => commitChange([...localPairs, { id: newId(), tag: "", response: "" }]);

  return (
    <div className={className}>
      <div className="my-2 space-y-2.5">
        {localPairs.length === 0 && (
          <p className="text-xs text-muted-foreground" data-testid="obj-empty">
            Aún no cargaste objeciones. Anota la objeción típica y cómo responderla; Adrián la usa
            para cerrar.
          </p>
        )}
        {localPairs.map((obj) => (
          <div
            key={obj.id}
            data-testid={`obj-row-${obj.id}`}
            className="space-y-2 rounded-lg border border-border p-2.5 sm:flex sm:items-start sm:gap-2 sm:space-y-0"
          >
            <Input
              aria-label="Objeción"
              placeholder="Precio, Miedo, Tiempo…"
              value={obj.tag}
              disabled={disabled}
              onChange={(e) => patch(obj.id, { tag: e.target.value })}
              className="font-semibold sm:max-w-36"
            />
            <Textarea
              rows={2}
              aria-label="Cómo responder"
              placeholder="Cómo responde Adrián…"
              value={obj.response}
              disabled={disabled}
              onChange={(e) => patch(obj.id, { response: e.target.value })}
              className="sm:flex-1"
            />
            <button
              type="button"
              data-testid={`obj-del-${obj.id}`}
              title="Quitar objeción"
              aria-label="Quitar objeción"
              disabled={disabled}
              onClick={() => remove(obj.id)}
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
        + Agregar objeción
      </Button>
    </div>
  );
}
