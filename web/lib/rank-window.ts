/**
 * A team and its neighbors in one ranking (#199): the team with two on either side, or at
 * the ends the first or last `size` teams. Pure; ranks come from the API.
 */
export function rankWindow<T>(
  rows: T[],
  rankOf: (row: T) => number | null | undefined,
  isTeam: (row: T) => boolean,
  size = 5,
): { row: T; rank: number }[] {
  const ranked = rows
    .flatMap((row) => {
      const rank = rankOf(row)
      return rank == null ? [] : [{ row, rank }]
    })
    .sort((a, b) => a.rank - b.rank)
  const at = ranked.findIndex((r) => isTeam(r.row))
  if (at < 0) return []
  const start = Math.min(Math.max(at - Math.floor(size / 2), 0), Math.max(ranked.length - size, 0))
  return ranked.slice(start, start + size)
}
