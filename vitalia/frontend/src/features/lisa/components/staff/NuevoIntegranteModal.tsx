// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * NuevoIntegranteModal.tsx — Modal for creating a new doctor (NuevoIntegrante).
 *
 * Submit-driven (one exception to autosave rule — atomic create per spec).
 * RHF + Zod (doctorCreateSchema). Credential validation country-specific (SC-2).
 * On 422 → inline FormMessage + focus field.
 * On 409 → error toast "Ya existe un doctor con ese documento".
 * Focus trap + Escape closes (SC-10).
 *
 * Uses Shadcn Dialog (NOT Tabs) — focus trap built into Radix Dialog.
 * Microcopy per 01-spec.md § Microcopy (authoritative).
 * Spanish neutro LatAm — sin voseo.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § SC-2 + § SC-10 + § Microcopy
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { type MutableRefObject, type RefObject, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { ApiError } from "@/lib/api/fetchClient";
import {
  doctorCreateSchema,
  type DoctorCreateFormValues,
} from "../../types/staff-schema";
import { CREDENTIAL_LABELS } from "../../types/staff.types";
import {
  useCreateDoctor,
  mapDoctorCreateToPayload,
} from "../../api/staff";

interface NuevoIntegranteModalProps {
  open: boolean;
  onClose: () => void;
  /**
   * Ref to the trigger button so Radix Dialog can return focus to it on close.
   * Required for WCAG 2.4.3 focus-return (SC-10).
   * Radix Dialog only auto-returns focus when using the built-in DialogTrigger —
   * since we use a standalone Button + state, we must manage focus manually.
   */
  triggerRef?: RefObject<HTMLButtonElement | null>;
}

/**
 * NuevoIntegranteModal — atomic doctor creation modal.
 * On success: navigates to the new doctor's Perfil page.
 */
export function NuevoIntegranteModal({
  open,
  onClose,
  triggerRef,
}: NuevoIntegranteModalProps) {
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";
  const credentialRef = useRef<HTMLInputElement>(null);

  const form = useForm<DoctorCreateFormValues>({
    resolver: zodResolver(doctorCreateSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      dni: "",
      email: "",
      phone: "",
      specialty: "",
      credential: "",
      credentialCountry: "PE",
      active: true,
    },
  });

  const credentialCountry = form.watch("credentialCountry");
  const createDoctor = useCreateDoctor();

  // Reset form when modal closes.
  // Depend ONLY on the stable method references (RHF `reset` + react-query `reset`
  // are referentially stable), NOT the whole `form`/`createDoctor` objects.
  // The react-query mutation result is a fresh object every render, so depending on
  // it re-fired this effect on every render → reset() → re-render → infinite loop
  // ("Maximum update depth exceeded", regression 2026-06-06). See T-FIX-3 test.
  const { reset: resetForm } = form;
  const { reset: resetMutation } = createDoctor;
  useEffect(() => {
    if (!open) {
      resetForm();
      resetMutation();
    }
  }, [open, resetForm, resetMutation]);

  async function onSubmit(values: DoctorCreateFormValues) {
    try {
      const result = await createDoctor.mutateAsync(
        mapDoctorCreateToPayload(values),
      );
      toast.success("Integrante creado correctamente");
      onClose();
      // Navigate to new doctor's Perfil
      router.push(`/${tenantId}/lisa/staff/${result.id}/perfil`);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 422) {
          // Set credential field error + focus it (SC-2)
          const body = error.body as
            | { detail?: Array<{ loc: string[]; msg: string }> }
            | undefined;
          if (body?.detail) {
            for (const issue of body.detail) {
              const fieldPath = issue.loc[issue.loc.length - 1];
              if (fieldPath === "credential") {
                form.setError("credential", { message: issue.msg });
                setTimeout(() => credentialRef.current?.focus(), 50);
              }
            }
          } else {
            form.setError("credential", {
              message: "Credencial inválida",
            });
            setTimeout(() => credentialRef.current?.focus(), 50);
          }
          return;
        }
        if (error.status === 409) {
          toast.error("Ya existe un doctor con ese documento");
          return;
        }
      }
      toast.error("No pudimos guardar. Intenta de nuevo.");
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) {
          onClose();
          // WCAG 2.4.3: Return focus to the trigger button after modal closes.
          // Radix Dialog auto-returns focus only when using <DialogTrigger>;
          // since we manage open state externally, we must do it manually.
          // rAF ensures the dialog has unmounted before we attempt to focus.
          requestAnimationFrame(() => {
            triggerRef?.current?.focus();
          });
        }
      }}
    >
      <DialogContent
        className="sm:max-w-lg"
        data-testid="modal-nuevo-integrante"
        aria-describedby="nuevo-integrante-desc"
      >
        <DialogHeader>
          <DialogTitle>Nuevo integrante</DialogTitle>
          <DialogDescription id="nuevo-integrante-desc">
            Completa los datos del integrante del equipo.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-4"
            noValidate
          >
            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="firstName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nombre</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Ana"
                        {...field}
                        aria-required="true"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="lastName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Apellido</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="García"
                        {...field}
                        aria-required="true"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* DNI */}
            <FormField
              control={form.control}
              name="dni"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Documento de identidad</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="12345678"
                      {...field}
                      aria-required="true"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Email */}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Correo electrónico</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="doctora@clinica.com"
                      {...field}
                      aria-required="true"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Phone */}
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    Teléfono{" "}
                    <span className="text-muted-foreground text-xs">
                      (opcional)
                    </span>
                  </FormLabel>
                  <FormControl>
                    <Input placeholder="+51 999 888 777" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Specialty */}
            <FormField
              control={form.control}
              name="specialty"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    Especialidad{" "}
                    <span className="text-muted-foreground text-xs">
                      (opcional)
                    </span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Odontología cosmética"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Credential country + credential */}
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="credentialCountry"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>País de registro</FormLabel>
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <FormControl>
                        <SelectTrigger aria-label="País de registro">
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="PE">Perú (CMP)</SelectItem>
                        <SelectItem value="AR">Argentina</SelectItem>
                        <SelectItem value="MX">México</SelectItem>
                        <SelectItem value="CL">Chile</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="credential"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{CREDENTIAL_LABELS[credentialCountry]}</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        ref={(el) => {
                          field.ref(el);
                          (credentialRef as MutableRefObject<HTMLInputElement | null>).current = el;
                        }}
                        placeholder={
                          credentialCountry === "PE" ? "12345" : "AB-123"
                        }
                        aria-required="true"
                        aria-invalid={
                          !!form.formState.errors.credential
                        }
                        data-testid="input-credential"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                disabled={createDoctor.isPending}
              >
                Cancelar
              </Button>
              {/* Brand app-CTA gradient (cian→indigo #180D95). White text reads on the
                  indigo end; vivid brand treatment vs the flat navy. */}
              <Button
                type="submit"
                disabled={createDoctor.isPending}
                className="vt-bg-gradient-app-cta text-white hover:opacity-90 dark:text-white"
                data-testid="btn-crear-integrante"
              >
                {createDoctor.isPending ? "Creando…" : "Crear integrante"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

