"use client"

import { useTheme } from "next-themes"
import { useSyncExternalStore } from "react"

// Concrete chart colors per theme, mirroring the tokens in app/globals.css (SVG strokes
// need real colors). Keep the two in sync.
const TOKENS = {
  // The brand has no hue (#137): TSI's own series are drawn in the text color, solid,
  // and other series are told apart by dash pattern and tone.
  dark: {
    accent: "#f5f5f3",
    text: "#f5f5f3",
    muted: "#9a9a9f",
    grid: "#2b2b2e",
    surface: "#0e0e0f",
  },
  light: {
    accent: "#0a0a0a",
    text: "#0a0a0a",
    muted: "#5a5a60",
    grid: "#d4d4d6",
    surface: "#ffffff",
  },
}

export type ChartTheme = (typeof TOKENS)["dark"] & { mode: "dark" | "light" }

const subscribe = () => () => {}

/** The active theme's chart colors, or null until mounted (charts render client-side only). */
export function useChartTheme(): ChartTheme | null {
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  )
  const { resolvedTheme } = useTheme()
  if (!mounted) return null
  const mode = resolvedTheme === "light" ? "light" : "dark"
  return { ...TOKENS[mode], mode }
}

/** Axis styling shared by every chart: muted 12 px ticks on a grid-colored axis line. */
export function axisStyle(theme: ChartTheme) {
  return { tick: { fill: theme.muted, fontSize: 12 }, stroke: theme.grid }
}
