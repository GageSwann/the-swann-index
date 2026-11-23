import type { CSSProperties } from "react"

import type { TeamRef } from "@/lib/api/types"
import { teamColor } from "@/lib/format/color"

/**
 * Both teams' display colors per theme as CSS variables, for the scoreboard's two-color
 * strip (`tsi-team-split` in app/globals.css, #168; once #137's moving border light).
 */
export function borderLightVars(a: TeamRef, b: TeamRef): CSSProperties {
  return {
    "--bl-1-dark": teamColor(a, "dark"),
    "--bl-2-dark": teamColor(b, "dark"),
    "--bl-1-light": teamColor(a, "light"),
    "--bl-2-light": teamColor(b, "light"),
  } as CSSProperties
}
