import type { TeamProfile } from "@/lib/api/types"
import { rankText, teamDivision } from "@/lib/divisions"
import { describeAdjustment } from "@/lib/format/adjustments"
import { teamColorVars } from "@/lib/format/color"
import { record, signed } from "@/lib/format/numbers"
import { AdjustedCallout } from "@/components/game/adjusted-note"
import { Stat } from "@/components/ui/stat"

import { TeamLogo } from "./team-logo"

/**
 * Team identity and its headline numbers: logo, then the Power rank and name ("#5 Miami",
 * "#5 FCS" for FCS teams; Phase 13.7). A solid band in the team's (contrast-checked)
 * color tops the panel and casts light in that color (#137); no gradients.
 */
export function TeamHeader({ profile }: { profile: TeamProfile }) {
  const { team, ratings: r } = profile
  const division = teamDivision(team)
  const rank = (n: number | null | undefined) => (n ? rankText(n, division) : "—")
  const stats = r
    ? [
        { label: "Power rank", value: rank(r.rank_power) },
        { label: "Résumé rank", value: rank(r.rank_resume) },
        { label: "Rating", value: signed(r.rating) },
        {
          label: "Predictive",
          value:
            r.predictive_rating == null
              ? "—"
              : `${signed(r.predictive_rating)}${r.predictive_rank ? ` (${rank(r.predictive_rank)})` : ""}`,
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
      <div aria-hidden className="tsi-team-light tsi-glow-below h-2 bg-(--light)" />
      <div className="space-y-5 p-5">
        <div className="flex items-center gap-4">
          <TeamLogo team={team} size={72} priority />
          <div className="min-w-0">
            <h1 className="text-4xl leading-tight font-bold font-stretch-condensed sm:text-5xl">
              {r?.rank_power ? (
                <>
                  <span className="text-muted-foreground tabular-nums">
                    {rankText(r.rank_power, division)}
                  </span>{" "}
                </>
              ) : null}
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
              <Stat key={s.label} label={s.label} value={s.value} />
            ))}
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">
            TSI rates FBS teams, and FCS teams from 2022 on, so this team has no rating.
          </p>
        )}
        {r && (
          <p className="text-xs text-muted-foreground">
            Rating and ranks use this season&apos;s games only; the predictive rating also weighs
            the preseason prior and drives TSI&apos;s game predictions.
          </p>
        )}
        {profile.adjustments.length > 0 && (
          <AdjustedCallout>
            {profile.adjustments.map(describeAdjustment).join("; ")}, points per game. TSI&apos;s
            predictions for its upcoming games include this; the ratings and ranks above don&apos;t.
          </AdjustedCallout>
        )}
      </div>
    </section>
  )
}
