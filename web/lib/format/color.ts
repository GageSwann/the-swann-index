import type { CSSProperties } from "react"

import type { TeamRef } from "@/lib/api/types"

// Team colors are accents only and must stand out from the background (doc 06).
// Card backgrounds per theme (app/globals.css) and the fallback neutral.
const CARD = { dark: "#162532", light: "#ffffff" }
const NEUTRAL = { dark: "#93a6b5", light: "#4e6170" }
const MIN_CONTRAST = 2 // graphical accent next to a text label, not text itself

/**
 * CSS variables `--team-dark` / `--team-light`: the team's primary color if it contrasts
 * with that theme's background, else its alternate color, else a neutral. Use with
 * `bg-[var(--team-light)] dark:bg-[var(--team-dark)]`.
 */
export function teamColorVars(team: TeamRef): CSSProperties {
  return {
    "--team-dark": pick(team, "dark"),
    "--team-light": pick(team, "light"),
  } as CSSProperties
}

function pick(team: TeamRef, theme: "dark" | "light"): string {
  for (const color of [team.color, team.alt_color]) {
    if (color && isHex(color) && contrast(color, CARD[theme]) >= MIN_CONTRAST) return color
  }
  return NEUTRAL[theme]
}

function isHex(color: string): boolean {
  return /^#[0-9a-f]{6}$/i.test(color)
}

/** WCAG contrast ratio between two #rrggbb colors. */
function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

function luminance(hex: string): number {
  const channel = (i: number) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5)
}

/** The contrast-checked team color for one theme (SVG strokes need a concrete color). */
export function teamColor(team: TeamRef, theme: "dark" | "light"): string {
  return pick(team, theme)
}

/** Perceptual distance (OKLab ΔE × 100). Under ~15, two colors read as the same. */
export function separation(a: string, b: string): number {
  const [l1, a1, b1] = oklab(a)
  const [l2, a2, b2] = oklab(b)
  return 100 * Math.hypot(l1 - l2, a1 - a2, b1 - b2)
}

function oklab(hex: string): [number, number, number] {
  const lin = (i: number) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  const [r, g, b] = [lin(1), lin(3), lin(5)]
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ]
}
