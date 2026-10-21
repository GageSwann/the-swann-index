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

/** Every game of the season with the result and TSI's pre-game (or current) view. */
export function ScheduleTable({ schedule, odds, ranks }: Props) {
  const anyToday = [...odds.values()].some((o) => o.source === "today")
  return (
    <section aria-labelledby="schedule-heading" className="space-y-3">
      <h2 id="schedule-heading" className="text-2xl font-semibold font-stretch-condensed">
        Schedule
      </h2>
      <div className="overflow-x-auto rounded-md border border-border">
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
              const rank = ranks.get(g.opponent.slug)
              return (
                <tr key={g.game_id} className="border-b border-border last:border-0">
                  <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                    {g.kickoff ? formatShortDay(g.kickoff) : `Week ${g.week}`}
                  </td>
                  <td className="px-3 py-2">
                    <span className="flex items-center gap-2">
                      <span className="w-5 shrink-0 text-muted-foreground">
                        {g.site === "away" ? "at" : "vs"}
                      </span>
                      {rank != null && rank <= 25 && (
                        <span className="text-xs text-muted-foreground tabular-nums">#{rank}</span>
                      )}
                      <TeamLink team={g.opponent} />
                      {g.site === "neutral" && (
                        <span className="text-xs text-muted-foreground">(neutral)</span>
                      )}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <Link href={`/games/${g.game_id}`} className="hover:underline">
                      {g.outcome ? (
                        <>
                          <span
                            className={cn(
                              "font-semibold",
                              g.outcome === "W" ? "text-up" : g.outcome === "L" && "text-down",
                            )}
                          >
                            {g.outcome}
                          </span>{" "}
                          {g.team_points}–{g.opponent_points}
                        </>
                      ) : o ? (
                        <span className="text-muted-foreground">
                          Proj. {Math.round(o.teamPoints)}–{Math.round(o.opponentPoints)}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">Game center</span>
                      )}
                    </Link>
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                    {o ? teamSpread(Math.round(o.spread * 10) / 10) : "—"}
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                    {o ? (
                      <>
                        {percent(o.winProb, 0)}
                        {o.source === "today" && (
                          <span className="text-muted-foreground" title="If played today">
                            *
                          </span>
                        )}
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">
        TSI line and win chance are from the team&apos;s side, as published before kickoff
        (predictions began Oct 20, 2026).
        {anyToday && " * Not yet published: if the game were played today, with current ratings."}
      </p>
    </section>
  )
}
