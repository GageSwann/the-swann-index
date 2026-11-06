import type { CSSProperties } from "react"

import type { TeamRef } from "@/lib/api/types"
import { teamColor } from "@/lib/format/color"

/**
 * The border light (decision #137): two arcs, one per team color, run around the border
 * of a page's focal point (the scoreboard, a game of the week). Put `tsi-border-light`
 * plus `borderLightVars(a, b)` on the panel and `<BorderLightRings />` inside it; the
 * panel keeps its own border as the track. Styles in app/globals.css; reduced motion
 * turns it into a still two-color border.
 */
export function borderLightVars(a: TeamRef, b: TeamRef): CSSProperties {
  return {
    "--bl-1-dark": teamColor(a, "dark"),
    "--bl-2-dark": teamColor(b, "dark"),
    "--bl-1-light": teamColor(a, "light"),
    "--bl-2-light": teamColor(b, "light"),
  } as CSSProperties
}

export function BorderLightRings() {
  return (
    <>
      <span aria-hidden className="tsi-ring tsi-ring-bloom" />
      <span aria-hidden className="tsi-ring" />
    </>
  )
}
