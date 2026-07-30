// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * NewLeadPage — ruta-hoja /adrian/embudo/nuevo (V5, spec v3).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * RHF+Zod form for creating a new lead:
 *   Nombre* · Canal* · Teléfono / Email (≥1) · Etapa inicial ·
 *   Servicio de interés · Etiquetas · Notas
 *
 * EntitySubNavBar: [‹ Embudo] · Nuevo lead (no leaf tabs — it's workspace mode).
 *
 * Submit → POST /crm/leads → redirect /embudo?view=kanban&highlight={leadId}
 * Cancelar → back to /embudo (no create).
 *
 * spec_anchor: 01-spec.md § V5 D.10 + SC-nuevo
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { EntitySubNavBar } from "@luana/ui-kit";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCreateLead } from "../../../api/create-lead";
import {
  newLeadSchema,
  CHANNEL_OPTIONS,
  STAGE_LABELS,
  BOARD_HOT_STAGES,
  type NewLeadFormData,
} from "../../../types/embudo-schema";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface NewLeadPageProps {
  tenantId: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * NewLeadPage — creates a lead via RHF+Zod form.
 *
 * After successful submit, redirects to /embudo?view=kanban&highlight={id}.
 * Cancelar navigates back to /embudo without creating.
 */
export function NewLeadPage({ tenantId }: NewLeadPageProps) {
  const router = useRouter();
  const { mutateAsync, isPending } = useCreateLead();

  // RHF + zodResolver type friction: schema has defaulted fields (stage/tags/notes),
  // so the resolver INPUT type makes them optional while NewLeadFormData (output) requires
  // them — the two ResolverOptions generics don't unify. `any` here is the documented escape.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const form = useForm<any>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(newLeadSchema) as any,
    defaultValues: {
      stage: "interesado",
      tags: [],
      notes: "",
    },
  });
  const { register, handleSubmit, setValue, formState: { errors } } = form;

  const handleCancel = () => {
    router.push(`/${tenantId}/adrian/embudo`);
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const onSubmit = async (data: any) => {
    try {
      const created = await mutateAsync({
        name: data.name,
        channel: data.channel,
        phone: data.phone ?? null,
        email: data.email ?? null,
        stage: data.stage,
        serviceInterest: data.serviceInterest ?? null,
        tags: data.tags,
        notes: data.notes,
      });
      toast.success("Lead creado. Redirigiendo al tablero…");
      router.push(
        `/${tenantId}/adrian/embudo?view=kanban&highlight=${created.id}`,
      );
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Error al crear el lead";
      toast.error(message);
    }
  };

  return (
    <div className="flex flex-col min-h-0">
      {/* EntitySubNavBar workspace mode — no leaf tabs for /nuevo */}
      <EntitySubNavBar
        rootHref={`/${tenantId}/adrian/embudo`}
        rootLabel="Embudo"
        entity={{ id: "nuevo", name: "Nuevo lead" }}
        leaves={[]}
        activeLeaf={null}
      />

      {/* Form */}
      <div className="flex-1 overflow-auto p-4 max-w-xl">
        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          aria-label="Formulario de nuevo lead"
        >
          <div className="flex flex-col gap-4">
            {/* Nombre */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">
                Nombre <span aria-hidden="true" className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                placeholder="Ej. María Torres"
                aria-required="true"
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? "name-error" : undefined}
                {...register("name")}
              />
              {errors.name && (
                <p
                  id="name-error"
                  role="alert"
                  className="text-xs text-destructive"
                >
                  {String(errors.name?.message ?? "")}
                </p>
              )}
            </div>

            {/* Canal */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="channel">
                Canal <span aria-hidden="true" className="text-destructive">*</span>
              </Label>
              <Select
                onValueChange={(val) => setValue("channel", val, { shouldValidate: true })}
                defaultValue=""
              >
                <SelectTrigger id="channel" data-testid="lead-channel-select" aria-required="true" aria-invalid={!!errors.channel}>
                  <SelectValue placeholder="Selecciona un canal" />
                </SelectTrigger>
                <SelectContent>
                  {CHANNEL_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.channel && (
                <p role="alert" className="text-xs text-destructive">
                  {String(errors.channel?.message ?? "")}
                </p>
              )}
            </div>

            {/* Teléfono */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="phone">
                Teléfono{" "}
                <span className="text-xs text-muted-foreground font-normal">
                  (al menos teléfono o correo)
                </span>
              </Label>
              <Input
                id="phone"
                type="tel"
                placeholder="Ej. +51 999 111 222"
                aria-describedby={errors.phone ? "contact-error" : undefined}
                {...register("phone")}
              />
            </div>

            {/* Correo */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Correo electrónico</Label>
              <Input
                id="email"
                type="email"
                placeholder="Ej. maria@ejemplo.com"
                {...register("email")}
              />
              {errors.phone && (
                <p
                  id="contact-error"
                  role="alert"
                  className="text-xs text-destructive"
                >
                  {String(errors.phone?.message ?? "")}
                </p>
              )}
              {errors.email && (
                <p role="alert" className="text-xs text-destructive">
                  {String(errors.email?.message ?? "")}
                </p>
              )}
            </div>

            {/* Etapa inicial */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="stage">Etapa inicial</Label>
              <Select
                defaultValue="interesado"
                onValueChange={(val) =>
                  setValue("stage", val as NewLeadFormData["stage"], { shouldValidate: true })
                }
              >
                <SelectTrigger id="stage">
                  <SelectValue placeholder="Interesado" />
                </SelectTrigger>
                <SelectContent>
                  {BOARD_HOT_STAGES.filter(
                    (s) => s !== "reservado",
                  ).map((stage) => (
                    <SelectItem key={stage} value={stage}>
                      {STAGE_LABELS[stage]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Servicio de interés */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="serviceInterest">Servicio de interés</Label>
              <Input
                id="serviceInterest"
                placeholder="Ej. Ortodoncia, Blanqueamiento…"
                {...register("serviceInterest")}
              />
            </div>

            {/* Notas */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="notes">Notas</Label>
              <Textarea
                id="notes"
                placeholder="Información adicional sobre el lead…"
                rows={3}
                {...register("notes")}
              />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 pt-2">
              <Button type="submit" disabled={isPending} aria-busy={isPending}>
                {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isPending ? "Creando lead…" : "Crear lead"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={handleCancel}
                disabled={isPending}
              >
                Cancelar
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
