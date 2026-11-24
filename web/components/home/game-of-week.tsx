import Link from "next/link"

import { WinProbBar } from "@/components/board/win-prob-bar"
import { TeamLogo } from "@/components/team/team-logo"
import type { GameOfWeekView, TeamRecord, TeamRef } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { chance, points, record } from "@/lib/format/numbers"
import { tsiMoneyline, tsiSpread, tsiTotal } from "@/lib/format/odds"
import { cfb } from "@/lib/routes"
import { cn } from "@/lib/utils"

import { PickSign } from "./pick-sign"

/** What the card shows: a game of the week, or a team page's next game (#199). */
export type CardGame = Pick<
  GameOfWeekView,
  "game" | "home_record" | "away_record" | "home_conf_record" | "away_conf_record" | "lines"
>

type Props = {
  pick: CardGame | null // this poll week's pick (#141, #142), or a team's next game
  teams: { team: { id: number }; rank: number }[] // the ranks shown (Top 25 only)
  division: Division
  when: string | null // kickoff, formatted on the server ("Saturday, Nov 7, 7:30 PM ET")
  className?: string
  title?: string // default: "FBS Game of the Week"
  id?: string // the heading's id (default: gotw-<division>)
  empty?: string // shown without a game or a prediction
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
export function GameOfWeekCard({
  pick,
  teams,
  division,
  when,
  className,
  title,
  id,
  empty,
}: Props) {
  const headingId = id ?? `gotw-${division}`
  const heading = (
    <h2 id={headingId} className="text-lg font-semibold font-stretch-condensed">
      {title ?? TITLE[division]}
    </h2>
  )
  const p = pick?.game.prediction ?? null
  if (!pick) {
    return (
      <section aria-labelledby={headingId} className={cn("flex min-w-0 flex-col gap-2", className)}>
        {heading}
        <p className="flex-1 rounded-md border border-border bg-card p-5 text-sm text-muted-foreground">
          {empty ??
            "The games of the week are chosen each Sunday from the coming week's schedule, using the new rankings."}
        </p>
      </section>
    )
  }
  const { game } = pick
  const lines = pick.lines ?? null // TSI's lines with their fair odds (#188)
  const rank = new Map(teams.map((t) => [t.team.id, t.rank]))
  const final = game.result?.final ? game.result : null
  const matchup = `${game.away.school} ${game.neutral ? "vs." : "at"} ${game.home.school}`
  // TSI's straight-up pick (13.10), home on a tie; none without a prediction (#200).
  const homePicked = p ? p.home_win_prob >= 0.5 : null
  return (
    <section aria-labelledby={headingId} className={cn("flex min-w-0 flex-col gap-2", className)}>
      {heading}
      <div className="tsi-lit-hover relative flex flex-1 flex-col justify-between gap-5 rounded-md border border-border bg-card p-5">
        <Link
          href={cfb.game(game.id)}
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
            {final ? "Final" : p ? "Predicted Score" : "Upcoming"}
          </span>
        </div>

        {/* Logos above the names give each name the column's full width; the scores share
            one row, so they line up even if a long name wraps. */}
        {p && homePicked !== null && (
          <p className="sr-only">
            TSI&apos;s pick: {homePicked ? game.home.school : game.away.school},{" "}
            {chance(homePicked ? p.home_win_prob : 1 - p.home_win_prob)}.
          </p>
        )}
        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] gap-x-4 gap-y-1">
          <Side
            team={game.away}
            rank={rank.get(game.away.id) ?? null}
            rec={pick.away_record}
            conf={pick.away_conf_record}
            picked={homePicked === false}
          />
          <span className="self-center pt-8 text-sm text-muted-foreground">
            {game.neutral ? "vs." : "at"}
          </span>
          <Side
            team={game.home}
            rank={rank.get(game.home.id) ?? null}
            rec={pick.home_record}
            conf={pick.home_conf_record}
            picked={homePicked === true}
            alignEnd
          />
          {(final || p) && (
            <>
              <Score value={final ? final.away_points : p!.proj_away} />
              <span aria-hidden />
              <Score value={final ? final.home_points : p!.proj_home} alignEnd />
            </>
          )}
        </div>

        {p ? (
          <>
            <div className="space-y-1">
              <p className="sr-only">
                {final
                  ? "Final score. TSI's win probability before the game:"
                  : "TSI's projected score and win probability:"}
              </p>
              <WinProbBar homeProb={p.home_win_prob} home={game.home} away={game.away} digits={1} />
              {final && (
                <p className="text-xs text-muted-foreground">
                  TSI projected {points(p.proj_away)}–{points(p.proj_home)}.
                </p>
              )}
            </div>

            {/* A thin rule between the win chances and TSI's lines (owner). */}
            <hr className="border-border" />

            <LinesBoard
              rows={[
                {
                  team: game.away,
                  spread: tsiSpread(-(lines?.spread.line ?? p.spread)),
                  spreadOdds: lines?.spread.second.fair,
                  total: ["O", tsiTotal(lines?.total.line ?? p.total)],
                  totalOdds: lines?.total.first.fair,
                  moneyline: tsiMoneyline(p.fair_away_ml),
                },
                {
                  team: game.home,
                  spread: tsiSpread(lines?.spread.line ?? p.spread),
                  spreadOdds: lines?.spread.first.fair,
                  total: ["U", tsiTotal(lines?.total.line ?? p.total)],
                  totalOdds: lines?.total.second.fair,
                  moneyline: tsiMoneyline(p.fair_home_ml),
                },
              ]}
            />
          </>
        ) : (
          // No prediction (#200): the card keeps the teams, ranks and records and says why.
          <p className="border-t border-border pt-4 text-sm text-muted-foreground">
            {noPredictionReason(game, !!final)}
          </p>
        )}
      </div>
    </section>
  )
}

