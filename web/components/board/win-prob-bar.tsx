import type { TeamRef } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"

const SEGMENT = "h-full bg-[var(--team-light)] dark:bg-[var(--team-dark)]"

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
  const awayPct = Math.round((1 - homeProb) * 100)
  const homePct = 100 - awayPct
  return (
    <div className="space-y-1">
      <div
        className="flex h-2 gap-0.5 overflow-hidden rounded-full"
        role="img"
        aria-label={`Win probability: ${away.school} ${awayPct}%, ${home.school} ${homePct}%`}
      >
        <span className={SEGMENT} style={{ width: `${awayPct}%`, ...teamColorVars(away) }} />
        <span className={SEGMENT} style={{ width: `${homePct}%`, ...teamColorVars(home) }} />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground" aria-hidden>
        <span>{awayPct}%</span>
        <span>{homePct}%</span>
      </div>
    </div>
  )
}
