// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
"use client";
/**
 * KnowledgeSourcesPanel.tsx — Sub-phase A: process a document and prefill fields.
 *
 * Scope (Sub-phase A):
 *   - URL-only source (upload is Sub-phase B)
 *   - "Procesar con Lisa" → POST knowledge/extract → returns ExtractionPrefill
 *   - RAG ingest (storing doc for retrieval) is OUT of Sub-phase A scope
 *
 * When offerId is null (inside BibliotecaPicker before creation), the panel is
 * shown in a "disabled" state explaining the feature is available after save.
 *
 * spec §Knowledge extraction · 03-arch-fe.md §5 KnowledgeSourcesPanel
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useProcessDocument } from "../../api/servicios";
import type { ExtractionPrefill } from "../../types/servicios.types";

const extractSchema = z.object({
  url: z.string().url("Ingresa una URL válida").min(1, "La URL es requerida"),
});
type ExtractFormValues = z.infer<typeof extractSchema>;

interface KnowledgeSourcesPanelProps {
  /** offerId is required to fire the extract endpoint. Null = pre-creation (disabled). */
  offerId: string | null;
  /** Called when prefill data arrives so the parent can apply it to the form. */
  onPrefill?: (prefill: ExtractionPrefill) => void;
}

export function KnowledgeSourcesPanel({
  offerId,
  onPrefill,
}: KnowledgeSourcesPanelProps) {
  const [prefillResult, setPrefillResult] = useState<ExtractionPrefill | null>(null);
  const { mutate: extract, isPending } = useProcessDocument(offerId ?? "__disabled__");

  const form = useForm<ExtractFormValues>({
    resolver: zodResolver(extractSchema),
    defaultValues: { url: "" },
  });

  const disabled = !offerId;

  if (disabled) {
    return (
      <Alert className="mt-3">
        <AlertDescription className="text-sm text-muted-foreground">
          Guarda el servicio primero para habilitar la extracción de conocimiento desde documentos.
        </AlertDescription>
      </Alert>
    );
  }

  const onSubmit = ({ url }: ExtractFormValues) => {
    extract(
      { url },
      {
        onSuccess: (result) => {
          setPrefillResult(result.prefill);
          onPrefill?.(result.prefill);
          form.reset();
        },
      },
    );
  };

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-border bg-card/50 p-4">
      <div className="flex items-center gap-2">
        <p className="text-sm font-medium">Extraer información desde documento</p>
        <Badge variant="secondary" className="text-xs">Sub-phase A</Badge>
      </div>

      <p className="text-xs text-muted-foreground">
        Pega la URL de un documento (ficha técnica, brochure, artículo científico)
        y Lisa extraerá automáticamente los campos del servicio.
      </p>

      <form onSubmit={form.handleSubmit(onSubmit)} className="flex gap-2">
        <div className="flex-1 space-y-1">
          <Label htmlFor="doc_url" className="sr-only">URL del documento</Label>
          <Input
            id="doc_url"
            {...form.register("url")}
            placeholder="https://ejemplo.com/ficha-tecnica.pdf"
            disabled={isPending}
          />
          {form.formState.errors.url && (
            <p className="text-xs text-destructive">{form.formState.errors.url.message}</p>
          )}
        </div>
        <Button type="submit" size="sm" disabled={isPending}>
          {isPending ? "Procesando…" : "Procesar con Lisa"}
        </Button>
      </form>

      {prefillResult && (
        <div className="rounded-md bg-muted/50 p-3 space-y-1.5">
          <p className="text-xs font-medium text-foreground">
            Lisa extrajo los siguientes campos:
          </p>
          {prefillResult.source_label && (
            <p className="text-xs text-muted-foreground">
              Fuente: {prefillResult.source_label}
            </p>
          )}
          {prefillResult.description_long && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              Descripción: {prefillResult.description_long}
            </p>
          )}
          {prefillResult.keywords.length > 0 && (
            <div className="flex gap-1 flex-wrap">
              {prefillResult.keywords.slice(0, 5).map((kw) => (
                <Badge key={kw} variant="outline" className="text-xs h-4">
                  {kw}
                </Badge>
              ))}
              {prefillResult.keywords.length > 5 && (
                <span className="text-xs text-muted-foreground">
                  +{prefillResult.keywords.length - 5} más
                </span>
              )}
            </div>
          )}
          <p className="text-xs text-muted-foreground">
            Los campos se han aplicado al formulario de Resumen.
          </p>
        </div>
      )}
    </div>
  );
}
