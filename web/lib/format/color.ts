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
export function contrast(a: string, b: string): number {
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
