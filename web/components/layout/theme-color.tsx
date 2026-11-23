"use client"

import { useTheme } from "next-themes"
import { useEffect } from "react"

// The header's panel color in each theme (globals.css --card), so the browser's own bars
// blend into it (#165).
const BAR: Record<string, string> = { dark: "#252526", light: "#ffffff" }

/** Keeps `<meta name="theme-color">` in step with the light/dark toggle. */
export function ThemeColor() {
  const { resolvedTheme } = useTheme()
  useEffect(() => {
    const color = BAR[resolvedTheme ?? "dark"] ?? BAR.dark
    // Next renders this tag from `viewport.themeColor`: change its value, never remove it
    // (React still owns the node).
    document
      .querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]')
      .forEach((meta) => (meta.content = color))
  }, [resolvedTheme])
  return null
}
