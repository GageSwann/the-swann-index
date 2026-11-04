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

/** The Résumé benchmark team: a typical #12 FBS team, or #10 FCS team (#24, #91). */
export function benchmarkName(division: Division): string {
  return division === "fcs" ? "#10 FCS team" : "#12 team"
}

/** "#7", or "#7 FCS": ranks are within a division, so FCS ranks say so. */
export function rankText(rank: number, division: Division): string {
  return division === "fcs" ? `#${rank} FCS` : `#${rank}`
}
