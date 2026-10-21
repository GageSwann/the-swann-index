import Link from "next/link"

import { TeamLink } from "@/components/team/team-link"
import type { GameOdds } from "@/lib/api/schedule-odds"
import type { ScheduleGame } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { teamSpread } from "@/lib/format/odds"
import { formatShortDay } from "@/lib/format/time"
import { cn } from "@/lib/utils"

type Props = {
  schedule: ScheduleGame[]
  odds: Map<number, GameOdds>
  ranks: Map<string, number> // opponent slug → current power rank
}

/**
 * Every game of the season with the result and TSI's pre-game (or current) view. A table
 * from `sm` up; on phones each game is a two-line row so nothing scrolls sideways.
 */
export function ScheduleTable({ schedule, odds, ranks }: Props) {
  const anyToday = [...odds.values()].some((o) => o.source === "today")
  const date = (g: ScheduleGame) => (g.kickoff ? formatShortDay(g.kickoff) : `Week ${g.week}`)
  return (
    <section aria-labelledby="schedule-heading" className="space-y-3">
      <h2 id="schedule-heading" className="text-2xl font-semibold font-stretch-condensed">
        Schedule
      </h2>
      <div className="hidden rounded-md border border-border sm:block">
        <table className="w-full text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <th scope="col" className="px-3 py-2 text-left font-medium">
                Date
              </th>
              <th scope="col" className="px-3 py-2 text-left font-medium">
                Opponent
              </th>
              <th scope="col" className="px-3 py-2 text-left font-medium">
                Result
              </th>
              <th scope="col" className="px-3 py-2 text-right font-medium">
                TSI line
              </th>
              <th scope="col" className="px-3 py-2 text-right font-medium">
                Win chance
              </th>
            </tr>
          </thead>
          <tbody>
            {schedule.map((g) => {
              const o = odds.get(g.game_id)
              return (
                <tr key={g.game_id} className="border-b border-border last:border-0">
                  <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">{date(g)}</td>
                  <td className="px-3 py-2">
                    <Opponent game={g} rank={ranks.get(g.opponent.slug)} />
                  </td>
                  <td className="px-3 py-1 whitespace-nowrap">
                    <Result game={g} odds={o} />
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                    {o ? teamSpread(Math.round(o.spread * 10) / 10) : "—"}
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                    <WinChance odds={o} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <ol className="divide-y divide-border rounded-md border border-border text-sm sm:hidden">
        {schedule.map((g) => {
          const o = odds.get(g.game_id)
          return (
            <li key={g.game_id} className="space-y-1 px-3 py-2">
              <div className="flex items-center justify-between gap-3">
                <Opponent game={g} rank={ranks.get(g.opponent.slug)} />
                <Result game={g} odds={o} />
              </div>
              <p className="flex justify-between gap-3 text-muted-foreground tabular-nums">
                <span>{date(g)}</span>
                {o && (
                  <span>
                    TSI {teamSpread(Math.round(o.spread * 10) / 10)}, win <WinChance odds={o} />
                  </span>
                )}
              </p>
            </li>
          )
        })}
      </ol>
      <p className="text-xs text-muted-foreground">
        TSI line and win chance are from the team&apos;s side, as published before kickoff
        (predictions began Oct 20, 2026).
        {anyToday && " * Not yet published: if the game were played today, with current ratings."}
      </p>
    </section>
  )
}

function Opponent({ game, rank }: { game: ScheduleGame; rank: number | undefined }) {
  return (
    <span className="flex min-w-0 items-center gap-2">
      <span className="w-5 shrink-0 text-muted-foreground">
        {game.site === "away" ? "at" : "vs"}
      </span>
      {rank != null && rank <= 25 && (
        <span className="text-xs text-muted-foreground tabular-nums">#{rank}</span>
      )}
      <TeamLink team={game.opponent} />
      {game.site === "neutral" && <span className="text-xs text-muted-foreground">(neutral)</span>}
    </span>
  )
}

/** Final score, else the projected score; either way a link to the game center. */
function Result({ game, odds }: { game: ScheduleGame; odds: GameOdds | undefined }) {
  return (
    <Link
      href={`/games/${game.game_id}`}
      className="inline-flex min-h-8 shrink-0 items-center whitespace-nowrap hover:underline"
    >
      {game.outcome ? (
        <span>
          <span
            className={cn(
              "font-semibold",
              game.outcome === "W" ? "text-up" : game.outcome === "L" && "text-down",
            )}
          >
            {game.outcome}
          </span>{" "}
          {game.team_points}–{game.opponent_points}
        </span>
      ) : odds ? (
        <span className="text-muted-foreground">
          Proj. {Math.round(odds.teamPoints)}–{Math.round(odds.opponentPoints)}
        </span>
      ) : (
        <span className="text-muted-foreground">Game center</span>
      )}
    </Link>
  )
}

function WinChance({ odds }: { odds: GameOdds | undefined }) {
  if (!odds) return <>—</>
  return (
    <>
      <span className="text-foreground">{percent(odds.winProb, 0)}</span>
      {odds.source === "today" && (
        <span className="text-muted-foreground" title="If played today">
          *
        </span>
      )}
    </>
  )
}
