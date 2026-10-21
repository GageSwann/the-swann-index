import type { ReactNode } from "react"

import type { GameCenter, PickView } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { american, favoriteLine, totalLine } from "@/lib/format/odds"

/** One market on the odds board: TSI's fair price, the Book's price and Vegas. */
export type MarketRow = {
  label: string
  fair: ReactNode
  book: ReactNode
  market: ReactNode | null
  pick?: PickView
}

export const COLUMNS = [
  { key: "fair", label: "TSI fair", help: "No vig: TSI's own line" },
  { key: "book", label: "TSI Book", help: "TSI's line with standard vig" },
  { key: "market", label: "Vegas", help: "Consensus of sportsbooks" },
] as const

/** The odds board's rows (spread, total, moneyline, team totals); null without a forecast. */
export function marketRows(center: GameCenter): MarketRow[] | null {
  const { game, markets } = center
  const p = game.prediction
  const m = game.market
  if (!p || !markets) return null
  const { home, away } = game
  const pickFor = (market: string) => p.picks.find((x) => x.market === market)
  const name = (t: typeof home) => t.abbreviation ?? t.school

  return [
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
