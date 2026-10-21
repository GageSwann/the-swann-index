import type { AtsRow, TotalsRow } from "@/lib/api/types"
import { percent, record, signed } from "@/lib/format/numbers"

const BREAK_EVEN = 110 / 210 // a −110 bet needs to win 52.4%

/**
 * The honest part: does TSI beat the closing line? Spreads (when it disagrees by N+
 * points) and totals (error vs. the closing total), validation seasons.
 */
export function MarketChecks({ ats, totals }: { ats: AtsRow[]; totals: TotalsRow[] }) {
  const validate = totals.find((t) => t.period.startsWith("Validate"))
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Spreads at the closing line</h3>
        <p className="text-sm text-muted-foreground">
          Picking TSI&apos;s side whenever it disagrees with the close. Break-even at −110 is{" "}
          {percent(BREAK_EVEN)}; TSI doesn&apos;t clear it, which is why the Book almost never bets
          spreads.
        </p>
        <table className="w-full text-sm">
          <thead className="text-muted-foreground">
            <tr className="border-b border-border">
              <th scope="col" className="py-1.5 text-left font-medium">
                Disagreement
              </th>
              <th scope="col" className="py-1.5 text-right font-medium">
                Record
              </th>
              <th scope="col" className="py-1.5 text-right font-medium">
                Win rate
              </th>
            </tr>
          </thead>
          <tbody>
            {ats.map((a) => (
              <tr key={a.min_edge} className="border-b border-border last:border-0">
                <th scope="row" className="py-1.5 text-left font-normal">
                  {a.min_edge === 0 ? "Any" : `${a.min_edge}+ points`}
                </th>
                <td className="py-1.5 text-right tabular-nums">
                  {record(a.wins, a.losses, a.pushes)}
                </td>
                <td className="py-1.5 text-right tabular-nums">{percent(a.win_rate)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {validate && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">Game totals</h3>
          <p className="text-sm text-muted-foreground">
            Average miss on the combined score over {validate.games.toLocaleString()} validation
            games. The closing total is a little sharper, but TSI beats the <em>opening</em> total
            often enough for the Book to bet it.
          </p>
          <dl className="grid grid-cols-3 gap-4">
            <div>
              <dt className="text-sm text-muted-foreground">TSI</dt>
              <dd className="text-2xl font-bold font-stretch-condensed">
                {validate.tsi_mae.toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-muted-foreground">Vegas close</dt>
              <dd className="text-2xl font-bold font-stretch-condensed">
                {validate.vegas_mae.toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-muted-foreground">TSI bias</dt>
              <dd className="text-2xl font-bold font-stretch-condensed">{signed(validate.bias)}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  )
}
