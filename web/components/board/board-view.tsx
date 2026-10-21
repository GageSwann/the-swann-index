"use client"

import { useMemo, useState } from "react"

import type { GameSummary } from "@/lib/api/types"
import { formatDay } from "@/lib/format/time"

import { MatchupCard } from "./matchup-card"

type Sort = "kickoff" | "edge" | "closest"
type Props = { games: GameSummary[]; ranks: Record<number, number> }

const SORTS: { value: Sort; label: string }[] = [
  { value: "kickoff", label: "Kickoff" },
  { value: "edge", label: "Biggest edge" },
  { value: "closest", label: "Closest game" },
]

export function BoardView({ games, ranks }: Props) {
  const [top25, setTop25] = useState(false)
  const [playsOnly, setPlaysOnly] = useState(false)
  const [conference, setConference] = useState("")
  const [sort, setSort] = useState<Sort>("kickoff")

  const conferences = useMemo(
    () =>
      [...new Set(games.flatMap((g) => [g.home.conference, g.away.conference]))]
        .filter((c): c is string => !!c)
        .sort(),
    [games],
  )
  const shown = useMemo(() => {
    const ranked = (g: GameSummary) =>
      (ranks[g.home.id] ?? 99) <= 25 || (ranks[g.away.id] ?? 99) <= 25
    const filtered = games.filter(
      (g) =>
        (!top25 || ranked(g)) &&
        (!playsOnly || (g.prediction?.picks.length ?? 0) > 0) &&
        (!conference || g.home.conference === conference || g.away.conference === conference),
    )
    if (sort === "kickoff") return filtered
    return [...filtered].sort((a, b) => sortKey(a, sort) - sortKey(b, sort))
  }, [games, ranks, top25, playsOnly, conference, sort])

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3 text-sm">
        <Check label="Top 25 only" checked={top25} onChange={setTop25} />
        <Check label="TSI plays only" checked={playsOnly} onChange={setPlaysOnly} />
        <label className="flex items-center gap-2 text-muted-foreground">
          Conference
          <select
            value={conference}
            onChange={(e) => setConference(e.target.value)}
            className="rounded-md border border-border bg-card px-2 py-1.5 text-foreground"
          >
            <option value="">All conferences</option>
            {conferences.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-muted-foreground">
          Sort by
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as Sort)}
            className="rounded-md border border-border bg-card px-2 py-1.5 text-foreground"
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <span className="text-muted-foreground">
          {shown.length} of {games.length} games
        </span>
      </div>

      {shown.length === 0 ? (
        <p className="text-muted-foreground">No games match these filters.</p>
      ) : sort === "kickoff" ? (
        groupByDay(shown).map(([day, dayGames]) => (
          <section key={day} aria-label={day} className="space-y-3">
            <h2 className="text-xl font-semibold font-stretch-condensed">{day}</h2>
            <Grid games={dayGames} ranks={ranks} />
          </section>
        ))
      ) : (
        <Grid games={shown} ranks={ranks} />
      )}
    </div>
  )
}

function Grid({ games, ranks }: Props) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {games.map((g) => (
        <MatchupCard key={g.id} game={g} ranks={ranks} />
      ))}
    </div>
  )
}

function Check({
  label,
  checked,
  onChange,
}: {
  label: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <label className="flex items-center gap-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="size-4 accent-primary"
      />
      {label}
    </label>
  )
}

function sortKey(g: GameSummary, sort: Sort): number {
  const p = g.prediction
  if (p === null) return Number.POSITIVE_INFINITY
  if (sort === "edge") return -Math.max(-1, ...p.picks.map((pick) => pick.edge))
  return Math.abs(p.home_win_prob - 0.5) // closest first
}

function groupByDay(games: GameSummary[]): [string, GameSummary[]][] {
  const days = new Map<string, GameSummary[]>()
  for (const g of games) {
    const day = g.kickoff ? formatDay(g.kickoff) : "Date to be announced"
    days.set(day, [...(days.get(day) ?? []), g])
  }
  return [...days.entries()]
}
