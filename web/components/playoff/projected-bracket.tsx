import { TeamLink } from "@/components/team/team-link"
import type { Playoff, PlayoffTeam } from "@/lib/api/types"
import { cn } from "@/lib/utils"

type Entry = { seed: number; team: PlayoffTeam }
type Game = { a: Entry; b: Entry; winner: Entry }

/** Columns per round count: the CFP's 4 rounds, the FCS's 5 (three columns below 1536 px). */
const GRID: Record<number, string> = {
  4: "md:grid-cols-2 xl:grid-cols-4",
  5: "md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5",
}

/**
 * The projected field as a bracket (decisions #100, #125), drawn from the API's generic
 * `rounds`, so the CFP and the FCS playoff share it. Each slot is a position in the projected
 * field or the winner of a game in the previous round. In each projected game the team with
 * the better chance of reaching the next round (the round's `advance` field) moves on, all the
 * way to a projected champion.
 */
export function ProjectedBracket({ playoff }: { playoff: Playoff }) {
  const { projected, rounds, seeds } = playoff
  if (rounds.length === 0 || projected.length < playoff.field_size) return null

  const played: Game[][] = []
  for (const round of rounds) {
    const previous = played.at(-1) ?? []
    const odds = (t: PlayoffTeam) => {
      const value = t[round.advance as keyof PlayoffTeam]
      return typeof value === "number" ? value : 0
    }
    played.push(
      round.games.map(([x, y]) => {
        const [a, b] = [x, y].map((slot): Entry => {
          if (slot.seed != null) return { seed: slot.seed, team: projected[slot.seed - 1] }
          return previous[slot.game ?? 0].winner
        })
        return { a, b, winner: odds(a.team) >= odds(b.team) ? a : b }
      }),
    )
  }
  const champion = played.at(-1)?.[0]?.winner

  return (
    <div className={cn("grid gap-6", GRID[rounds.length] ?? GRID[5])}>
      {rounds.map((round, i) => (
        <Round
          key={round.name}
          title={round.name}
          note={round.note}
          games={played[i]}
          seeds={seeds}
          champion={i === rounds.length - 1 ? champion : undefined}
        />
      ))}
    </div>
  )
}

function Round({
  title,
  note,
  games,
  seeds,
  champion,
}: {
  title: string
  note: string | null
  games: Game[]
  seeds: number
  champion?: Entry
}) {
  return (
    <section aria-label={title} className="min-w-0 space-y-3">
      <h3 className="font-semibold">
        {title}
        {note && <span className="ml-2 text-sm font-normal text-muted-foreground">{note}</span>}
      </h3>
      <ol className="space-y-3">
        {games.map((g) => (
          <li
            key={`${g.a.seed}-${g.b.seed}`}
            className="divide-y divide-border rounded-md border border-border bg-card"
          >
            {[g.a, g.b].map((e) => (
              <Slot key={e.seed} entry={e} seeded={e.seed <= seeds} advances={e === g.winner} />
            ))}
          </li>
        ))}
      </ol>
      {champion && (
        <p className="text-sm">
          Projected champion: <span className="font-semibold">{champion.team.team.school}</span>
        </p>
      )}
    </section>
  )
}

/** One team in a game; unseeded FCS teams (placed by rank) show no seed number. */
function Slot({ entry, seeded, advances }: { entry: Entry; seeded: boolean; advances: boolean }) {
  return (
    <div className={cn("flex items-center gap-3 px-3 py-2", !advances && "text-muted-foreground")}>
      <span className="w-5 text-right text-sm tabular-nums">{seeded ? entry.seed : ""}</span>
      {/* A flex box, so long names truncate instead of running into the record (12.7). */}
      <span
        className={cn("flex min-w-0 flex-1", advances && "font-semibold")}
        title={entry.team.team.school}
      >
        <TeamLink team={entry.team.team} />
      </span>
      <span className="text-sm tabular-nums">
        {entry.team.wins}-{entry.team.losses}
      </span>
    </div>
  )
}
