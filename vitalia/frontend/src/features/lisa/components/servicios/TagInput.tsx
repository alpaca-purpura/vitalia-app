// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// TagInput — free-form keyword chips for "cómo lo nombra el paciente" (carillas,
// fundas, "arreglarme los dientes"…). These help Adrián match an inbound message
// to this service even when the patient doesn't use the clinical term. Add with
// Enter (or the "+ Agregar" button), remove with the ✕ on each chip. Autosave is
// wired by the caller via onChange (no "Guardar" button).
"use client";

import { useState } from "react";
import { Badge, Input } from "@luana/ui-kit";
import { cn } from "@/lib/cn";

interface TagInputProps {
  value: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
}

export function TagInput({
  value,
  onChange,
  placeholder = "Agregar palabra clave…",
  disabled = false,
  className,
  "aria-label": ariaLabel = "Palabras clave",
}: TagInputProps) {
  const [draft, setDraft] = useState("");

  const commit = () => {
    const tag = draft.trim();
    if (!tag) return;
    // de-dupe (case-insensitive) — keep the first casing the user typed
    if (value.some((t) => t.toLowerCase() === tag.toLowerCase())) {
      setDraft("");
      return;
    }
    onChange([...value, tag]);
    setDraft("");
  };

  const remove = (tag: string) => onChange(value.filter((t) => t !== tag));

  return (
    <div className={className}>
      <div className="mb-2 flex flex-wrap gap-1.5" data-testid="tag-chips">
        {value.map((tag) => (
          <Badge
            key={tag}
            variant="secondary"
            data-testid={`tag-${tag}`}
            className="gap-1 pr-1 font-normal"
          >
            {tag}
            <button
              type="button"
              data-testid={`tag-del-${tag}`}
              title={`Quitar ${tag}`}
              aria-label={`Quitar ${tag}`}
              disabled={disabled}
              onClick={() => remove(tag)}
              className={cn(
                "ml-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full text-xs leading-none transition-colors",
                "hover:bg-foreground/10",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                "disabled:cursor-not-allowed disabled:opacity-50",
              )}
            >
              ✕
            </button>
          </Badge>
        ))}
      </div>
      <Input
        value={draft}
        disabled={disabled}
        placeholder={placeholder}
        aria-label={ariaLabel}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            commit();
          } else if (e.key === "Backspace" && draft === "" && value.length > 0) {
            remove(value[value.length - 1]);
          }
        }}
        onBlur={commit}
      />
    </div>
  );
}
