"use client"

import { useState } from "react"

import { Segmented } from "@/components/ui/segmented"
import type { LedgerPick } from "@/lib/api/types"
import { MARKET_LABEL } from "@/lib/format/picks"

import { PickList, PickTable } from "./pick-rows"

type Market = "all" | "spread" | "total" | "ml"
type Tier = "all" | "1" | "2" | "3"
type Outcome = "all" | "open" | "win" | "loss" | "push"

const MARKETS = (["all", "spread", "total", "ml"] as const).map((m) => ({
  value: m,
  label: m === "all" ? "All" : MARKET_LABEL[m],
}))
const TIERS: { value: Tier; label: string }[] = [
  { value: "all", label: "All" },
  { value: "1", label: "★" },
  { value: "2", label: "★★" },
  { value: "3", label: "★★★" },
]
const OUTCOMES: { value: Outcome; label: string }[] = [
  { value: "all", label: "All" },
  { value: "open", label: "Not graded" },
  { value: "win", label: "Won" },
  { value: "loss", label: "Lost" },
  { value: "push", label: "Push" },
]

/** Every published pick, newest kickoff first, filterable by market, tier and result. */
export function PickLedger({ picks }: { picks: LedgerPick[] }) {
  const [market, setMarket] = useState<Market>("all")
  const [tier, setTier] = useState<Tier>("all")
  const [outcome, setOutcome] = useState<Outcome>("all")

  const shown = picks.filter(
    (p) =>
      (market === "all" || p.pick.market === market) &&
      (tier === "all" || p.pick.tier === Number(tier)) &&
      (outcome === "all" ||
        (outcome === "open" ? p.status !== "graded" : p.pick.result === outcome)),
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <Segmented label="Market" value={market} onChange={setMarket} options={MARKETS} />
        <Segmented label="Tier" value={tier} onChange={setTier} options={TIERS} />
        <Segmented label="Result" value={outcome} onChange={setOutcome} options={OUTCOMES} />
      </div>
      <p className="text-sm text-muted-foreground" aria-live="polite">
        {shown.length} of {picks.length} picks
      </p>
      {shown.length === 0 ? (
        <p className="text-muted-foreground">No picks match these filters.</p>
      ) : (
        <>
          <PickTable picks={shown} />
          <PickList picks={shown} />
        </>
      )}
    </div>
  )
}
