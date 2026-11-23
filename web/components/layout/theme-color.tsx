"use client"

import { useTheme } from "next-themes"
import { useEffect } from "react"

// The header's panel color in each theme (globals.css --card), so the browser's own bars
// blend into it (#165).
const BAR: Record<string, string> = { dark: "#252526", light: "#f5f5f5" }

/** Keeps `<meta name="theme-color">` and the tab icon in step with the light/dark toggle. */
export function ThemeColor() {
  const { resolvedTheme } = useTheme()
  useEffect(() => {
    const color = BAR[resolvedTheme ?? "dark"] ?? BAR.dark
    // Next renders this tag from `viewport.themeColor`: change its value, never remove it
    // (React still owns the node).
    document
      .querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]')
      .forEach((meta) => (meta.content = color))
    // The tab icon follows the theme like the header badge (#175): every icon link points at
    // this theme's version (`/icon/light` or `/icon/dark`). Next can add icon links after
    // the page loads, so new ones are pointed there too.
    const mode = resolvedTheme === "light" ? "light" : "dark"
    const apply = () => {
      const links = [...document.querySelectorAll<HTMLLinkElement>('link[rel="icon"]')]
      links.forEach((l) => (l.dataset.tsiHref ??= l.getAttribute("href") ?? ""))
      const href = links.find((l) => l.dataset.tsiHref?.includes(`/icon/${mode}`))?.dataset.tsiHref
      if (!href) return
      links.forEach((l) => {
        if (l.getAttribute("href") !== href) l.setAttribute("href", href)
      })
    }
    apply()
    const watch = new MutationObserver(apply)
    watch.observe(document.head, { childList: true })
    return () => watch.disconnect()
  }, [resolvedTheme])
  return null
}
