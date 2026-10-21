"use client"

import { type SortingState, useTable } from "@tanstack/react-table"
import { useRouter } from "next/navigation"
import { useState } from "react"

import type { RankedTeam } from "@/lib/api/types"
import { cn } from "@/lib/utils"

import { columns, features, HEADER_HELP } from "./rankings-columns"

// Rank and team stay put while the stat columns scroll under them on narrow screens.
const PINNED: Record<string, string> = {
  rank: "max-sm:sticky max-sm:left-0 w-19 min-w-19",
  team: "max-sm:sticky max-sm:left-19 max-sm:max-w-44 max-sm:shadow-[inset_-1px_0_0_var(--border)]",
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
      <table className="w-full min-w-180 border-collapse text-sm">
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
                      "bg-card px-3 py-1.5 text-left font-medium text-muted-foreground",
                      header.id === "team" ? "w-full" : "whitespace-nowrap",
                      PINNED[header.id],
                      PINNED[header.id] && "max-sm:z-20",
                    )}
                  >
                    <button
                      type="button"
                      onClick={header.column.getToggleSortingHandler()}
                      className={cn(
                        "inline-flex min-h-8 min-w-6 items-center gap-1",
                        sorted && "text-foreground",
                      )}
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
              className="group cursor-pointer border-b border-border last:border-0"
            >
              {row.getAllCells().map((cell) => (
                <td
                  key={cell.id}
                  className={cn(
                    // Opaque backgrounds so pinned cells cover the columns scrolling under them.
                    "bg-background px-3 py-2 whitespace-nowrap group-hover:bg-muted",
                    PINNED[cell.column.id],
                    PINNED[cell.column.id] && "max-sm:z-1",
                  )}
                >
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
