// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ProactiveOutboundModal.tsx — Proactive outbound conversation initiator.
 *
 * Opened via useInboxStore.proactiveModalOpen.
 * Allows clinic operator to start a WhatsApp conversation from a template.
 *
 * Slice 1: 5 hardcoded HSM templates (per 05-guidelines.md § 9 open question #3).
 * Slice 2: Dynamic template list from API.
 *
 * Behavior:
 *   - Operator enters leadId (patient phone or ID)
 *   - Selects one of 5 HSM templates
 *   - Preview renders with auto-filled variables
 *   - Confirm triggers useProactiveOutbound mutation
 *   - ComplianceService validation runs server-side (channel guard per hipaa-lite.md)
 *
 * "use client" required: useState, useProactiveOutbound mutation, useInboxStore.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState } from "react";
import { cn } from "@/lib/cn";
import { useProactiveOutbound } from "../../api/use-proactive-outbound";
import { INBOX_COPY } from "../../lib/copy";

interface ProactiveOutboundModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Called when user cancels or modal is dismissed */
  onClose: () => void;
  /** Additional CSS classes */
  className?: string;
}

/** HSM Template definition (Slice 1 hardcoded set) */
interface HsmTemplate {
  id: string;
  name: string;
  /** Display label (Spanish neutro) */
  label: string;
  /** Template preview text with {var} placeholders */
  preview: string;
  /** Variable names expected */
  variables: string[];
}

/** Slice 1: 5 hardcoded WhatsApp HSM templates */
const HSM_TEMPLATES: HsmTemplate[] = [
  {
    id: "vitalia_bienvenida_v1",
    name: "Bienvenida inicial",
    label: "Bienvenida a la clínica",
    preview:
      "Hola {nombre}, te damos la bienvenida a Vitalia. Estamos aquí para ayudarte con tu salud y bienestar.",
    variables: ["nombre"],
  },
  {
    id: "vitalia_recordatorio_cita_v1",
    name: "Recordatorio de cita",
    label: "Recordatorio de cita próxima",
    preview:
      "Hola {nombre}, te recordamos tu cita el {fecha} a las {hora}. Si necesitas cambiarla, escríbenos aquí.",
    variables: ["nombre", "fecha", "hora"],
  },
  {
    id: "vitalia_seguimiento_postratamiento_v1",
    name: "Seguimiento post-tratamiento",
    label: "Seguimiento después del tratamiento",
    preview:
      "Hola {nombre}, queremos saber cómo te sientes después de tu tratamiento del {fecha}. ¿Tienes alguna pregunta?",
    variables: ["nombre", "fecha"],
  },
  {
    id: "vitalia_oferta_especial_v1",
    name: "Oferta especial",
    label: "Promoción personalizada",
    preview:
      "Hola {nombre}, tenemos una oferta especial para ti: {descripcion_oferta}. ¿Te interesa conocer más detalles?",
    variables: ["nombre", "descripcion_oferta"],
  },
  {
    id: "vitalia_reactivacion_v1",
    name: "Reactivación de paciente",
    label: "Reactivar contacto inactivo",
    preview:
      "Hola {nombre}, hace tiempo que no sabemos de ti. ¿Podemos ayudarte con algo relacionado a tu salud?",
    variables: ["nombre"],
  },
];

/** Renders template preview with variables highlighted */
function TemplatePreview({
  template,
  vars,
}: {
  template: HsmTemplate;
  vars: Record<string, string>;
}) {
  const text = template.preview.replace(
    /\{(\w+)\}/g,
    (_, key: string) => vars[key] ?? `{${key}}`,
  );

  return (
    <div
      className={cn(
        "rounded-xl rounded-tl-none px-4 py-3 text-sm leading-relaxed",
        "vt-bg-success-12 vt-text-foreground max-w-xs shadow-sm",
        "border vt-border-success-30",
      )}
      aria-label="Vista previa del mensaje"
      data-testid="template-preview-bubble"
    >
      {text}
    </div>
  );
}

