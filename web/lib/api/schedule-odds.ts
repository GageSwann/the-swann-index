import type { ScheduleGame } from "./types"

/** TSI's view of one game from the team's side; `source` says where it came from. */
export type GameOdds = {
  winProb: number
  spread: number // team's view, negative = favored
  teamPoints: number
  opponentPoints: number
  source: "published" | "forecast"
  adjusted: boolean // includes manual adjustments
}

/**
 * Odds for every schedule game TSI has a view on: the published snapshot when there is
 * one (finished games keep their locked pre-game prediction), else last night's season
 * simulation forecast for games not published yet (#144). No API calls.
 */
export function scheduleOdds(schedule: ScheduleGame[]): Map<number, GameOdds> {
  return new Map(
    schedule.flatMap((g) => {
      const odds = publishedOdds(g) ?? forecastOdds(g)
      return odds ? [[g.game_id, odds] as const] : []
    }),
  )
}

function publishedOdds(g: ScheduleGame): GameOdds | null {
  if (
    g.win_prob == null ||
    g.spread == null ||
    g.projected_team == null ||
    g.projected_opponent == null
  ) {
    return null
  }
  return {
    winProb: g.win_prob,
    spread: g.spread,
    teamPoints: g.projected_team,
    opponentPoints: g.projected_opponent,
    source: "published",
    adjusted: g.adjusted,
  }
}

function forecastOdds(g: ScheduleGame): GameOdds | null {
  const f = g.forecast
  if (!f) return null
  return {
    winProb: f.win_prob,
    spread: f.spread,
    teamPoints: f.team_points,
    opponentPoints: f.opponent_points,
    source: "forecast",
    adjusted: f.adjusted,
  }
}
