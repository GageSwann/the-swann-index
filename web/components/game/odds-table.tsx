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
 * consensus. A table from `sm` up; on phones a compact grid with the same columns, sized
 * to fit (#165), so nothing scrolls sideways.
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
      <div className="rounded-md border border-border text-sm sm:hidden">
        <div
          aria-hidden
          className={`grid ${vegas ? "grid-cols-[minmax(0,0.9fr)_minmax(0,1.3fr)_minmax(0,0.9fr)]" : "grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]"} gap-2 border-b border-border bg-card px-3 py-1.5 text-xs text-muted-foreground`}
        >
          <span>Market</span>
          {columns.map((c) => (
            <span key={c.key} className="text-right">
              {c.label}
            </span>
          ))}
        </div>
        <dl className="divide-y divide-border">
          {rows.map((r) => (
            <div
              key={r.label}
              className={`grid ${vegas ? "grid-cols-[minmax(0,0.9fr)_minmax(0,1.3fr)_minmax(0,0.9fr)]" : "grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]"} items-start gap-2 px-3 py-2`}
            >
              <dt className="font-medium">{r.label}</dt>
              {columns.map((c) => (
                <dd key={c.key} className="text-right">
                  <span className="sr-only">{c.label}: </span>
                  {cell(r, c.key)}
                </dd>
              ))}
            </div>
          ))}
        </dl>
      </div>
      {note && <p className="text-xs text-muted-foreground">{note}</p>}
    </section>
  )
}
