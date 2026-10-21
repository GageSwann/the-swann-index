import type { ReactNode } from "react"

import type { GameCenter, PickView } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { american, favoriteLine, totalLine } from "@/lib/format/odds"
import { cn } from "@/lib/utils"

type MarketRow = {
  label: string
  fair: ReactNode
  book: ReactNode
  market: ReactNode | null
  pick?: PickView
}

const COLUMNS = [
  { key: "fair", label: "TSI fair", help: "No vig: TSI's own line" },
  { key: "book", label: "TSI Book", help: "TSI's line with standard vig" },
  { key: "market", label: "Vegas", help: "Consensus of sportsbooks" },
] as const

/**
 * Every market three ways: TSI's fair price (no vig), the TSI Book's price (with vig),
 * and the market consensus. A TSI play is outlined in amber. A table from `sm` up; on
 * phones each market is its own block so nothing scrolls sideways.
 */
export function OddsBoard({ center }: { center: GameCenter }) {
  const { game, markets } = center
  const p = game.prediction
  const m = game.market
  if (!p || !markets) return null
  const { home, away } = game
  const pickFor = (market: string) => p.picks.find((x) => x.market === market)
  const name = (t: typeof home) => t.abbreviation ?? t.school

  const rows: MarketRow[] = [
    {
      label: "Spread",
      pick: pickFor("spread"),
      fair: favoriteLine(markets.fair_spread, home, away),
      book: (
        <Priced
          line={favoriteLine(markets.spread.line ?? 0, home, away, 1)}
          odds={markets.spread.first.book}
          note={`${name(home)} covers ${percent(markets.spread.first.prob, 0)}`}
        />
      ),
      market: m?.spread != null ? favoriteLine(m.spread, home, away) : null,
    },
    {
      label: "Total",
      pick: pickFor("total"),
      fair: markets.fair_total.toFixed(1),
      book: (
        <Priced
          line={`O/U ${totalLine(markets.total.line ?? 0)}`}
          odds={markets.total.first.book}
          note={`over ${percent(markets.total.first.prob, 0)}`}
        />
      ),
      market: m?.total != null ? totalLine(m.total) : null,
    },
    {
      label: "Moneyline",
      pick: pickFor("ml"),
      fair: (
        <Pair
          a={`${name(away)} ${american(p.fair_away_ml)}`}
          b={`${name(home)} ${american(p.fair_home_ml)}`}
        />
      ),
      book: (
        <Pair
          a={`${name(away)} ${american(p.book_away_ml)}`}
          b={`${name(home)} ${american(p.book_home_ml)}`}
        />
      ),
      market:
        m?.home_ml != null && m.away_ml != null ? (
          <Pair
            a={`${name(away)} ${american(m.away_ml)}`}
            b={`${name(home)} ${american(m.home_ml)}`}
          />
        ) : null,
    },
    {
      label: `${home.school} points`,
      fair: p.proj_home.toFixed(1),
      book: (
        <Priced
          line={`O/U ${totalLine(markets.home_total.line ?? 0)}`}
          odds={markets.home_total.first.book}
        />
      ),
      market: null,
    },
    {
      label: `${away.school} points`,
      fair: p.proj_away.toFixed(1),
      book: (
        <Priced
          line={`O/U ${totalLine(markets.away_total.line ?? 0)}`}
          odds={markets.away_total.first.book}
        />
      ),
      market: null,
    },
  ]

  return (
    <section aria-labelledby="odds-heading" className="space-y-3">
      <h2 id="odds-heading" className="text-2xl font-semibold font-stretch-condensed">
        Odds board
      </h2>
      <div className="hidden rounded-md border border-border sm:block">
        <table className="w-full text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <th scope="col" className="px-3 py-2 text-left font-medium">
                Market
              </th>
              {COLUMNS.map((c) => (
                <th
                  key={c.key}
                  scope="col"
                  className="px-3 py-2 text-right font-medium"
                  title={c.help}
                >
                  {c.label}
                </th>
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

function Priced({ line, odds, note }: { line: string; odds: number; note?: string }) {
  return (
    <span className="inline-flex flex-col items-end">
      <span>
        {line} <span className="text-muted-foreground">{american(odds)}</span>
      </span>
      {note && <span className="text-xs text-muted-foreground">{note}</span>}
    </span>
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
