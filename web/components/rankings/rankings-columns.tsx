import {
  createColumnHelper,
  createSortedRowModel,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_basic,
  tableFeatures,
} from "@tanstack/react-table"

import Link from "next/link"

import { TeamLink } from "@/components/team/team-link"
import type { RankedTeam } from "@/lib/api/types"
import { chance, percent, record, signed } from "@/lib/format/numbers"

import { RankChange } from "./rank-change"

// Rankings table columns (TanStack Table v9): sorting, cells and header help text.

export const features = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  sortFns: { basic: sortFn_basic, alphanumeric: sortFn_alphanumeric },
})
const col = createColumnHelper<typeof features, RankedTeam>()

const numeric = { sortFn: "basic", sortUndefined: "last" } as const

export const columns = col.columns([
  col.accessor("rank", {
    header: "Rank",
    ...numeric,
    cell: ({ row }) => (
      <span className="text-lg font-bold font-stretch-condensed">{row.original.rank}</span>
    ),
  }),
  col.accessor((t) => t.team.school, {
    id: "team",
    header: "Team",
    sortFn: "alphanumeric",
    cell: ({ row }) => (
      <span className="flex min-w-0 items-baseline gap-1.5">
        <TeamLink team={row.original.team} />
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
    cell: ({ getValue, row }) => {
      const v = getValue()
      if (v === undefined) return "—"
      return (
        <Link
          href={`/teams/${row.original.team.slug}#resume`}
          className="underline-offset-4 hover:underline"
          title="See how this résumé was built"
        >
          {percent(v)}
        </Link>
      )
    },
  }),
  col.accessor((t) => t.projected_wins ?? undefined, {
    id: "projected_wins",
    header: "Proj. W",
    ...numeric,
    sortDescFirst: true,
    cell: ({ getValue, row }) => {
      const v = getValue()
      if (v === undefined) return "—"
      return (
        <Link
          href={`/teams/${row.original.team.slug}#projection`}
          className="underline-offset-4 hover:underline"
          title="See the projected record"
        >
          {v.toFixed(1)}
        </Link>
      )
    },
  }),
  col.accessor((t) => t.conference_title_prob ?? undefined, {
    id: "conference_title",
    header: "Conf",
    ...numeric,
    sortDescFirst: true,
    cell: ({ getValue }) => {
      const v = getValue()
      return v === undefined ? "—" : chance(v)
    },
  }),
])

export const HEADER_HELP: Record<string, string> = {
  change: "Rank change over the past week",
  rating: "Points better than an average FBS team on a neutral field",
  off_rating: "Offense in points per game vs. average (rank among FBS)",
  def_rating: "Defense in points per game vs. average; higher is better (rank)",
  sos: "Average current rating of opponents played",
  sor: "Chance a typical #12 team would match this record against this schedule (lower is more impressive)",
  projected_wins:
    "Average final wins in 10,000 simulated seasons, including a conference title game",
  conference_title: "Chance of winning the conference title (simulated)",
}

function SideRating({ value, rank }: { value: number; rank: number }) {
  return (
    <span>
      {signed(value)} <span className="text-xs text-muted-foreground">({rank})</span>
    </span>
  )
}
