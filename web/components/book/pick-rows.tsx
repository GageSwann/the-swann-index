import Link from "next/link"

import { HeadCell } from "@/components/ui/head-cell"
import type { LedgerPick } from "@/lib/api/types"
import { percent, signed } from "@/lib/format/numbers"
import { american } from "@/lib/format/odds"
import { describePick, units } from "@/lib/format/picks"
import { formatShortDay } from "@/lib/format/time"
import { cn } from "@/lib/utils"

const kickoff = (p: LedgerPick) => (p.kickoff ? formatShortDay(p.kickoff) : "TBA")
const rowKey = (p: LedgerPick) => `${p.game_id}-${p.pick.market}`

/** Picks as a table (from `sm` up). */
export function PickTable({ picks }: { picks: LedgerPick[] }) {
  return (
    <div className="hidden rounded-md border border-border sm:block">
      <table className="w-full text-sm">
        <thead className="bg-card text-muted-foreground">
          <tr className="border-b border-border">
            <HeadCell>Kickoff</HeadCell>
            <HeadCell>Game</HeadCell>
            <HeadCell>Pick</HeadCell>
            <HeadCell
              align="right"
              title="TSI's (shrunk) win chance minus the break-even chance at this price"
            >
              Edge
            </HeadCell>
            <HeadCell align="right" title="Flat stake; ¼ Kelly stake">
              Stake
            </HeadCell>
            <HeadCell>Result</HeadCell>
            <HeadCell
              align="right"
              title="Closing-line value: how far the line moved toward TSI's side"
            >
              CLV
            </HeadCell>
          </tr>
        </thead>
        <tbody>
          {picks.map((p) => (
            <tr key={rowKey(p)} className="border-b border-border last:border-0">
              <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">{kickoff(p)}</td>
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
                  <span className="text-muted-foreground"> / {p.pick.kelly_units.toFixed(1)}u</span>
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
  )
}

/** Picks as stacked rows (phones). */
export function PickList({ picks }: { picks: LedgerPick[] }) {
  return (
    <ol className="divide-y divide-border rounded-md border border-border text-sm sm:hidden">
      {picks.map((p) => (
        <li key={rowKey(p)} className="space-y-1 px-3 py-2">
          <div className="flex items-baseline justify-between gap-3">
            <PickText pick={p} />
            <Status pick={p} />
          </div>
          <GameLink pick={p} />
          <p className="flex justify-between gap-3 text-muted-foreground tabular-nums">
            <span>{kickoff(p)}</span>
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
  const result = p.pick.result
  return (
    <span className={cn(result === "win" ? "text-up" : result === "loss" && "text-down")}>
      {result === "win" ? "✔ Won" : result === "loss" ? "✘ Lost" : "Push"}{" "}
      <span className="tabular-nums">{units(p.pick.units_won ?? 0)}</span>
    </span>
  )
}

function Clv({ pick: p }: { pick: LedgerPick }) {
  const clv = p.pick.clv
  if (clv == null) return <span className="text-muted-foreground">—</span>
  return (
    <span className={cn(clv > 0 ? "text-up" : clv < 0 && "text-down")}>
      {p.pick.market === "ml" ? `${signed(clv * 100)}%` : signed(clv)}
    </span>
  )
}
