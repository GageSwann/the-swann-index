import type { GameSummary, PickView } from "@/lib/api/types"
import { signed } from "@/lib/format/numbers"
import { describePick } from "@/lib/format/picks"

/** A TSI play: "★★ Over 45.5", then ✔/✘ and CLV once graded. */
export function PickBadge({ pick, game }: { pick: PickView; game: GameSummary }) {
  const outcome = pick.result === "win" ? "✔" : pick.result === "loss" ? "✘" : "–"
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
      <span className="rounded-sm bg-primary px-1.5 py-0.5 font-semibold text-primary-foreground">
        <span aria-label={`${pick.tier} star play`}>{"★".repeat(pick.tier)}</span>{" "}
        {describePick(pick, game.home, game.away)}
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
