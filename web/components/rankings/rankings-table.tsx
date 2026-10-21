"use client"

import {
  createColumnHelper,
  createSortedRowModel,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_basic,
  tableFeatures,
  useTable,
  type SortingState,
} from "@tanstack/react-table"
import { useRouter } from "next/navigation"
import { useState } from "react"

import { TeamLink } from "@/components/team/team-link"
import type { RankedTeam } from "@/lib/api/types"
import { percent, record, signed } from "@/lib/format/numbers"
import { cn } from "@/lib/utils"

import { RankChange } from "./rank-change"

const features = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  sortFns: { basic: sortFn_basic, alphanumeric: sortFn_alphanumeric },
})
const col = createColumnHelper<typeof features, RankedTeam>()

const numeric = { sortFn: "basic", sortUndefined: "last" } as const

const columns = col.columns([
  col.accessor("rank", {
    header: "Rank",
    ...numeric,
    cell: ({ row }) => (
      <span className="flex items-baseline gap-1.5">
        <span className="text-lg font-bold font-stretch-condensed">{row.original.rank}</span>
        {row.original.provisional && (
          <span className="text-xs text-muted-foreground" title="Fewer than 4 games played">
            provisional
          </span>
        )}
      </span>
    ),
  }),
  col.accessor((t) => (t.previous_rank === null ? undefined : t.previous_rank - t.rank), {
    id: "change",
    header: "Δ",
    ...numeric,
    sortDescFirst: true,
    cell: ({ row }) => (
      <RankChange rank={row.original.rank} previous={row.original.previous_rank} />
    ),
  }),
  col.accessor((t) => t.team.school, {
    id: "team",
    header: "Team",
    sortFn: "alphanumeric",
    cell: ({ row }) => <TeamLink team={row.original.team} />,
  }),
  col.accessor((t) => (t.wins + t.ties / 2) / Math.max(1, t.wins + t.losses + t.ties), {
    id: "record",
    header: "Record",
    ...numeric,
    sortDescFirst: true,
    cell: ({ row }) => record(row.original.wins, row.original.losses, row.original.ties),
  }),
  col.accessor("rating", {
    header: "Rating",
    ...numeric,
    sortDescFirst: true,
    cell: ({ getValue }) => <span className="font-semibold">{signed(getValue())}</span>,
  }),
  col.accessor("off_rating", {
    header: "Off",
    ...numeric,
    sortDescFirst: true,
    cell: ({ row }) => <SideRating value={row.original.off_rating} rank={row.original.off_rank} />,
  }),
  col.accessor("def_rating", {
    header: "Def",
    ...numeric,
    sortDescFirst: true,
    cell: ({ row }) => <SideRating value={row.original.def_rating} rank={row.original.def_rank} />,
  }),
  col.accessor((t) => t.sos ?? undefined, {
    id: "sos",
    header: "SOS",
    ...numeric,
    sortDescFirst: true,
    cell: ({ getValue }) => {
      const v = getValue()
      return v === undefined ? "—" : signed(v)
    },
  }),
  col.accessor((t) => t.sor ?? undefined, {
    id: "sor",
    header: "SOR",
    ...numeric,
    cell: ({ getValue }) => {
      const v = getValue()
      return v === undefined ? "—" : percent(v)
    },
  }),
])

const HEADER_HELP: Record<string, string> = {
  change: "Rank change since yesterday's ratings",
  rating: "Points better than an average FBS team on a neutral field",
  off_rating: "Offense in points per game vs. average (rank among FBS)",
  def_rating: "Defense in points per game vs. average; higher is better (rank)",
  sos: "Average current rating of opponents played",
  sor: "Chance a typical #12 team would match this record against this schedule (lower is more impressive)",
}

export function RankingsTable({ teams }: { teams: RankedTeam[] }) {
  const router = useRouter()
  const [sorting, setSorting] = useState<SortingState>([{ id: "rank", desc: false }])
  const table = useTable({
    features,
    columns,
    data: teams,
    state: { sorting },
    onSortingChange: setSorting,
  })

  return (
    <div className="max-h-[75vh] overflow-auto rounded-md border border-border">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead className="sticky top-0 z-10 bg-card">
          {table.getHeaderGroups().map((group) => (
            <tr key={group.id} className="border-b border-border">
              {group.headers.map((header) => {
                const sorted = header.column.getIsSorted()
                return (
                  <th
                    key={header.id}
                    scope="col"
                    title={HEADER_HELP[header.id]}
                    aria-sort={
                      sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : undefined
                    }
                    className={cn(
                      "px-3 py-2.5 text-left font-medium text-muted-foreground",
                      header.id === "team" ? "w-full" : "whitespace-nowrap",
                    )}
                  >
                    <button
                      type="button"
                      onClick={header.column.getToggleSortingHandler()}
                      className={cn("inline-flex items-center gap-1", sorted && "text-foreground")}
                    >
                      <table.FlexRender header={header} />
                      <span aria-hidden className="text-xs">
                        {sorted === "asc" ? "▲" : sorted === "desc" ? "▼" : ""}
                      </span>
                    </button>
                  </th>
                )
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={(e) => {
                if (!(e.target instanceof Element && e.target.closest("a, button"))) {
                  router.push(`/teams/${row.original.team.slug}`)
                }
              }}
              className="cursor-pointer border-b border-border last:border-0 hover:bg-muted/60"
            >
              {row.getAllCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2 whitespace-nowrap">
                  <table.FlexRender cell={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SideRating({ value, rank }: { value: number; rank: number }) {
  return (
    <span>
      {signed(value)} <span className="text-xs text-muted-foreground">({rank})</span>
    </span>
  )
}
