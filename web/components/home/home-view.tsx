"use client"

import { useState } from "react"

import type { GameOfWeekView, RankingType, TopTeam } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { cfb } from "@/lib/routes"

import { GameOfWeekCard } from "./game-of-week"
import { type HomeStatus, RankingTabs } from "./ranking-tabs"
import { RankingsRail } from "./rankings-rail"

type PerType<T> = Record<RankingType, T>
type Pick = { pick: GameOfWeekView | null; when: string | null }
export type HomePicks = Record<Division, PerType<Pick>>

type Props = {
  rails: Record<Division, PerType<TopTeam[]>>
  picks: HomePicks
  status: HomeStatus // the week and when the rankings were last updated
}

const LABEL: Record<RankingType, string> = { power: "Power", resume: "Résumé" }

/**
 * The home page (Phase 13.4): the FBS and FCS games of the week in the middle, each
 * division's Top 25 in a side rail. One ranking choice (Power or Résumé) drives both. On
 * desktop the three columns share one height, so the cards and the lists end level.
 * Phones: games first, then the lists.
 */
export function HomeView({ rails, picks, status }: Props) {
  const [type, setType] = useState<RankingType>("resume") // Résumé first (owner, 2026-11-23, #159)
  // Phones and tablets: one division at a time (#163), its whole Top 25 (owner, #197).
  const [division, setDivision] = useState<Division>("fbs")
  const only = (d: Division) => (d === division ? "" : "max-lg:hidden")
  return (
    <div className="space-y-6">
      <RankingTabs
        value={type}
        onChange={setType}
        division={division}
        onDivision={setDivision}
        status={status}
      />
      <div
        id="home-rankings"
        className="grid gap-8 lg:grid-cols-[15.5rem_minmax(0,1fr)_15.5rem] xl:grid-cols-[18rem_minmax(0,1fr)_18rem]"
      >
        <div className="flex min-w-0 flex-col gap-6 lg:col-start-2 lg:row-start-1">
          <GameOfWeekCard
            division="fbs"
            teams={rails.fbs[type]}
            className={`flex-1 ${only("fbs")}`}
            {...picks.fbs[type]}
          />
          <GameOfWeekCard
            division="fcs"
            teams={rails.fcs[type]}
            className={`flex-1 ${only("fcs")}`}
            {...picks.fcs[type]}
          />
        </div>
        {(["fbs", "fcs"] as const).map((d) => (
          <div
            key={d}
            className={`min-w-0 lg:row-start-1 ${d === "fbs" ? "lg:col-start-1" : "lg:col-start-3"} ${only(d)}`}
          >
            <RankingsRail
              id={d}
              title={`${d.toUpperCase()} ${LABEL[type]} Top 25`}
              teams={rails[d][type]}
              href={cfb.rankings(d)}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
