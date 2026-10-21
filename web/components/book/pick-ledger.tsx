"use client"

import Link from "next/link"
import { useState } from "react"

import { Segmented } from "@/components/ui/segmented"
import type { LedgerPick } from "@/lib/api/types"
import { percent, signed } from "@/lib/format/numbers"
import { american } from "@/lib/format/odds"
import { describePick, MARKET_LABEL, units } from "@/lib/format/picks"
import { cn } from "@/lib/utils"

type Market = "all" | "spread" | "total" | "ml"
type Tier = "all" | "1" | "2" | "3"
type Outcome = "all" | "open" | "win" | "loss" | "push"

// Kickoff is formatted from the API's ISO time in US Eastern on server and client alike.
const kickoffFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  weekday: "short",
  month: "short",
  day: "numeric",
})

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
        <Segmented
          label="Market"
          value={market}
          onChange={setMarket}
          options={(["all", "spread", "total", "ml"] as const).map((m) => ({
            value: m,
            label: m === "all" ? "All" : MARKET_LABEL[m],
          }))}
        />
        <Segmented
          label="Tier"
          value={tier}
          onChange={setTier}
          options={[
            { value: "all", label: "All" },
            { value: "1", label: "★" },
            { value: "2", label: "★★" },
            { value: "3", label: "★★★" },
          ]}
        />
        <Segmented
          label="Result"
          value={outcome}
          onChange={setOutcome}
          options={[
            { value: "all", label: "All" },
            { value: "open", label: "Not graded" },
            { value: "win", label: "Won" },
            { value: "loss", label: "Lost" },
            { value: "push", label: "Push" },
          ]}
        />
      </div>
      <p className="text-sm text-muted-foreground" aria-live="polite">
        {shown.length} of {picks.length} picks
      </p>
      {shown.length === 0 ? (
        <p className="text-muted-foreground">No picks match these filters.</p>
      ) : (
        <>
          <div className="hidden rounded-md border border-border sm:block">
            <table className="w-full text-sm">
              <thead className="bg-card text-muted-foreground">
                <tr className="border-b border-border">
                  <th scope="col" className="px-3 py-2 text-left font-medium">
                    Kickoff
                  </th>
                  <th scope="col" className="px-3 py-2 text-left font-medium">
                    Game
                  </th>
                  <th scope="col" className="px-3 py-2 text-left font-medium">
                    Pick
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-right font-medium"
                    title="TSI's (shrunk) win chance minus the break-even chance at this price"
                  >
                    Edge
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-right font-medium"
                    title="Flat stake; ¼ Kelly stake"
                  >
                    Stake
                  </th>
                  <th scope="col" className="px-3 py-2 text-left font-medium">
                    Result
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-right font-medium"
                    title="Closing-line value: how far the line moved toward TSI's side"
                  >
                    CLV
                  </th>
                </tr>
              </thead>
              <tbody>
                {shown.map((p) => (
                  <tr
                    key={`${p.game_id}-${p.pick.market}`}
                    className="border-b border-border last:border-0"
                  >
                    <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                      {p.kickoff ? kickoffFormat.format(new Date(p.kickoff)) : "TBA"}
                    </td>
                    <td className="px-3 py-1">
                      <GameLink pick={p} />
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <PickText pick={p} />
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">{percent(p.pick.edge, 1)}</td>
                    <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                      1u
                      {p.pick.kelly_units != null && (
                        <span className="text-muted-foreground">
                          {" "}
                          / {p.pick.kelly_units.toFixed(1)}u
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <Status pick={p} />
                    </td>
                    <td className="px-3 py-2 text-right whitespace-nowrap tabular-nums">
                      <Clv pick={p} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ol className="divide-y divide-border rounded-md border border-border text-sm sm:hidden">
            {shown.map((p) => (
              <li key={`${p.game_id}-${p.pick.market}`} className="space-y-1 px-3 py-2">
                <div className="flex items-baseline justify-between gap-3">
                  <PickText pick={p} />
                  <Status pick={p} />
                </div>
                <GameLink pick={p} />
                <p className="flex justify-between gap-3 text-muted-foreground tabular-nums">
                  <span>{p.kickoff ? kickoffFormat.format(new Date(p.kickoff)) : "TBA"}</span>
                  <span>
                    edge {percent(p.pick.edge, 1)}
                    {p.pick.clv != null && (
                      <>
                        , CLV <Clv pick={p} />
                      </>
                    )}
                  </span>
                </p>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  )
}

function GameLink({ pick }: { pick: LedgerPick }) {
  return (
    <Link
      href={`/games/${pick.game_id}`}
      className="inline-flex min-h-8 items-center hover:underline"
    >
      {pick.away.school} at {pick.home.school}
    </Link>
  )
}

function PickText({ pick: p }: { pick: LedgerPick }) {
  return (
    <span className="font-semibold">
      <span className="text-primary" aria-label={`${p.pick.tier} star`}>
        {"★".repeat(p.pick.tier)}
      </span>{" "}
      {describePick(p.pick, p.home, p.away)}
      {p.pick.market !== "ml" && (
        <span className="font-normal text-muted-foreground"> {american(p.pick.odds)}</span>
      )}
    </span>
  )
}

/** Open (can still change), locked (kicked off, not graded), or the graded result. */
function Status({ pick: p }: { pick: LedgerPick }) {
  if (p.status === "open") return <span className="text-muted-foreground">Open</span>
  if (p.status === "pending") return <span className="text-muted-foreground">Locked</span>
  const won = p.pick.units_won ?? 0
  return (
    <span
      className={cn(p.pick.result === "win" ? "text-up" : p.pick.result === "loss" && "text-down")}
    >
      {p.pick.result === "win" ? "✔ Won" : p.pick.result === "loss" ? "✘ Lost" : "Push"}{" "}
      <span className="tabular-nums">{units(won)}</span>
    </span>
  )
}

function Clv({ pick: p }: { pick: LedgerPick }) {
  if (p.pick.clv == null) return <span className="text-muted-foreground">—</span>
  const text = p.pick.market === "ml" ? `${signed(p.pick.clv * 100)}%` : `${signed(p.pick.clv)}`
  return (
    <span className={cn(p.pick.clv > 0 ? "text-up" : p.pick.clv < 0 && "text-down")}>{text}</span>
  )
}
