"use client"

import Link from "next/link"
import { useState } from "react"

import { TeamLogo } from "@/components/team/team-logo"
import type { Playoff } from "@/lib/api/types"
import { chance } from "@/lib/format/numbers"
import { cfb } from "@/lib/routes"
import { cn } from "@/lib/utils"

import { type BracketGame, buildBracket, type Entry } from "./bracket-layout"

/**
 * Phones only (owner, 2026-11-23, #165): the bracket one round at a time, like a sports app,
 * instead of five columns that scroll sideways. A row of round tabs (opening on the first
 * round not yet finished) over that round's games, full width, each with its two teams,
 * seeds and the score or TSI's win chance. Wider screens draw the full bracket.
 */
export function BracketByRound({ playoff }: { playoff: Playoff }) {
  const bracket = buildBracket(playoff)
  const current = bracket
    ? bracket.games.findIndex((round) => round.some((g) => !g.real?.completed))
    : 0
  const [round, setRound] = useState(Math.max(0, current))
  if (!bracket) return null
  const games = bracket.games[round] ?? []
  const info = playoff.rounds[round]

  return (
    <div className="space-y-3">
      <div
        role="tablist"
        aria-label="Round"
        className="-mx-4 flex [scrollbar-width:none] gap-1.5 overflow-x-auto px-4 pb-1"
      >
        {playoff.rounds.map((r, i) => (
          <button
            key={r.name}
            type="button"
            role="tab"
            aria-selected={i === round}
            onClick={() => setRound(i)}
            className={cn(
              "shrink-0 rounded-full border px-3 py-1.5 text-sm font-medium whitespace-nowrap",
              i === round
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-muted-foreground",
            )}
          >
            {r.name}
          </button>
        ))}
      </div>
      {info?.note && <p className="text-xs text-muted-foreground">{info.note}</p>}
      <ol className="space-y-2.5">
        {games.map((g) => (
          <li key={g.index}>
            <GameCard game={g} seeds={playoff.seeds} />
          </li>
        ))}
      </ol>
      {round === playoff.rounds.length - 1 && (
        <p className="text-sm text-muted-foreground">
          {bracket.games.at(-1)?.[0]?.real?.completed ? "Champion: " : "Projected champion: "}
          <span className="font-semibold text-foreground">{bracket.champion.team.team.school}</span>
          {bracket.games.at(-1)?.[0]?.real?.completed
            ? ""
            : `, ${chance(bracket.champion.team.champion_prob)} to win it all`}
        </p>
      )}
    </div>
  )
}

function GameCard({ game, seeds }: { game: BracketGame; seeds: number }) {
  const body = (
    <div className="divide-y divide-border rounded-md border border-border bg-card">
      {game.entries.map((e, side) => (
        <Row
          key={e.seed}
          entry={e}
          seeded={e.seed <= seeds}
          advances={e === game.winner}
          value={value(game, e, side)}
        />
      ))}
    </div>
  )
  return game.real ? (
    <Link href={cfb.game(game.real.id)} className="block active:opacity-80">
      {body}
    </Link>
  ) : (
    body
  )
}

/** The score once final, TSI's win chance before, else the team's record. */
function value(game: BracketGame, entry: Entry, side: number): string {
  const real = game.real
  if (real?.completed && real.points[side] != null) return String(real.points[side])
  if (real?.winProb) return chance(real.winProb[side])
  return `${entry.team.wins}-${entry.team.losses}`
}

function Row({
  entry,
  seeded,
  advances,
  value,
}: {
  entry: Entry
  seeded: boolean
  advances: boolean
  value: string
}) {
  return (
    <div
      className={cn(
        "grid min-h-12 grid-cols-[1.5rem_1.75rem_minmax(0,1fr)_auto] items-center gap-2 px-3",
        !advances && "text-muted-foreground",
      )}
    >
      <span className="text-right text-xs tabular-nums">{seeded ? entry.seed : ""}</span>
      <TeamLogo team={entry.team.team} size={26} />
      <span className={cn("truncate text-sm", advances && "font-semibold text-foreground")}>
        {entry.team.team.school}
      </span>
      <span className={cn("text-sm tabular-nums", advances && "font-semibold text-foreground")}>
        {value}
      </span>
    </div>
  )
}
