import type { TeamProfile } from "@/lib/api/types"
import { describeAdjustment } from "@/lib/format/adjustments"
import { teamColorVars } from "@/lib/format/color"
import { record } from "@/lib/format/numbers"
import { AdjustedCallout } from "@/components/game/adjusted-note"
import { SportTag } from "@/components/ui/sport-tag"

import { TeamLogo } from "./team-logo"

/**
 * Team identity and its headline numbers. A solid band in the team's (contrast-checked)
 * color tops the panel (#137, flat since #168). The name is the school and mascot ("Utah
 * Utes"), then a CFB tag (the sport's page, as CBB and CBASE get their own), division and
 * conference, and the record with the conference record in parentheses (owner, #199). The
 * ranks and ratings moved out of the header (owner, #199): the rankings panels and Profile
 * below show them.
 */
export function TeamHeader({ profile }: { profile: TeamProfile }) {
  const { team, ratings: r } = profile
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
              {[team.school, team.mascot].filter(Boolean).join(" ")}
            </h1>
            <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-muted-foreground">
              <SportTag label="CFB" />
              <span>
                {[team.division?.toUpperCase(), team.conference].filter(Boolean).join(" · ")}
              </span>
              <span aria-hidden className="max-sm:hidden">
                ·
              </span>
              <span>
                <span className="font-semibold text-foreground">
                  {record(profile.wins, profile.losses, profile.ties)}
                </span>
                {profile.conf_record && (
                  <>
                    {" "}
                    (
                    {record(
                      profile.conf_record.wins,
                      profile.conf_record.losses,
                      profile.conf_record.ties,
                    )}
                    )
                  </>
                )}{" "}
                in {profile.season}
              </span>
            </p>
            {r?.provisional && (
              <p className="mt-1 text-sm text-muted-foreground">
                Provisional rating (fewer than 4 games)
              </p>
            )}
          </div>
        </div>
        {!r && (
          <p className="text-sm text-muted-foreground">
            TSI rates FBS teams, and FCS teams from 2022 on, so this team has no rating.
          </p>
        )}
        {profile.adjustments.length > 0 && (
          <AdjustedCallout>
            {profile.adjustments.map(describeAdjustment).join("; ")}, points per game. TSI&apos;s
            predictions for its upcoming games include this; its ratings and ranks don&apos;t.
          </AdjustedCallout>
        )}
      </div>
    </section>
  )
}
