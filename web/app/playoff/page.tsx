import type { Metadata } from "next"

import { PageHeading } from "@/components/layout/page-heading"
import { PlayoffOdds } from "@/components/playoff/playoff-odds"
import { ProjectedBracket } from "@/components/playoff/projected-bracket"
import { getPlayoff } from "@/lib/api/queries"
import { formatDay } from "@/lib/format/time"
import { pageMeta } from "@/lib/metadata"

export const metadata: Metadata = pageMeta({
  title: "Playoff",
  description:
    "TSI's College Football Playoff odds and projected 12-team bracket from 10,000 simulated seasons, with fair odds for the national title.",
})

export default async function PlayoffPage() {
  const playoff = await getPlayoff()

  return (
    <div className="space-y-10">
      <PageHeading title="Playoff">
        {playoff
          ? `Week ${playoff.week}, ${playoff.season}. Updated ${formatDay(playoff.as_of)}. `
          : ""}
        Who makes the 12-team field and who wins it, from{" "}
        {playoff?.sims?.toLocaleString("en-US") ?? "10,000"} simulated seasons of TSI&apos;s
        predictions.
      </PageHeading>
      {playoff ? (
        <>
          <section aria-labelledby="bracket-heading" className="space-y-4">
            <h2 id="bracket-heading" className="text-2xl font-semibold font-stretch-condensed">
              Projected bracket
            </h2>
            <ProjectedBracket playoff={playoff} />
            <p className="max-w-[70ch] text-sm text-muted-foreground">
              One representative field: each power conference&apos;s likeliest champion, the
              likeliest group-of-six team, Notre Dame if it&apos;s among the twelve likeliest, then
              at-large teams by playoff odds, seeded by their average seed. In each game the team
              more likely to reach the next round advances.
            </p>
          </section>
          <section aria-labelledby="odds-heading" className="space-y-4">
            <h2 id="odds-heading" className="text-2xl font-semibold font-stretch-condensed">
              Playoff odds
            </h2>
            <PlayoffOdds teams={playoff.teams} />
            <p className="max-w-[70ch] text-sm text-muted-foreground">
              In each simulated season, TSI ranks teams by Résumé on their final records (its
              stand-in for the selection committee), picks the field with this season&apos;s rules
              (the ACC, Big Ten, Big 12 and SEC champions, the best group-of-six team, Notre Dame if
              it&apos;s in the top 12, then at-large by rank), and plays the bracket: first-round
              games at the higher seed, the rest at neutral sites. Title odds are TSI&apos;s title
              chance as fair American odds (no vig), not a betting line.
            </p>
          </section>
        </>
      ) : (
        <p className="text-muted-foreground">
          Playoff odds run during the regular season, from the nightly simulation. Once the real
          field is set, they stop until next season.
        </p>
      )}
    </div>
  )
}
