import Link from "next/link"

import { WinProbBar } from "@/components/board/win-prob-bar"
import { TeamLogo } from "@/components/team/team-logo"
import type { GameOfWeekView, RankedTeam, RankingType, TeamRef } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { chance, points, record } from "@/lib/format/numbers"
import { favoriteLine, totalLine } from "@/lib/format/odds"
import { cn } from "@/lib/utils"

type Props = {
  pick: GameOfWeekView | null // this poll week's pick (#141, #142)
  teams: RankedTeam[] // the chosen ranking now: ranks and records shown
  division: Division
  type: RankingType
  when: string | null // kickoff, formatted on the server ("Saturday, Nov 7, 7:30 PM ET")
  className?: string
}

const TITLE: Record<Division, string> = {
  fbs: "FBS game of the week",
  fcs: "FCS game of the week",
}

/**
 * One game of the week. Its title sits above the card, like the Top 25 lists' titles, so
 * the card lines up with them; the card stretches to fill its column (the home page lines
 * up the bottoms). The whole card opens the game center, except the team names and logos,
 * which open the team pages; it lights on hover in the page's plain light (owner).
 */
export function GameOfWeekCard({ pick, teams, division, type, when, className }: Props) {
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
  const m = game.market
  const row = new Map(teams.map((t) => [t.team.id, t]))
  const final = game.result?.final ? game.result : null
  const matchup = `${game.away.school} ${game.neutral ? "vs." : "at"} ${game.home.school}`
  return (
    <section aria-labelledby={headingId} className={cn("flex min-w-0 flex-col gap-2", className)}>
      {heading}
      <div className="tsi-lit-hover relative flex flex-1 flex-col gap-5 rounded-md border border-border bg-card p-5">
        <Link
          href={`/games/${game.id}`}
          aria-label={`Game center: ${matchup}`}
          className="absolute inset-0 rounded-md"
        />
        {when && <p className="text-sm text-muted-foreground">{final ? `Final. ${when}` : when}</p>}

        {/* Logos above the names give each name the column's full width; the scores share
            one row, so they line up even if a long name wraps. */}
        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] gap-x-4 gap-y-1">
          <Side team={game.away} row={row.get(game.away.id) ?? null} />
          <span className="self-center pt-8 text-sm text-muted-foreground">
            {game.neutral ? "vs." : "at"}
          </span>
          <Side team={game.home} row={row.get(game.home.id) ?? null} alignEnd />
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

        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
          <dt className="text-muted-foreground">TSI line</dt>
          <dd className="text-right">
            {favoriteLine(p.spread, game.home, game.away)}, total {p.total.toFixed(1)}
          </dd>
          <dt className="text-muted-foreground">Vegas line</dt>
          <dd className="text-right">
            {m?.spread != null && m.total != null
              ? `${favoriteLine(m.spread, game.home, game.away)}, total ${totalLine(m.total)}`
              : "Not posted yet"}
          </dd>
        </dl>

        <p className="text-sm">{whyThisGame(pick, row, type)}</p>
      </div>
    </section>
  )
}

function Side({
  team,
  row,
  alignEnd = false,
}: {
  team: TeamRef
  row: RankedTeam | null
  alignEnd?: boolean
}) {
  const rank = row && row.rank <= 25 ? `#${row.rank} ` : ""
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
      {row && (
        <span className="text-sm text-muted-foreground">
          {record(row.wins, row.losses, row.ties)}
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

/** Plain-language reasons: who's in it, how close TSI has it, and what rides on it. */
function whyThisGame(
  pick: GameOfWeekView,
  row: Map<number, RankedTeam>,
  type: RankingType,
): string {
  const { game } = pick
  const ranking = type === "power" ? "Power" : "Résumé"
  const ranked = [game.away, game.home]
    .map((t) => row.get(t.id))
    .filter((r): r is RankedTeam => !!r && r.rank <= 25)
  const who =
    ranked.length === 2
      ? `Both teams are in the ${ranking} Top 25.`
      : ranked.length === 1
        ? `${ranked[0].team.school} is No. ${ranked[0].rank} in the ${ranking} rankings.`
        : ""
  const p = game.prediction!.home_win_prob
  const fav = p >= 0.5 ? game.home : game.away
  const close = `TSI gives ${fav.school} a ${chance(Math.max(p, 1 - p))} chance to win.`
  return [who, close, stakesText(pick)].filter(Boolean).join(" ")
}

const MEANINGFUL = 0.05 // a swing under 5 percentage points isn't worth a sentence

/** "A win would raise Notre Dame's playoff chances by 31 percentage points, and Miami's by 24." */
function stakesText(pick: GameOfWeekView): string {
  const { game } = pick
  const sides = [
    { team: game.away, playoff: pick.away_playoff_swing, title: pick.away_title_swing },
    { team: game.home, playoff: pick.home_playoff_swing, title: pick.home_title_swing },
  ]
  for (const [key, what] of [
    ["playoff", "playoff chances"],
    ["title", "chances of winning its conference"],
  ] as const) {
    const big = sides
      .filter((s) => (s[key] ?? 0) >= MEANINGFUL)
      .sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0))
    if (big.length === 0) continue
    const pts = (v: number | null) => Math.round((v ?? 0) * 100)
    const first = `${big[0].team.school}'s ${what} by ${pts(big[0][key])} percentage points`
    const second = big[1] ? `, and ${big[1].team.school}'s by ${pts(big[1][key])}` : ""
    return `A win would raise ${first}${second}.`
  }
  return ""
}
