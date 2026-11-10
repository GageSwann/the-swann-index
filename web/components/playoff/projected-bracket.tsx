import Link from "next/link"
import type { CSSProperties } from "react"

import { TeamLink } from "@/components/team/team-link"
import { TeamLogo } from "@/components/team/team-logo"
import { BorderLightRings, borderLightVars } from "@/components/ui/border-light"
import type { Playoff } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { percent } from "@/lib/format/numbers"
import { cn } from "@/lib/utils"

import { type BracketGame, buildBracket, type Entry } from "./bracket-layout"

// Geometry (px). A game is two 36 px slots; rows are one game plus a gap apart. Columns
// narrow for five rounds (the FCS playoff), so its champion fits a desktop screen too.
type Columns = { width: number; gutter: number }
const WIDE: Columns = { width: 236, gutter: 40 }
const COMPACT: Columns = { width: 210, gutter: 28 }
const SLOT_H = 36
const GAME_H = 2 * SLOT_H + 2 // + top and bottom border
const UNIT = GAME_H + 18
const HEAD_H = 52
const CHAMP_H = 112
const CHAMP_GAP = 28 // the champion card sits below the final, in its column
const PAD = 12 // room for glows inside the scroll frame

const left = (c: Columns, round: number) => PAD + round * (c.width + c.gutter)
const top = (row: number) => HEAD_H + row * UNIT

/**
 * The projected field as a real bracket (Phase 13.6; decisions #100, #125): rounds left to
 * right with connector lines, the projected champion's path lit in its team color and the
 * champion card carrying the border light (#137). Wider than a phone (and the FCS bracket
 * wider than most screens), so it scrolls sideways inside its own frame; the page never does.
 */
export function ProjectedBracket({ playoff }: { playoff: Playoff }) {
  const bracket = buildBracket(playoff)
  if (!bracket) return null
  const { games, rows, champion } = bracket
  const rounds = playoff.rounds
  const cols = rounds.length >= 5 ? COMPACT : WIDE
  const final = games.at(-1)![0]
  const champTop = top(final.row) + GAME_H + CHAMP_GAP
  const width = left(cols, rounds.length) - cols.gutter + PAD
  const height = Math.max(top(rows - 1) + GAME_H, champTop + CHAMP_H) + PAD

  return (
    <div className="space-y-2">
      <p className="text-sm text-muted-foreground lg:hidden">Scroll sideways for later rounds.</p>
      <div className="overflow-x-auto rounded-md border border-border">
        <div
          className="tsi-team-light relative"
          style={{ width, height, ...teamColorVars(champion.team.team) }}
        >
          <Connectors games={games} cols={cols} />
          {rounds.map((round, r) => (
            <section key={round.name} aria-label={round.name}>
              <h3 className="absolute" style={{ left: left(cols, r), top: PAD, width: cols.width }}>
                <span className="block font-semibold">{round.name}</span>
                {round.note && (
                  <span className="block text-xs text-muted-foreground">{round.note}</span>
                )}
              </h3>
              <ol>
                {games[r].map((g) => (
                  <Game key={g.index} game={g} seeds={playoff.seeds} cols={cols} />
                ))}
              </ol>
            </section>
          ))}
          <Champion
            entry={champion}
            style={{ left: left(cols, final.round), top: champTop, width: cols.width }}
          />
        </div>
      </div>
    </div>
  )
}

function Game({ game, seeds, cols }: { game: BracketGame; seeds: number; cols: Columns }) {
  return (
    <li
      className={cn(
        "absolute divide-y divide-border rounded-md border border-border bg-card",
        game.onChampionPath && "tsi-lit",
      )}
      style={{
        left: left(cols, game.round),
        top: top(game.row),
        width: cols.width,
        height: GAME_H,
      }}
    >
      {game.entries.map((e) => (
        <Slot key={e.seed} entry={e} seeded={e.seed <= seeds} advances={e === game.winner} />
      ))}
    </li>
  )
}

/** One team in a game; unseeded FCS teams (placed by rank) show no seed number. */
function Slot({ entry, seeded, advances }: { entry: Entry; seeded: boolean; advances: boolean }) {
  return (
    <div
      className={cn("flex items-center gap-2 px-2", !advances && "text-muted-foreground")}
      style={{ height: SLOT_H }}
    >
      <span className="w-5 shrink-0 text-right text-xs tabular-nums">
        {seeded ? entry.seed : ""}
      </span>
      {/* A flex box, so long names truncate instead of running into the record (12.7). */}
      <span
        className={cn("flex min-w-0 flex-1 text-sm", advances && "font-semibold")}
        title={entry.team.team.school}
      >
        <TeamLink team={entry.team.team} />
      </span>
      <span className="shrink-0 text-xs tabular-nums">
        {entry.team.wins}-{entry.team.losses}
      </span>
    </div>
  )
}

/** Lines from each game to the slot its winner fills; the champion's path in its color. */
function Connectors({ games, cols }: { games: BracketGame[][]; cols: Columns }) {
  const paths: { d: string; lit: boolean }[] = []
  for (const round of games.slice(1)) {
    for (const g of round) {
      g.feeders.forEach((f, slot) => {
        if (f === null) return
        const from = games[g.round - 1][f]
        const x0 = left(cols, from.round) + cols.width
        const y0 = top(from.row) + GAME_H / 2
        const x1 = left(cols, g.round)
        const y1 = top(g.row) + 1 + SLOT_H * (slot + 0.5)
        const mid = x0 + cols.gutter / 2
        paths.push({
          d: `M${x0} ${y0}H${mid}V${y1}H${x1}`,
          lit: from.onChampionPath && g.onChampionPath,
        })
      })
    }
  }
  const final = games.at(-1)![0]
  const x = left(cols, final.round) + cols.width / 2
  const y = top(final.row) + GAME_H
  paths.push({ d: `M${x} ${y}V${y + CHAMP_GAP}`, lit: true }) // down to the champion card

  return (
    <svg aria-hidden className="absolute inset-0 size-full" fill="none">
      {paths
        .sort((a, b) => Number(a.lit) - Number(b.lit)) // lit lines on top
        .map((p, i) => (
          <path
            key={i}
            d={p.d}
            className={p.lit ? "stroke-(--light)" : "stroke-border"}
            strokeWidth={p.lit ? 2 : 1.5}
          />
        ))}
    </svg>
  )
}

function Champion({ entry, style }: { entry: Entry; style: CSSProperties }) {
  const t = entry.team
  return (
    <div className="absolute" style={{ ...style, height: CHAMP_H }}>
      <div
        className="tsi-border-light flex h-full flex-col justify-center gap-1 rounded-md border border-border bg-card p-3"
        style={borderLightVars(t.team, t.team)}
      >
        <BorderLightRings />
        <p className="text-xs text-muted-foreground">Projected champion</p>
        <Link href={`/teams/${t.team.slug}`} className="group flex min-w-0 items-center gap-2">
          <TeamLogo team={t.team} size={36} />
          <span className="truncate text-xl font-bold font-stretch-condensed group-hover:underline">
            {t.team.school}
          </span>
        </Link>
        <p className="text-xs text-muted-foreground">
          {t.wins}-{t.losses}, {percent(t.champion_prob, 0)} to win it all
        </p>
      </div>
    </div>
  )
}
