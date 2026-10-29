import { TeamLink } from "@/components/team/team-link"
import type { Playoff, PlayoffTeam } from "@/lib/api/types"
import { cn } from "@/lib/utils"

type Entry = { seed: number; team: PlayoffTeam }
type Game = { a: Entry; b: Entry; winner: Entry }

/**
 * The projected field as a bracket (decision #100). Pairings come from the API's format,
 * so a format change needs no change here. In each projected game the team with the better
 * chance of reaching the next round advances, all the way to a projected champion.
 */
export function ProjectedBracket({ playoff }: { playoff: Playoff }) {
  const { format, projected } = playoff
  if (projected.length < format.field_size) return null
  const seed = (s: number): Entry => ({ seed: s, team: projected[s - 1] })
  const play = (a: Entry, b: Entry, next: (t: PlayoffTeam) => number): Game => ({
    a,
    b,
    winner: next(a.team) >= next(b.team) ? a : b,
  })

  const first = format.first_round.map(([hi, lo]) =>
    play(seed(hi), seed(lo), (t) => t.quarterfinal_prob),
  )
  const quarters = format.quarterfinals.map(([bye, game]) =>
    play(seed(bye), first[game].winner, (t) => t.semifinal_prob),
  )
  const semis = format.semifinals.map(([i, j]) =>
    play(quarters[i].winner, quarters[j].winner, (t) => t.final_prob),
  )
  const final = play(semis[0].winner, semis[1].winner, (t) => t.champion_prob)

  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
      <Round title="First round" note="At the higher seed" games={first} />
      <Round title="Quarterfinals" games={quarters} />
      <Round title="Semifinals" games={semis} />
      <Round title="Championship" games={[final]} champion={final.winner} />
    </div>
  )
}

function Round({
  title,
  note,
  games,
  champion,
}: {
  title: string
  note?: string
  games: Game[]
  champion?: Entry
}) {
  return (
    <section aria-label={title} className="space-y-3">
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
              <Slot key={e.seed} entry={e} advances={e === g.winner} />
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

function Slot({ entry, advances }: { entry: Entry; advances: boolean }) {
  return (
    <div className={cn("flex items-center gap-3 px-3 py-2", !advances && "text-muted-foreground")}>
      <span className="w-5 text-right text-sm tabular-nums">{entry.seed}</span>
      <span className={cn("min-w-0 flex-1", advances && "font-semibold")}>
        <TeamLink team={entry.team.team} />
      </span>
      <span className="text-sm tabular-nums">
        {entry.team.wins}-{entry.team.losses}
      </span>
    </div>
  )
}
