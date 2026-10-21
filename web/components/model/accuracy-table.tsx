import type { AccuracyRow, LiveAccuracy } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { cn } from "@/lib/utils"
import { HeadCell } from "@/components/ui/head-cell"

// Secondary columns (games, Elo, Vegas winners) are hidden on phones so the comparison
// that matters (TSI vs. the closing line) fits without scrolling.
const WIDE = "hidden sm:table-cell"
const CELL = "px-3 py-2 text-right tabular-nums"

/**
 * Prediction accuracy by period: TSI's published (stacked) prediction vs. the Elo baseline
 * and the closing line. Lower error is better; the best of each row is bold.
 */
export function AccuracyTable({ rows, live }: { rows: AccuracyRow[]; live: LiveAccuracy }) {
  return (
    <div className="rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="bg-card text-muted-foreground">
          <tr className="border-b border-border">
            <HeadCell>Period</HeadCell>
            <HeadCell align="right" className={WIDE}>
              Games
            </HeadCell>
            <HeadCell align="right" title="Average miss on the final margin, in points">
              TSI error
            </HeadCell>
            <HeadCell align="right" className={WIDE}>
              Elo error
            </HeadCell>
            <HeadCell align="right">Vegas error</HeadCell>
            <HeadCell align="right" title="Predicted winner won (straight up)">
              TSI winners
            </HeadCell>
            <HeadCell align="right" className={WIDE}>
              Vegas winners
            </HeadCell>
          </tr>
        </thead>
        <tbody>
          {live.games > 0 && live.mae != null && (
            <tr className="border-b border-border bg-card/60">
              <th scope="row" className="px-3 py-2 text-left font-semibold">
                This season, live
              </th>
              <td className={cn(CELL, WIDE)}>{live.games}</td>
              <td className={cn(CELL, "font-semibold")}>{live.mae.toFixed(2)}</td>
              <td className={cn(CELL, WIDE, "text-muted-foreground")}>—</td>
              <td className={CELL}>{live.market_mae == null ? "—" : live.market_mae.toFixed(2)}</td>
              <td className={CELL}>{live.su_accuracy == null ? "—" : percent(live.su_accuracy)}</td>
              <td className={cn(CELL, WIDE, "text-muted-foreground")}>—</td>
            </tr>
          )}
          {rows.map((r) => {
            const best = Math.min(r.predictive_mae, r.elo_mae, r.vegas_mae)
            const err = (v: number, wide = false) => (
              <td className={cn(CELL, wide && WIDE, v === best && "font-bold")}>{v.toFixed(2)}</td>
            )
            return (
              <tr key={r.label} className="border-b border-border last:border-0">
                <th scope="row" className="px-3 py-2 text-left font-medium">
                  {r.label}
                </th>
                <td className={cn(CELL, WIDE)}>{r.games.toLocaleString()}</td>
                {err(r.predictive_mae)}
                {err(r.elo_mae, true)}
                {err(r.vegas_mae)}
                <td className={CELL}>{percent(r.predictive_su)}</td>
                <td className={cn(CELL, WIDE)}>{percent(r.vegas_su)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
