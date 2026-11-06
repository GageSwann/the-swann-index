import Image from "next/image"
import Link from "next/link"

import { WinProbBar } from "@/components/board/win-prob-bar"
import { BorderLightRings, borderLightVars } from "@/components/ui/border-light"
import type { GameOfWeekView, RankedTeam, RankingType, TeamRef } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { chance, points, record } from "@/lib/format/numbers"
import { favoriteLine, totalLine } from "@/lib/format/odds"
import { cn } from "@/lib/utils"

type Props = {
  pick: GameOfWeekView | null // this poll week's pick (#141)
  teams: RankedTeam[] // the chosen ranking now: ranks and records shown
  division: Division
  type: RankingType
  when: string | null // kickoff, formatted on the server ("Saturday, Nov 7, 3:30 PM ET")
  size: "lead" | "second"
}

const TITLE: Record<Division, string> = {
  fbs: "FBS game of the week",
  fcs: "FCS game of the week",
}

/**
 * One game of the week: the page's focal point, so it carries the border light in both
 * teams' colors (#137). Ranks shown are the chosen ranking's (Power or Résumé), as of now.
 * Once the game is played it shows the final score next to TSI's projection.
 */
export function GameOfWeekCard({ pick, teams, division, type, when, size }: Props) {
  const headingId = `gotw-${division}`
  const p = pick?.game.prediction
  // The title sits above the card, like the Top 25 lists' titles, so the card's top edge
  // lines up with theirs.
  const heading = (
    <h2 id={headingId} className="text-lg font-semibold font-stretch-condensed">
      {TITLE[division]}
    </h2>
  )
  if (!pick || !p) {
    return (
      <section aria-labelledby={headingId} className="min-w-0 space-y-2">
        {heading}
        <p className="rounded-md border border-border bg-card p-5 text-sm text-muted-foreground">
          Picked each Sunday with the new rankings, from the coming week&apos;s games. Check back
          after Sunday&apos;s update.
        </p>
      </section>
    )
  }
  const { game } = pick
  const m = game.market
  const lead = size === "lead"
  const row = new Map(teams.map((t) => [t.team.id, t]))
  const final = game.result?.final ? game.result : null
  return (
    <section aria-labelledby={headingId} className="min-w-0 space-y-2">
      {heading}
      <div
        className="tsi-border-light space-y-5 rounded-md border border-border bg-card p-5 sm:p-6"
        style={borderLightVars(game.away, game.home)}
      >
        <BorderLightRings />
        {when && <p className="text-sm text-muted-foreground">{when}</p>}

        {/* Two rows, so the scores line up even when one team's name wraps. */}
        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-start gap-x-3 gap-y-2 sm:gap-x-6">
          <Side team={game.away} row={row.get(game.away.id) ?? null} lead={lead} />
          <span className="mt-4 text-sm text-muted-foreground">{game.neutral ? "vs" : "at"}</span>
          <Side team={game.home} row={row.get(game.home.id) ?? null} lead={lead} alignEnd />
          <Score value={final ? final.away_points : p.proj_away} lead={lead} />
          <span aria-hidden />
          <Score value={final ? final.home_points : p.proj_home} lead={lead} alignEnd />
        </div>

        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            {final
              ? `Final. TSI projected ${points(p.proj_away)}–${points(p.proj_home)} with these win chances.`
              : "TSI's projected score and win chance"}
          </p>
          <WinProbBar homeProb={p.home_win_prob} home={game.home} away={game.away} />
        </div>

        <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:max-w-md">
          <dt className="text-muted-foreground">TSI line</dt>
          <dd className="text-right">
            {favoriteLine(p.spread, game.home, game.away)}, total {p.total.toFixed(1)}
          </dd>
          <dt className="text-muted-foreground">Vegas</dt>
          <dd className="text-right">
            {m?.spread != null && m.total != null
              ? `${favoriteLine(m.spread, game.home, game.away)}, total ${totalLine(m.total)}`
              : "No line yet"}
          </dd>
        </dl>

        <p className="max-w-[65ch] text-sm">{whyThisGame(pick, row, type)}</p>

        <Link
          href={`/games/${game.id}`}
          className="inline-flex min-h-8 items-center text-sm underline decoration-muted-foreground underline-offset-4 hover:decoration-foreground"
        >
          Game center
        </Link>
      </div>
    </section>
  )
}