/** Why a game has no TSI prediction (#200): an opponent TSI doesn't rate (D-II and below),
 * or it is more than 8 days away (TSI publishes 8 days ahead). */
function noPredictionReason(game: CardGame["game"], final: boolean): string {
  const unrated = [game.home, game.away].some((t) => t.division !== "fbs" && t.division !== "fcs")
  if (unrated) return "TSI doesn't predict games against teams outside FBS and FCS."
  if (final) return "TSI didn't publish a prediction for this game."
  return "TSI publishes its prediction for a game 8 days before kickoff."
}

function Side({
  team,
  rank: current,
  rec,
  conf,
  picked,
  alignEnd = false,
}: {
  team: TeamRef
  rank: number | null // in the chosen ranking's Top 25, if there
  rec: TeamRecord | null | undefined // from the pick (any team, ranked or not; #155)
  conf?: TeamRecord | null // conference record (#190); none for independents
  picked: boolean // TSI expects this team to win: its sign stands by the logo (13.10)
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
        href={cfb.team(team.slug)}
        className={cn(
          "group relative z-10 flex min-w-0 flex-col gap-2",
          alignEnd ? "items-end" : "items-start",
        )}
      >
        <span className="relative">
          <TeamLogo team={team} size={48} />
          {/* On the logo's outer side, overlapping its edge, leaning away from the middle. */}
          {picked && (
            <PickSign
              lean={alignEnd ? "right" : "left"}
              className={cn("absolute -bottom-2.5", alignEnd ? "-right-1.5" : "-left-1.5")}
            />
          )}
        </span>
        <span className="max-w-full text-2xl leading-tight font-bold text-balance font-stretch-condensed group-hover:underline">
          <span className="text-muted-foreground">{rank}</span>
          {team.school}
        </span>
      </Link>
      {rec && (
        <span className="text-sm text-muted-foreground">
          {record(rec.wins, rec.losses, rec.ties)}
          {conf && ` (${record(conf.wins, conf.losses, conf.ties)})`}
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

type LinesRow = {
  team: TeamRef
  spread: string
  spreadOdds?: number // TSI's fair odds for this side at that line (#188)
  total: [string, string] // ["O" | "U", line]
  totalOdds?: number
  moneyline: string
}

/** TSI's fair odds for one side of a spread or total, small under the line, like a book's
 * board (owner, #188); rounded like TSI's moneylines. Nothing when the API sent none. */
function Price({ odds }: { odds?: number }) {
  if (odds === undefined) return null
  return (
    <span className="block text-xs font-normal text-muted-foreground">{tsiMoneyline(odds)}</span>
  )
}

/**
 * TSI's lines laid out like a sportsbook's board (owner, 2026-11-23): one row per team, away
 * on top, and each market in its own cell under its column (Spread, Total, Moneyline), so
 * the two sides of a line sit in separate cells instead of a stacked list.
 */
function LinesBoard({ rows }: { rows: LinesRow[] }) {
  const cell =
    "rounded-md border border-border bg-background px-1 py-2 text-center text-sm font-semibold tabular-nums"
  return (
    <table className="-mx-1.5 w-[calc(100%+0.75rem)] table-fixed border-separate border-spacing-1.5">
      <caption className="sr-only">TSI&apos;s lines</caption>
      <colgroup>
        <col className="w-[34%]" />
        <col />
        <col />
        <col />
      </colgroup>
      <thead>
        <tr className="text-xs text-muted-foreground">
          <th scope="col" className="text-left font-normal">
            TSI lines
          </th>
          <th scope="col" className="font-normal">
            Spread
          </th>
          <th scope="col" className="font-normal">
            Total
          </th>
          <th scope="col" className="font-normal">
            Moneyline
          </th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.team.id}>
            <th scope="row" className="text-left font-medium">
              <span className="flex min-w-0 items-center gap-2">
                <TeamLogo team={r.team} size={22} />
                <span className="truncate text-sm" title={r.team.school}>
                  {short(r.team)}
                </span>
              </span>
            </th>
            <td className={cell}>
              {r.spread}
              <Price odds={r.spreadOdds} />
            </td>
            <td className={cell}>
              <span className="mr-1 font-normal text-muted-foreground">{r.total[0]}</span>
              {r.total[1]}
              <Price odds={r.totalOdds} />
            </td>
            <td className={cell}>{r.moneyline}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
