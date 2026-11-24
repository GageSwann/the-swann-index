"use client"

import type { ReactNode } from "react"

import { Segmented } from "@/components/ui/segmented"
import type { RankingType } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"

export type HomeStatus = {
  week: string // "Week 13", "Bowl season", "Preseason"
  season: number
  updated: string | null // "Nov 23, 8:52 AM EST"
}

// Desktop names the rankings in full ("Résumé Rankings"); phones keep it short (owner).
const TYPES: { value: RankingType; label: ReactNode }[] = [
  {
    value: "resume",
    label: (
      <>
        Résumé<span className="max-lg:hidden"> Rankings</span>
      </>
    ),
  },
  {
    value: "power",
    label: (
      <>
        Power<span className="max-lg:hidden"> Rankings</span>
      </>
    ),
  },
]

const DIVISIONS: { value: Division; label: string }[] = [
  { value: "fbs", label: "FBS" },
  { value: "fcs", label: "FCS" },
]

/**
 * The home page's header (owner, 2026-11-24, #197): a "WEEK 13 · 2026 SEASON" label over the
 * "College Football" title and when the rankings were last updated; beside it (below on
 * phones, full width) the ranking that drives the Top 25 lists and the games of the week,
 * and on phones and tablets the division shown (desktop shows both), in the Rankings page's
 * segmented style.
 */
export function RankingTabs({
  value,
  onChange,
  division,
  onDivision,
  status,
}: {
  value: RankingType
  onChange: (value: RankingType) => void
  division: Division
  onDivision: (value: Division) => void
  status: HomeStatus
}) {
  return (
    <div className="flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
          {status.week}
          <span aria-hidden> · </span>
          {status.season} season
        </p>
        <h1 className="mt-1.5 text-4xl leading-none font-bold font-stretch-condensed">
          College Football
        </h1>
        {status.updated && (
          <p className="mt-2 text-sm text-muted-foreground">Updated {status.updated}</p>
        )}
      </div>
      <div className="flex flex-col gap-2 max-lg:w-full lg:items-end">
        <div className="flex items-center gap-2.5">
          <Segmented
            label="Rank teams by"
            value={value}
            onChange={onChange}
            options={TYPES}
            controls="home-rankings"
            stretch
            className="max-lg:flex-[3]"
          />
          {/* Phones and tablets show one division at a time; desktop has room for both. */}
          <Segmented
            label="Division"
            value={division}
            onChange={onDivision}
            options={DIVISIONS}
            controls="home-rankings"
            stretch
            className="flex-[2] lg:hidden"
          />
        </div>
      </div>
    </div>
  )
}
