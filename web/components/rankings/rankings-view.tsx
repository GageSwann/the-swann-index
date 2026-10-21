"use client"

import { useMemo, useState } from "react"

import { Segmented } from "@/components/ui/segmented"
import type { RankedTeam, RankingType } from "@/lib/api/types"

import { RankingsTable } from "./rankings-table"

const EXPLAINER: Record<RankingType, string> = {
  power:
    "How good each team is right now, from this season's games only: no preseason expectations, no past seasons.",
  resume:
    "How hard would it be for a typical #12 team to match this record against this schedule? Re-evaluated daily as opponents' seasons play out.",
}

type Props = { power: RankedTeam[]; resume: RankedTeam[] }

export function RankingsView({ power, resume }: Props) {
  const [type, setType] = useState<RankingType>("power")
  const [scope, setScope] = useState<"top25" | "all">("top25")
  const [conference, setConference] = useState("")

  const conferences = useMemo(
    () => [...new Set(power.map((t) => t.team.conference).filter((c): c is string => !!c))].sort(),
    [power],
  )
  const teams = useMemo(() => {
    const source = type === "power" ? power : resume
    return source.filter(
      (t) =>
        (conference ? t.team.conference === conference : true) &&
        (scope === "all" || conference !== "" || t.rank <= 25),
    )
  }, [type, scope, conference, power, resume])

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
      {teams.length > 0 ? (
        <RankingsTable key={type} teams={teams} />
      ) : (
        <p className="text-muted-foreground">No ranked teams match these filters.</p>
      )}
    </div>
  )
}
