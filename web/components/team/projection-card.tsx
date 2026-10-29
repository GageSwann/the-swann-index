import { ScrollIntoView } from "@/components/ui/scroll-into-view"
import type { TeamProfile } from "@/lib/api/types"
import { chance, record } from "@/lib/format/numbers"

import { WinHistogram } from "./win-histogram"

/**
 * Where the season is headed (decision #98): projected wins, the chance to win out, and
 * conference title odds from the nightly season simulation, plus the spread of final
 * win totals. Shown for every rated team; a value the API doesn't have is left out.
 */
export function ProjectionCard({ profile }: { profile: TeamProfile }) {
  if (!profile.ratings) return null // non-FBS teams aren't simulated
  const proj = profile.projection
  const conf = profile.team.conference ?? "conference"
  const rec = record(profile.wins, profile.losses, profile.ties)

  return (
    <section id="projection" aria-labelledby="projection-heading" className="scroll-mt-6 space-y-3">
      <ScrollIntoView id="projection" />
      <h2 id="projection-heading" className="text-2xl font-semibold font-stretch-condensed">
        Projected record
      </h2>
      <div className="space-y-5 rounded-md border border-border bg-card p-5">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
          <Stat label="Record now" value={rec} />
          {proj && <Stat label="Projected wins" value={proj.expected_wins.toFixed(1)} />}
          {proj && <Stat label="Wins out" value={chance(proj.win_out_prob)} />}
          {proj?.conference_title_prob != null && (
            <Stat label={`Wins the ${conf}`} value={chance(proj.conference_title_prob)} />
          )}
        </dl>
        {proj?.title_game_prob != null && (
          <p className="text-sm text-muted-foreground">
            Plays in the {conf} title game in {chance(proj.title_game_prob)} of simulated seasons.
          </p>
        )}
        {proj && <WinHistogram dist={proj.win_dist} school={profile.team.school} />}
        <p className="max-w-[70ch] text-sm text-muted-foreground">
          {proj
            ? "Each remaining game uses TSI's published prediction, and in every simulated season each team can be better or worse than its rating for the rest of the year. Conference title games follow the simulated standings (simplified tiebreakers) and count as a win."
            : "The season projection appears after the next nightly update."}
        </p>
      </div>
    </section>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-2xl font-bold font-stretch-condensed">{value}</dd>
    </div>
  )
}
