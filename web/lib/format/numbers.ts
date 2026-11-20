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

/**
 * A probability that never claims certainty (owner, 2026-11-20): "<1%", "37%", ">99%".
 * With `digits`, the bounds follow the shown precision: "<0.1%" / ">99.9%" for 1.
 */
export function chance(value: number, digits = 0): string {
  const step = 10 ** -digits // smallest shown step, in percent
  const shown = Number((value * 100).toFixed(digits))
  if (shown < step) return `<${step.toFixed(digits)}%`
  if (shown > 100 - step) return `>${(100 - step).toFixed(digits)}%`
  return percent(value, digits)
}