/**
 * ProactiveOutboundModal — initiates proactive outbound WhatsApp conversation.
 * Uses native dialog semantics for accessibility.
 */
export function ProactiveOutboundModal({
  open,
  onClose,
  className,
}: ProactiveOutboundModalProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(
    null,
  );
  const [leadId, setLeadId] = useState("");
  const [templateVars, setTemplateVars] = useState<Record<string, string>>({});

  const { mutate, isPending, isSuccess } = useProactiveOutbound();

  const selectedTemplate =
    HSM_TEMPLATES.find((t) => t.id === selectedTemplateId) ?? null;
  const canSubmit = Boolean(leadId.trim() && selectedTemplateId && !isPending);

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);
    // Reset vars when template changes
    setTemplateVars({});
  };

  const handleVarChange = (varName: string, value: string) => {
    setTemplateVars((prev) => ({ ...prev, [varName]: value }));
  };

  const handleConfirm = () => {
    if (!canSubmit || !selectedTemplateId) return;

    mutate(
      {
        leadId: leadId.trim(),
        templateId: selectedTemplateId,
        templateVars,
        channel: "whatsapp",
      },
      {
        onSuccess: () => {
          onClose();
          setLeadId("");
          setSelectedTemplateId(null);
          setTemplateVars({});
        },
      },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape" && !isPending) onClose();
  };

  if (!open) return null;

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isPending) onClose();
      }}
      onKeyDown={handleKeyDown}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/40" aria-hidden="true" />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="proactive-modal-title"
        data-testid="proactive-outbound-modal"
        className={cn(
          "relative z-10 w-full max-w-lg rounded-xl border vt-border",
          "vt-bg-surface shadow-xl overflow-y-auto max-h-[90vh]",
          className,
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b vt-border">
          <h2
            id="proactive-modal-title"
            className="text-base font-semibold vt-text-foreground"
          >
            {INBOX_COPY.proactiveOutboundModal.title}
          </h2>
          <button
            onClick={onClose}
            disabled={isPending}
            aria-label="Cerrar"
            className={cn(
              "inline-flex items-center justify-center rounded-md p-1.5",
              "vt-text-muted hover:vt-text-foreground hover:vt-bg-muted/40",
              "transition-colors disabled:opacity-50",
              "focus-visible:outline focus-visible:outline-2",
              "focus-visible:outline-[var(--vitalia-cian)]",
            )}
          >
            <svg
              aria-hidden="true"
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-5">
          {/* Success state — vt-* semantic tokens per globals.css */}
          {isSuccess && (
            <div
              className="rounded-lg vt-bg-success-soft border vt-border-success-30 px-4 py-3 text-sm vt-text-success"
              role="status"
            >
              {INBOX_COPY.proactiveOutboundModal.sentSuccess}
            </div>
          )}

          {/* Lead ID input */}
          <div className="space-y-1.5">
            <label
              htmlFor="proactive-lead-id"
              className="text-sm font-medium vt-text-foreground"
            >
              {INBOX_COPY.proactiveOutboundModal.selectContact}
            </label>
            <input
              id="proactive-lead-id"
              data-testid="lead-id-input"
              type="text"
              value={leadId}
              onChange={(e) => setLeadId(e.target.value)}
              placeholder="ID del contacto o teléfono (+54911…)"
              disabled={isPending}
              className={cn(
                "w-full rounded-lg border vt-border px-3 py-2 text-sm",
                "vt-text-foreground vt-bg-surface",
                "placeholder:vt-text-muted",
                "focus-visible:outline focus-visible:outline-2",
                "focus-visible:outline-[var(--vitalia-cian)]",
                "disabled:opacity-50",
              )}
            />
          </div>

          {/* Template picker */}
          <div className="space-y-2">
            <p className="text-sm font-medium vt-text-foreground">
              {INBOX_COPY.proactiveOutboundModal.selectTemplate}
            </p>
            <ul
              className="space-y-2"
              role="radiogroup"
              aria-label={INBOX_COPY.proactiveOutboundModal.selectTemplate}
            >
              {HSM_TEMPLATES.map((template) => {
                const isSelected = selectedTemplateId === template.id;
                return (
                  <li key={template.id}>
                    <button
                      role="radio"
                      aria-checked={isSelected}
                      data-testid={`template-option-${template.id}`}
                      onClick={() => handleTemplateSelect(template.id)}
                      disabled={isPending}
                      className={cn(
                        "w-full text-left px-3 py-2.5 rounded-lg border transition-colors",
                        "text-sm",
                        "focus-visible:outline focus-visible:outline-2",
                        "focus-visible:outline-[var(--vitalia-cian)]",
                        isSelected
                          ? "border-[var(--vitalia-cian)] bg-[var(--vitalia-cian)]/8 vt-text-foreground"
                          : "vt-border vt-bg-surface vt-text-foreground hover:vt-bg-muted/40",
                        "disabled:opacity-50",
                      )}
                    >
                      <span className="font-medium block">
                        {template.label}
                      </span>
                      <span className="text-xs vt-text-muted mt-0.5 block leading-snug line-clamp-2">
                        {template.preview}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Variable inputs (auto-fill) — shown when template selected */}
          {selectedTemplate && selectedTemplate.variables.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium vt-text-faint uppercase tracking-wide">
                Variables
              </p>
              <div className="space-y-2">
                {selectedTemplate.variables.map((varName) => (
                  <div key={varName} className="flex items-center gap-2">
                    <label
                      htmlFor={`var-${varName}`}
                      className="text-xs vt-text-muted w-28 shrink-0"
                    >
                      {`{${varName}}`}
                    </label>
                    <input
                      id={`var-${varName}`}
                      data-testid={`template-var-${varName}`}
                      type="text"
                      value={templateVars[varName] ?? ""}
                      onChange={(e) => handleVarChange(varName, e.target.value)}
                      placeholder={`Valor para {${varName}}`}
                      disabled={isPending}
                      className={cn(
                        "flex-1 rounded-md border vt-border px-2.5 py-1.5 text-sm",
                        "vt-text-foreground vt-bg-surface",
                        "placeholder:vt-text-muted",
                        "focus-visible:outline focus-visible:outline-2",
                        "focus-visible:outline-[var(--vitalia-cian)]",
                        "disabled:opacity-50",
                      )}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* WA Preview */}
          {selectedTemplate && (
            <div className="space-y-2">
              <p className="text-sm font-medium vt-text-foreground">
                {INBOX_COPY.proactiveOutboundModal.preview}
              </p>
              <div
                className={cn("rounded-xl p-4", "vt-bg-muted")}
                data-testid="wa-preview-container"
                aria-label={INBOX_COPY.proactiveOutboundModal.preview}
              >
                <TemplatePreview
                  template={selectedTemplate}
                  vars={templateVars}
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer — actions */}
        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t vt-border">
          <button
            data-testid="proactive-cancel-btn"
            onClick={onClose}
            disabled={isPending}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium",
              "vt-text-muted vt-bg-muted/40 hover:vt-bg-muted/60",
              "transition-colors disabled:opacity-50",
            )}
          >
            {INBOX_COPY.proactiveOutboundModal.cancelCta}
          </button>

          <button
            data-testid="proactive-confirm-btn"
            onClick={handleConfirm}
            disabled={!canSubmit}
            aria-busy={isPending}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium",
              "text-white bg-[var(--vitalia-cian)] hover:opacity-90",
              "transition-opacity disabled:opacity-40 disabled:cursor-not-allowed",
            )}
          >
            {isPending
              ? "Enviando…"
              : INBOX_COPY.proactiveOutboundModal.confirmCta}
          </button>
        </div>
      </div>
    </div>
  );
}
