import Link from "next/link"

import { TeamLogo } from "@/components/team/team-logo"
import type { RankedTeam } from "@/lib/api/types"
import { DIVISION_NAME, type Division } from "@/lib/divisions"
import { record } from "@/lib/format/numbers"
import { rankWindow } from "@/lib/rank-window"
import { cfb } from "@/lib/routes"
import { cn } from "@/lib/utils"

const RANKINGS = [
  { key: "resume", title: "Résumé Rankings", rankOf: (t: RankedTeam) => t.rank_resume },
  { key: "power", title: "Power Rankings", rankOf: (t: RankedTeam) => t.rank_power },
] as const

/**
 * Where the team stands in the Résumé and Power rankings (owner, #199): the team and the two
 * teams on either side, or the next four at #1 and the four above when last, in the home
 * page's Top 25 row style; the team's own row is highlighted, a rule between the two
 * rankings, and both lists stretch to the Next Game card's height. Ranks are within its
 * division.
 */
export function RankNeighbors({
  ranked,
  slug,
  division,
}: {
  ranked: RankedTeam[] // the division's rated teams, each with both ranks
  slug: string
  division: Division
}) {
  return (
    <div className="flex h-full min-w-0 flex-col gap-5">
      {RANKINGS.map((r, i) => {
        const rows = rankWindow(ranked, r.rankOf, (t) => t.team.slug === slug)
        const headingId = `neighbors-${r.key}`
        return (
          <section
            key={r.key}
            aria-labelledby={headingId}
            className={cn(
              "flex flex-1 flex-col gap-2",
              i > 0 && "border-t border-border pt-5", // the rule between Résumé and Power
            )}
          >
            <div className="flex items-baseline justify-between gap-3">
              <h2 id={headingId} className="text-lg font-semibold font-stretch-condensed">
                {r.title}
              </h2>
              <Link
                href={cfb.rankings(division)}
                className="text-sm text-muted-foreground underline decoration-muted-foreground underline-offset-4 hover:text-foreground hover:decoration-foreground"
              >
                Full Rankings
              </Link>
            </div>
            {rows.length === 0 ? (
              <p className="rounded-md border border-border bg-card p-4 text-sm text-muted-foreground">
                Not ranked yet.
              </p>
            ) : (
              <ol
                aria-label={`${r.title}, ${DIVISION_NAME[division]}`}
                className="flex flex-1 flex-col divide-y divide-border rounded-md border border-border bg-card text-sm"
              >
                {rows.map(({ row, rank }) => {
                  const me = row.team.slug === slug
                  return (
                    <li key={row.team.id} className={cn("flex flex-1", me && "bg-muted")}>
                      <Link
                        href={cfb.team(row.team.slug)}
                        aria-current={me ? "page" : undefined}
                        className="group grid w-full grid-cols-[1.75rem_1.5rem_minmax(0,1fr)_auto] items-center gap-2 px-2.5 py-1.5"
                      >
                        <span className="font-semibold tabular-nums">{rank}</span>
                        <TeamLogo team={row.team} size={22} />
                        <span
                          className={cn("truncate group-hover:underline", me && "font-semibold")}
                        >
                          {row.team.school}
                        </span>
                        <span className="text-muted-foreground tabular-nums">
                          {record(row.wins, row.losses, row.ties)}
                        </span>
                      </Link>
                    </li>
                  )
                })}
              </ol>
            )}
          </section>
        )
      })}
    </div>
  )
}
