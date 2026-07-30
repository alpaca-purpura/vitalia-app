// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * SocialMediaLinksEditor.tsx — 5 social media rows with brand-colored icons.
 *
 * Social channels per 03-arch.md § 4.3:
 *   1. Instagram (handle, gradient icon)
 *   2. TikTok (handle, black icon)
 *   3. Facebook (page URL, blue icon)
 *   4. Google Business (URL, Google blue icon)
 *   5. WhatsApp Business (number, green icon)
 *
 * Autosaves on change via onScheduleAutosave prop (600ms debounce in parent).
 * "+ Agregar otra red" button is present but disabled (future story).
 *
 * RHF + Zod: socialMediaSchema fields.
 * Spanish neutro LatAm — no voseo.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 + mockups/presencia-section.html § social-rows
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { socialMediaSchema } from "../../../types/marca/presence-schema";
import type { SocialMediaFormValues } from "../../../types/marca/presence-schema";
import type { ContactPatchPayload } from "../../../hooks/useContactAutosave";

// ── Social channel configs ─────────────────────────────────────────────────────

interface SocialChannel {
  id: keyof SocialMediaFormValues;
  label: string;
  placeholder: string;
  hint: string;
  /** Rendered as a small colored dot/icon next to the label */
  colorClass: string;
  ariaLabel: string;
}

const SOCIAL_CHANNELS: SocialChannel[] = [
  {
    id: "instagram",
    label: "Instagram",
    placeholder: "@tuclínica",
    hint: "Ingresa el nombre de usuario sin @",
    colorClass: "social-instagram",
    ariaLabel: "Usuario de Instagram",
  },
  {
    id: "tiktok",
    label: "TikTok",
    placeholder: "@tuclínica",
    hint: "Ingresa el nombre de usuario sin @",
    colorClass: "social-tiktok",
    ariaLabel: "Usuario de TikTok",
  },
  {
    id: "facebook",
    label: "Facebook",
    placeholder: "@TuClínicaFacebook",
    hint: "Nombre de página o URL de Facebook",
    colorClass: "social-facebook",
    ariaLabel: "Página de Facebook",
  },
  {
    id: "google_business",
    label: "Google Business",
    placeholder: "https://maps.app.goo.gl/...",
    hint: "URL de tu perfil de Google Business",
    colorClass: "social-google",
    ariaLabel: "URL de Google Business",
  },
  {
    id: "whatsapp",
    label: "WhatsApp Business",
    placeholder: "+51 999 000 000",
    hint: "Número con código de país (ej: +51...)",
    colorClass: "social-whatsapp",
    ariaLabel: "Número de WhatsApp Business",
  },
];

// ── Social icon component ──────────────────────────────────────────────────────

/** Maps social channel id to inline SVG icon. */
function SocialIcon({ channelId }: { channelId: keyof SocialMediaFormValues }) {
  switch (channelId) {
    case "instagram":
      return (
        <span
          aria-hidden="true"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
          style={{
            background: "var(--social-instagram-gradient)",
          }}
        >
          <svg className="h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
          </svg>
        </span>
      );
    case "tiktok":
      return (
        <span
          aria-hidden="true"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
          style={{ backgroundColor: "var(--social-tiktok-bg)" }}
        >
          <svg className="h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.78 1.52V6.76a4.85 4.85 0 01-1.01-.07z" />
          </svg>
        </span>
      );
    case "facebook":
      return (
        <span
          aria-hidden="true"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
          style={{ backgroundColor: "var(--social-facebook-bg)" }}
        >
          <svg className="h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
        </span>
      );
    case "google_business":
      return (
        <span
          aria-hidden="true"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
          style={{ backgroundColor: "var(--social-google-bg)" }}
        >
          <svg className="h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z" />
          </svg>
        </span>
      );
    case "whatsapp":
      return (
        <span
          aria-hidden="true"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
          style={{ backgroundColor: "var(--social-whatsapp-bg)" }}
        >
          <svg className="h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
          </svg>
        </span>
      );
    default:
      return null;
  }
}

