// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
"use client";
/**
 * PruebaSocialView.tsx — Leaf 5: Prueba social (testimonios + casos).
 *
 * spec §Workspace Pestaña 5 · 01-spec.md §Workspace Pestaña 5
 *
 * Sub-phase A scope:
 *   - Testimonials: add (form) + list + display (read-only)
 *   - Cases (before/after PHI): read-only display with "Próximamente" gate for uploads
 *     (PHI write path requires consent-signed flow — Sub-phase B)
 *
 * Autosave: testimonials added immediately on submit (no pending state per RN-20 spirit).
 * HIPAA-lite: Cases are PHI. Display only; form disabled pending Sub-phase B consent flow.
 *
 * spec_anchor: 03-arch-fe.md §5 PruebaSocialView
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Group, GroupHeader } from "@luana/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  useServicioDetail,
  useAddTestimonial,
} from "../../../api/servicios";

// ── Testimonial form schema ───────────────────────────────────────────────────────
const testimonialSchema = z.object({
  author: z.string().min(1, "El nombre es requerido"),
  rating: z
    .number()
    .int()
    .min(1, "Mínimo 1 estrella")
    .max(5, "Máximo 5 estrellas"),
  text: z.string().min(10, "El testimonio debe tener al menos 10 caracteres"),
  source: z.string().min(1, "La fuente es requerida"),
});
type TestimonialFormValues = z.infer<typeof testimonialSchema>;

interface PruebaSocialViewProps {
  offerId: string;
}

export function PruebaSocialView({ offerId }: PruebaSocialViewProps) {
  const { data: servicio } = useServicioDetail({ offerId });
  const { mutate: addTestimonial, isPending } = useAddTestimonial(offerId);
  const [showForm, setShowForm] = useState(false);

  const form = useForm<TestimonialFormValues>({
    resolver: zodResolver(testimonialSchema),
    defaultValues: { author: "", rating: 5, text: "", source: "Google" },
  });

  if (!servicio) {
    return (
      <div className="p-6 space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-20 bg-muted rounded-md animate-pulse" />
        ))}
      </div>
    );
  }

  const testimonials = servicio.testimonials;
  const cases = servicio.cases;

  const onSubmit = (values: TestimonialFormValues) => {
    addTestimonial(values, {
      onSuccess: () => {
        form.reset();
        setShowForm(false);
      },
    });
  };

  return (
    <div className="p-5 md:p-6 space-y-6 pb-24">
      {/* ── Testimonios ────────────────────────────────────────────────────────── */}
      <Group accentVar="--agent-lisa">
        <GroupHeader title="Testimonios" />

        <p className="text-sm text-muted-foreground">
          Los testimonios reales de pacientes ayudan a Adrián a generar confianza.
        </p>

        {/* List (read-only display — add via form below, RN-33 manual) */}
        {testimonials.length > 0 ? (
          <ul className="space-y-2">
            {testimonials.map((t) => (
              <li
                key={t.id}
                className="rounded-lg border border-border p-3 space-y-1"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{t.author}</span>
                  <span
                    className="text-xs text-amber-500"
                    aria-label={`${t.rating} de 5 estrellas`}
                  >
                    {"★".repeat(t.rating)}
                    {"☆".repeat(Math.max(0, 5 - t.rating))}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{t.text}</p>
                {t.source && (
                  <Badge variant="outline" className="text-xs">
                    {t.source}
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="rounded-lg border border-dashed border-border p-6 text-center">
            <p className="text-sm text-muted-foreground">
              No hay testimonios todavía.
            </p>
          </div>
        )}

        {/* Add testimonial */}
        {showForm ? (
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-2 border-t border-border">
            <p className="text-sm font-medium">Agregar testimonio</p>

            <div className="flex gap-3 [&>div]:flex-1">
              <div className="space-y-1">
                <Label htmlFor="author">Nombre del paciente</Label>
                <Input
                  id="author"
                  {...form.register("author")}
                  placeholder="Ej. Dr. García"
                />
                {form.formState.errors.author && (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.author.message}
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <Label htmlFor="rating">Calificación (1-5)</Label>
                <Input
                  id="rating"
                  type="number"
                  min={1}
                  max={5}
                  {...form.register("rating", { valueAsNumber: true })}
                />
                {form.formState.errors.rating && (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.rating.message}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="text">Texto del testimonio</Label>
              <Textarea
                id="text"
                {...form.register("text")}
                placeholder="El tratamiento cambió mi vida…"
                rows={3}
              />
              {form.formState.errors.text && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.text.message}
                </p>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="source">Fuente</Label>
              <Input
                id="source"
                {...form.register("source")}
                placeholder="Google · Instagram · Directo"
              />
              {form.formState.errors.source && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.source.message}
                </p>
              )}
            </div>

            <div className="flex gap-2 justify-end">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  form.reset();
                  setShowForm(false);
                }}
              >
                Cancelar
              </Button>
              <Button type="submit" size="sm" disabled={isPending}>
                {isPending ? "Guardando…" : "Agregar"}
              </Button>
            </div>
          </form>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowForm(true)}
          >
            + Agregar testimonio
          </Button>
        )}
      </Group>

      {/* ── Casos (before/after) ─────────────────────────────────────────────── */}
      <Group>
        <div className="flex items-center gap-2">
          <GroupHeader title="Casos antes/después" />
          <Badge variant="secondary" className="text-xs">Próximamente</Badge>
        </div>

        <p className="text-sm text-muted-foreground">
          Los casos visuales aumentan la confianza y la tasa de reserva.
          Carga fotos de antes y después con consentimiento del paciente.
        </p>

        {cases.length > 0 ? (
          <ul className="grid grid-cols-2 gap-3">
            {cases.map((c) => (
              <li key={c.id} className="rounded-lg border border-border p-3 text-xs text-muted-foreground">
                <div className="flex gap-1 items-center">
                  <span>Antes:</span>
                  <span className="truncate">{c.before_asset_url}</span>
                </div>
                <div className="flex gap-1 items-center mt-1">
                  <span>Después:</span>
                  <span className="truncate">{c.after_asset_url}</span>
                </div>
                {c.consent_signed && (
                  <Badge variant="outline" className="mt-2 text-xs">
                    Consentimiento firmado
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Los casos PHI (antes/después) estarán disponibles en la próxima actualización.
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Incluirán flujo de consentimiento digital del paciente.
            </p>
          </div>
        )}
      </Group>
    </div>
  );
}
