import type { ModelVersion } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { formatUpdated } from "@/lib/format/time"

/** Each model version's latest backtest on the validation seasons, newest first. */
export function VersionHistory({ versions }: { versions: ModelVersion[] }) {
  if (versions.length === 0) return null
  return (
    <div className="rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="bg-card text-muted-foreground">
          <tr className="border-b border-border">
            <th scope="col" className="px-3 py-2 text-left font-medium">
              Version
            </th>
            <th scope="col" className="hidden px-3 py-2 text-left font-medium sm:table-cell">
              Backtested
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium">
              TSI error
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium">
              Vegas error
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium">
              Winners
            </th>
          </tr>
        </thead>
        <tbody>
          {[...versions].reverse().map((v, i) => (
            <tr key={v.model_version} className="border-b border-border last:border-0">
              <th scope="row" className="px-3 py-2 text-left font-semibold">
                {v.model_version.replace(/^tsi-/, "")}
                {i === 0 && <span className="ml-2 text-xs font-normal text-primary">current</span>}
              </th>
              <td className="hidden px-3 py-2 whitespace-nowrap text-muted-foreground sm:table-cell">
                {formatUpdated(v.run_at)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {v.validate_mae == null ? "—" : v.validate_mae.toFixed(2)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {v.validate_market_mae == null ? "—" : v.validate_market_mae.toFixed(2)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">
                {v.validate_su == null ? "—" : percent(v.validate_su)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
