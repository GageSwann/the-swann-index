import type { ReactNode } from "react"

import type { LedgerRecord } from "@/lib/api/types"
import { percent, record, signed } from "@/lib/format/numbers"
import { MARKET_LABEL, units } from "@/lib/format/picks"
import { cn } from "@/lib/utils"

/** Graded record per market, then per ★ tier within it (bigger edges should do better). */
export function TierTable({ records }: { records: LedgerRecord[] }) {
  const markets = records.filter((r) => r.market !== "all" && r.tier === 0)
  if (markets.length === 0) return null

  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="bg-card text-muted-foreground">
          <tr className="border-b border-border">
            <th scope="col" className="px-2 py-2 text-left font-medium sm:px-3">
              Market
            </th>
            <th scope="col" className="px-2 py-2 text-right font-medium sm:px-3">
              Record
            </th>
            <th scope="col" className="px-2 py-2 text-right font-medium sm:px-3">
              Units
            </th>
            <th
              scope="col"
              className="hidden px-2 py-2 text-right font-medium sm:table-cell sm:px-3"
            >
              ROI
            </th>
            <th
              scope="col"
              className="px-2 py-2 text-right font-medium sm:px-3"
              title="Average closing-line value; share that beat the close"
            >
              CLV
            </th>
          </tr>
        </thead>
        <tbody>
          {markets.flatMap((m) => [
            <Row key={m.market} r={m} label={MARKET_LABEL[m.market]} strong />,
            ...records
              .filter((r) => r.market === m.market && r.tier > 0)
              .map((r) => (
                <Row
                  key={`${r.market}-${r.tier}`}
                  r={r}
                  label={
                    <span className="pl-3 text-primary" aria-label={`${r.tier} star`}>
                      {"★".repeat(r.tier)}
                    </span>
                  }
                />
              )),
          ])}
        </tbody>
      </table>
    </div>
  )
}

function Row({
  r,
  label,
  strong = false,
}: {
  r: LedgerRecord
  label: ReactNode
  strong?: boolean
}) {
  return (
    <tr
      className={cn("border-b border-border last:border-0", strong && "bg-card/60 font-semibold")}
    >
      <th
        scope="row"
        className={cn("px-2 py-2 text-left sm:px-3", strong ? "font-semibold" : "font-normal")}
      >
        {label}
      </th>
      <td className="px-2 py-2 text-right whitespace-nowrap tabular-nums sm:px-3">
        {record(r.wins, r.losses, r.pushes)}
      </td>
      <td
        className={cn(
          "px-2 py-2 text-right tabular-nums sm:px-3",
          r.units > 0 ? "text-up" : r.units < 0 && "text-down",
        )}
      >
        {units(r.units)}
      </td>
      <td className="hidden px-2 py-2 text-right tabular-nums sm:table-cell sm:px-3">
        {signed(r.roi * 100)}%
      </td>
      <td className="px-2 py-2 text-right whitespace-nowrap tabular-nums sm:px-3">
        {r.clv == null ? (
          "—"
        ) : (
          <>
            {signed(r.clv)} pts
            {r.beat_close != null && (
              <span className="hidden text-muted-foreground sm:inline">
                {" "}
                ({percent(r.beat_close, 0)})
              </span>
            )}
          </>
        )}
      </td>
    </tr>
  )
}
