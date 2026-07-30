// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * ColorTriadEditor.tsx — 3 color swatches editor (primario, accent, fondo).
 *
 * Per 06-tickets.yaml T-5 A4: "uses CSS vars (no hex literals in className)".
 * Color values are stored as form state (hex strings) but UI tokens use
 * CSS variables (--primary, --accent, etc.).
 *
 * Includes:
 *   - 3 inline color pickers with native <input type="color"> + hex text input
 *   - WCAG contrast warning per primary/accent pair (AA 4.5:1 target)
 *   - ExtractFromWebsiteButton (D4-extract stub disabled)
 *
 * Note: Radix Popover is NOT installed. Color inputs render inline (expanded)
 * using native <input type="color"> + hex text input in a disclosure pattern.
 *
 * Accessibility:
 *   - Color swatch buttons have aria-label with hex value
 *   - Contrast warning has role="alert"
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 A4
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */


import { useCallback, useId, useState } from "react";
import { cn } from "@/lib/utils";
import { ExtractFromWebsiteButton } from "./ExtractFromWebsiteButton";

// ── WCAG contrast ratio (simplified luminance) ─────────────────────────────────

function hexToRgb(hex: string): [number, number, number] | null {
  const clean = hex.replace("#", "");
  if (clean.length !== 6) return null;
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  if (isNaN(r) || isNaN(g) || isNaN(b)) return null;
  return [r, g, b];
}

function relativeLuminance(r: number, g: number, b: number): number {
  const c = [r, g, b].map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}

function contrastRatio(hex1: string, hex2: string): number | null {
  const rgb1 = hexToRgb(hex1);
  const rgb2 = hexToRgb(hex2);
  if (!rgb1 || !rgb2) return null;
  const L1 = relativeLuminance(...rgb1);
  const L2 = relativeLuminance(...rgb2);
  const lighter = Math.max(L1, L2);
  const darker = Math.min(L1, L2);
  return (lighter + 0.05) / (darker + 0.05);
}

// ── Color Swatch Inline ────────────────────────────────────────────────────────

interface SwatchInlineProps {
  label: string;
  idPrefix: string;
  value: string | undefined;
  onChange: (hex: string) => void;
}

/** Fallback swatch color when no value is set — matches border color (CSS var not available inline). */
const SWATCH_FALLBACK = "var(--border, currentColor)";

