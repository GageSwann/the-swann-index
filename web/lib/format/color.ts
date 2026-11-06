import type { CSSProperties } from "react"

import type { TeamRef } from "@/lib/api/types"

// Team colors are accents only and must stand out from the background (doc 06, #138).
// Card backgrounds per theme (app/globals.css) and the fallback neutral.
const CARD = { dark: "#0e0e0f", light: "#ffffff" }
const NEUTRAL = { dark: "#9a9a9f", light: "#5a5a60" }
const MIN_CONTRAST = 2 // graphical accent next to a text label, not text itself
// An adjusted color aims a little higher: dark navies and greens lifted to exactly 2:1
// still read as dull on black (contact sheet, 2026-11-06).
const FIT_CONTRAST = 2.5
// Below this OKLCH chroma a color reads as white, black or gray: the brand's own tones,
// so never a team's light (decision #137).
const MIN_CHROMA = 0.04

type Theme = "dark" | "light"

/**
 * CSS variables `--team-dark` / `--team-light`: the team's display color per theme
 * (`teamColor`). Use with `bg-[var(--team-light)] dark:bg-[var(--team-dark)]`.
 */
export function teamColorVars(team: TeamRef): CSSProperties {
  return {
    "--team-dark": pick(team, "dark"),
    "--team-light": pick(team, "light"),
  } as CSSProperties
}

/** The team's display color for one theme (SVG strokes need a concrete color). */
export function teamColor(team: TeamRef, theme: Theme): string {
  return pick(team, theme)
}

/**
 * Phase 13.2 (#138): never white, black or gray, never invisible. The first of the team's
 * colors that stands out from that theme's card as is; else its first color lightened
 * (dark theme) or darkened (light theme) just enough, same hue; else the neutral.
 */
function pick(team: TeamRef, theme: Theme): string {
  const colors = [team.color, team.alt_color]
    .filter((c): c is string => !!c && isHex(c))
    .map((c) => c.toLowerCase())
    .filter((c) => oklch(c)[1] >= MIN_CHROMA)
  const visible = colors.find((c) => contrast(c, CARD[theme]) >= MIN_CONTRAST)
  if (visible) return visible
  for (const color of colors) {
    const fitted = fitToTheme(color, theme)
    if (fitted) return fitted
  }
  return NEUTRAL[theme]
}

/** The color with its OKLCH lightness moved toward the theme's text until it stands out. */
function fitToTheme(hex: string, theme: Theme): string | null {
  const [l, c, h] = oklch(hex)
  const step = theme === "dark" ? 0.01 : -0.01
  for (let lightness = l + step; lightness > 0 && lightness < 1; lightness += step) {
    const candidate = fromOklch(lightness, c, h)
    if (contrast(candidate, CARD[theme]) >= FIT_CONTRAST) return candidate
  }
  return null
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
  const [r, g, b] = linearRgb(hex)
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** Perceptual distance (OKLab ΔE × 100). Under ~15, two colors read as the same. */
export function separation(a: string, b: string): number {
  const [l1, a1, b1] = oklab(a)
  const [l2, a2, b2] = oklab(b)
  return 100 * Math.hypot(l1 - l2, a1 - a2, b1 - b2)
}

function linearRgb(hex: string): [number, number, number] {
  const lin = (i: number) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  return [lin(1), lin(3), lin(5)]
}

function oklab(hex: string): [number, number, number] {
  const [r, g, b] = linearRgb(hex)
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ]
}

/** [lightness, chroma, hue in radians]. */
function oklch(hex: string): [number, number, number] {
  const [l, a, b] = oklab(hex)
  return [l, Math.hypot(a, b), Math.atan2(b, a)]
}

/** OKLCH to #rrggbb; chroma is reduced until the color fits in sRGB (hue and lightness kept). */
function fromOklch(l: number, c: number, h: number): string {
  let rgb = oklchToLinearRgb(l, c, h)
  if (!inGamut(rgb)) {
    let [lo, hi] = [0, c]
    for (let i = 0; i < 20; i++) {
      const mid = (lo + hi) / 2
      if (inGamut(oklchToLinearRgb(l, mid, h))) lo = mid
      else hi = mid
    }
    rgb = oklchToLinearRgb(l, lo, h)
  }
  return "#" + rgb.map(toHexChannel).join("")
}

function oklchToLinearRgb(l: number, c: number, h: number): [number, number, number] {
  const [a, b] = [c * Math.cos(h), c * Math.sin(h)]
  const l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
  const m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
  const s_ = (l - 0.0894841775 * a - 1.291485548 * b) ** 3
  return [
    4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
    -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
    -0.0041960863 * l_ - 0.7034186147 * m_ + 1.707614701 * s_,
  ]
}

function inGamut(rgb: number[]): boolean {
  return rgb.every((v) => v >= -1e-4 && v <= 1 + 1e-4)
}

function toHexChannel(linear: number): string {
  const v = Math.min(1, Math.max(0, linear))
  const srgb = v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055
  return Math.round(srgb * 255)
    .toString(16)
    .padStart(2, "0")
}
