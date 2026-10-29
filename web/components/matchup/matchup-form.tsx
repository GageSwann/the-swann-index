import Link from "next/link"

import type { TeamRef } from "@/lib/api/types"
import { type MatchupPick, matchupQuery } from "@/lib/matchup"

type Props = { teams: TeamRef[]; pick: MatchupPick }

/**
 * Pick two teams. A plain GET form: it works without JavaScript and the result's URL is
 * shareable (`/matchup?away=…&home=…&neutral=1`).
 */
export function MatchupForm({ teams, pick }: Props) {
  const { away, home, neutral } = pick
  const byConference = new Map<string, TeamRef[]>()
  for (const t of teams) {
    const key = t.conference ?? "Other"
    byConference.set(key, [...(byConference.get(key) ?? []), t])
  }
  const groups = [...byConference.entries()].sort(([a], [b]) => a.localeCompare(b))
  const swap = away && home ? `/matchup?${matchupQuery({ away: home, home: away, neutral })}` : null

  return (
    <form
      action="/matchup"
      method="get"
      className="space-y-4 rounded-md border border-border bg-card p-5"
    >
      <div className="grid gap-4 sm:grid-cols-[1fr_auto_1fr] sm:items-end">
        <TeamSelect name="away" label="Away team" value={away} groups={groups} />
        <span className="hidden pb-2.5 text-sm text-muted-foreground sm:block">at</span>
        <TeamSelect name="home" label="Home team" value={home} groups={groups} />
      </div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <label className="flex min-h-8 items-center gap-2 text-sm">
          <input
            type="checkbox"
            name="neutral"
            value="1"
            defaultChecked={neutral}
            className="size-4 accent-primary"
          />
          Neutral site (no home-field edge)
        </label>
        <button
          type="submit"
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
        >
          Predict
        </button>
        {swap && (
          <Link href={swap} className="text-sm text-primary underline-offset-4 hover:underline">
            Swap home and away
          </Link>
        )}
      </div>
    </form>
  )
}

function TeamSelect({
  name,
  label,
  value,
  groups,
}: {
  name: string
  label: string
  value?: string
  groups: [string, TeamRef[]][]
}) {
  return (
    <label className="flex flex-col gap-1.5 text-sm text-muted-foreground">
      {label}
      <select
        name={name}
        defaultValue={value ?? ""}
        required
        className="min-h-10 rounded-md border border-border bg-background px-2 text-base text-foreground"
      >
        <option value="" disabled>
          Choose a team
        </option>
        {groups.map(([conference, list]) => (
          <optgroup key={conference} label={conference}>
            {list.map((t) => (
              <option key={t.slug} value={t.slug}>
                {t.school}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
  )
}
