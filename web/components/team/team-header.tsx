import Image from "next/image"

import type { TeamProfile } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { record, signed } from "@/lib/format/numbers"

/**
 * Team identity and its headline numbers. A solid band in the team's (contrast-checked)
 * color tops the panel: flat like the rest of the design, no gradients.
 */
export function TeamHeader({ profile }: { profile: TeamProfile }) {
  const { team, ratings: r } = profile
  const stats = r
    ? [
        { label: "Power rank", value: r.rank_power ? `#${r.rank_power}` : "—" },
        { label: "Résumé rank", value: r.rank_resume ? `#${r.rank_resume}` : "—" },
        { label: "Rating", value: signed(r.rating) },
        {
          label: "Predictive",
          value:
            r.predictive_rating == null
              ? "—"
              : `${signed(r.predictive_rating)}${r.predictive_rank ? ` (#${r.predictive_rank})` : ""}`,
        },
        { label: "Schedule strength", value: r.sos == null ? "—" : signed(r.sos) },
      ]
    : []

  return (
    <section
      aria-label="Team summary"
      className="overflow-hidden rounded-md border border-border bg-card"
      style={teamColorVars(team)}
    >
      <div aria-hidden className="h-2 bg-[var(--team-light)] dark:bg-[var(--team-dark)]" />
      <div className="space-y-5 p-5">
        <div className="flex items-center gap-4">
          <span className="flex size-16 shrink-0 items-center justify-center rounded-md bg-white sm:size-20">
            {team.logo_url && (
              <Image
                src={team.logo_url}
                alt=""
                width={64}
                height={64}
                className="size-13 object-contain sm:size-16"
                priority
              />
            )}
          </span>
          <div className="min-w-0">
            <h1 className="text-4xl leading-tight font-bold font-stretch-condensed sm:text-5xl">
              {team.school}
            </h1>
            <p className="text-muted-foreground">
              {[team.mascot, team.conference].filter(Boolean).join(", ")}
              {". "}
              {record(profile.wins, profile.losses, profile.ties)} in {profile.season}
              {r?.provisional && ". Provisional rating (fewer than 4 games)"}
            </p>
          </div>
        </div>
        {r ? (
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-5">
            {stats.map((s) => (
              <div key={s.label}>
                <dt className="text-sm text-muted-foreground">{s.label}</dt>
                <dd className="text-2xl font-bold font-stretch-condensed">{s.value}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">
            TSI rates FBS teams only, so this team has no rating.
          </p>
        )}
        {r && (
          <p className="text-xs text-muted-foreground">
            Rating and ranks use this season&apos;s games only; the predictive rating also weighs
            the preseason prior and drives TSI&apos;s game predictions.
          </p>
        )}
      </div>
    </section>
  )
}
