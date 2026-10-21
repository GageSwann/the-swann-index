import type { GameSummary, PickView } from "@/lib/api/types"
import { american, teamSpread, totalLine } from "@/lib/format/odds"
import { signed } from "@/lib/format/numbers"

/** A TSI play: "★★ Over 45.5", then ✔/✘ and CLV once graded. */
export function PickBadge({ pick, game }: { pick: PickView; game: GameSummary }) {
  const outcome = pick.result === "win" ? "✔" : pick.result === "loss" ? "✘" : "–"
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
      <span className="rounded-sm bg-primary px-1.5 py-0.5 font-semibold text-primary-foreground">
        <span aria-label={`${pick.tier} star play`}>{"★".repeat(pick.tier)}</span>{" "}
        {describe(pick, game)}
      </span>
      {pick.result && (
        <span
          className={pick.result === "win" ? "text-up" : pick.result === "loss" ? "text-down" : ""}
        >
          {outcome} {pick.result}
        </span>
      )}
      {pick.clv !== null && pick.market !== "ml" && (
        <span className="text-xs text-muted-foreground">CLV {signed(pick.clv)} pts</span>
      )}
    </div>
  )
}

function describe(pick: PickView, game: GameSummary): string {
  if (pick.market === "total") {
    return `${pick.side === "over" ? "Over" : "Under"} ${totalLine(pick.line ?? 0)}`
  }
  const team = pick.side === "home" ? game.home : game.away
  const name = team.abbreviation ?? team.school
  if (pick.market === "ml") return `${name} ML ${american(pick.odds)}`
  // Pick lines are home-view spreads; the away side gets the opposite sign.
  const line = pick.line ?? 0
  return `${name} ${teamSpread(pick.side === "home" ? line : -line)}`
}
