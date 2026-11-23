import type { Playoff, PlayoffGame, PlayoffTeam } from "@/lib/api/types"

/**
 * The projected bracket as positioned games (Phase 13.6), from the API's generic `rounds`
 * (#125), so the 12-team CFP and the 24-team FCS playoff share one drawing. Pure: no React.
 *
 * Each slot is a seed in the projected field or the winner of a game in the previous round.
 * In each game the team with the better chance of reaching the next round (the round's
 * `advance` odds) moves on, all the way to a projected champion. With the official FCS
 * bracket (#157), a game the two teams really play shows its score once final (the winner
 * moves on) or TSI's win chance before (the favorite moves on).
 *
 * Vertical order comes from walking back from the championship: a game fed by two games
 * sits midway between them, a game fed by one (a bye team meets a winner) lines up with
 * it, and a game fed by none (a first-round game) takes the next free row. Rows are in
 * game units: game i of the first column is at row i.
 */

export type Entry = { seed: number; team: PlayoffTeam }

/** The real game behind a bracket game, from each entry's side. */
export type RealGame = {
  id: number
  completed: boolean
  points: [number | null, number | null]
  winProb: [number, number] | null // TSI's shown forecast
}

export type BracketGame = {
  round: number
  index: number // within its round, as the API lists it
  entries: [Entry, Entry]
  feeders: [number | null, number | null] // per slot: the previous round's game, if any
  winner: Entry
  real: RealGame | null
  row: number // vertical position, in game units (may be fractional)
}

export type Bracket = { games: BracketGame[][]; rows: number; champion: Entry }

export function buildBracket(playoff: Playoff): Bracket | null {
  const { projected, rounds } = playoff
  if (rounds.length === 0 || projected.length < playoff.field_size) return null

  const games: BracketGame[][] = []
  rounds.forEach((round, r) => {
    const previous = games[r - 1] ?? []
    const odds = (t: PlayoffTeam) => {
      const value = t[round.advance as keyof PlayoffTeam]
      return typeof value === "number" ? value : 0
    }
    games.push(
      round.games.map((slots, index) => {
        const entries = slots.map((slot): Entry => {
          if (slot.seed != null) return { seed: slot.seed, team: projected[slot.seed - 1] }
          return previous[slot.game ?? 0].winner
        }) as [Entry, Entry]
        const [a, b] = entries
        const real = realGame(playoff.games ?? [], a, b)
        return {
          round: r,
          index,
          entries,
          feeders: slots.map((s) => (s.seed == null ? (s.game ?? 0) : null)) as [
            number | null,
            number | null,
          ],
          winner: real ? realWinner(real, a, b, odds) : odds(a.team) >= odds(b.team) ? a : b,
          real,
          row: 0,
        }
      }),
    )
  })

  let next = 0
  const place = (g: BracketGame): number => {
    const fed = g.feeders
      .filter((f): f is number => f !== null)
      .map((f) => place(games[g.round - 1][f]))
    g.row = fed.length === 0 ? next++ : fed.reduce((s, y) => s + y, 0) / fed.length
    return g.row
  }
  const final = games.at(-1)?.[0]
  if (!final) return null
  place(final)

  return { games, rows: next, champion: final.winner }
}

function realGame(games: PlayoffGame[], a: Entry, b: Entry): RealGame | null {
  const ids = [a.team.team.id, b.team.team.id]
  const g = games.find((x) => ids.includes(x.home_team_id) && ids.includes(x.away_team_id))
  if (!g || g.home_team_id === g.away_team_id) return null
  const aHome = g.home_team_id === ids[0]
  const p = g.home_win_prob
  return {
    id: g.game_id,
    completed: g.completed && g.home_points != null && g.away_points != null,
    points: aHome ? [g.home_points, g.away_points] : [g.away_points, g.home_points],
    winProb: p == null ? null : aHome ? [p, 1 - p] : [1 - p, p],
  }
}

/** A final game's winner; before it, TSI's favorite (else the likelier to advance). */
function realWinner(real: RealGame, a: Entry, b: Entry, odds: (t: PlayoffTeam) => number): Entry {
  const [pa, pb] = real.points
  if (real.completed && pa != null && pb != null) return pa > pb ? a : b
  if (real.winProb) return real.winProb[0] >= real.winProb[1] ? a : b
  return odds(a.team) >= odds(b.team) ? a : b
}
