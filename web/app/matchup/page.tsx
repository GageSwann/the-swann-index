import type { Metadata } from "next"
import Link from "next/link"
import { Suspense } from "react"

import { MarginChart } from "@/components/game/margin-chart"
import { AltLadder } from "@/components/game/alt-ladder"
import { ScoreBoard } from "@/components/game/score-board"
import { TaleOfTape } from "@/components/game/tale-of-tape"
import { PageHeading } from "@/components/layout/page-heading"
import { MatchupForm } from "@/components/matchup/matchup-form"
import { MatchupOdds } from "@/components/matchup/matchup-odds"
import { getMatchup, getRankings, getTeam, getTeams } from "@/lib/api/queries"
import type { RankedTeam } from "@/lib/api/types"

export const metadata: Metadata = {
  title: "Matchup",
  description: "How TSI would price any two FBS teams if they played today.",
}

type Props = PageProps<"/matchup">

export default function MatchupPage(props: Props) {
  return (
    <div className="space-y-10">
      <PageHeading title="Matchup">
        Pick any two FBS teams to see how TSI would price the game if it were played today.
      </PageHeading>
      <Suspense fallback={<p className="text-muted-foreground">Loading teams.</p>}>
        <MatchupView {...props} />
      </Suspense>
    </div>
  )
}

const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) || undefined

async function MatchupView({ searchParams }: Props) {
  const q = await searchParams
  const away = one(q.away)
  const home = one(q.home)
  const neutral = one(q.neutral) === "1"
  const [teams, rankings] = await Promise.all([getTeams(), getRankings()])
  // Keyed by the picks so the dropdowns reset after a client-side navigation (e.g. "Swap").
  const form = (
    <MatchupForm
      key={`${away}-${home}-${neutral}`}
      teams={teams}
      away={away}
      home={home}
      neutral={neutral}
    />
  )

  if (!away || !home) {
    return (
      <>
        {form}
        <Suggestions top={rankings?.teams.slice(0, 6) ?? []} />
      </>
    )
  }
  if (away === home) {
    return (
      <>
        {form}
        <p className="text-muted-foreground">Pick two different teams.</p>
      </>
    )
  }
  const matchup = await getMatchup(home, away, neutral).catch(() => null)
  if (!matchup) {
    return (
      <>
        {form}
        <p className="text-muted-foreground">
          TSI couldn&apos;t price that matchup. Check both teams are picked from the lists.
        </p>
      </>
    )
  }
  const [homeProfile, awayProfile] = await Promise.all([getTeam(home), getTeam(away)])
  const margin = matchup.proj_home - matchup.proj_away

  return (
    <>
      {form}
      <ScoreBoard
        away={{ team: matchup.away, profile: awayProfile, score: matchup.proj_away }}
        home={{ team: matchup.home, profile: homeProfile, score: matchup.proj_home }}
        neutral={matchup.neutral}
        context={`Hypothetical${matchup.neutral ? ", neutral site" : ""}, using today's ratings.`}
        note="Projected score and win probability if this game were played today."
        homeWinProb={matchup.home_win_prob}
      />
      <MatchupOdds matchup={matchup} />
      <section aria-labelledby="margin-heading" className="space-y-3">
        <h2 id="margin-heading" className="text-2xl font-semibold font-stretch-condensed">
          Margin distribution
        </h2>
        <MarginChart
          home={matchup.home}
          away={matchup.away}
          margin={margin}
          sigma={matchup.sigma_margin}
          marketSpread={null}
          ladder={matchup.markets.alt_spreads}
        />
      </section>
      <AltLadder markets={matchup.markets} home={matchup.home} />
      {homeProfile && awayProfile && <TaleOfTape home={homeProfile} away={awayProfile} />}
      <p className="max-w-[70ch] text-sm text-muted-foreground">
        This is a what-if, not a published prediction: it isn&apos;t saved, graded or part of the
        TSI Book. It uses the same model as the weekly predictions with today&apos;s ratings, so
        early-season matchups lean on preseason expectations.
      </p>
    </>
  )
}

/** Before anything is picked: a few matchups among the top teams, on neutral fields. */
function Suggestions({ top }: { top: RankedTeam[] }) {
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
              href={`/matchup?away=${b.team.slug}&home=${a.team.slug}&neutral=1`}
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
