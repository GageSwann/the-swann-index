import Link from "next/link"

import type { GameOdds } from "@/lib/api/schedule-odds"
import type { ScheduleGame } from "@/lib/api/types"
import { chance } from "@/lib/format/numbers"
import { formatMonthDay } from "@/lib/format/time"
import { cfb } from "@/lib/routes"
import { cn } from "@/lib/utils"

import { TeamLogo } from "./team-logo"

/**
 * The season's schedule as a compact vertical list (owner, #199), in the style of the home
 * page's Top 25 rails: date, opponent (its rank when in the Top 25; "vs" at home, "at" away, "vs" with an N tag on a
 * neutral field), then the result once final (W in the up color, L in the down color) or
 * TSI's win chance before it. The next game is highlighted; every row opens the game center.
 * The list stretches to the Next Game card's height (rows share the extra space). "Details"
 * jumps to this team's full schedule table further down the page.
 */
export function ScheduleList({
  schedule,
  odds,
  nextId,
}: {
  schedule: ScheduleGame[]
  odds: Map<number, GameOdds>
  nextId: number | null // the Next Game card's game
}) {
  return (
    <section aria-labelledby="schedule-list-heading" className="flex h-full min-w-0 flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="schedule-list-heading" className="text-lg font-semibold font-stretch-condensed">
          Schedule
        </h2>
        <Link
          href="#schedule-heading"
          aria-label="Schedule details, further down this page"
          className="text-sm text-muted-foreground underline decoration-muted-foreground underline-offset-4 hover:text-foreground hover:decoration-foreground"
        >
          Details ↓
        </Link>
      </div>
      {schedule.length === 0 ? (
        <p className="rounded-md border border-border bg-card p-4 text-sm text-muted-foreground">
          No games on the schedule yet.
        </p>
      ) : (
        <ol className="flex flex-1 flex-col divide-y divide-border rounded-md border border-border bg-card text-sm">
          {schedule.map((g) => (
            <li key={g.game_id} className={cn("flex flex-1", g.game_id === nextId && "bg-muted")}>
              <Link
                href={cfb.game(g.game_id)}
                aria-current={g.game_id === nextId ? "true" : undefined}
                className="group grid w-full grid-cols-[3rem_1.5rem_minmax(0,1fr)_auto] items-center gap-2 px-2.5 py-1.5"
              >
                <span className="text-xs text-muted-foreground tabular-nums">
                  {g.kickoff ? formatMonthDay(g.kickoff) : `Wk ${g.week}`}
                </span>
                <TeamLogo team={g.opponent} size={22} />
                <span className="flex min-w-0 items-center gap-1.5">
                  <span className="truncate group-hover:underline">
                    <span className="text-muted-foreground">
                      {g.site === "away" ? "at " : "vs "}
                    </span>
                    {/* The opponent's rank when in the Top 25, like the full table below. */}
                    {g.opponent_rank != null && g.opponent_rank <= 25 && (
                      <span className="text-xs text-muted-foreground tabular-nums">
                        #{g.opponent_rank}{" "}
                      </span>
                    )}
                    {g.opponent.school}
                  </span>
                  {g.site === "neutral" && (
                    <span
                      title="Neutral site"
                      className="shrink-0 rounded-sm border border-border px-1 text-[0.625rem] leading-4 font-semibold text-muted-foreground"
                    >
                      N<span className="sr-only">eutral site</span>
                    </span>
                  )}
                </span>
                <Outcome game={g} odds={odds.get(g.game_id)} />
              </Link>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

/** "W 35–14" once final; before that TSI's win chance ("62%"), or a dash without one. */
function Outcome({ game, odds }: { game: ScheduleGame; odds: GameOdds | undefined }) {
  if (game.outcome && game.team_points != null && game.opponent_points != null) {
    return (
      <span className="text-right tabular-nums">
        <span
          className={cn(
            "font-semibold",
            game.outcome === "W" ? "text-up" : game.outcome === "L" ? "text-down" : "",
          )}
        >
          {game.outcome}
        </span>{" "}
        <span className="text-muted-foreground">
          {game.team_points}–{game.opponent_points}
        </span>
      </span>
    )
  }
  return (
    <span className="text-right text-muted-foreground tabular-nums">
      {odds ? chance(odds.winProb) : "–"}
      {odds && <span className="sr-only"> TSI win chance</span>}
    </span>
  )
}
