import type { ReactNode } from "react"

import type { FairMarkets, GameCenter, TeamRef } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { american, favoriteLine, teamSpread, totalLine } from "@/lib/format/odds"

/** One market in an odds table: TSI's own line (no vig) and, for games, Vegas. */
export type MarketRow = {
  label: string
  fair: ReactNode
  market?: ReactNode | null
}

type Priced = {
  markets: FairMarkets
  home: TeamRef
  away: TeamRef
  projHome: number
  projAway: number
}

/**
 * TSI's lines for spread, total, moneyline and team totals, with TSI's chance at the
 * nearest bettable line. The Book's prices are owner-only (decision #139).
 */
export function tsiRows({ markets, home, away, projHome, projAway }: Priced): MarketRow[] {
  const ml = markets.moneyline
  const totalAt = totalLine(markets.total.line ?? 0)
  return [
    {
      label: "Spread",
      fair: (
        <Line
          value={favoriteLine(markets.fair_spread, home, away)}
          note={`${short(home)} ${teamSpread(markets.spread.line ?? 0)} covers ${percent(markets.spread.first.prob, 0)}${pushNote(markets.spread.push)}`}
        />
      ),
    },
    {
      label: "Total",
      fair: (
        <Line
          value={markets.fair_total.toFixed(1)}
          note={`over ${totalAt} ${percent(markets.total.first.prob, 0)}${pushNote(markets.total.push)}`}
        />
      ),
    },
    {
      label: "Moneyline",
      fair: <TeamPair home={home} away={away} homeOdds={ml.first.fair} awayOdds={ml.second.fair} />,
    },
    { label: `${home.school} points`, fair: projHome.toFixed(1) },
    { label: `${away.school} points`, fair: projAway.toFixed(1) },
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
  const rows = tsiRows({ markets, home, away, projHome: p.proj_home, projAway: p.proj_away })
  return rows.map((r) => ({ ...r, market: vegas[r.label] ?? null }))
}

const short = (t: TeamRef) => t.abbreviation ?? t.school

function Line({ value, note }: { value: string; note?: string }) {
  return (
    <span className="inline-flex flex-col items-end">
      <span>{value}</span>
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

/** ", push 6%" on a whole-number line (key numbers, decision #118); nothing otherwise. */
function pushNote(push: number): string {
  return push >= 0.005 ? `, push ${percent(push, 0)}` : ""
}
