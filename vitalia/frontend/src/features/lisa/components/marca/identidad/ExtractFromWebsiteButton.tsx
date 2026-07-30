// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * ExtractFromWebsiteButton.tsx — Visual extraction stub button (D4-extract).
 *
 * Per D4-extract architectural decision:
 * "Visual extraction pipeline = STUB local + botón disabled until /pm-luana
 *  accepts proposal 2026-05-26-lift-brand-visual-extraction-to-core.md."
 *
 * The button is permanently disabled with tooltip "Próximamente — extracción automática".
 * Clicking the disabled button does nothing (no navigation, no API call).
 *
 * Telemetry event lisa_marca_extract_stub_clicked emitted on click attempt
 * for future funnel analysis (not yet wired to backend — D4 stub).
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 A3 + CONTEXT-BRIEF § 2 D4-extract
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */


import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ExtractFromWebsiteButtonProps {
  className?: string;
}

/**
 * ExtractFromWebsiteButton — disabled stub per D4-extract.
 * Tooltip explains the feature is coming soon.
 * aria-disabled="true" for screen readers (the button is within a TooltipTrigger
 * which requires a non-disabled element to show the tooltip on hover).
 */
export function ExtractFromWebsiteButton({ className }: ExtractFromWebsiteButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {/* Wrapper span needed so disabled button still triggers tooltip on hover */}
        <span
          className={cn("inline-flex", className)}
          aria-describedby="extract-tooltip"
        >
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled
            aria-disabled="true"
            aria-label="Extraer colores y tipografía del sitio web (próximamente)"
            className="pointer-events-none gap-1.5 text-xs"
          >
            {/* Globe icon (inline SVG to avoid extra dep) */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            Extraer del sitio web
          </Button>
        </span>
      </TooltipTrigger>
      <TooltipContent id="extract-tooltip" side="bottom">
        <p className="text-xs">
          Próximamente — extracción automática de colores y tipografía desde tu sitio web.
        </p>
      </TooltipContent>
    </Tooltip>
  );
}

ExtractFromWebsiteButton.displayName = "ExtractFromWebsiteButton";
