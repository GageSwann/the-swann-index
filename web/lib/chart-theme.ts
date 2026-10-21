"use client"

import { useTheme } from "next-themes"
import { useSyncExternalStore } from "react"

// Concrete chart colors per theme, mirroring the tokens in app/globals.css (SVG strokes
// need real colors). Keep the two in sync.
const TOKENS = {
  dark: {
    accent: "#f2b33d",
    text: "#e6edf2",
    muted: "#93a6b5",
    grid: "#2a3c4b",
    surface: "#162532",
  },
  light: {
    accent: "#9a6400",
    text: "#13212c",
    muted: "#4e6170",
    grid: "#cfd9e1",
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
