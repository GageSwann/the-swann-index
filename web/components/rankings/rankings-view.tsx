"use client"

import { type ReactNode, useMemo, useState, useSyncExternalStore } from "react"

import { Segmented } from "@/components/ui/segmented"
import type { RankedTeam, RankingType } from "@/lib/api/types"
import { benchmarkName, type DivisionView } from "@/lib/divisions"

import { Movers } from "./movers"
import { RankingsList } from "./rankings-list"
import { RankingsTable } from "./rankings-table"

function explainer(
  type: RankingType,
  division: DivisionView,
  benchmarkRank: number | null,
): string {
  if (type === "resume") {
    const team = benchmarkName(division === "fcs" ? "fcs" : "fbs", benchmarkRank)
    return `How hard would it be for a typical ${team} to match this record against this schedule? Re-evaluated daily as opponents' seasons play out.`
  }
  return division === "all"
    ? "FBS and FCS teams on one scale: points better or worse than an average FBS team, from this season's games only. Résumé ranks stay within each division."
    : "How good each team is right now, from this season's games only: no preseason expectations, no past seasons."
}

// The ranking in the address (#204): `#power` opens Power, so a "Full Rankings" link next to
// a Power list lands on Power. Read from the URL, not the server, so the page stays one
// cached page; a hash change (or a page change that brings one) re-reads it.
function subscribeHash(onChange: () => void): () => void {
  window.addEventListener("hashchange", onChange)
  return () => window.removeEventListener("hashchange", onChange)
}
const readHash = () => window.location.hash
const noHash = () => ""

// Columns a view leaves out: the season sim is FBS only (decision #111), and SOR is
// measured against each division's own benchmark, so it isn't comparable across them.
const HIDDEN: Record<DivisionView, string[]> = {
  fbs: ["division"],
  fcs: ["division", "projected_wins", "conference_title"],
  all: ["sor", "projected_wins", "conference_title"],
}

type Props = {
  nav: ReactNode // the FBS / FCS / All links, first in the controls row
  power: RankedTeam[]
  resume: RankedTeam[] | null // null: no Résumé view ("all")
  since: string | null
  division: DivisionView
  benchmarkRank: number | null // the Résumé benchmark the run used (#133)
}

export function RankingsView({ nav, power, resume, since, division, benchmarkRank }: Props) {
  // Résumé first (owner, #159); "all" has no Résumé view, so it opens on Power. `#power` in
  // the address opens Power (#204). A choice made here holds while the address it set stays.
  const hash = useSyncExternalStore(subscribeHash, readHash, noHash)
  const [picked, setPicked] = useState<{ type: RankingType; hash: string } | null>(null)
  const fromHash: RankingType = hash === "#power" || resume === null ? "power" : "resume"
  const type = picked?.hash === hash ? picked.type : fromHash
  const setType = (next: RankingType) => {
    // Keep the address in step, so a copied link opens the same ranking.
    const nextHash = next === "power" && resume !== null ? "#power" : ""
    window.history.replaceState(window.history.state, "", `${window.location.pathname}${nextHash}`)
    setPicked({ type: next, hash: nextHash })
  }
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
      (type === "power" || resume === null ? power : resume).filter((t) =>
        conference ? t.team.conference === conference : true,
      ),
    [type, conference, power, resume],
  )
  const teams = useMemo(
    () => pool.filter((t) => scope === "all" || conference !== "" || t.rank <= 25),
    [pool, scope, conference],
  )

  return (
    // A column, so on phones the explainer can follow the list (#164).
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        {/* Phones: division and ranking share the first row, the filters the second. */}
        <div className="flex w-full flex-wrap items-center justify-between gap-3 sm:w-auto sm:justify-start sm:gap-4">
          {nav}
          {resume !== null && (
            <Segmented
              label="Ranking"
              value={type}
              onChange={setType}
              options={[
                { value: "resume", label: "Résumé" },
                { value: "power", label: "Power" },
              ]}
            />
          )}
        </div>
        <div className="flex w-full items-center justify-between gap-3 sm:w-auto sm:justify-start sm:gap-4">
          <Segmented
            label="Teams shown"
            value={scope}
            onChange={setScope}
            options={[
              { value: "top25", label: "Top 25" },
              { value: "all", label: `All ${power.length}` },
            ]}
          />
          <label className="flex min-w-0 items-center gap-2 text-sm text-muted-foreground">
            <span className="max-sm:sr-only">Conference</span>
            <select
              value={conference}
              onChange={(e) => setConference(e.target.value)}
              className="max-w-44 min-w-0 rounded-md border border-border bg-card px-2 py-1.5 text-foreground"
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
      </div>
      <p className="max-w-[75ch] text-sm text-muted-foreground max-sm:order-last max-sm:text-xs">
        {explainer(type, division, benchmarkRank)}
      </p>
      {/* Wide screens: the movers panel beside the table; below it otherwise. */}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_19rem] xl:items-start">
        {teams.length > 0 ? (
          <>
            <div className="sm:hidden">
              <RankingsList teams={teams} type={resume === null ? "power" : type} since={since} />
            </div>
            <div className="max-sm:hidden">
              <RankingsTable key={type} teams={teams} since={since} hidden={HIDDEN[division]} />
            </div>
          </>
        ) : (
          <p className="text-muted-foreground">No ranked teams match these filters.</p>
        )}
        {since && <Movers teams={pool} since={since} />}
      </div>
    </div>
  )
}
