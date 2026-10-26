/** Movement over the past week (decision #79): ▲ up, ▼ down, – no change, "new" if unranked. */
export function RankChange({ rank, previous }: { rank: number; previous: number | null }) {
  if (previous === null) {
    return <span className="text-xs text-muted-foreground">new</span>
  }
  const moved = previous - rank
  if (moved === 0) {
    return (
      <span className="text-muted-foreground" aria-label="No change over the past week">
        –
      </span>
    )
  }
  const up = moved > 0
  return (
    <span
      className={up ? "text-up" : "text-down"}
      aria-label={`${up ? "Up" : "Down"} ${Math.abs(moved)} over the past week`}
    >
      {up ? "▲" : "▼"}
      {Math.abs(moved)}
    </span>
  )
}
