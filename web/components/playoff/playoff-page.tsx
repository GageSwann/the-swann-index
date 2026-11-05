import type { ReactNode } from "react"

import { PageHeading } from "@/components/layout/page-heading"
import { DivisionNav } from "@/components/ui/division-nav"
import { getPlayoff } from "@/lib/api/queries"
import type { Division } from "@/lib/divisions"
import { formatDay } from "@/lib/format/time"

import { PlayoffOdds } from "./playoff-odds"
import { ProjectedBracket } from "./projected-bracket"

const PLAYOFF_HREF: Record<Division, string> = { fbs: "/playoff", fcs: "/playoff/fcs" }

const COPY: Record<
  Division,
  { title: string; field: string; bracket: ReactNode; odds: ReactNode; offSeason: string }
> = {
  fbs: {
    title: "Playoff",
    field: "Who makes the 12-team field and who wins it",
    bracket: (
      <>
        One representative field: each power conference&apos;s likeliest champion, the likeliest
        group-of-six team, Notre Dame if it&apos;s among the twelve likeliest, then at-large teams
        by playoff odds, seeded by their average seed. In each game the team more likely to reach
        the next round advances.
      </>
    ),
    odds: (
      <>
        In each simulated season, TSI ranks teams by Résumé on their final records (its stand-in for
        the selection committee), picks the field with this season&apos;s rules (the ACC, Big Ten,
        Big 12 and SEC champions, the best group-of-six team, Notre Dame if it&apos;s in the top 12,
        then at-large by rank), and plays the bracket: first-round games at the higher seed, the
        rest at neutral sites. Title odds are TSI&apos;s title chance as fair American odds (no
        vig), not a betting line.
      </>
    ),
    offSeason:
      "Playoff odds run during the regular season, from the nightly simulation. Once the real field is set, they stop until next season.",
  },
  fcs: {
    title: "FCS playoff",
    field: "Who makes the 24-team FCS field and who wins it",
    bracket: (
      <>
        One representative field: each automatic-bid conference&apos;s likeliest champion, then
        at-large teams by playoff odds. The 16 teams likeliest to be seeded are numbered by their
        average seed; the other eight are placed by playoff odds (the real committee places them by
        region). In each game the team more likely to reach the next round advances.
      </>
    ),
    odds: (
      <>
        In each simulated season, TSI gives automatic bids to the champions of 11 conferences, then
        ranks the rest by the FCS Résumé on their final records (its stand-in for the selection
        committee) for the at-large bids. Seeds 1–8 get first-round byes and seeds 9–16 host the
        first round; the better seed hosts after that, until the final at a neutral site. The SWAC
        and MEAC don&apos;t take part, and teams in their first four FCS seasons after moving up
        aren&apos;t eligible. Title odds are TSI&apos;s title chance as fair American odds (no vig),
        not a betting line.
      </>
    ),
    offSeason:
      "FCS playoff odds run during the regular season, from the nightly simulation. Once the real field is set, they stop until next season.",
  },
}

/** `/playoff` (the CFP, #101) and `/playoff/fcs` (the 24-team FCS playoff, #125). */
export async function PlayoffPage({ division }: { division: Division }) {
  const playoff = await getPlayoff(division)
  const copy = COPY[division]

  return (
    <div className="space-y-10">
      <div>
        <PageHeading title={copy.title}>
          {playoff
            ? `Week ${playoff.week}, ${playoff.season}. Updated ${formatDay(playoff.as_of)}. `
            : ""}
          {copy.field}, from {playoff?.sims?.toLocaleString("en-US") ?? "10,000"} simulated seasons
          of TSI&apos;s predictions.
        </PageHeading>
        <DivisionNav current={division} hrefs={PLAYOFF_HREF} label="Playoff division" />
      </div>
      {playoff ? (
        <>
          <section aria-labelledby="bracket-heading" className="space-y-4">
            <h2 id="bracket-heading" className="text-2xl font-semibold font-stretch-condensed">
              Projected bracket
            </h2>
            <ProjectedBracket playoff={playoff} />
            <p className="max-w-[70ch] text-sm text-muted-foreground">{copy.bracket}</p>
          </section>
          <section aria-labelledby="odds-heading" className="space-y-4">
            <h2 id="odds-heading" className="text-2xl font-semibold font-stretch-condensed">
              Playoff odds
            </h2>
            <PlayoffOdds teams={playoff.teams} division={division} />
            <p className="max-w-[70ch] text-sm text-muted-foreground">{copy.odds}</p>
          </section>
        </>
      ) : (
        <p className="text-muted-foreground">{copy.offSeason}</p>
      )}
    </div>
  )
}
