import type { Rankings } from "@/lib/api/types"

/**
 * A team's Power rank on the week board. In the All view an FCS team carries its FCS rank,
 * marked `fcs`, so the card can say "FCS 3" (Phase 12.6); FBS ranks stay plain numbers.
 */
export type BoardRank = { rank: number; fcs?: boolean }
export type BoardRanks = Record<number, BoardRank>

export const TOP = 25

/** Team id -> rank from one division's rankings (`fcs`: mark them as FCS ranks). */
export function boardRanks(rankings: Rankings | null, fcs = false): BoardRanks {
  return Object.fromEntries(
    (rankings?.teams ?? []).map((t) => [t.team.id, fcs ? { rank: t.rank, fcs } : { rank: t.rank }]),
  )
}

/** The rank to show: only the Top 25 get one. */
export function shownRank(rank: BoardRank | undefined): BoardRank | undefined {
  return rank && rank.rank <= TOP ? rank : undefined
}
