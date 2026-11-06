"use client"

import { useLayoutEffect } from "react"

import type { TeamRef } from "@/lib/api/types"
import { teamColor } from "@/lib/format/color"

/** The team page currently lighting the site; a page's cleanup only clears its own light. */
let owner: symbol | null = null

/**
 * A team page takes on the team's light (decision #137): the header rule, focus and
 * selected-tab glows and the page's bars use the team's color per theme (`--light` in
 * app/globals.css reads `--page-team-*` on :root).
 *
 * Next.js keeps visited pages in the document, hidden (React Activity, Cache Components),
 * so a page-level `<style>` would keep applying after you leave. Instead the light is set on
 * <html> while the page is shown and removed in the effect cleanup, which runs when the page
 * is hidden. The `<style>` only covers the first paint: it stops matching once any team page
 * has hydrated (`data-page-light`), so hidden copies are inert.
 */
export function PageTeamLight({ team }: { team: TeamRef }) {
  const dark = teamColor(team, "dark")
  const light = teamColor(team, "light")

  useLayoutEffect(() => {
    const root = document.documentElement
    const me = Symbol(team.slug)
    owner = me
    root.dataset.pageLight = ""
    root.style.setProperty("--page-team-dark", dark)
    root.style.setProperty("--page-team-light", light)
    return () => {
      if (owner !== me) return // another team page already took over
      owner = null
      root.style.removeProperty("--page-team-dark")
      root.style.removeProperty("--page-team-light")
    }
  }, [team.slug, dark, light])

  // `teamColor` only ever returns a #rrggbb value, so this can't inject CSS.
  const css = `:root:not([data-page-light]){--page-team-dark:${dark};--page-team-light:${light}}`
  return <style>{css}</style>
}
