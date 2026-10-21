import type { ReactNode } from "react"

import type { GameCenter, PickView } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { american, favoriteLine, totalLine } from "@/lib/format/odds"
import { cn } from "@/lib/utils"

/**
 * Every market three ways: TSI's fair price (no vig), the TSI Book's price (with vig),
 * and the market consensus. A TSI play is outlined in amber.
 */
export function OddsBoard({ center }: { center: GameCenter }) {
  const { game, markets } = center
  const p = game.prediction
  const m = game.market
  if (!p || !markets) return null
  const { home, away } = game
  const pickFor = (market: string) => p.picks.find((x) => x.market === market)
  const name = (t: typeof home) => t.abbreviation ?? t.school

  return (
    <section aria-labelledby="odds-heading" className="space-y-3">
      <h2 id="odds-heading" className="text-2xl font-semibold font-stretch-condensed">
        Odds board
      </h2>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <th scope="col" className="px-3 py-2 text-left font-medium">
                Market
              </th>
              <th
                scope="col"
                className="px-3 py-2 text-right font-medium"
                title="No vig: TSI's own line"
              >
                TSI fair
              </th>
              <th
                scope="col"
                className="px-3 py-2 text-right font-medium"
                title="TSI's line with standard vig"
              >
                TSI Book
              </th>
              <th
                scope="col"
                className="px-3 py-2 text-right font-medium"
                title="Consensus of sportsbooks"
              >
                Vegas
              </th>
            </tr>
          </thead>
          <tbody>
            <Row
              label="Spread"
              pick={pickFor("spread")}
              fair={favoriteLine(markets.fair_spread, home, away)}
              book={
                <Priced
                  line={favoriteLine(markets.spread.line ?? 0, home, away, 1)}
                  odds={markets.spread.first.book}
                  note={`${name(home)} covers ${percent(markets.spread.first.prob, 0)}`}
                />
              }
              market={m?.spread != null ? favoriteLine(m.spread, home, away) : null}
            />
            <Row
              label="Total"
              pick={pickFor("total")}
              fair={markets.fair_total.toFixed(1)}
              book={
                <Priced
                  line={`O/U ${totalLine(markets.total.line ?? 0)}`}
                  odds={markets.total.first.book}
                  note={`over ${percent(markets.total.first.prob, 0)}`}
                />
              }
              market={m?.total != null ? totalLine(m.total) : null}
            />
            <Row
              label="Moneyline"
              pick={pickFor("ml")}
              fair={
                <Pair
                  a={`${name(away)} ${american(p.fair_away_ml)}`}
                  b={`${name(home)} ${american(p.fair_home_ml)}`}
                />
              }
              book={
                <Pair
                  a={`${name(away)} ${american(p.book_away_ml)}`}
                  b={`${name(home)} ${american(p.book_home_ml)}`}
                />
              }
              market={
                m?.home_ml != null && m.away_ml != null ? (
                  <Pair
                    a={`${name(away)} ${american(m.away_ml)}`}
                    b={`${name(home)} ${american(m.home_ml)}`}
                  />
                ) : null
              }
            />
            <Row
              label={`${home.school} points`}
              fair={p.proj_home.toFixed(1)}
              book={
                <Priced
                  line={`O/U ${totalLine(markets.home_total.line ?? 0)}`}
                  odds={markets.home_total.first.book}
                />
              }
              market={null}
            />
            <Row
              label={`${away.school} points`}
              fair={p.proj_away.toFixed(1)}
              book={
                <Priced
                  line={`O/U ${totalLine(markets.away_total.line ?? 0)}`}
                  odds={markets.away_total.first.book}
                />
              }
              market={null}
            />
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">
        Vegas is the median of sportsbooks&apos; current lines (closing lines once the game starts).
        Team totals aren&apos;t in the market data yet.
      </p>
    </section>
  )
}

function Row({
  label,
  fair,
  book,
  market,
  pick,
}: {
  label: string
  fair: ReactNode
  book: ReactNode
  market: ReactNode | null
  pick?: PickView
}) {
  return (
    <tr className="border-b border-border last:border-0">
      <th scope="row" className="px-3 py-2.5 text-left font-medium">
        {label}
        {pick && (
          <span className="ml-2 rounded-sm bg-primary px-1 py-0.5 text-xs text-primary-foreground">
            {"★".repeat(pick.tier)} TSI play
          </span>
        )}
      </th>
      <td className="px-3 py-2.5 text-right">{fair}</td>
      <td className={cn("px-3 py-2.5 text-right", pick && "ring-1 ring-primary ring-inset")}>
        {book}
      </td>
      <td className="px-3 py-2.5 text-right">
        {market ?? <span className="text-muted-foreground">—</span>}
      </td>
    </tr>
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
