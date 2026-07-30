// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * OverrideReasonDialog — Modal dialog for manual stage override with reason (D.12).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * spec_anchor: 01-spec.md § V1 D.12 + RN-4 + SC-1b/SC-2
 */
"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { STAGE_LABELS } from "../../types/embudo-schema";
import type { LeadFunnelStage } from "../../types/embudo.types";

// Separate schema to avoid Zod ZodType cast issues
const reasonSchema = z.object({
  reason: z
    .string()
    .min(1, "La razón es requerida")
    .max(500, "La razón debe tener máximo 500 caracteres"),
});

type ReasonData = z.infer<typeof reasonSchema>;

export interface OverrideReasonDialogProps {
  open: boolean;
  fromStage: LeadFunnelStage;
  toStage: LeadFunnelStage;
  onConfirm: (data: { reason: string; toStage: LeadFunnelStage }) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function OverrideReasonDialog({
  open,
  fromStage,
  toStage,
  onConfirm,
  onCancel,
  isLoading = false,
}: OverrideReasonDialogProps) {
  const form = useForm<ReasonData>({
    resolver: zodResolver(reasonSchema),
    defaultValues: { reason: "" },
  });

  useEffect(() => {
    if (open) form.reset({ reason: "" });
  }, [open, form]);

  const handleSubmit = form.handleSubmit((data) => {
    onConfirm({ reason: data.reason, toStage });
  });

  const fromLabel = STAGE_LABELS[fromStage] ?? fromStage;
  const toLabel = STAGE_LABELS[toStage] ?? toStage;
  const reasonValue = form.watch("reason");

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onCancel(); }}>
      <DialogContent className="max-w-md" aria-describedby="override-dialog-description" data-testid="override-reason-dialog">
        <DialogHeader>
          <DialogTitle>Mover de etapa</DialogTitle>
          <DialogDescription id="override-dialog-description">
            Estás moviendo este lead de <strong>{fromLabel}</strong> a{" "}
            <strong>{toLabel}</strong>. Adrián tomará nota para ajustar su próximo paso.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} id="override-reason-form" noValidate>
          <div className="flex flex-col gap-2 py-4">
            <Label htmlFor="override-reason-input">
              Razón del movimiento{" "}
              <span className="text-destructive" aria-hidden>*</span>
            </Label>
            <Textarea
              id="override-reason-input"
              data-testid="override-reason-input"
              placeholder="Ej: Ya coordiné la cita por teléfono"
              rows={3}
              aria-required="true"
              aria-describedby={form.formState.errors.reason ? "override-reason-error" : undefined}
              {...form.register("reason")}
            />
            {form.formState.errors.reason && (
              <p id="override-reason-error" role="alert" className="text-sm text-destructive">
                {form.formState.errors.reason.message}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              Adrián la incorporará y no repetirá lo ya resuelto.
            </p>
          </div>
        </form>

        <DialogFooter className="gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
            data-testid="override-cancel"
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="override-reason-form"
            disabled={isLoading || !reasonValue?.trim()}
            data-testid="override-confirm"
          >
            {isLoading ? "Moviendo…" : `Mover a ${toLabel}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
