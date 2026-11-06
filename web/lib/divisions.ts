import type { TeamRef } from "@/lib/api/types"

/** The divisions TSI ranks (decision #111); "all" lists both on one rating scale (#113). */
export type Division = "fbs" | "fcs"
export type DivisionView = Division | "all"

export const DIVISION_NAME: Record<DivisionView, string> = {
  fbs: "FBS",
  fcs: "FCS",
  all: "FBS + FCS",
}

export function teamDivision(team: Pick<TeamRef, "division">): Division {
  return team.division === "fcs" ? "fcs" : "fbs"
}

/** Today's Résumé benchmark ranks: a typical #12 FBS team, or #24 FCS team (#24, #133). */
const BENCHMARK_RANK: Record<Division, number> = { fbs: 12, fcs: 24 }

/**
 * The Résumé benchmark team, "#12 team" or "#24 FCS team". Pass the API's
 * `benchmark_rank` (the rank that run measured against: FCS was #10 before 2026-11-06).
 */
export function benchmarkName(division: Division, rank?: number | null): string {
  const n = rank ?? BENCHMARK_RANK[division]
  return division === "fcs" ? `#${n} FCS team` : `#${n} team`
}

/** "#7", or "#7 FCS": ranks are within a division, so FCS ranks say so. */
export function rankText(rank: number, division: Division): string {
  return division === "fcs" ? `#${rank} FCS` : `#${rank}`
}
