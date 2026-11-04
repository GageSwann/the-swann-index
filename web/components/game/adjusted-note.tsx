import type { ReactNode } from "react"

import type { GameSummary, SnapshotView } from "@/lib/api/types"
import { describeAdjustment } from "@/lib/format/adjustments"
import { chance } from "@/lib/format/numbers"
import { favoriteLine } from "@/lib/format/odds"
import { cn } from "@/lib/utils"

type Props = { prediction: SnapshotView; game: GameSummary; className?: string }

/**
 * Shown when a prediction includes the operator's manual adjustments (decision #104):
 * what was adjusted and why, and the raw model's own numbers, so both are always visible.
 */
export function AdjustedNote({ prediction: p, game, className }: Props) {
  if (!p.adjusted) return null
  const raw = p.raw
  const favorite = raw && (raw.home_win_prob >= 0.5 ? game.home : game.away)
  return (
    <AdjustedCallout className={className}>
      {p.adjustments.map(describeAdjustment).join("; ") || "manual adjustment"}.
      {raw && favorite && (
        <>
          {" "}
          The model alone: {favoriteLine(raw.spread, game.home, game.away)}, total{" "}
          {raw.total.toFixed(1)}, {favorite.abbreviation ?? favorite.school} wins{" "}
          {chance(Math.max(raw.home_win_prob, 1 - raw.home_win_prob))}.
        </>
      )}
    </AdjustedCallout>
  )
}

/** "Adjusted: …" set off with the accent rule (game notes and the team header). */
export function AdjustedCallout({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <p className={cn("border-l-2 border-primary pl-2 text-sm text-muted-foreground", className)}>
      <span className="font-semibold text-foreground">Adjusted:</span> {children}
    </p>
  )
}
