import Image from "next/image"
import Link from "next/link"

import { RankChange } from "@/components/rankings/rank-change"
import type { RankedTeam } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { record } from "@/lib/format/numbers"

type Props = {
  title: string // "FBS Top 25"
  teams: RankedTeam[] // the chosen ranking (Power or Résumé), in order
  href: string // the full rankings page
  linkLabel: string
}

/** A compact Top 25 for the home page's side rails; the full table lives at /rankings. */
export function RankingsRail({ title, teams, href, linkLabel }: Props) {
  const top = teams.slice(0, 25)
  const headingId = `rail-${title.replace(/\W+/g, "-").toLowerCase()}`
  return (
    <section aria-labelledby={headingId} className="min-w-0 space-y-2">
      <h2 id={headingId} className="text-lg font-semibold font-stretch-condensed">
        {title}
      </h2>
      {top.length === 0 ? (
        <p className="text-sm text-muted-foreground">No rankings yet.</p>
      ) : (
        <ol className="divide-y divide-border rounded-md border border-border bg-card text-sm">
          {top.map((t) => (
            <li
              key={t.team.id}
              className="tsi-team-light tsi-row-light group relative"
              style={teamColorVars(t.team)}
            >
              <Link
                href={`/teams/${t.team.slug}`}
                className="grid grid-cols-[1.75rem_1.5rem_minmax(0,1fr)_auto_2.25rem] items-center gap-2 px-2.5 py-1.5"
              >
                <span className="text-right font-semibold">{t.rank}</span>
                {/* A white tile, as on the scoreboard: dark logos vanish on the black theme. */}
                <span className="flex size-6 items-center justify-center rounded-sm bg-white">
                  {t.team.logo_url && (
                    <Image
                      src={t.team.logo_url}
                      alt=""
                      width={20}
                      height={20}
                      className="size-5 object-contain"
                    />
                  )}
                </span>
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
      <Link
        href={href}
        className="inline-flex min-h-8 items-center text-sm underline decoration-muted-foreground underline-offset-4 hover:decoration-foreground"
      >
        {linkLabel}
      </Link>
    </section>
  )
}
