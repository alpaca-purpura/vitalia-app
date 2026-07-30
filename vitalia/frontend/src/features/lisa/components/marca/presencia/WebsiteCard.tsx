// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * WebsiteCard.tsx — Website URL input with connection status indicator.
 *
 * Fields: websiteUrl (URL input).
 * Displays conn-status: ✓ OK (green) | error (red) | missing (muted).
 * Autosaves on change via scheduleAutosave prop (600ms debounce in parent).
 *
 * RHF + Zod: presenceSchema.website_url (optionalUrl validator).
 * Spanish neutro LatAm — no voseo.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 + mockups/presencia-section.html § website-card
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import type { ContactPatchPayload } from "../../../hooks/useContactAutosave";

// ── Schema ─────────────────────────────────────────────────────────────────────

const websiteSchema = z.object({
  websiteUrl: z
    .string()
    .url("Ingresa una URL válida (ej: https://tuclínica.com)")
    .optional()
    .or(z.literal("")),
});

type WebsiteFormValues = z.infer<typeof websiteSchema>;

// ── Connection status helpers ──────────────────────────────────────────────────

type ConnStatus = "ok" | "error" | "missing";

function getConnStatus(url: string | undefined | null): ConnStatus {
  if (!url) return "missing";
  try {
    new URL(url);
    return "ok";
  } catch {
    return "error";
  }
}

const CONN_STYLES: Record<ConnStatus, { icon: string; label: string; className: string }> = {
  ok: {
    icon: "✓",
    label: "URL válida",
    className: "text-emerald-600 dark:text-emerald-400",
  },
  error: {
    icon: "✗",
    label: "URL inválida",
    className: "text-destructive",
  },
  missing: {
    icon: "—",
    label: "Sin URL",
    className: "text-muted-foreground",
  },
};

// ── Props ──────────────────────────────────────────────────────────────────────

export interface WebsiteCardProps {
  /** Current value from server. */
  websiteUrl?: string | null;
  /** Called on every change (debounce handled by parent hook). */
  onScheduleAutosave: (values: ContactPatchPayload) => void;
  className?: string;
}

// ── Component ──────────────────────────────────────────────────────────────────

/**
 * WebsiteCard — URL input with real-time format validation and conn-status indicator.
 */
export function WebsiteCard({ websiteUrl, onScheduleAutosave, className }: WebsiteCardProps) {
  const form = useForm<WebsiteFormValues>({
    resolver: zodResolver(websiteSchema),
    defaultValues: { websiteUrl: websiteUrl ?? "" },
  });

  // Hydrate from server data when it arrives
  useEffect(() => {
    form.reset({ websiteUrl: websiteUrl ?? "" });
  }, [websiteUrl, form]);

  const currentUrl = form.watch("websiteUrl");
  const connStatus = getConnStatus(currentUrl);
  const connInfo = CONN_STYLES[connStatus];

  const handleChange = (value: string) => {
    onScheduleAutosave({ websiteUrl: value || undefined } as ContactPatchPayload);
  };

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-4 shadow-sm",
        className,
      )}
    >
      <Form {...form}>
        <div className="flex flex-col gap-3">
          {/* Card header */}
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Sitio web</h3>
            {/* Connection status badge */}
            <span
              aria-label={`Estado: ${connInfo.label}`}
              className={cn("flex items-center gap-1 text-xs font-medium", connInfo.className)}
            >
              <span aria-hidden="true">{connInfo.icon}</span>
              <span>{connInfo.label}</span>
            </span>
          </div>

          {/* URL field */}
          <FormField
            control={form.control}
            name="websiteUrl"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs text-muted-foreground">
                  URL del sitio web
                </FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    type="url"
                    placeholder="https://tuclínica.com"
                    aria-label="URL del sitio web"
                    autoComplete="url"
                    onChange={(e) => {
                      field.onChange(e);
                      handleChange(e.target.value);
                    }}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Hint */}
          <p className="text-xs text-muted-foreground">
            Incluye el protocolo https:// para asegurar la conexión.
          </p>
        </div>
      </Form>
    </div>
  );
}

WebsiteCard.displayName = "WebsiteCard";
