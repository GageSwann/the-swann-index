import Link from "next/link"

import { RankChange } from "@/components/rankings/rank-change"
import { TeamLogo } from "@/components/team/team-logo"
import type { RankedTeam } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { record } from "@/lib/format/numbers"

type Props = {
  id: string // for the heading
  title: string // "FBS Top 25"
  teams: RankedTeam[] // the chosen ranking (Power or Résumé), in order
  href: string // the full rankings page
}

/**
 * A compact Top 25 for the home page's side rails; the full table lives at /rankings.
 * The list stretches to its column's height (rows share any extra space evenly), so its
 * bottom lines up with the games of the week beside it.
 */
export function RankingsRail({ id, title, teams, href }: Props) {
  const top = teams.slice(0, 25)
  const headingId = `rail-${id}`
  return (
    <section aria-labelledby={headingId} className="flex h-full min-w-0 flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id={headingId} className="text-lg font-semibold font-stretch-condensed">
          {title}
        </h2>
        <Link
          href={href}
          className="text-sm text-muted-foreground underline decoration-muted-foreground underline-offset-4 hover:text-foreground hover:decoration-foreground"
        >
          Full Rankings
        </Link>
      </div>
      {top.length === 0 ? (
        <p className="rounded-md border border-border bg-card p-4 text-sm text-muted-foreground">
          The rankings appear after the first nightly update of the season.
        </p>
      ) : (
        <ol className="flex flex-1 flex-col divide-y divide-border rounded-md border border-border bg-card text-sm">
          {top.map((t) => (
            <li
              key={t.team.id}
              className="tsi-team-light tsi-row-light group flex flex-1"
              style={teamColorVars(t.team)}
            >
              <Link
                href={`/teams/${t.team.slug}`}
                className="grid w-full grid-cols-[1.25rem_1.5rem_minmax(0,1fr)_auto_2.25rem] items-center gap-2 px-2.5 py-1.5"
              >
                <span className="font-semibold">{t.rank}</span>
                <TeamLogo team={t.team} size={22} />
                <span className="truncate group-hover:underline">{t.team.school}</span>
                <span className="text-muted-foreground">{record(t.wins, t.losses, t.ties)}</span>
                <span className="text-right text-xs">
                  {/* No "new" on every row before a division's first Sunday poll. */}
                  {t.previous_rank !== null && (
                    <RankChange rank={t.rank} previous={t.previous_rank} />
                  )}
                </span>
              </Link>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
