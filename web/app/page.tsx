import { PageHeading } from "@/components/layout/page-heading"
import { RankingsView } from "@/components/rankings/rankings-view"
import { getRankings } from "@/lib/api/queries"
import { formatMonthDay, formatUpdated } from "@/lib/format/time"

export default async function RankingsPage() {
  const [power, resume] = await Promise.all([
    getRankings({ type: "power" }).catch(() => null),
    getRankings({ type: "resume" }).catch(() => null),
  ])

  if (power === null || resume === null) {
    return (
      <PageHeading title="Rankings">
        Rankings aren&apos;t available right now: the TSI API didn&apos;t return them. They appear
        after the first daily ratings run of the season.
      </PageHeading>
    )
  }

  // Weekly movement compares with ratings from about a week earlier (decision #79).
  const since = power.previous_as_of ? formatMonthDay(power.previous_as_of) : null

  return (
    <>
      <PageHeading title="Rankings">
        Week {power.week}, {power.season}. Updated {formatUpdated(power.as_of)}.
        {since && ` Arrows show each team's move since ${since}.`}
      </PageHeading>
      <RankingsView power={power.teams} resume={resume.teams} since={since} />
    </>
  )
}
