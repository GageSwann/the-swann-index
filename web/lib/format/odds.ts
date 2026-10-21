import type { TeamRef } from "@/lib/api/types"

const MINUS = "−"

/** American odds: "+150", "−110". */
export function american(odds: number): string {
  return odds > 0 ? `+${odds}` : `${MINUS}${Math.abs(odds)}`
}

/**
 * A home-view spread (negative = home favored) as "LSU −7.9", naming the favorite.
 * "Pick 'em" when it rounds to zero.
 */
export function favoriteLine(spread: number, home: TeamRef, away: TeamRef, digits = 1): string {
  const size = Math.abs(spread).toFixed(digits)
  if (Number(size) === 0) return "Pick 'em"
  const favorite = spread < 0 ? home : away
  return `${favorite.abbreviation ?? favorite.school} ${MINUS}${size}`
}

/** A spread from one team's view: "−3.5", "+7", "PK". */
export function teamSpread(spread: number): string {
  if (spread === 0) return "PK"
  const size = Number.isInteger(spread) ? Math.abs(spread).toFixed(0) : Math.abs(spread).toString()
  return `${spread < 0 ? MINUS : "+"}${size}`
}

/** A total: "50.5" (market quarter lines like 52.75 keep two decimals). */
export function totalLine(total: number): string {
  return Number.isInteger(total * 2) ? total.toFixed(1) : total.toFixed(2)
}
