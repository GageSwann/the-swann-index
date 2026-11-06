import type { ReactNode } from "react"

import { HeadCell } from "@/components/ui/head-cell"

import type { MarketRow } from "./odds-rows"

const COLUMNS = [
  { key: "fair", label: "TSI", help: "TSI's own line, no vig" },
  { key: "market", label: "Vegas", help: "Consensus of sportsbooks" },
] as const

type Props = { title: string; rows: MarketRow[]; vegas: boolean; note?: ReactNode }

/**
 * Markets side by side: TSI's own line (no vig) and, for scheduled games, the market
 * consensus. A table from `sm` up; on phones each market is its own block so nothing
 * scrolls sideways.
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
                </th>
                {columns.map((c) => (
                  <td key={c.key} className="px-3 py-2.5 text-right">
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
            <h3 className="font-medium">{r.label}</h3>
            <dl className="space-y-1">
              {columns.map((c) => (
                <div key={c.key} className="flex items-start justify-between gap-4">
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
