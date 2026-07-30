// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * LogoMark — brand logo atom for Vitalia TopBar
 * F1-S2 vitalia-fase1-topbar-global — T-2
 *
 * Server Component (no "use client").
 * Renders a Next.js <Image> pair for CSS-based dark mode swap (SSR-safe).
 * No useEffect / no JS viewport detection.
 *
 * Variants:
 *   full — horizontal logo (3:1 aspect), light + dark PNGs
 *   mark — square icon mark (1:1 aspect), single PNG for both modes
 *
 * Sizes: sm (24px height) | md (32px height, default) | lg (40px height)
 * Width is auto-derived from aspect ratio to preserve PNG shape.
 *
 * Accessibility: <a> wrapper carries aria-label="Vitalia inicio";
 *   images are decorative (alt="").
 *
 * 03-arch.md § 2.2 — implementation verbatim.
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — UI shell component, zero PHI.
 *
 * downstream-regression-na: brand-local shell atom; no cross-brand consumers
 */

import Image from "next/image";
import Link from "next/link";

export type LogoMarkSize = "sm" | "md" | "lg";
export type LogoMarkVariant = "full" | "mark";

export interface LogoMarkProps {
  /** Size variant controls height; width is auto from aspect ratio */
  size?: LogoMarkSize;
  /** full = horizontal logo, mark = square icon */
  variant?: LogoMarkVariant;
  /** Additional CSS classes for the wrapper <a> */
  className?: string;
}

/** Height in px per size variant */
const heights: Record<LogoMarkSize, number> = {
  sm: 24,
  md: 32,
  lg: 40,
};

/** Approximate aspect ratio (width / height) per logo variant */
const aspectRatios: Record<LogoMarkVariant, number> = {
  full: 3,
  mark: 1,
};

/** Source paths per variant and mode */
const assetSrc = {
  full: {
    light: "/brand/vitalia-logo.png",
    dark: "/brand/vitalia-logo-dark.png",
  },
  mark: {
    light: "/brand/vitalia-ico.png",
    dark: "/brand/vitalia-ico.png", // same PNG for both modes
  },
} as const;

/**
 * LogoMark — brand logo atom.
 * Server Component: no state, no effects, pure markup.
 */
export function LogoMark({
  size = "md",
  variant = "full",
  className,
}: LogoMarkProps) {
  const h = heights[size];
  const w = Math.round(h * aspectRatios[variant]);
  const lightSrc = assetSrc[variant].light;
  const darkSrc = assetSrc[variant].dark;
  const sameSrc = lightSrc === darkSrc;

  return (
    <Link
      href="/"
      aria-label="Vitalia inicio"
      className={className}
      data-testid="logo-mark"
    >
      {sameSrc ? (
        // mark variant: single image (same PNG for both modes)
        <Image
          src={lightSrc}
          alt=""
          height={h}
          width={w}
          priority
          draggable={false}
          data-testid="logo-mark-img"
        />
      ) : (
        // full variant: two images, CSS dark mode swap
        <>
          {/* Light mode image — hidden when dark */}
          <Image
            src={lightSrc}
            alt=""
            height={h}
            width={w}
            priority
            draggable={false}
            className="block dark:hidden"
            data-testid="logo-mark-light"
          />
          {/* Dark mode image — hidden when light */}
          <Image
            src={darkSrc}
            alt=""
            height={h}
            width={w}
            priority
            draggable={false}
            className="hidden dark:block"
            data-testid="logo-mark-dark"
          />
        </>
      )}
    </Link>
  );
}
