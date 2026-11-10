/**
 * Where a game stands right now (Phase 13.5), worked out from its kickoff and the viewer's
 * clock, because the site's data changes only with the nightly run: without this a 3:30 PM
 * game would read "in progress" until the next morning.
 *
 * - scheduled: before kickoff (or a date-only kickoff, which never flips on its own)
 * - live: from kickoff until LIVE_WINDOW after it ("In progress")
 * - pending: later, until the nightly run records the final ("Final score pending")
 * - final: the API has the final score
 */

export type GamePhase = "scheduled" | "live" | "pending" | "final"

/** College games run ~3¼ hours; 4 covers overtime and most delays. */
export const LIVE_WINDOW_MS = 4 * 60 * 60 * 1000

export type PhaseInput = {
  kickoff: string | null
  tbd: boolean // date only: no real kickoff time
  final: boolean
  locked?: boolean // the API's "kicked off" as of the last nightly run
}

export function gamePhase(game: PhaseInput, now: number): GamePhase {
  if (game.final) return "final"
  if (game.kickoff === null || game.tbd) return "scheduled"
  const kickoff = Date.parse(game.kickoff)
  if (now < kickoff) return "scheduled"
  return now < kickoff + LIVE_WINDOW_MS ? "live" : "pending"
}

/** Before the browser's clock takes over (server render, no JavaScript): what the data
 * knows. A game that had kicked off at the nightly run is long over by then. */
export function dataPhase(game: PhaseInput): GamePhase {
  if (game.final) return "final"
  return game.locked ? "pending" : "scheduled"
}

export const PHASE_LABEL: Record<GamePhase, string | null> = {
  scheduled: null,
  live: "In progress",
  pending: "Final score pending",
  final: "Final",
}

export const PENDING_HINT = "TSI adds final scores with its morning update."
