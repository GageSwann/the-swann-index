const MINUS = "−" // typographic minus: lines up with "+" in tabular figures

/** "+22.8", "−3.1", "0.0" (ratings and margins in points). */
export function signed(value: number, digits = 1): string {
  const text = Math.abs(value).toFixed(digits)
  if (Number(text) === 0) return (0).toFixed(digits)
  return `${value > 0 ? "+" : MINUS}${text}`
}

/**
 * A score as shown: whole points, never below 0 (Phase 12.3). The model floors the
 * underdog's projection since v1.7 (#132); this also covers forecasts published before.
 */
export function points(value: number): number {
  return Math.max(0, Math.round(value))
}

/** "6-1", or "6-1-1" with ties. */
export function record(wins: number, losses: number, ties = 0): string {
  return ties > 0 ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`
}

/** 0.108 → "10.8%". */
export function percent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`
}

/** A probability as a whole percent that never claims certainty: "<1%", "37%", ">99%". */
export function chance(value: number): string {
  if (value < 0.005) return "<1%"
  if (value > 0.995) return ">99%"
  return percent(value, 0)
}
