"use client"

import { useMemo, useState } from "react"

import { Segmented } from "@/components/ui/segmented"
import type { RankedTeam, RankingType } from "@/lib/api/types"

import { Movers } from "./movers"
import { RankingsTable } from "./rankings-table"

const EXPLAINER: Record<RankingType, string> = {
  power:
    "How good each team is right now, from this season's games only: no preseason expectations, no past seasons.",
  resume:
    "How hard would it be for a typical #12 team to match this record against this schedule? Re-evaluated daily as opponents' seasons play out.",
}

type Props = { power: RankedTeam[]; resume: RankedTeam[]; since: string | null }

export function RankingsView({ power, resume, since }: Props) {
  const [type, setType] = useState<RankingType>("power")
  const [scope, setScope] = useState<"top25" | "all">("top25")
  const [conference, setConference] = useState("")

  const conferences = useMemo(
    () => [...new Set(power.map((t) => t.team.conference).filter((c): c is string => !!c))].sort(),
    [power],
  )
  // The table follows every filter; the movers panel ignores Top 25 (moves inside the
  // Top 25 are usually small) but follows the ranking and conference.
  const pool = useMemo(
    () =>
      (type === "power" ? power : resume).filter((t) =>
        conference ? t.team.conference === conference : true,
      ),
    [type, conference, power, resume],
  )
  const teams = useMemo(
    () => pool.filter((t) => scope === "all" || conference !== "" || t.rank <= 25),
    [pool, scope, conference],
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <Segmented
          label="Ranking"
          value={type}
          onChange={setType}
          options={[
            { value: "power", label: "Power" },
            { value: "resume", label: "Résumé" },
          ]}
        />
        <Segmented
          label="Teams shown"
          value={scope}
          onChange={setScope}
          options={[
            { value: "top25", label: "Top 25" },
            { value: "all", label: `All ${power.length}` },
          ]}
        />
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          Conference
          <select
            value={conference}
            onChange={(e) => setConference(e.target.value)}
            className="rounded-md border border-border bg-card px-2 py-1.5 text-foreground"
          >
            <option value="">All conferences</option>
            {conferences.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="max-w-[75ch] text-sm text-muted-foreground">{EXPLAINER[type]}</p>
      {/* Wide screens: the movers panel beside the table; below it otherwise. */}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_19rem] xl:items-start">
        {teams.length > 0 ? (
          <RankingsTable key={type} teams={teams} since={since} />
        ) : (
          <p className="text-muted-foreground">No ranked teams match these filters.</p>
        )}
        {since && <Movers teams={pool} since={since} />}
      </div>
    </div>
  )
}
