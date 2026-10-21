import { UnitsChart } from "@/components/book/units-chart"
import type { BookBacktestRow, BookUnitsPoint } from "@/lib/api/types"
import { percent, record, signed } from "@/lib/format/numbers"
import { MARKET_LABEL, units } from "@/lib/format/picks"
import { cn } from "@/lib/utils"
import { HeadCell } from "@/components/ui/head-cell"

/**
 * The Book replayed on past seasons at the median opening line (openers exist from 2021),
 * graded against final scores, with CLV against the closing consensus.
 */
export function BookBacktest({
  rows,
  points,
}: {
  rows: BookBacktestRow[]
  points: BookUnitsPoint[]
}) {
  const tier0 = rows.filter((r) => r.tier === 0)
  const isSeason = (r: BookBacktestRow) => /^\d{4}$/.test(r.period)
  const periods = tier0.filter((r) => !isSeason(r))
  const seasons = tier0.filter(isSeason)
  const last = seasons[seasons.length - 1]?.period
  // Name the market only when more than one has picks (in practice: totals only).
  const multi = new Set(tier0.map((r) => r.market)).size > 1

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <HeadCell>Period</HeadCell>
              <HeadCell align="right">Record</HeadCell>
              <HeadCell align="right">Units</HeadCell>
              <HeadCell align="right" className="hidden sm:table-cell">
                ROI
              </HeadCell>
              <HeadCell align="right" title="Average closing-line value; share that beat the close">
                CLV
              </HeadCell>
            </tr>
          </thead>
          <tbody>
            {[...periods, ...seasons].map((r, i) => (
              <tr
                key={`${r.period}-${r.market}`}
                className={cn(
                  "border-b border-border last:border-0",
                  i < periods.length && "bg-card/60 font-semibold",
                  i === periods.length && "border-t-2",
                )}
              >
                <th
                  scope="row"
                  className={cn(
                    "px-3 py-2 text-left",
                    i < periods.length ? "font-semibold" : "font-normal",
                  )}
                >
                  {r.period}
                  {r.period === last && "*"}
                  {multi && `, ${MARKET_LABEL[r.market] ?? r.market}`}
                </th>
                <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                  {record(r.wins, r.losses, r.pushes)}
                </td>
                <td
                  className={cn(
                    "px-3 py-2 text-right tabular-nums",
                    r.units > 0 ? "text-up" : r.units < 0 && "text-down",
                  )}
                >
                  {units(r.units)}
                </td>
                <td className="hidden px-3 py-2 text-right tabular-nums sm:table-cell">
                  {signed(r.roi * 100)}%
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                  {r.clv == null ? "—" : `${signed(r.clv)} pts`}
                  {r.beat_close != null && (
                    <span className="hidden text-muted-foreground sm:inline">
                      {" "}
                      ({percent(r.beat_close, 0)})
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <UnitsChart points={points} />
      <p className="text-xs text-muted-foreground">
        Simulated, not live: picks are made with the same rules at the median opening line and
        graded at −110. Train seasons tuned the trust factor; validation seasons were never used to
        fit anything. * {last} so far.
      </p>
    </div>
  )
}
