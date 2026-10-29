import type { ReactNode } from "react"

import type { GameCenter, GameMarkets, PickView, TeamRef } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { american, favoriteLine, totalLine } from "@/lib/format/odds"

/** One market in an odds table: TSI's fair price, the Book's price and (games only) Vegas. */
export type MarketRow = {
  label: string
  fair: ReactNode
  book: ReactNode
  market?: ReactNode | null
  pick?: PickView
}

type Priced = {
  markets: GameMarkets
  home: TeamRef
  away: TeamRef
  projHome: number
  projAway: number
  picks?: PickView[]
}

/** TSI's fair and Book prices for spread, total, moneyline and team totals. */
export function tsiRows({
  markets,
  home,
  away,
  projHome,
  projAway,
  picks = [],
}: Priced): MarketRow[] {
  const pickFor = (market: string) => picks.find((x) => x.market === market)
  const ml = markets.moneyline
  return [
    {
      label: "Spread",
      pick: pickFor("spread"),
      fair: favoriteLine(markets.fair_spread, home, away),
      book: (
        <Price
          line={favoriteLine(markets.spread.line ?? 0, home, away, 1)}
          odds={markets.spread.first.book}
          note={`${short(home)} covers ${percent(markets.spread.first.prob, 0)}`}
        />
      ),
    },
    {
      label: "Total",
      pick: pickFor("total"),
      fair: markets.fair_total.toFixed(1),
      book: (
        <Price
          line={`O/U ${totalLine(markets.total.line ?? 0)}`}
          odds={markets.total.first.book}
          note={`over ${percent(markets.total.first.prob, 0)}`}
        />
      ),
    },
    {
      label: "Moneyline",
      pick: pickFor("ml"),
      fair: <TeamPair home={home} away={away} homeOdds={ml.first.fair} awayOdds={ml.second.fair} />,
      book: <TeamPair home={home} away={away} homeOdds={ml.first.book} awayOdds={ml.second.book} />,
    },
    {
      label: `${home.school} points`,
      fair: projHome.toFixed(1),
      book: (
        <Price
          line={`O/U ${totalLine(markets.home_total.line ?? 0)}`}
          odds={markets.home_total.first.book}
        />
      ),
    },
    {
      label: `${away.school} points`,
      fair: projAway.toFixed(1),
      book: (
        <Price
          line={`O/U ${totalLine(markets.away_total.line ?? 0)}`}
          odds={markets.away_total.first.book}
        />
      ),
    },
  ]
}

/** The game center's rows: TSI's prices plus the Vegas consensus; null without a forecast. */
export function marketRows(center: GameCenter): MarketRow[] | null {
  const { game, markets } = center
  const p = game.prediction
  if (!p || !markets) return null
  const { home, away } = game
  const m = game.market
  const vegas: Record<string, ReactNode | null> = {
    Spread: m?.spread != null ? favoriteLine(m.spread, home, away) : null,
    Total: m?.total != null ? totalLine(m.total) : null,
    Moneyline:
      m?.home_ml != null && m.away_ml != null ? (
        <TeamPair home={home} away={away} homeOdds={m.home_ml} awayOdds={m.away_ml} />
      ) : null,
  }
  const rows = tsiRows({
    markets,
    home,
    away,
    projHome: p.proj_home,
    projAway: p.proj_away,
    picks: p.picks,
  })
  return rows.map((r) => ({ ...r, market: vegas[r.label] ?? null }))
}

const short = (t: TeamRef) => t.abbreviation ?? t.school

function Price({ line, odds, note }: { line: string; odds: number; note?: string }) {
  return (
    <span className="inline-flex flex-col items-end">
      <span>
        {line} <span className="text-muted-foreground">{american(odds)}</span>
      </span>
      {note && <span className="text-xs text-muted-foreground">{note}</span>}
    </span>
  )
}

type PairProps = { home: TeamRef; away: TeamRef; homeOdds: number; awayOdds: number }

/** Both sides' moneylines, away on top (as the teams are listed everywhere). */
function TeamPair({ home, away, homeOdds, awayOdds }: PairProps) {
  return (
    <span className="inline-flex flex-col items-end">
      <span>{`${short(away)} ${american(awayOdds)}`}</span>
      <span>{`${short(home)} ${american(homeOdds)}`}</span>
    </span>
  )
}
