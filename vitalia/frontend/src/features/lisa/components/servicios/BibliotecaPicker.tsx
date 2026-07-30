// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
"use client";
/**
 * BibliotecaPicker.tsx — "Nuevo servicio" creation flow.
 *
 * Two paths:
 *   1. Seleccionar de biblioteca → search canonical templates → POST from-template → redirect
 *   2. Crear personalizado → minimal form → POST custom → redirect
 *
 * spec §Nuevo servicio · RN-16 (crear = editar), RN-25 (NOT a modal — renders in page)
 * spec_anchor: 03-arch-fe.md §5 + 01-spec.md §Nuevo
 *
 * FSD note: clinicType is NOT fetched cross-feature (FSD boundary forbids config→lisa).
 * User selects their clinic vertical via an inline Select so useBiblioteca can fire.
 */

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Group, GroupHeader } from "@luana/ui-kit";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useBiblioteca, useCreateServicioCustom, useCreateServicioFromTemplate } from "../../api/servicios";
import { KnowledgeSourcesPanel } from "./KnowledgeSourcesPanel";
import type { ServiceModality } from "../../types/servicios.types";
import { useTenantLocale } from "@/hooks/useTenantLocale";

// ── Clinic type options (mirror ClinicType enum in vitalia) ──────────────────────
const CLINIC_TYPES = [
  { value: "dental", label: "Odontología cosmética" },
  { value: "estetica", label: "Medicina estética" },
  { value: "oftalmologia", label: "Oftalmología refractiva" },
  { value: "psychology", label: "Psicología / Psiquiatría" },
  { value: "dermatologia", label: "Dermatología" },
  { value: "nutricion", label: "Nutrición clínica" },
  { value: "fisioterapia", label: "Fisioterapia" },
  { value: "capilar", label: "Medicina capilar" },
  { value: "fertilidad", label: "Fertilidad" },
  { value: "wellness", label: "Bienestar general" },
] as const;

// ── Custom service form schema ────────────────────────────────────────────────────
const customSchema = z.object({
  public_name: z.string().min(1, "El nombre es requerido"),
  price: z.number().min(0, "El precio no puede ser negativo"),
  modality: z.enum(["unica", "sesiones", "recurrente"] as const),
  category: z.string().nullable().optional(),
});
type CustomFormValues = z.infer<typeof customSchema>;

interface BibliotecaPickerProps {
  tenantId: string;
}

type FlowMode = "library" | "custom";