// ── Props ──────────────────────────────────────────────────────────────────────

export interface SocialMediaLinksEditorProps {
  /** Current social values from server. */
  instagram?: string | null;
  tiktok?: string | null;
  facebook?: string | null;
  googleBusiness?: string | null;
  whatsapp?: string | null;
  /** Called on every change (debounce handled by parent hook). */
  onScheduleAutosave: (values: ContactPatchPayload) => void;
  className?: string;
}

// ── SocialRow type ─────────────────────────────────────────────────────────────

type SocialFormValues = SocialMediaFormValues;

// ── Component ──────────────────────────────────────────────────────────────────

/**
 * SocialMediaLinksEditor — 5 social rows (Instagram, TikTok, Facebook, Google Business,
 * WhatsApp Business) with brand icons + autosave on change.
 */
export function SocialMediaLinksEditor({
  instagram,
  tiktok,
  facebook,
  googleBusiness,
  whatsapp,
  onScheduleAutosave,
  className,
}: SocialMediaLinksEditorProps) {
  const form = useForm<SocialFormValues>({
    resolver: zodResolver(socialMediaSchema),
    defaultValues: {
      instagram: instagram ?? "",
      tiktok: tiktok ?? "",
      facebook: facebook ?? "",
      google_business: googleBusiness ?? "",
      whatsapp: whatsapp ?? "",
    },
  });

  // Hydrate from server data when it arrives
  useEffect(() => {
    form.reset({
      instagram: instagram ?? "",
      tiktok: tiktok ?? "",
      facebook: facebook ?? "",
      google_business: googleBusiness ?? "",
      whatsapp: whatsapp ?? "",
    });
  }, [instagram, tiktok, facebook, googleBusiness, whatsapp, form]);

  const handleFieldChange = (fieldId: keyof SocialFormValues, value: string) => {
    // Map form field to API payload key
    const apiKeyMap: Record<keyof SocialFormValues, keyof ContactPatchPayload> = {
      instagram: "instagramHandle",
      tiktok: "tiktokHandle",
      facebook: "facebookPage",
      google_business: "googleBusinessUrl",
      whatsapp: "whatsappBusiness",
    };
    onScheduleAutosave({ [apiKeyMap[fieldId]]: value || undefined });
  };

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-4 shadow-sm",
        className,
      )}
    >
      <Form {...form}>
        <div className="flex flex-col gap-4">
          {/* Card header */}
          <h3 className="text-sm font-semibold text-foreground">Redes sociales</h3>

          {/* Social rows */}
          <div className="flex flex-col gap-3">
            {SOCIAL_CHANNELS.map((channel) => (
              <FormField
                key={channel.id}
                control={form.control}
                name={channel.id}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="sr-only">{channel.label}</FormLabel>
                    <div className="flex items-start gap-3">
                      {/* Social icon */}
                      <div className="pt-2">
                        <SocialIcon channelId={channel.id} />
                      </div>

                      {/* Input + hint */}
                      <div className="flex min-w-0 flex-1 flex-col gap-1">
                        <span className="text-xs font-medium text-foreground">{channel.label}</span>
                        <FormControl>
                          <Input
                            {...field}
                            placeholder={channel.placeholder}
                            aria-label={channel.ariaLabel}
                            autoComplete="off"
                            onChange={(e) => {
                              field.onChange(e);
                              handleFieldChange(channel.id, e.target.value);
                            }}
                          />
                        </FormControl>
                        <FormMessage />
                        <p className="text-xs text-muted-foreground">{channel.hint}</p>
                      </div>
                    </div>
                  </FormItem>
                )}
              />
            ))}
          </div>

          {/* + Agregar otra red — disabled (future story) */}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled
            aria-disabled="true"
            aria-label="Agregar otra red social (próximamente)"
            className="w-fit text-xs text-muted-foreground"
          >
            <svg
              aria-hidden="true"
              className="mr-1 h-3.5 w-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            Agregar otra red
          </Button>
        </div>
      </Form>
    </div>
  );
}

SocialMediaLinksEditor.displayName = "SocialMediaLinksEditor";