function SwatchInline({ label, idPrefix, value, onChange }: SwatchInlineProps) {
  const [inputText, setInputText] = useState(value ?? "");

  const handleNativeColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setInputText(v);
    onChange(v);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const v = raw.startsWith("#") ? raw : `#${raw}`;
    setInputText(raw);
    if (/^#[0-9a-fA-F]{6}$/.test(v)) {
      onChange(v);
    }
  };

  // Use the current value or a safe fallback; native color input always has a value
  const nativeColorValue = value && /^#[0-9a-fA-F]{6}$/.test(value) ? value : undefined;

  return (
    <div className="flex items-center gap-3">
      {/* Swatch + native color picker */}
      <div className="relative">
        {nativeColorValue ? (
          <input
            id={`${idPrefix}-native`}
            type="color"
            value={nativeColorValue}
            onChange={handleNativeColorChange}
            aria-label={`${label}: selector de color`}
            className="sr-only"
          />
        ) : (
          <input
            id={`${idPrefix}-native`}
            type="color"
            onChange={handleNativeColorChange}
            aria-label={`${label}: selector de color`}
            className="sr-only"
          />
        )}
        <label
          htmlFor={`${idPrefix}-native`}
          aria-label={`${label}: ${value ?? "sin valor"}`}
          className={cn(
            "flex h-9 w-9 cursor-pointer shrink-0 rounded-md border border-border transition-transform",
            "hover:scale-105 focus-within:ring-2 focus-within:ring-ring",
            !value && "bg-muted",
          )}
          style={value ? { backgroundColor: value } : { backgroundColor: SWATCH_FALLBACK }}
        />
      </div>

      {/* Label + hex text input */}
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-xs font-medium text-foreground">{label}</span>
        <div className="flex items-center gap-1">
          <span className="font-mono text-[11px] text-muted-foreground">#</span>
          <input
            id={`${idPrefix}-hex`}
            type="text"
            value={inputText.replace("#", "")}
            onChange={handleTextChange}
            maxLength={6}
            placeholder="RRGGBB"
            aria-label={`${label}: valor hexadecimal`}
            className={cn(
              "w-[72px] rounded border border-border bg-background px-1.5 py-0.5",
              "font-mono text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            )}
          />
        </div>
      </div>
    </div>
  );
}

// ── ColorTriadEditor ───────────────────────────────────────────────────────────

export interface ColorTriadEditorProps {
  primaryColor?: string;
  accentColor?: string;
  backgroundColor?: string;
  onChangePrimary?: (hex: string) => void;
  onChangeAccent?: (hex: string) => void;
  onChangeBackground?: (hex: string) => void;
  className?: string;
}

/**
 * ColorTriadEditor — 3 swatches: primario, accent, fondo + contrast warning.
 * Uses CSS variables for UI theming (no hex literals in className).
 */
export function ColorTriadEditor({
  primaryColor,
  accentColor,
  backgroundColor,
  onChangePrimary,
  onChangeAccent,
  onChangeBackground,
  className,
}: ColorTriadEditorProps) {
  const uid = useId();
  const [localPrimary, setLocalPrimary] = useState(primaryColor ?? "");
  const [localAccent, setLocalAccent] = useState(accentColor ?? "");
  const [localBg, setLocalBg] = useState(backgroundColor ?? "");

  const handlePrimary = useCallback(
    (hex: string) => {
      setLocalPrimary(hex);
      onChangePrimary?.(hex);
    },
    [onChangePrimary],
  );

  const handleAccent = useCallback(
    (hex: string) => {
      setLocalAccent(hex);
      onChangeAccent?.(hex);
    },
    [onChangeAccent],
  );

  const handleBg = useCallback(
    (hex: string) => {
      setLocalBg(hex);
      onChangeBackground?.(hex);
    },
    [onChangeBackground],
  );

  // WCAG contrast check: primary on background
  const primaryOnBgContrast = contrastRatio(localPrimary, localBg);
  const hasContrastWarning =
    primaryOnBgContrast !== null && primaryOnBgContrast < 4.5;

  return (
    <section
      aria-label="Paleta de colores de la marca"
      className={cn("rounded-lg border border-border bg-card p-4 flex flex-col gap-4", className)}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            Paleta de colores
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Define los colores principales de tu identidad visual.
          </p>
        </div>
        <ExtractFromWebsiteButton />
      </div>

      <div className="flex flex-col gap-4">
        <SwatchInline
          label="Color primario"
          idPrefix={`${uid}-primary`}
          value={localPrimary || undefined}
          onChange={handlePrimary}
        />
        <SwatchInline
          label="Color accent"
          idPrefix={`${uid}-accent`}
          value={localAccent || undefined}
          onChange={handleAccent}
        />
        <SwatchInline
          label="Color de fondo"
          idPrefix={`${uid}-bg`}
          value={localBg || undefined}
          onChange={handleBg}
        />
      </div>

      {/* WCAG contrast warning */}
      {hasContrastWarning && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 p-2.5 dark:border-amber-800 dark:bg-amber-950/30"
        >
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
            className="mt-0.5 shrink-0 text-amber-600 dark:text-amber-400"
            aria-hidden="true"
          >
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <p className="text-xs text-amber-700 dark:text-amber-300">
            El contraste entre el color primario y el fondo puede dificultar la lectura
            (relación {primaryOnBgContrast?.toFixed(1)}:1 · mínimo WCAG AA 4.5:1).
          </p>
        </div>
      )}
    </section>
  );
}

ColorTriadEditor.displayName = "ColorTriadEditor";