export function BibliotecaPicker({ tenantId }: BibliotecaPickerProps) {
  const router = useRouter();
  const locale = useTenantLocale();
  const [mode, setMode] = useState<FlowMode>("library");
  const [q, setQ] = useState("");
  const [clinicType, setClinicType] = useState<string | null>(null);
  const [showKnowledge, setShowKnowledge] = useState(false);

  const { data: biblioteca, isLoading: isSearching } = useBiblioteca(q, clinicType);
  const { mutateAsync: createFromTemplate, isPending: isFromTemplate } =
    useCreateServicioFromTemplate();
  const { mutateAsync: createCustom, isPending: isCustom } =
    useCreateServicioCustom();

  const form = useForm<CustomFormValues>({
    resolver: zodResolver(customSchema),
    defaultValues: { public_name: "", price: 0, modality: "unica", category: null },
  });

  const handleTemplateSelect = useCallback(
    async (canonicalRef: string) => {
      if (!clinicType) return;
      const detail = await createFromTemplate({
        canonical_service_ref: canonicalRef,
        clinic_type: clinicType,
      });
      router.push(`/${tenantId}/lisa/servicios/${detail.offer_id}/resumen`);
    },
    [createFromTemplate, clinicType, tenantId, router],
  );

  const onCustomSubmit = useCallback(
    async (values: CustomFormValues) => {
      const detail = await createCustom({
        public_name: values.public_name,
        price: values.price,
        currency: locale.currency,
        modality: values.modality as ServiceModality,
        category: values.category ?? null,
      });
      router.push(`/${tenantId}/lisa/servicios/${detail.offer_id}/resumen`);
    },
    [createCustom, tenantId, router, locale.currency],
  );

  const items = biblioteca?.items ?? [];

  return (
    <div className="max-w-2xl mx-auto p-5 md:p-8 space-y-6">
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-xl font-semibold">Nuevo servicio</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Elige si quieres basarte en nuestra biblioteca de servicios estándar
          o crearlo completamente personalizado.
        </p>
      </div>

      {/* ── Mode toggle ─────────────────────────────────────────────────────── */}
      <div className="flex gap-2">
        <Button
          variant={mode === "library" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("library")}
        >
          Desde la biblioteca
        </Button>
        <Button
          variant={mode === "custom" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("custom")}
        >
          Personalizado
        </Button>
      </div>

      {/* ── Library mode ────────────────────────────────────────────────────── */}
      {mode === "library" && (
        <Group>
          <GroupHeader title="Buscar en la biblioteca" />

          <div className="space-y-3">
            {/* Clinic type selector — required to enable the search */}
            <div className="space-y-1.5">
              <Label htmlFor="clinic_type_select">Especialidad de tu clínica</Label>
              <Select onValueChange={(v) => setClinicType(v)}>
                <SelectTrigger id="clinic_type_select">
                  <SelectValue placeholder="Selecciona tu especialidad…" />
                </SelectTrigger>
                <SelectContent>
                  {CLINIC_TYPES.map((ct) => (
                    <SelectItem key={ct.value} value={ct.value}>
                      {ct.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Search input */}
            <div className="space-y-1.5">
              <Label htmlFor="biblioteca_search">Buscar servicio</Label>
              <Input
                id="biblioteca_search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ej. Blanqueamiento dental, Botox…"
                disabled={!clinicType}
              />
            </div>
          </div>

          {/* Results */}
          {!clinicType && (
            <p className="text-xs text-muted-foreground">
              Selecciona tu especialidad para buscar en la biblioteca.
            </p>
          )}

          {clinicType && isSearching && (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-14 bg-muted rounded animate-pulse" />
              ))}
            </div>
          )}

          {clinicType && !isSearching && items.length === 0 && q.length > 0 && (
            <p className="text-sm text-muted-foreground py-2">
              No se encontraron servicios para &ldquo;{q}&rdquo;. Prueba otro término o crea uno personalizado.
            </p>
          )}

          {clinicType && !isSearching && items.length > 0 && (
            <ul className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {items.map((item) => (
                <li
                  key={item.canonical_ref}
                  className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/40 transition-colors"
                >
                  <div>
                    <p className="text-sm font-medium">{item.name}</p>
                    <div className="flex gap-1.5 mt-0.5 flex-wrap">
                      {item.category && (
                        <Badge variant="secondary" className="text-xs h-5">
                          {item.category}
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs h-5">
                        {item.modality}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isFromTemplate}
                    onClick={() => handleTemplateSelect(item.canonical_ref)}
                  >
                    Usar plantilla
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Group>
      )}

      {/* ── Custom mode ─────────────────────────────────────────────────────── */}
      {mode === "custom" && (
        <Group>
          <GroupHeader title="Crear servicio personalizado" />

          <form onSubmit={form.handleSubmit(onCustomSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="custom_name">Nombre del servicio</Label>
              <Input
                id="custom_name"
                {...form.register("public_name")}
                placeholder="Ej. Diseño de sonrisa"
              />
              {form.formState.errors.public_name && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.public_name.message}
                </p>
              )}
            </div>

            <div className="flex gap-3 [&>div]:flex-1">
              <div className="space-y-1.5">
                <Label htmlFor="custom_price">
                  Precio ({locale.currency})
                </Label>
                <Input
                  id="custom_price"
                  type="number"
                  min={0}
                  step={50}
                  {...form.register("price", { valueAsNumber: true })}
                />
                {form.formState.errors.price && (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.price.message}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="custom_modality">Modalidad</Label>
                <Controller
                  control={form.control}
                  name="modality"
                  render={({ field }) => (
                    <Select onValueChange={field.onChange} value={field.value}>
                      <SelectTrigger id="custom_modality">
                        <SelectValue placeholder="Modalidad…" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unica">Sesión única</SelectItem>
                        <SelectItem value="sesiones">Paquete de sesiones</SelectItem>
                        <SelectItem value="recurrente">Recurrente</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="custom_category">Especialidad / categoría (opcional)</Label>
              <Input
                id="custom_category"
                {...form.register("category")}
                placeholder="Ej. Odontología estética"
              />
            </div>

            {/* Knowledge sources panel (attach-doc extract) */}
            <div className="pt-2 border-t border-border">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowKnowledge((p) => !p)}
              >
                {showKnowledge ? "Ocultar" : "Adjuntar documento de conocimiento"}
              </Button>
              {showKnowledge && <KnowledgeSourcesPanel offerId={null} />}
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={isCustom}>
                {isCustom ? "Creando…" : "Crear y configurar"}
              </Button>
            </div>
          </form>
        </Group>
      )}
    </div>
  );
}
