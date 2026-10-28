import { ScrollIntoView } from "@/components/ui/scroll-into-view"
import type { TeamProfile } from "@/lib/api/types"
import { chance, record, signed } from "@/lib/format/numbers"

/**
 * Why the team ranks where it does in Résumé (decision #89): how a typical #12 team would
 * fare against the same games, with each opponent's current rating. Shown for every
 * rated team (the API always returns the summary for them); the expected wins are left
 * out while a counted game's difficulty is unknown. Every number comes from the API.
 */
export function ResumeCard({ profile }: { profile: TeamProfile }) {
  const res = profile.resume
  if (!res) return null // non-FBS teams: no rating, no résumé
  const rank = profile.ratings?.rank_resume
  const school = profile.team.school
  const rec = record(profile.wins, profile.losses, profile.ties)
  const expected = res.benchmark_expected_wins

  return (
    <section id="resume" aria-labelledby="resume-heading" className="scroll-mt-6 space-y-3">
      <ScrollIntoView id="resume" />
      <h2 id="resume-heading" className="text-2xl font-semibold font-stretch-condensed">
        Résumé
      </h2>
      <div className="space-y-4 rounded-md border border-border bg-card p-5">
        {res.games === 0 ? (
          <p className="text-sm text-muted-foreground">
            No games played yet: the Résumé starts after {school}&apos;s first game.
          </p>
        ) : (
          <>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
              <Stat label="Résumé rank" value={rank ? `#${rank}` : "—"} />
              <Stat label="Record" value={rec} />
              {expected != null && (
                <Stat label="#12 team expects" value={`${expected.toFixed(1)} wins`} />
              )}
              <Stat label="#12 team matches it" value={res.sor == null ? "—" : chance(res.sor)} />
            </dl>
            <p className="max-w-[70ch] text-sm text-muted-foreground">
              How hard is {school}&apos;s record to match? A typical #12 team (rating{" "}
              {signed(res.benchmark_rating)}) playing these same {res.games} games, against each
              opponent&apos;s current rating,
              {expected != null && ` would win ${expected.toFixed(1)} on average and`}
              {res.sor != null &&
                `${expected != null ? "" : " would"} do at least as well as ${rec} ${chance(res.sor)} of the time`}
              . The lower that chance, the more impressive the record. The &ldquo;#12 team
              wins&rdquo; column in the schedule shows how hard each game was.
            </p>
          </>
        )}
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
