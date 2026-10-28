import { TeamLink } from "@/components/team/team-link"
import type { RankedTeam } from "@/lib/api/types"

import { RankChange } from "./rank-change"

type Move = { team: RankedTeam; moved: number }

/**
 * The week's biggest risers and fallers among the given teams (the active ranking and
 * conference filter). Sorting only: ranks and week-ago ranks both come from the API.
 * Ties go to the higher-ranked team.
 */
export function Movers({
  teams,
  since,
  count = 5,
}: {
  teams: RankedTeam[]
  since: string
  count?: number
}) {
  const moves: Move[] = teams
    .filter((t) => t.previous_rank !== null && t.previous_rank !== t.rank)
    .map((t) => ({ team: t, moved: (t.previous_rank ?? t.rank) - t.rank }))
  const byRank = (a: Move, b: Move) => a.team.rank - b.team.rank
  const risers = moves
    .filter((m) => m.moved > 0)
    .sort((a, b) => b.moved - a.moved || byRank(a, b))
    .slice(0, count)
  const fallers = moves
    .filter((m) => m.moved < 0)
    .sort((a, b) => a.moved - b.moved || byRank(a, b))
    .slice(0, count)
  if (risers.length + fallers.length === 0) return null

  return (
    <aside
      aria-labelledby="movers-heading"
      className="space-y-4 rounded-md border border-border bg-card p-4"
    >
      <div>
        <h2 id="movers-heading" className="text-xl font-semibold font-stretch-condensed">
          Biggest movers
        </h2>
        <p className="text-sm text-muted-foreground">Rank change since {since}.</p>
      </div>
      <MoveList title="Risers" moves={risers} />
      <MoveList title="Fallers" moves={fallers} />
    </aside>
  )
}

function MoveList({ title, moves }: { title: string; moves: Move[] }) {
  if (moves.length === 0) return null
  return (
    <div className="space-y-1.5">
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <ol className="space-y-1">
        {moves.map(({ team: t }) => (
          <li key={t.team.slug} className="flex items-center gap-2 text-sm">
            <span className="w-9 shrink-0 tabular-nums">
              <RankChange rank={t.rank} previous={t.previous_rank} />
            </span>
            <span className="min-w-0 flex-1">
              <TeamLink team={t.team} />
            </span>
            <span className="shrink-0 text-muted-foreground tabular-nums">
              #{t.previous_rank} → #{t.rank}
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
