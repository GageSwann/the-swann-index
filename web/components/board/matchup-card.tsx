import Link from "next/link"

import { TeamLink } from "@/components/team/team-link"
import type { GameSummary, TeamRef } from "@/lib/api/types"
import { american, favoriteLine, totalLine } from "@/lib/format/odds"
import { formatKickoff } from "@/lib/format/time"

import { PickBadge } from "./pick-badge"
import { WinProbBar } from "./win-prob-bar"

type Props = { game: GameSummary; ranks: Record<number, number> }

/** One game: teams, projected (or final) score, win probability, TSI vs. market, TSI plays. */
export function MatchupCard({ game, ranks }: Props) {
  const p = game.prediction
  const m = game.market
  const final = game.result?.final === true
  const status = final ? "Final" : p?.locked ? "Kicked off" : null

  return (
    <article className="flex flex-col gap-3 rounded-md border border-border bg-card p-4">
      <header className="flex items-baseline justify-between gap-2 text-sm text-muted-foreground">
        <span>
          {formatKickoff(game.kickoff, game.kickoff_tbd)}
          {game.neutral && ", neutral site"}
        </span>
        {status && <span className="font-medium text-foreground">{status}</span>}
      </header>

      <div className="space-y-1.5">
        <TeamRow
          team={game.away}
          rank={ranks[game.away.id]}
          score={final ? game.result?.away_points : p?.proj_away}
          isFinal={final}
        />
        <TeamRow
          team={game.home}
          rank={ranks[game.home.id]}
          score={final ? game.result?.home_points : p?.proj_home}
          isFinal={final}
        />
        {final && p && (
          <p className="text-xs text-muted-foreground">
            TSI projected {Math.round(p.proj_away)}–{Math.round(p.proj_home)}
          </p>
        )}
      </div>

      {p ? (
        <>
          <WinProbBar homeProb={p.home_win_prob} home={game.home} away={game.away} />
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-muted-foreground">
                <th scope="col" className="text-left font-normal">
                  <span className="sr-only">Market</span>
                </th>
                <th scope="col" className="text-right font-normal">
                  TSI
                </th>
                <th scope="col" className="text-right font-normal">
                  Vegas
                </th>
              </tr>
            </thead>
            <tbody>
              <LineRow
                label="Spread"
                tsi={favoriteLine(p.spread, game.home, game.away)}
                market={m?.spread != null ? favoriteLine(m.spread, game.home, game.away) : null}
              />
              <LineRow
                label="Total"
                tsi={p.total.toFixed(1)}
                market={m?.total != null ? totalLine(m.total) : null}
              />
              <LineRow
                label="Moneyline"
                tsi={favoriteMoneyline(game.home, game.away, p.fair_home_ml, p.fair_away_ml)}
                market={
                  m?.home_ml != null && m.away_ml != null
                    ? favoriteMoneyline(game.home, game.away, m.home_ml, m.away_ml)
                    : null
                }
              />
            </tbody>
          </table>
          {p.picks.map((pick) => (
            <PickBadge key={`${pick.market}-${pick.side}`} pick={pick} game={game} />
          ))}
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          {final || game.result
            ? "TSI didn't publish a prediction for this game (predictions began Oct 20, 2026)."
            : "TSI hasn't published a prediction for this game yet."}
        </p>
      )}

      <Link
        href={`/games/${game.id}`}
        className="mt-auto inline-flex min-h-8 items-center self-start text-sm text-primary underline-offset-4 hover:underline"
      >
        Game center
      </Link>
    </article>
  )
}

function TeamRow({
  team,
  rank,
  score,
  isFinal,
}: {
  team: TeamRef
  rank?: number
  score?: number | null
  isFinal: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="flex min-w-0 items-center gap-1.5">
        <span className="w-5 shrink-0 text-right text-xs text-muted-foreground">
          {rank !== undefined && rank <= 25 ? rank : ""}
        </span>
        <TeamLink team={team} />
      </span>
      <span
        className={
          isFinal
            ? "text-2xl font-bold font-stretch-condensed"
            : "text-xl font-semibold text-muted-foreground font-stretch-condensed"
        }
      >
        {score == null ? "" : Math.round(score)}
      </span>
    </div>
  )
}

function LineRow({ label, tsi, market }: { label: string; tsi: string; market: string | null }) {
  return (
    <tr className="border-t border-border">
      <th scope="row" className="py-1 text-left font-normal text-muted-foreground">
        {label}
      </th>
      <td className="py-1 text-right font-medium">{tsi}</td>
      <td className="py-1 text-right">{market ?? "—"}</td>
    </tr>
  )
}

function favoriteMoneyline(home: TeamRef, away: TeamRef, homeMl: number, awayMl: number) {
  const homeFav = homeMl <= awayMl
  const team = homeFav ? home : away
  return `${team.abbreviation ?? team.school} ${american(homeFav ? homeMl : awayMl)}`
}
