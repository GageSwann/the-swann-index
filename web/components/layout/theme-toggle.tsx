"use client"

import { MoonIcon, SunIcon } from "lucide-react"
import { useTheme } from "next-themes"

/** Switches between the night (dark) and press-box (light) themes. */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const next = resolvedTheme === "light" ? "dark" : "light"
  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} theme`}
      className="inline-flex size-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
    >
      {/* Both icons render; CSS shows the right one, so nothing flips after hydration. */}
      <SunIcon className="hidden size-4 dark:block" aria-hidden />
      <MoonIcon className="size-4 dark:hidden" aria-hidden />
    </button>
  )
}
