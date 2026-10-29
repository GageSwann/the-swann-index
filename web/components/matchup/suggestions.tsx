import Link from "next/link"

import type { RankedTeam } from "@/lib/api/types"
import { matchupQuery } from "@/lib/matchup"

/** Before anything is picked: a few matchups among the top teams, on neutral fields. */
export function Suggestions({ top }: { top: RankedTeam[] }) {
  const pairs = [0, 2, 4]
    .map((i) => [top[i], top[i + 1]] as const)
    .filter((p): p is readonly [RankedTeam, RankedTeam] => Boolean(p[0] && p[1]))
  if (pairs.length === 0) return null
  return (
    <section aria-labelledby="ideas-heading" className="space-y-3">
      <h2 id="ideas-heading" className="text-2xl font-semibold font-stretch-condensed">
        Try one
      </h2>
      <ul className="space-y-2">
        {pairs.map(([a, b]) => (
          <li key={`${a.team.slug}-${b.team.slug}`}>
            <Link
              href={`/matchup?${matchupQuery({ away: b.team.slug, home: a.team.slug, neutral: true })}`}
              className="inline-flex min-h-8 items-center text-primary underline-offset-4 hover:underline"
            >
              #{b.rank} {b.team.school} vs #{a.rank} {a.team.school}, neutral site
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
