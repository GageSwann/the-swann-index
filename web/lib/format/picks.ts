import type { PickView, TeamRef } from "@/lib/api/types"

import { american, teamSpread, totalLine } from "./odds"

/** "Over 45.5", "LSU −7.5", "LSU ML +150". Pick lines are home-view spreads. */
export function describePick(pick: PickView, home: TeamRef, away: TeamRef): string {
  if (pick.market === "total") {
    return `${pick.side === "over" ? "Over" : "Under"} ${totalLine(pick.line ?? 0)}`
  }
  const team = pick.side === "home" ? home : away
  const name = team.abbreviation ?? team.school
  if (pick.market === "ml") return `${name} ML ${american(pick.odds)}`
  const line = pick.line ?? 0
  return `${name} ${teamSpread(pick.side === "home" ? line : -line)}`
}

export const MARKET_LABEL: Record<string, string> = {
  all: "All picks",
  spread: "Spread",
  total: "Total",
  ml: "Moneyline",
}

/** Units won or lost: "+2.7u", "−1.0u". */
export function units(value: number): string {
  const text = Math.abs(value).toFixed(1)
  if (Number(text) === 0) return "0.0u"
  return `${value > 0 ? "+" : "−"}${text}u`
}
