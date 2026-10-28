import type { ReactNode } from "react"

import { HeadCell } from "@/components/ui/head-cell"
import type { Matchup } from "@/lib/api/types"
import { american, favoriteLine, totalLine } from "@/lib/format/odds"

/**
 * TSI's prices for a hypothetical game: the fair line (no vig) and the TSI Book's price
 * (with vig). No Vegas column: books only post lines for scheduled games.
 */
export function MatchupOdds({ matchup }: { matchup: Matchup }) {
  const { home, away, markets: m } = matchup
  const name = (t: typeof home) => t.abbreviation ?? t.school
  const rows: { label: string; fair: ReactNode; book: ReactNode }[] = [
    {
      label: "Spread",
      fair: favoriteLine(m.fair_spread, home, away),
      book: (
        <>
          {favoriteLine(m.spread.line ?? 0, home, away, 1)}{" "}
          <span className="text-muted-foreground">{american(m.spread.first.book)}</span>
        </>
      ),
    },
    {
      label: "Total",
      fair: m.fair_total.toFixed(1),
      book: (
        <>
          O/U {totalLine(m.total.line ?? 0)}{" "}
          <span className="text-muted-foreground">{american(m.total.first.book)}</span>
        </>
      ),
    },
    {
      label: "Moneyline",
      fair: (
        <Pair
          a={`${name(away)} ${american(m.moneyline.second.fair)}`}
          b={`${name(home)} ${american(m.moneyline.first.fair)}`}
        />
      ),
      book: (
        <Pair
          a={`${name(away)} ${american(m.moneyline.second.book)}`}
          b={`${name(home)} ${american(m.moneyline.first.book)}`}
        />
      ),
    },
    {
      label: `${away.school} points`,
      fair: matchup.proj_away.toFixed(1),
      book: `O/U ${totalLine(m.away_total.line ?? 0)}`,
    },
    {
      label: `${home.school} points`,
      fair: matchup.proj_home.toFixed(1),
      book: `O/U ${totalLine(m.home_total.line ?? 0)}`,
    },
  ]

  return (
    <section aria-labelledby="odds-heading" className="space-y-3">
      <h2 id="odds-heading" className="text-2xl font-semibold font-stretch-condensed">
        TSI&apos;s line
      </h2>
      <div className="rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <HeadCell>Market</HeadCell>
              <HeadCell align="right" title="No vig: TSI's own line">
                TSI fair
              </HeadCell>
              <HeadCell align="right" title="TSI's line with standard vig">
                TSI Book
              </HeadCell>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className="border-b border-border last:border-0">
                <th scope="row" className="px-3 py-2.5 text-left font-medium">
                  {r.label}
                </th>
                <td className="px-3 py-2.5 text-right tabular-nums">{r.fair}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">{r.book}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function Pair({ a, b }: { a: string; b: string }) {
  return (
    <span className="inline-flex flex-col items-end">
      <span>{a}</span>
      <span>{b}</span>
    </span>
  )
}
