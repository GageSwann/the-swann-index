"use client"

import { MoonIcon, SunIcon } from "lucide-react"
import { useTheme } from "next-themes"

/** Switches between the black swan (dark) and white swan (light) themes. */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const next = resolvedTheme === "light" ? "dark" : "light"
  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      // A fixed label: the server can't know the saved theme, so a "Switch to …" label
      // didn't match after hydration for anyone on the light theme.
      aria-label="Switch between dark and light theme"
      className="inline-flex size-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
    >
      {/* Both icons render; CSS shows the right one, so nothing flips after hydration. */}
      <SunIcon className="hidden size-4 dark:block" aria-hidden />
      <MoonIcon className="size-4 dark:hidden" aria-hidden />
    </button>
  )
}
