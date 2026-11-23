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

/** The favorite's moneyline: "ND −144" (the shorter price; home on a tie). */
export function favoriteMoneyline(home: TeamRef, away: TeamRef, homeMl: number, awayMl: number) {
  const homeFav = homeMl <= awayMl
  const team = homeFav ? home : away
  return `${team.abbreviation ?? team.school} ${american(homeFav ? homeMl : awayMl)}`
}

/*
 * TSI's own lines as a sportsbook posts them (owner, #158, #187): spreads, totals and team
 * totals always on a half point, the nearest one ending in .5 (−8.8 → −8.5, 9 → 9.5,
 * 44.9 → 44.5), so they never push; moneylines at the nearest 5 (−273 → −275). Rounded by
 * size, so both sides always mirror; the API's main lines follow the same rule. Vegas lines
 * are shown as the books post them and never pass through these.
 */

/** The nearest line ending in .5, by size (#187): −8.8 → −8.5, 9 → 9.5; zero → +0.5. */
export function bookLine(value: number): number {
  const size = Math.floor(Math.abs(value)) + 0.5
  return value < 0 ? -size : size
}

/** "−8.5", "45.5" (whole numbers, which TSI no longer posts, print without a decimal). */
export function halfText(value: number): string {
  const size = Math.abs(value)
  const text = Number.isInteger(size) ? size.toFixed(0) : size.toFixed(1)
  return value < 0 ? `${MINUS}${text}` : text
}

/** A fair moneyline at the nearest 5, never inside ±100 (an even price reads "+100"). */
export function bookMoneyline(odds: number): number {
  const size = Math.max(100, Math.round(Math.abs(odds) / 5) * 5)
  return odds < 0 && size > 100 ? -size : size
}

/** TSI's spread naming the favorite: "LSU −8.5". */
export function tsiFavoriteLine(spread: number, home: TeamRef, away: TeamRef): string {
  const line = bookLine(spread)
  if (line === 0) return "Pick 'em"
  const favorite = line < 0 ? home : away
  return `${favorite.abbreviation ?? favorite.school} ${halfText(-Math.abs(line))}`
}

/** TSI's spread from one team's side: "+8.5", "−8.5". */
export function tsiSpread(spread: number): string {
  return teamSpread(bookLine(spread))
}

/** TSI's total or team total: "44.5", "56.5". */
export function tsiTotal(total: number): string {
  return halfText(bookLine(total))
}

/** TSI's fair moneyline as posted: "−275", "+155". */
export function tsiMoneyline(odds: number): string {
  return american(bookMoneyline(odds))
}

/** TSI's favorite on the moneyline: "ND −145" (home on a tie). */
export function tsiFavoriteMoneyline(home: TeamRef, away: TeamRef, homeMl: number, awayMl: number) {
  const homeFav = homeMl <= awayMl
  const team = homeFav ? home : away
  return `${team.abbreviation ?? team.school} ${tsiMoneyline(homeFav ? homeMl : awayMl)}`
}
