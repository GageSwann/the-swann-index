import { MarginChart } from "@/components/charts/lazy"
import { AltLadder } from "@/components/game/alt-ladder"
import { ScoreBoard } from "@/components/game/score-board"
import { TaleOfTape } from "@/components/game/tale-of-tape"
import { getRankings, getTeam, getTeams } from "@/lib/api/queries"
import { type MatchupPick, pricedMatchup } from "@/lib/matchup"

import { MatchupForm } from "./matchup-form"
import { MatchupOdds } from "./matchup-odds"
import { Suggestions } from "./suggestions"

/** The form, then (once two teams are picked) TSI's projection and prices for the game. */
export async function MatchupView({ pick }: { pick: MatchupPick }) {
  const { away, home } = pick
  const [teams, rankings] = await Promise.all([getTeams(), getRankings()])
  // Keyed by the picks so the dropdowns reset after a client-side navigation (e.g. "Swap").
  const form = <MatchupForm key={`${away}-${home}-${pick.neutral}`} teams={teams} pick={pick} />

  if (!away || !home) {
    return (
      <>
        {form}
        <Suggestions top={rankings?.teams.slice(0, 6) ?? []} />
      </>
    )
  }
  const matchup = await pricedMatchup(pick)
  if (!matchup) {
    return (
      <>
        {form}
        <p className="text-muted-foreground">
          {away === home
            ? "Pick two different teams."
            : "TSI couldn't price that matchup. Check both teams are picked from the lists."}
        </p>
      </>
    )
  }
  const [homeProfile, awayProfile] = await Promise.all([getTeam(home), getTeam(away)])

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
          margin={matchup.proj_home - matchup.proj_away}
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
