import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { Suspense } from "react"

import { RatingTrendChart } from "@/components/charts/rating-trend-chart"
import { PageHeading } from "@/components/layout/page-heading"
import { RankProfile } from "@/components/team/rank-profile"
import { ScheduleTable } from "@/components/team/schedule-table"
import { TeamHeader } from "@/components/team/team-header"
import { getRankings, getTeam } from "@/lib/api/queries"
import { scheduleOdds } from "@/lib/api/schedule-odds"
import { pageMeta } from "@/lib/metadata"
import { record, signed } from "@/lib/format/numbers"

type Props = PageProps<"/teams/[slug]">

/** Prerender the current Top 25; every other team renders on first visit and is cached. */
export async function generateStaticParams() {
  const rankings = await getRankings()
  return (rankings?.teams ?? []).slice(0, 25).map((t) => ({ slug: t.team.slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const profile = await getTeam((await params).slug).catch(() => null)
  if (!profile) return { title: "Team" }
  const { team, ratings: r } = profile
  const rec = record(profile.wins, profile.losses, profile.ties)
  return pageMeta({
    ownImage: true,
    title: team.school,
    description: r?.rank_power
      ? `${team.school} (${rec}) is #${r.rank_power} in the TSI Power rankings and #${r.rank_resume ?? "—"} in Résumé, rating ${signed(r.rating)}. Schedule, win chances and rating trend.`
      : `${team.school} (${rec}): schedule and TSI win chances.`,
  })
}

export default function TeamPage(props: Props) {
  return (
    <Suspense fallback={<PageHeading title="Team">Loading the team.</PageHeading>}>
      <TeamView {...props} />
    </Suspense>
  )
}

async function TeamView({ params }: Props) {
  const { slug } = await params
  const [profile, rankings] = await Promise.all([getTeam(slug), getRankings()])
  if (!profile) notFound()
  const odds = await scheduleOdds(profile.team, profile.schedule)
  const ranked = rankings?.teams ?? []
  const row = ranked.find((t) => t.team.slug === slug)
  const ranks = new Map(ranked.map((t) => [t.team.slug, t.rank]))

  return (
    <div className="space-y-10">
      <TeamHeader profile={profile} />
      {row && <RankProfile row={row} count={ranked.length} />}
      {profile.history.length > 0 && (
        <section aria-labelledby="trend-heading" className="space-y-3">
          <h2 id="trend-heading" className="text-2xl font-semibold font-stretch-condensed">
            Rating trend
          </h2>
          <RatingTrendChart series={[{ team: profile.team, history: profile.history }]} />
        </section>
      )}
      <ScheduleTable schedule={profile.schedule} odds={odds} ranks={ranks} />
    </div>
  )
}
