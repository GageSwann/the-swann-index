import { HeadCell } from "@/components/ui/head-cell"
import type { GameCenter, PickView } from "@/lib/api/types"
import { cn } from "@/lib/utils"

import { COLUMNS, marketRows } from "./odds-rows"

/**
 * Every market three ways: TSI's fair price (no vig), the TSI Book's price (with vig),
 * and the market consensus. A TSI play is outlined in amber. A table from `sm` up; on
 * phones each market is its own block so nothing scrolls sideways.
 */
export function OddsBoard({ center }: { center: GameCenter }) {
  const rows = marketRows(center)
  if (!rows) return null

  return (
    <section aria-labelledby="odds-heading" className="space-y-3">
      <h2 id="odds-heading" className="text-2xl font-semibold font-stretch-condensed">
        Odds board
      </h2>
      <div className="hidden rounded-md border border-border sm:block">
        <table className="w-full text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <HeadCell>Market</HeadCell>
              {COLUMNS.map((c) => (
                <HeadCell key={c.key} align="right" title={c.help}>
                  {c.label}
                </HeadCell>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className="border-b border-border last:border-0">
                <th scope="row" className="px-3 py-2.5 text-left font-medium">
                  {r.label}
                  {r.pick && <PlayTag pick={r.pick} />}
                </th>
                {COLUMNS.map((c) => (
                  <td
                    key={c.key}
                    className={cn(
                      "px-3 py-2.5 text-right",
                      c.key === "book" && r.pick && "ring-1 ring-primary ring-inset",
                    )}
                  >
                    {r[c.key] ?? <span className="text-muted-foreground">—</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="divide-y divide-border rounded-md border border-border text-sm sm:hidden">
        {rows.map((r) => (
          <div key={r.label} className="space-y-1.5 px-3 py-2.5">
            <h3 className="font-medium">
              {r.label}
              {r.pick && <PlayTag pick={r.pick} />}
            </h3>
            <dl className="space-y-1">
              {COLUMNS.map((c) => (
                <div
                  key={c.key}
                  className={cn(
                    "flex items-start justify-between gap-4 rounded-sm",
                    c.key === "book" && r.pick && "-mx-1.5 px-1.5 py-0.5 ring-1 ring-primary",
                  )}
                >
                  <dt className="text-muted-foreground">{c.label}</dt>
                  <dd className="text-right">
                    {r[c.key] ?? <span className="text-muted-foreground">—</span>}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Vegas is the median of sportsbooks&apos; current lines (closing lines once the game starts).
        Team totals aren&apos;t in the market data yet.
      </p>
    </section>
  )
}

function PlayTag({ pick }: { pick: PickView }) {
  return (
    <span className="ml-2 rounded-sm bg-primary px-1 py-0.5 text-xs text-primary-foreground">
      {"★".repeat(pick.tier)} TSI play
    </span>
  )
}
