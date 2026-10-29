import type { ReactNode } from "react"

import { HeadCell } from "@/components/ui/head-cell"
import type { PickView } from "@/lib/api/types"
import { cn } from "@/lib/utils"

import type { MarketRow } from "./odds-rows"

const COLUMNS = [
  { key: "fair", label: "TSI fair", help: "No vig: TSI's own line" },
  { key: "book", label: "TSI Book", help: "TSI's line with standard vig" },
  { key: "market", label: "Vegas", help: "Consensus of sportsbooks" },
] as const

type Props = { title: string; rows: MarketRow[]; vegas: boolean; note?: ReactNode }

/**
 * Markets side by side: TSI's fair price (no vig), the TSI Book's price (with vig) and,
 * for scheduled games, the market consensus. A TSI play is outlined in amber. A table
 * from `sm` up; on phones each market is its own block so nothing scrolls sideways.
 */
export function OddsTable({ title, rows, vegas, note }: Props) {
  const columns = vegas ? COLUMNS : COLUMNS.filter((c) => c.key !== "market")
  const cell = (r: MarketRow, key: (typeof columns)[number]["key"]) =>
    r[key] ?? <span className="text-muted-foreground">—</span>

  return (
    <section aria-labelledby="odds-heading" className="space-y-3">
      <h2 id="odds-heading" className="text-2xl font-semibold font-stretch-condensed">
        {title}
      </h2>
      <div className="hidden rounded-md border border-border sm:block">
        <table className="w-full text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <HeadCell>Market</HeadCell>
              {columns.map((c) => (
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
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={cn(
                      "px-3 py-2.5 text-right",
                      c.key === "book" && r.pick && "ring-1 ring-primary ring-inset",
                    )}
                  >
                    {cell(r, c.key)}
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
              {columns.map((c) => (
                <div
                  key={c.key}
                  className={cn(
                    "flex items-start justify-between gap-4 rounded-sm",
                    c.key === "book" && r.pick && "-mx-1.5 px-1.5 py-0.5 ring-1 ring-primary",
                  )}
                >
                  <dt className="text-muted-foreground">{c.label}</dt>
                  <dd className="text-right">{cell(r, c.key)}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
      {note && <p className="text-xs text-muted-foreground">{note}</p>}
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
