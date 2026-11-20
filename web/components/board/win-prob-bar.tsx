import type { TeamRef } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { chance } from "@/lib/format/numbers"

// Each side is its team's color and casts light in it (#137); not clipped, so the glow shows.
const SEGMENT = "tsi-team-light tsi-glow-below h-full rounded-full bg-(--light)"

/**
 * Away share on the left, home on the right, in each team's color (contrast-checked per
 * theme, lib/format/color.ts); a 2 px gap keeps similar colors apart. Percentages are text.
 */
export function WinProbBar({
  homeProb,
  home,
  away,
}: {
  homeProb: number
  home: TeamRef
  away: TeamRef
}) {
  const awayPct = (1 - homeProb) * 100 // bar widths; the labels never say 0% or 100%
  const homePct = homeProb * 100
  const awayLabel = chance(1 - homeProb)
  const homeLabel = chance(homeProb)
  return (
    <div className="space-y-1">
      <div
        className="flex h-2 gap-0.5"
        role="img"
        aria-label={`Win probability: ${away.school} ${awayLabel}, ${home.school} ${homeLabel}`}
      >
        <span className={SEGMENT} style={{ width: `${awayPct}%`, ...teamColorVars(away) }} />
        <span className={SEGMENT} style={{ width: `${homePct}%`, ...teamColorVars(home) }} />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground" aria-hidden>
        <span>{awayLabel}</span>
        <span>{homeLabel}</span>
      </div>
    </div>
  )
}
