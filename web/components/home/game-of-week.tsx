import Link from "next/link"

import { WinProbBar } from "@/components/board/win-prob-bar"
import { TeamLogo } from "@/components/team/team-logo"
import type { GameOfWeekView, TeamRecord, TeamRef, TopTeam } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { points, record, signed } from "@/lib/format/numbers"
import { american } from "@/lib/format/odds"
import { cn } from "@/lib/utils"

type Props = {
  pick: GameOfWeekView | null // this poll week's pick (#141, #142)
  teams: TopTeam[] // the chosen ranking's Top 25 now: the ranks shown
  division: Division
  when: string | null // kickoff, formatted on the server ("Saturday, Nov 7, 7:30 PM ET")
  className?: string
}

const TITLE: Record<Division, string> = {
  fbs: "FBS Game of the Week",
  fcs: "FCS Game of the Week",
}

/**
 * One game of the week. Its title sits above the card, like the Top 25 lists' titles, so
 * the card lines up with them; the card stretches to fill its column (the home page lines
 * up the bottoms). The whole card opens the game center, except the team names and logos,
 * which open the team pages; it lights on hover in the page's plain light (owner).
 */
export function GameOfWeekCard({ pick, teams, division, when, className }: Props) {
  const headingId = `gotw-${division}`
  const heading = (
    <h2 id={headingId} className="text-lg font-semibold font-stretch-condensed">
      {TITLE[division]}
    </h2>
  )
  const p = pick?.game.prediction
  if (!pick || !p) {
    return (
      <section aria-labelledby={headingId} className={cn("flex min-w-0 flex-col gap-2", className)}>
        {heading}
        <p className="flex-1 rounded-md border border-border bg-card p-5 text-sm text-muted-foreground">
          The games of the week are chosen each Sunday from the coming week&apos;s schedule, using
          the new rankings.
        </p>
      </section>
    )
  }
  const { game } = pick
  const rank = new Map(teams.map((t) => [t.team.id, t.rank]))
  const final = game.result?.final ? game.result : null
  const matchup = `${game.away.school} ${game.neutral ? "vs." : "at"} ${game.home.school}`
  return (
    <section aria-labelledby={headingId} className={cn("flex min-w-0 flex-col gap-2", className)}>
      {heading}
      <div className="tsi-lit-hover relative flex flex-1 flex-col justify-between gap-5 rounded-md border border-border bg-card p-5">
        <Link
          href={`/games/${game.id}`}
          aria-label={`Game center: ${matchup}`}
          className="absolute inset-0 rounded-md"
        />
        {/* The big numbers are TSI's prediction until the game is played (owner): say so. */}
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">{when}</p>
          <span
            className={cn(
              "shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium",
              final ? "border-foreground text-foreground" : "border-border text-foreground",
            )}
          >
            {final ? "Final" : "Predicted Score"}
          </span>
        </div>

        {/* Logos above the names give each name the column's full width; the scores share
            one row, so they line up even if a long name wraps. */}
        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] gap-x-4 gap-y-1">
          <Side team={game.away} rank={rank.get(game.away.id) ?? null} rec={pick.away_record} />
          <span className="self-center pt-8 text-sm text-muted-foreground">
            {game.neutral ? "vs." : "at"}
          </span>
          <Side
            team={game.home}
            rank={rank.get(game.home.id) ?? null}
            rec={pick.home_record}
            alignEnd
          />
          <Score value={final ? final.away_points : p.proj_away} />
          <span aria-hidden />
          <Score value={final ? final.home_points : p.proj_home} alignEnd />
        </div>

        <div className="space-y-1">
          <p className="sr-only">
            {final
              ? "Final score. TSI's win probability before the game:"
              : "TSI's projected score and win probability:"}
          </p>
          <WinProbBar homeProb={p.home_win_prob} home={game.home} away={game.away} />
          {final && (
            <p className="text-xs text-muted-foreground">
              TSI projected {points(p.proj_away)}–{points(p.proj_home)}.
            </p>
          )}
        </div>

        {/* TSI's lines only (owner): a stat strip, each label above both sides of its line,
            away on top and home below like the card (owner, 2026-11-23). */}
        <dl className="grid grid-cols-3 divide-x divide-border rounded-md border border-border">
          {[
            {
              label: "TSI Spread",
              rows: [
                [short(game.away), spreadText(-p.spread)],
                [short(game.home), spreadText(p.spread)],
              ],
            },
            {
              label: "TSI Total",
              rows: [
                ["Over", p.total.toFixed(1)],
                ["Under", p.total.toFixed(1)],
              ],
            },
            {
              label: "TSI Moneyline",
              rows: [
                [short(game.away), american(p.fair_away_ml)],
                [short(game.home), american(p.fair_home_ml)],
              ],
            },
          ].map(({ label, rows }) => (
            <div key={label} className="flex flex-col items-center gap-1 px-2 py-2.5 text-center">
              <dt className="text-xs text-muted-foreground">{label}</dt>
              {rows.map(([side, value]) => (
                <dd key={side} className="flex max-w-full gap-1.5 text-sm whitespace-nowrap">
                  <span className="truncate text-muted-foreground" title={side}>
                    {side}
                  </span>
                  <span className="shrink-0 font-semibold tabular-nums">{value}</span>
                </dd>
              ))}
            </div>
          ))}
        </dl>
      </div>
    </section>
  )
}

function Side({
  team,
  rank: current,
  rec,
  alignEnd = false,
}: {
  team: TeamRef
  rank: number | null // in the chosen ranking's Top 25, if there
  rec: TeamRecord | null | undefined // from the pick (any team, ranked or not; #155)
  alignEnd?: boolean
}) {
  const rank = current !== null && current <= 25 ? `#${current} ` : ""
  return (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-2",
        alignEnd ? "items-end text-right" : "items-start",
      )}
    >
      {/* Above the card's link, so a click here opens the team page. */}
      <Link
        href={`/teams/${team.slug}`}
        className={cn(
          "group relative z-10 flex min-w-0 flex-col gap-2",
          alignEnd ? "items-end" : "items-start",
        )}
      >
        <TeamLogo team={team} size={48} />
        <span className="max-w-full text-2xl leading-tight font-bold text-balance font-stretch-condensed group-hover:underline">
          <span className="text-muted-foreground">{rank}</span>
          {team.school}
        </span>
      </Link>
      {rec && (
        <span className="text-sm text-muted-foreground">
          {record(rec.wins, rec.losses, rec.ties)}
        </span>
      )}
    </div>
  )
}

function Score({ value, alignEnd = false }: { value: number; alignEnd?: boolean }) {
  return (
    <p
      className={cn(
        "text-5xl font-bold font-stretch-condensed proportional-nums",
        alignEnd && "text-right",
      )}
    >
      {points(value)}
    </p>
  )
}

/** A team's short name for the line rows: its abbreviation, else the school. */
function short(team: TeamRef): string {
  return team.abbreviation ?? team.school
}

/** One side's fair spread: "+3.4", "−3.4", "PK" when it rounds to zero. */
function spreadText(spread: number): string {
  const text = signed(spread, 1)
  return Number(text.replace("−", "-")) === 0 ? "PK" : text
}
