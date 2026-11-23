import Link from "next/link"

import { PhaseLabel, useGamePhase } from "@/components/game/game-phase"
import { TeamLogo } from "@/components/team/team-logo"
import type { GameSummary, TeamRef } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { chance, points } from "@/lib/format/numbers"
import { favoriteLine, totalLine, tsiFavoriteLine, tsiTotal } from "@/lib/format/odds"
import { formatKickoff } from "@/lib/format/time"
import { cn } from "@/lib/utils"

import { type BoardRank, type BoardRanks, shownRank } from "./board-ranks"

/**
 * Phones only (owner, 2026-11-23, #165): one game as a compact scoreboard card. Kickoff, each
 * team with its Top 25 rank, projected (or final) score and TSI's win chance, then one line
 * of TSI's spread and total next to Vegas. The whole card opens the game center, which has
 * the moneylines and everything else. Wider screens use `MatchupCard`.
 */
export function MatchupCompact({ game, ranks }: { game: GameSummary; ranks: BoardRanks }) {
  const p = game.prediction
  const m = game.market
  const final = game.result?.final === true
  const phase = useGamePhase({
    kickoff: game.kickoff,
    tbd: game.kickoff_tbd,
    final,
    locked: p?.locked,
  })
  const underway = phase === "live" || phase === "pending"
  const favorite = p ? (p.home_win_prob >= 0.5 ? game.home : game.away) : null
  const score = (side: "home" | "away") =>
    final
      ? (game.result?.[`${side}_points`] ?? null)
      : underway || !p
        ? null
        : points(side === "home" ? p.proj_home : p.proj_away)

  return (
    <Link
      href={`/games/${game.id}`}
      aria-label={`${game.away.school} ${game.neutral ? "vs." : "at"} ${game.home.school}: game center`}
      className={cn(
        "tsi-lit-hover block rounded-md border border-border bg-card px-3.5 py-3 active:bg-muted",
        favorite && "tsi-team-light",
      )}
      style={favorite ? teamColorVars(favorite) : undefined}
    >
      <div className="mb-2 flex items-baseline justify-between gap-2 text-xs text-muted-foreground">
        <span>
          {formatKickoff(game.kickoff, game.kickoff_tbd)}
          {game.neutral && ", neutral site"}
        </span>
        <span className="font-medium text-foreground">
          <PhaseLabel phase={phase} />
        </span>
      </div>
      <div className="space-y-1.5">
        <Side
          team={game.away}
          rank={shownRank(ranks[game.away.id])}
          score={score("away")}
          prob={p && !final ? 1 - p.home_win_prob : null}
          won={final && (game.result?.away_points ?? 0) > (game.result?.home_points ?? 0)}
          final={final}
        />
        <Side
          team={game.home}
          rank={shownRank(ranks[game.home.id])}
          score={score("home")}
          prob={p && !final ? p.home_win_prob : null}
          won={final && (game.result?.home_points ?? 0) > (game.result?.away_points ?? 0)}
          final={final}
        />
      </div>
      {p && (
        <dl className="mt-2.5 grid grid-cols-2 gap-3 border-t border-border pt-2 text-xs">
          <Line
            label="TSI"
            value={`${tsiFavoriteLine(p.spread, game.home, game.away)}, ${tsiTotal(p.total)}`}
          />
          <Line
            label="Vegas"
            value={
              m?.spread != null
                ? `${favoriteLine(m.spread, game.home, game.away)}${m.total != null ? `, ${totalLine(m.total)}` : ""}`
                : "No line yet"
            }
          />
        </dl>
      )}
    </Link>
  )
}

function Side({
  team,
  rank,
  score,
  prob,
  won,
  final,
}: {
  team: TeamRef
  rank?: BoardRank
  score: number | null
  prob: number | null // TSI's win chance before the game; null once final
  won: boolean
  final: boolean
}) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_2rem_2.75rem] items-center gap-2">
      <span className="flex min-w-0 items-center gap-2">
        <TeamLogo team={team} size={24} />
        <span className={cn("truncate text-sm", (!final || won) && "font-medium")}>
          {rank && (
            <span className="mr-1 text-xs text-muted-foreground">
              {rank.fcs ? `FCS ${rank.rank}` : rank.rank}
            </span>
          )}
          {team.school}
        </span>
      </span>
      <span
        className={cn(
          "text-right text-lg leading-none font-stretch-condensed tabular-nums",
          final ? (won ? "font-bold" : "text-muted-foreground") : "text-muted-foreground",
        )}
      >
        {score ?? "—"}
      </span>
      <span className="text-right text-xs text-muted-foreground tabular-nums">
        {prob == null ? "" : chance(prob)}
      </span>
    </div>
  )
}

function Line({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="truncate font-medium tabular-nums">{value}</dd>
    </div>
  )
}
