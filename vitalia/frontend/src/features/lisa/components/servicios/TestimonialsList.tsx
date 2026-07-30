// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// TestimonialsList — manual testimonials Lisa loads (typed or pasted from
// Google / Instagram / surveys) that Adrián cites to build trust. Controlled
// array editor: 5-star marker + quote + author + origin + remove, plus an
// "Agregar testimonio" action. Autosave is wired by the caller via onChange
// (no "Guardar" button — form-runtime-array doctrine).
"use client";

import { Button, Input, Textarea } from "@luana/ui-kit";
import { cn } from "@/lib/cn";

export interface Testimonial {
  id: string;
  quote: string;
  author?: string;
  /** Where it came from: "Google", "Instagram", "encuesta"… (free text). */
  source?: string;
}

interface TestimonialsListProps {
  value: Testimonial[];
  onChange: (next: Testimonial[]) => void;
  disabled?: boolean;
  className?: string;
}

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `t-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function TestimonialsList({
  value,
  onChange,
  disabled = false,
  className,
}: TestimonialsListProps) {
  const patch = (id: string, fields: Partial<Testimonial>) =>
    onChange(value.map((t) => (t.id === id ? { ...t, ...fields } : t)));

  const remove = (id: string) => onChange(value.filter((t) => t.id !== id));

  const add = () => onChange([...value, { id: newId(), quote: "", author: "", source: "" }]);

  return (
    <div className={className}>
      <div className="my-2 space-y-2.5">
        {value.length === 0 && (
          <p className="text-xs text-muted-foreground" data-testid="testi-empty">
            Aún no cargaste testimonios. Escríbelos o pégalos (de Google, Instagram, encuestas);
            Adrián los cita para generar confianza.
          </p>
        )}
        {value.map((testi) => (
          <div
            key={testi.id}
            data-testid={`testi-row-${testi.id}`}
            className="flex items-start gap-2 rounded-lg border border-border p-2.5"
          >
            <span
              aria-hidden
              className="shrink-0 text-sm leading-relaxed tracking-wide text-vitalia-warning"
            >
              ★★★★★
            </span>
            <div className="min-w-0 flex-1">
              <Textarea
                rows={2}
                aria-label="Testimonio"
                placeholder="Pega o escribe el testimonio…"
                value={testi.quote}
                disabled={disabled}
                onChange={(e) => patch(testi.id, { quote: e.target.value })}
              />
              <div className="mt-1.5 space-y-2 sm:flex sm:gap-2 sm:space-y-0">
                <Input
                  aria-label="Autor del testimonio"
                  placeholder="Autor (nombre o iniciales)"
                  value={testi.author ?? ""}
                  disabled={disabled}
                  onChange={(e) => patch(testi.id, { author: e.target.value })}
                  className="sm:flex-1"
                />
                <Input
                  aria-label="Origen del testimonio"
                  placeholder="Origen (Google, Instagram…)"
                  value={testi.source ?? ""}
                  disabled={disabled}
                  onChange={(e) => patch(testi.id, { source: e.target.value })}
                  className="sm:flex-1"
                />
              </div>
            </div>
            <button
              type="button"
              data-testid={`testi-del-${testi.id}`}
              title="Quitar testimonio"
              aria-label="Quitar testimonio"
              disabled={disabled}
              onClick={() => remove(testi.id)}
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
        + Agregar testimonio
      </Button>
    </div>
  );
}