function Side({
  team,
  row,
  lead,
  alignEnd = false,
}: {
  team: TeamRef
  row: RankedTeam | null
  lead: boolean
  alignEnd?: boolean
}) {
  const rank = row && row.rank <= 25 ? `#${row.rank} ` : ""
  return (
    <div className={cn("flex min-w-0 flex-col", alignEnd && "items-end text-right")}>
      <Link
        href={`/teams/${team.slug}`}
        className={cn(
          "flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center sm:gap-3",
          alignEnd ? "items-end sm:flex-row-reverse" : "items-start",
        )}
      >
        <span
          className={cn(
            "flex shrink-0 items-center justify-center rounded-md bg-white",
            lead ? "size-14" : "size-11",
          )}
        >
          {team.logo_url && (
            <Image
              src={team.logo_url}
              alt=""
              width={48}
              height={48}
              className={cn("object-contain", lead ? "size-12" : "size-9")}
            />
          )}
        </span>
        <span
          className={cn(
            "max-w-full leading-tight font-bold [overflow-wrap:anywhere] font-stretch-condensed hover:underline",
            lead ? "text-2xl sm:text-4xl" : "text-xl sm:text-3xl",
          )}
        >
          <span className="text-muted-foreground">{rank}</span>
          {team.school}
        </span>
      </Link>
      {row && (
        <p className="mt-1 text-sm text-muted-foreground">
          {record(row.wins, row.losses, row.ties)}
        </p>
      )}
    </div>
  )
}

function Score({
  value,
  lead,
  alignEnd = false,
}: {
  value: number
  lead: boolean
  alignEnd?: boolean
}) {
  return (
    <p
      className={cn(
        "font-bold font-stretch-condensed proportional-nums",
        lead ? "text-5xl sm:text-6xl" : "text-4xl sm:text-5xl",
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
      ? `Two Top 25 teams in the ${ranking} rankings.`
      : ranked.length === 1
        ? `${ranked[0].team.school} is #${ranked[0].rank} in the ${ranking} rankings.`
        : ""
  const p = game.prediction!.home_win_prob
  const fav = p >= 0.5 ? game.home : game.away
  const close = `TSI gives ${fav.school} a ${chance(Math.max(p, 1 - p))} chance to win.`
  return [who, close, stakesText(pick)].filter(Boolean).join(" ")
}

const MEANINGFUL = 0.05 // a swing under 5 points isn't worth a sentence

/** "A win would raise Notre Dame's playoff chances by 31 points and Miami's by 24." */
function stakesText(pick: GameOfWeekView): string {
  const { game } = pick
  const sides = [
    { team: game.away, playoff: pick.away_playoff_swing, title: pick.away_title_swing },
    { team: game.home, playoff: pick.home_playoff_swing, title: pick.home_title_swing },
  ]
  for (const [key, what] of [
    ["playoff", "playoff chances"],
    ["title", "conference-title chances"],
  ] as const) {
    const big = sides
      .filter((s) => (s[key] ?? 0) >= MEANINGFUL)
      .sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0))
    if (big.length === 0) continue
    const pts = (v: number | null) => Math.round((v ?? 0) * 100)
    const first = `${big[0].team.school}'s ${what} by ${pts(big[0][key])} points`
    const second = big[1] ? ` and ${big[1].team.school}'s by ${pts(big[1][key])}` : ""
    return `A win would raise ${first}${second}.`
  }
  return ""
}
