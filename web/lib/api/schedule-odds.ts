import "server-only"

import { getMatchup } from "./queries"
import type { ScheduleGame, TeamRef } from "./types"

/** TSI's view of one game from the team's side; `source` says where it came from. */
export type GameOdds = {
  winProb: number
  spread: number // team's view, negative = favored
  teamPoints: number
  opponentPoints: number
  source: "published" | "today"
}

/**
 * Odds for every schedule game TSI has a view on: the published snapshot when there is
 * one (finished games keep their locked pre-game prediction), else, for games not played
 * yet, the API's hypothetical matchup with today's ratings. Matchups run in parallel.
 */
export async function scheduleOdds(
  team: TeamRef,
  schedule: ScheduleGame[],
): Promise<Map<number, GameOdds>> {
  const entries = await Promise.all(
    schedule.map(async (g): Promise<[number, GameOdds] | null> => {
      if (
        g.win_prob != null &&
        g.spread != null &&
        g.projected_team != null &&
        g.projected_opponent != null
      ) {
        return [
          g.game_id,
          {
            winProb: g.win_prob,
            spread: g.spread,
            teamPoints: g.projected_team,
            opponentPoints: g.projected_opponent,
            source: "published",
          },
        ]
      }
      if (g.outcome !== null || g.result?.final) return null
      const atHome = g.site !== "away"
      const m = await getMatchup(
        atHome ? team.slug : g.opponent.slug,
        atHome ? g.opponent.slug : team.slug,
        g.site === "neutral",
      ).catch(() => null)
      if (!m) return null
      return [
        g.game_id,
        {
          winProb: atHome ? m.home_win_prob : 1 - m.home_win_prob,
          spread: atHome ? m.spread : -m.spread,
          teamPoints: atHome ? m.proj_home : m.proj_away,
          opponentPoints: atHome ? m.proj_away : m.proj_home,
          source: "today",
        },
      ]
    }),
  )
  return new Map(entries.filter((e) => e !== null))
}
